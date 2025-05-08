import pytest
from datetime import timedelta
from jose import jwt

import auth

def test_password_hashing():
    password = "test_password"
    hashed = auth.get_password_hash(password)
    
    # Hashed password should be different from original
    assert hashed != password
    
    # Verify should return True for correct password
    assert auth.verify_password(password, hashed) is True
    
    # Verify should return False for incorrect password
    assert auth.verify_password("wrong_password", hashed) is False

def test_create_access_token():
    data = {"sub": "testuser"}
    expires = timedelta(minutes=15)
    
    token = auth.create_access_token(data, expires)
    
    # Token should be a string
    assert isinstance(token, str)
    
    # Decode the token and verify payload
    payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert payload["sub"] == "testuser"
    assert "exp" in payload

def test_create_access_token_default_expiry():
    data = {"sub": "testuser"}
    
    token = auth.create_access_token(data)
    
    # Token should be a string
    assert isinstance(token, str)
    
    # Decode the token and verify payload
    payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert payload["sub"] == "testuser"
    assert "exp" in payload
