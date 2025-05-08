from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import get_db_fastapi
from notification_manager import create_notification

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db_fastapi)):
    """Register a new user"""
    # Check if username already exists
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    db_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,  # Changed from hashed_password to match the model
        credits=10  # Default starting credits
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create welcome notification
    create_notification(
        db=db,
        user_id=db_user.id,
        message=f"Welcome to Weather Cloud Service, {db_user.username}! You've been given 10 free credits to get started."
    )
    
    return db_user

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db_fastapi)):
    """Generate JWT token for user authentication"""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    """Get current user information"""
    return current_user

@router.get("/notifications", response_model=List[schemas.NotificationResponse])
def get_user_notifications(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db_fastapi)
):
    """Get all notifications for the current user"""
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    ).order_by(models.Notification.created_at.desc()).all()
    
    return notifications

@router.put("/notifications/{notification_id}", response_model=schemas.NotificationResponse)
def update_notification(
    notification_id: int,
    notification_update: schemas.NotificationUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db_fastapi)
):
    """Mark a notification as read/unread"""
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = notification_update.is_read
    db.commit()
    db.refresh(notification)
    
    return notification
