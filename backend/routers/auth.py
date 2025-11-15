from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import bcrypt
import uuid
from database import get_db
from models.db_models import User, Puller, UserRole
from models.schemas import SignUpRequest, LoginRequest, TokenResponse
import os

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/signup", response_model=TokenResponse)
def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    hashed_pwd = hash_password(request.password)
    
    user = User(
        user_id=user_id,
        email=request.email,
        hashed_password=hashed_pwd,
        role=request.role,
        name=request.name,
        phone=request.phone
    )
    db.add(user)
    db.commit()
    
    # If puller, create puller record
    if request.role == UserRole.PULLER:
        puller_id = f"puller_{uuid.uuid4().hex[:8]}"
        puller = Puller(puller_id=puller_id, user_id=user_id)
        db.add(puller)
        db.commit()
    
    token = create_access_token({"user_id": user_id, "email": request.email, "role": request.role.value})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": request.role.value,
        "user_id": user_id
    }

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"user_id": user.user_id, "email": user.email, "role": user.role.value})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role.value,
        "user_id": user.user_id
    }
