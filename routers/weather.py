from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import json

import models
import schemas
from database import get_db_fastapi
from auth import get_current_active_user
from weather_api import get_current_weather, get_weather_forecast
from queue_manager import add_to_queue, process_weather_request
from notification_manager import create_notification

# Helper function to make objects JSON serializable
def json_serializable(obj):
    """Convert a Python object to a JSON serializable format"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)

router = APIRouter()

@router.post("/request", response_model=schemas.WeatherRequestResponse)
async def request_weather(
    weather_request: schemas.WeatherRequestCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db_fastapi)
):
    """Create a new weather data request"""
    # Determine credits cost based on request type
    credits_cost = 1  # Default cost
    if weather_request.request_type == "forecast":
        credits_cost = 2
    elif weather_request.request_type == "historical":
        credits_cost = 3
    
    # Check if user has enough credits
    if current_user.credits < credits_cost:
        raise HTTPException(
            status_code=400, 
            detail=f"Not enough credits. Required: {credits_cost}, Available: {current_user.credits}"
        )
    
    # Deduct credits from user
    current_user.credits -= credits_cost
    
    # Create credit transaction
    credit_transaction = models.CreditTransaction(
        user_id=current_user.id,
        amount=-credits_cost,
        description=f"{weather_request.request_type.capitalize()} weather request for {weather_request.location}"
    )
    db.add(credit_transaction)
    
    # Create weather request
    db_weather_request = models.WeatherRequest(
        user_id=current_user.id,
        location=weather_request.location,
        request_type=weather_request.request_type,
        credits_used=credits_cost,
        status=models.RequestStatus.QUEUED
    )
    db.add(db_weather_request)
    db.commit()
    db.refresh(db_weather_request)
    
    # Add request to processing queue
    add_to_queue(db_weather_request.id)
    
    # Process request in background
    background_tasks.add_task(
        process_weather_request,
        request_id=db_weather_request.id,
        db=db
    )
    
    # Create notification for request
    create_notification(
        db=db,
        user_id=current_user.id,
        request_id=db_weather_request.id,
        message=f"Your weather request for {weather_request.location} has been queued."
    )
    
    return db_weather_request

@router.get("/requests", response_model=List[schemas.WeatherRequestResponse])
async def get_user_weather_requests(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db_fastapi),
    limit: int = 10,
    page: int = 1
):
    """Get all weather requests for the current user"""
    # Calculate skip value for pagination
    skip = (page - 1) * limit
    
    # Get requests with pagination
    requests = db.query(models.WeatherRequest).filter(
        models.WeatherRequest.user_id == current_user.id
    ).order_by(desc(models.WeatherRequest.created_at)).offset(skip).limit(limit).all()
    
    print(f"Retrieved {len(requests)} weather requests for user {current_user.username}")
    return requests

@router.get("/requests/{request_id}", response_model=schemas.WeatherRequestResponse)
async def get_weather_request(
    request_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db_fastapi)
):
    """Get a specific weather request"""
    request = db.query(models.WeatherRequest).filter(
        models.WeatherRequest.id == request_id,
        models.WeatherRequest.user_id == current_user.id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Weather request not found")
    
    return request

@router.get("/current", response_model=schemas.CurrentWeatherResponse)
async def get_current_weather_data(
    location: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db_fastapi)
):
    """Get current weather data directly (consumes 1 credit)"""
    # Check if user has enough credits
    credit_cost = 1
    if current_user.credits < credit_cost:
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits. You need {credit_cost} credits for this request, but you only have {current_user.credits}."
        )
    
    print(f"Fetching current weather for location: {location}")
    weather_data = await get_current_weather(location)
    if not weather_data:
        print(f"Failed to get weather data for {location}")
        # Create a notification for the failed request
        create_notification(
            db,
            current_user.id, 
            f"Failed to retrieve weather data for {location}. No credits were deducted."
        )
        raise HTTPException(status_code=404, detail=f"Weather data for {location} not found")
    
    # Deduct credits
    current_user.credits -= credit_cost
    
    # Record the transaction
    transaction = models.CreditTransaction(
        user_id=current_user.id,
        amount=-credit_cost,
        description=f"Used {credit_cost} credit for current weather data for {location}"
    )
    db.add(transaction)
    
    # Create weather request record for history
    weather_request = models.WeatherRequest(
        user_id=current_user.id,
        location=location,
        request_type="current",
        credits_used=credit_cost,
        status=models.RequestStatus.COMPLETED,
        result=json.dumps(weather_data, default=json_serializable),
        completed_at=datetime.utcnow()
    )
    db.add(weather_request)
    
    # Create a notification
    create_notification(
        db,
        current_user.id,
        f"Successfully retrieved current weather data for {location}. {credit_cost} credit was deducted."
    )
    
    # Commit changes
    db.commit()
    
    print(f"Successfully retrieved weather data: {weather_data}")
    return weather_data

@router.get("/forecast", response_model=schemas.ForecastResponse)
async def get_forecast_data(
    location: str,
    days: int = 5,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db_fastapi)
):
    """Get weather forecast data directly (consumes 2 credits)"""
    # Check if user has enough credits
    credit_cost = 2
    if current_user.credits < credit_cost:
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient credits. You need {credit_cost} credits for this request, but you only have {current_user.credits}."
        )
    
    print(f"Fetching {days}-day forecast for location: {location}")
    forecast_data = await get_weather_forecast(location, days)
    if not forecast_data:
        print(f"Failed to get forecast data for {location}")
        # Create a notification for the failed request
        create_notification(
            db,
            current_user.id, 
            f"Failed to retrieve {days}-day forecast for {location}. No credits were deducted."
        )
        raise HTTPException(status_code=404, detail=f"Forecast data for {location} not found")
    
    # Deduct credits
    current_user.credits -= credit_cost
    
    # Record the transaction
    transaction = models.CreditTransaction(
        user_id=current_user.id,
        amount=-credit_cost,
        description=f"Used {credit_cost} credits for {days}-day forecast for {location}"
    )
    db.add(transaction)
    
    # Create weather request record for history
    weather_request = models.WeatherRequest(
        user_id=current_user.id,
        location=location,
        request_type="forecast",
        credits_used=credit_cost,
        status=models.RequestStatus.COMPLETED,
        result=json.dumps(forecast_data, default=json_serializable),
        completed_at=datetime.utcnow()
    )
    db.add(weather_request)
    
    # Create a notification
    create_notification(
        db,
        current_user.id,
        f"Successfully retrieved {days}-day forecast for {location}. {credit_cost} credits were deducted."
    )
    
    # Commit changes
    db.commit()
    
    print(f"Successfully retrieved forecast data for {location}")
    return forecast_data
