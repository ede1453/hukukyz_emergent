"""Authentication API routes"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import bcrypt
import jwt
import logging
from datetime import datetime, timedelta

from backend.database.mongodb import mongodb_client
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = settings.openai_api_key[:32]  # Use first 32 chars as secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    email: EmailStr
    full_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and get current user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        db = mongodb_client.db
        user = await db.users.find_one({"email": email}, {"_id": 0, "password": 0})
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register new user"""
    try:
        db = mongodb_client.db
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        hashed_password = hash_password(user_data.password)
        
        user = {
            "email": user_data.email,
            "password": hashed_password,
            "full_name": user_data.full_name,
            "role": "avukat",  # Default role
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "preferences": {
                "include_deprecated": False
            }
        }
        
        await db.users.insert_one(user)
        
        # Create access token
        access_token = create_access_token({"sub": user_data.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user.get("role", "avukat"),
                "created_at": user["created_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user"""
    try:
        db = mongodb_client.db
        
        # Get user
        user = await db.users.find_one({"email": credentials.email})
        
        if not user or not verify_password(credentials.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        access_token = create_access_token({"sub": credentials.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user.get("role", "avukat"),
                "created_at": user.get("created_at", "")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "success": True,
        "user": current_user
    }


@router.put("/me")
async def update_profile(
    profile_data: UserProfile,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    try:
        db = mongodb_client.db
        
        await db.users.update_one(
            {"email": current_user["email"]},
            {
                "$set": {
                    "full_name": profile_data.full_name,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Profile updated"
        }
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Profile update failed")


@router.put("/preferences")
async def update_preferences(
    preferences: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update user preferences"""
    try:
        db = mongodb_client.db
        
        await db.users.update_one(
            {"email": current_user["email"]},
            {
                "$set": {
                    "preferences": preferences,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Preferences updated"
        }
        
    except Exception as e:
        logger.error(f"Preferences update error: {e}")
        raise HTTPException(status_code=500, detail="Preferences update failed")


async def require_admin(current_user: dict = Depends(get_current_user)):
    """Verify user has admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    return current_user


@router.get("/users")
async def list_users(current_user: dict = Depends(require_admin)):
    """Get all users (admin only)"""
    try:
        db = mongodb_client.db
        users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
        
        return {
            "success": True,
            "users": users
        }
        
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@router.put("/users/{user_email}/role")
async def update_user_role(
    user_email: str,
    role_data: dict,
    current_user: dict = Depends(require_admin)
):
    """Update user role (admin only)"""
    try:
        db = mongodb_client.db
        
        new_role = role_data.get("role")
        if new_role not in ["admin", "avukat"]:
            raise HTTPException(status_code=400, detail="Geçersiz rol. Sadece 'admin' veya 'avukat' olabilir")
        
        result = await db.users.update_one(
            {"email": user_email},
            {
                "$set": {
                    "role": new_role,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        return {
            "success": True,
            "message": f"Kullanıcı rolü '{new_role}' olarak güncellendi"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update role error: {e}")
        raise HTTPException(status_code=500, detail="Rol güncellenemedi")


@router.put("/change-password")
async def change_password(
    password_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Change user password"""
    try:
        db = mongodb_client.db
        
        current_password = password_data.get("current_password")
        new_password = password_data.get("new_password")
        
        if not current_password or not new_password:
            raise HTTPException(status_code=400, detail="Mevcut ve yeni şifre gereklidir")
        
        # Get user with password
        user = await db.users.find_one({"email": current_user["email"]})
        
        # Verify current password
        if not verify_password(current_password, user["password"]):
            raise HTTPException(status_code=401, detail="Mevcut şifre yanlış")
        
        # Hash new password
        new_hashed = hash_password(new_password)
        
        # Update password
        await db.users.update_one(
            {"email": current_user["email"]},
            {
                "$set": {
                    "password": new_hashed,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Şifre başarıyla değiştirildi"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(status_code=500, detail="Şifre değiştirilemedi")


@router.delete("/users/{user_email}")
async def delete_user(
    user_email: str,
    current_user: dict = Depends(require_admin)
):
    """Delete a user (admin only)"""
    try:
        # Prevent self-deletion
        if user_email == current_user["email"]:
            raise HTTPException(status_code=400, detail="Kendi hesabınızı silemezsiniz")
        
        db = mongodb_client.db
        
        result = await db.users.delete_one({"email": user_email})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        return {
            "success": True,
            "message": "Kullanıcı başarıyla silindi"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail="Kullanıcı silinemedi")


@router.post("/users/{user_email}/reset-password")
async def reset_user_password(
    user_email: str,
    current_user: dict = Depends(require_admin)
):
    """Reset user password to a default value (admin only)"""
    try:
        db = mongodb_client.db
        
        # Generate default password
        default_password = "Hukuk123!"
        new_hashed = hash_password(default_password)
        
        result = await db.users.update_one(
            {"email": user_email},
            {
                "$set": {
                    "password": new_hashed,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        return {
            "success": True,
            "message": f"Şifre sıfırlandı. Yeni şifre: {default_password}",
            "default_password": default_password
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        raise HTTPException(status_code=500, detail="Şifre sıfırlanamadı")
