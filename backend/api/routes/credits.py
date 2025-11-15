"""Credits management API routes"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from backend.database.mongodb import mongodb_client
from backend.api.routes.auth import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credits", tags=["credits"])


class CreditPurchase(BaseModel):
    amount: float
    payment_method: Optional[str] = "manual"


class CreditDeduction(BaseModel):
    amount: float
    reason: str
    metadata: Optional[dict] = None


async def get_user_credits(email: str) -> float:
    """Get user's current credit balance"""
    db = mongodb_client.db
    user = await db.users.find_one({"email": email}, {"_id": 0})
    return user.get("credit_balance", 0.0)


async def add_credits(email: str, amount: float, reason: str, metadata: dict = None):
    """Add credits to user account"""
    db = mongodb_client.db
    
    # Update user balance
    result = await db.users.update_one(
        {"email": email},
        {
            "$inc": {"credit_balance": amount},
            "$set": {"updated_at": datetime.utcnow().isoformat()}
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    # Log transaction
    transaction = {
        "user_email": email,
        "type": "credit",
        "amount": amount,
        "reason": reason,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat(),
        "balance_after": await get_user_credits(email)
    }
    
    await db.credit_transactions.insert_one(transaction)
    
    return transaction


async def deduct_credits(email: str, amount: float, reason: str, metadata: dict = None):
    """Deduct credits from user account"""
    db = mongodb_client.db
    
    # Check balance
    current_balance = await get_user_credits(email)
    if current_balance < amount:
        raise HTTPException(
            status_code=402,
            detail=f"Yetersiz kredi. Mevcut: {current_balance:.2f}, Gerekli: {amount:.2f}"
        )
    
    # Update user balance
    result = await db.users.update_one(
        {"email": email},
        {
            "$inc": {"credit_balance": -amount},
            "$set": {"updated_at": datetime.utcnow().isoformat()}
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    # Log transaction
    transaction = {
        "user_email": email,
        "type": "debit",
        "amount": -amount,
        "reason": reason,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat(),
        "balance_after": await get_user_credits(email)
    }
    
    await db.credit_transactions.insert_one(transaction)
    
    return transaction


@router.get("/balance")
async def get_balance(current_user: dict = Depends(get_current_user)):
    """Get current credit balance"""
    try:
        balance = await get_user_credits(current_user["email"])
        
        return {
            "success": True,
            "balance": balance,
            "formatted": f"{balance:.2f}"
        }
        
    except Exception as e:
        logger.error(f"Get balance error: {e}")
        raise HTTPException(status_code=500, detail="Kredi bakiyesi alınamadı")


@router.post("/purchase")
async def purchase_credits(
    purchase: CreditPurchase,
    current_user: dict = Depends(get_current_user)
):
    """Purchase credits (simplified - would integrate with payment gateway)"""
    try:
        # In production, this would verify payment with Stripe/PayPal etc.
        # For now, we'll simulate successful purchase
        
        transaction = await add_credits(
            current_user["email"],
            purchase.amount,
            "Credit purchase",
            {
                "payment_method": purchase.payment_method,
                "purchase_date": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "message": f"{purchase.amount:.2f} kredi başarıyla eklendi",
            "new_balance": transaction["balance_after"],
            "transaction_id": str(transaction.get("_id"))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Purchase credits error: {e}")
        raise HTTPException(status_code=500, detail="Kredi satın alma başarısız")


@router.post("/admin/add")
async def admin_add_credits(
    user_email: str,
    amount: float,
    reason: str,
    current_user: dict = Depends(require_admin)
):
    """Admin: Add credits to any user"""
    try:
        transaction = await add_credits(
            user_email,
            amount,
            f"Admin credit: {reason}",
            {"added_by": current_user["email"]}
        )
        
        return {
            "success": True,
            "message": f"{amount:.2f} kredi eklendi",
            "new_balance": transaction["balance_after"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin add credits error: {e}")
        raise HTTPException(status_code=500, detail="Kredi eklenemedi")


@router.get("/history")
async def get_credit_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get credit transaction history"""
    try:
        db = mongodb_client.db
        
        transactions = await db.credit_transactions.find(
            {"user_email": current_user["email"]},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {
            "success": True,
            "transactions": transactions,
            "total": len(transactions)
        }
        
    except Exception as e:
        logger.error(f"Get credit history error: {e}")
        raise HTTPException(status_code=500, detail="Kredi geçmişi alınamadı")


@router.get("/stats")
async def get_credit_stats(current_user: dict = Depends(get_current_user)):
    """Get credit usage statistics"""
    try:
        db = mongodb_client.db
        
        # Get all transactions
        transactions = await db.credit_transactions.find(
            {"user_email": current_user["email"]},
            {"_id": 0}
        ).to_list(1000)
        
        total_purchased = sum(t["amount"] for t in transactions if t["type"] == "credit")
        total_spent = abs(sum(t["amount"] for t in transactions if t["type"] == "debit"))
        
        return {
            "success": True,
            "stats": {
                "current_balance": await get_user_credits(current_user["email"]),
                "total_purchased": total_purchased,
                "total_spent": total_spent,
                "transaction_count": len(transactions)
            }
        }
        
    except Exception as e:
        logger.error(f"Get credit stats error: {e}")
        raise HTTPException(status_code=500, detail="İstatistikler alınamadı")


# Utility function to calculate token cost
def calculate_token_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Calculate credit cost based on token usage
    Pricing similar to OpenAI:
    - Input: $0.50 per 1M tokens = 0.0000005 per token
    - Output: $1.50 per 1M tokens = 0.0000015 per token
    
    For credits: 1 credit = $0.01
    """
    INPUT_COST_PER_TOKEN = 0.00005  # 0.05 credits per 1000 tokens
    OUTPUT_COST_PER_TOKEN = 0.00015  # 0.15 credits per 1000 tokens
    
    input_cost = (input_tokens / 1000) * INPUT_COST_PER_TOKEN
    output_cost = (output_tokens / 1000) * OUTPUT_COST_PER_TOKEN
    
    total_cost = input_cost + output_cost
    
    return round(total_cost, 4)
