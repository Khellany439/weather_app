import asyncio
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session

import models
from weather_api import get_current_weather, get_weather_forecast
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

# Simple in-memory queue for demonstration
# In a production environment, use a proper queue system like Redis, RabbitMQ, etc.
request_queue = []

def add_to_queue(request_id: int):
    """Add a weather request to the processing queue"""
    logging.info(f"Adding request {request_id} to the queue")
    request_queue.append(request_id)
    return True

async def process_weather_request(request_id: int, db: Session):
    """Process a weather request from the queue"""
    # Get the request from the database
    request = db.query(models.WeatherRequest).filter(models.WeatherRequest.id == request_id).first()
    
    if not request:
        logging.error(f"Request {request_id} not found in database")
        return False
    
    try:
        # Update request status to processing
        request.status = models.RequestStatus.PROCESSING
        db.commit()
        
        # Process request based on type
        if request.request_type == "current":
            result = await get_current_weather(request.location)
        elif request.request_type == "forecast":
            result = await get_weather_forecast(request.location)
        else:
            # Handle unsupported request type
            raise ValueError(f"Unsupported request type: {request.request_type}")
        
        if not result:
            raise ValueError(f"No data found for location: {request.location}")
        
        # Update request with result
        request.result = json.dumps(result, default=json_serializable)
        request.status = models.RequestStatus.COMPLETED
        request.completed_at = datetime.utcnow()
        db.commit()
        
        # Create notification for user
        create_notification(
            db=db,
            user_id=request.user_id,
            request_id=request.id,
            message=f"Your {request.request_type} weather request for {request.location} has been completed."
        )
        
        logging.info(f"Request {request_id} processed successfully")
        return True
    
    except Exception as e:
        # Handle error
        logging.error(f"Error processing request {request_id}: {str(e)}")
        
        # Update request with error
        request.status = models.RequestStatus.FAILED
        request.error_message = str(e)
        request.completed_at = datetime.utcnow()
        db.commit()
        
        # Create notification for user
        create_notification(
            db=db,
            user_id=request.user_id,
            request_id=request.id,
            message=f"Your {request.request_type} weather request for {request.location} failed: {str(e)}"
        )
        
        return False
    
    finally:
        # Remove request from queue
        if request_id in request_queue:
            request_queue.remove(request_id)

async def run_queue_processor(db: Session):
    """Background task to process the request queue"""
    while True:
        if request_queue:
            request_id = request_queue[0]
            await process_weather_request(request_id, db)
        await asyncio.sleep(1)  # Wait before checking the queue again
