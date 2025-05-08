from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

import models
import schemas
from database import get_db_fastapi
from auth import get_current_active_user
from notification_manager import create_notification

router = APIRouter()

@router.get("/balance", response_model=int)
async def get_credit_balance(
    current_user: models.User = Depends(get_current_active_user)
):
    """Get the current user's credit balance"""
    return current_user.credits

@router.get("/transactions", response_model=List[schemas.CreditTransactionResponse])
async def get_credit_transactions(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db_fastapi),
    limit: int = 10
):
    """Get the credit transaction history for the current user"""
    transactions = db.query(models.CreditTransaction).filter(
        models.CreditTransaction.user_id == current_user.id
    ).order_by(desc(models.CreditTransaction.created_at)).limit(limit).all()
    
    return transactions

@router.post("/purchase", response_model=schemas.CreditTransactionResponse)
async def purchase_credits(
    credit_purchase: schemas.CreditPurchase,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db_fastapi)
):
    """Purchase more credits"""
    # In a real application, this would integrate with a payment processor
    amount = credit_purchase.amount
    
    # Add credits to user's account
    current_user.credits += amount
    
    # Create credit transaction
    credit_transaction = models.CreditTransaction(
        user_id=current_user.id,
        amount=amount,
        description=f"Purchased {amount} credits"
    )
    db.add(credit_transaction)
    db.commit()
    db.refresh(credit_transaction)
    
    # Create notification
    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"You've successfully purchased {amount} credits. Your new balance is {current_user.credits} credits."
    )
    
    return credit_transaction

@router.post("/redeem", response_model=schemas.CreditTransactionResponse)
async def redeem_promo_code(
    promo_code: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db_fastapi)
):
    """Redeem a promotional code for free credits"""
    # In a real application, this would check a database of valid promo codes
    # For this demo, we'll just accept any code and give a random amount of credits
    
    import random
    valid_codes = ["WELCOME", "WEATHER2023", "CLOUDY"]
    
    if promo_code.upper() not in valid_codes:
        raise HTTPException(status_code=400, detail="Invalid promo code")
    
    amount = random.randint(5, 20)
    
    # Add credits to user's account
    current_user.credits += amount
    
    # Create credit transaction
    credit_transaction = models.CreditTransaction(
        user_id=current_user.id,
        amount=amount,
        description=f"Redeemed promo code: {promo_code}"
    )
    db.add(credit_transaction)
    db.commit()
    db.refresh(credit_transaction)
    
    # Create notification
    create_notification(
        db=db,
        user_id=current_user.id,
        message=f"You've successfully redeemed promo code {promo_code} for {amount} credits. Your new balance is {current_user.credits} credits."
    )
    
    return credit_transaction
