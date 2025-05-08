from typing import List, Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    credits: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Weather Request Schemas
class WeatherRequestBase(BaseModel):
    location: str
    request_type: str

class WeatherRequestCreate(WeatherRequestBase):
    pass

class WeatherRequestResponse(WeatherRequestBase):
    id: int
    user_id: int
    status: str
    credits_used: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        orm_mode = True

# Notification Schemas
class NotificationBase(BaseModel):
    message: str

class NotificationCreate(NotificationBase):
    user_id: int
    request_id: Optional[int] = None

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    request_id: Optional[int]
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True

class NotificationUpdate(BaseModel):
    is_read: bool

# Credit Transaction Schemas
class CreditTransactionBase(BaseModel):
    amount: int
    description: str

class CreditTransactionCreate(CreditTransactionBase):
    user_id: int

class CreditTransactionResponse(CreditTransactionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Weather Data Schemas
class CurrentWeatherResponse(BaseModel):
    location: str
    temperature: float
    humidity: float
    wind_speed: float
    description: str
    icon: str
    timestamp: datetime

class ForecastItem(BaseModel):
    date: datetime
    temperature: float
    humidity: float
    wind_speed: float
    description: str
    icon: str

class ForecastResponse(BaseModel):
    location: str
    forecast: List[ForecastItem]

# Credit Purchase Schema
class CreditPurchase(BaseModel):
    amount: int

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
