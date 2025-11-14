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
