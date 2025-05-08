import logging
from datetime import datetime
from sqlalchemy.orm import Session

import models

def create_notification(db: Session, user_id: int, message: str, request_id: int = None):
    """Create a new notification for a user"""
    try:
        notification = models.Notification(
            user_id=user_id,
            request_id=request_id,
            message=message,
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        logging.info(f"Created notification for user {user_id}: {message}")
        return notification
    
    except Exception as e:
        logging.error(f"Error creating notification: {str(e)}")
        db.rollback()
        return None

def mark_notification_as_read(db: Session, notification_id: int):
    """Mark a notification as read"""
    try:
        notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
        
        if notification:
            notification.is_read = True
            db.commit()
            db.refresh(notification)
            
            logging.info(f"Marked notification {notification_id} as read")
            return notification
        else:
            logging.warning(f"Notification {notification_id} not found")
            return None
    
    except Exception as e:
        logging.error(f"Error marking notification as read: {str(e)}")
        db.rollback()
        return None

def get_unread_notifications_count(db: Session, user_id: int):
    """Get the count of unread notifications for a user"""
    try:
        count = db.query(models.Notification).filter(
            models.Notification.user_id == user_id,
            models.Notification.is_read == False
        ).count()
        
        return count
    
    except Exception as e:
        logging.error(f"Error getting unread notifications count: {str(e)}")
        return 0
