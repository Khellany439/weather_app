# Weather Information Cloud Service: Quick Start Guide

This guide covers only the essentials: setting up your environment, installing dependencies, and running the application on Windows with VSCode.

## Setting Up Virtual Environment

1. **Open VSCode and the Terminal**
   - Open your project in VSCode
   - Open the terminal with `` Ctrl+` ``

2. **Create a Virtual Environment**
   ```bash
   # Create a virtual environment named 'venv'
   python -m venv venv
   ```

3. **Activate the Virtual Environment**
   ```bash
   # In Command Prompt
   venv\Scripts\activate

   # In PowerShell (if you get execution policy errors)
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\venv\Scripts\Activate.ps1
   ```

   You should see `(venv)` appear at the beginning of your terminal prompt, indicating the environment is active.

## Installing Dependencies

1. **Install all required packages**
   ```bash
   # Make sure your virtual environment is activated
   pip install -r requirements.txt

   # If requirements.txt doesn't exist, install the core packages
   pip install flask flask-login flask-sqlalchemy flask-wtf
   pip install fastapi uvicorn pydantic python-jose[cryptography]
   pip install psycopg2-binary sqlalchemy python-multipart
   pip install requests pytest pytest-cov httpx
   ```

2. **Verify installations**
   ```bash
   pip list
   ```

## Setting Up Environment Variables

```bash
# In Command Prompt
set DATABASE_URL=postgresql://postgres:your_password@localhost:5432/weather_service
set WEATHER_API_KEY=your_openweathermap_api_key
set SECRET_KEY=your_secret_key

# In PowerShell
$env:DATABASE_URL="postgresql://postgres:your_password@localhost:5432/weather_service"
$env:WEATHER_API_KEY="your_openweathermap_api_key"
$env:SECRET_KEY="your_secret_key"
```

## Running the Application

### Method 1: All-in-One Script (Recommended for Windows)

```bash
# This runs both Flask and FastAPI components
python run_windows.py
```

### Method 2: Running Components Separately

**Terminal 1: Start FastAPI Backend**
```bash
# Make sure your virtual environment is activated
python run_fastapi.py
```

**Terminal 2: Start Flask Frontend**
```bash
# Open a new terminal and activate the virtual environment
venv\Scripts\activate
python run_flask.py
```

If you encounter template not found errors, use:
```bash
python flask_app.py
```

### Method 3: Direct Component Commands

**FastAPI Backend:**
```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 5001 --reload
```

**Flask Frontend:**
```bash
python -m flask --app run_flask run --host=0.0.0.0 --port=5000 --debug
```

## Accessing the Application

- Web Interface: http://localhost:5000
- API Documentation: http://localhost:5000/swagger-ui
- Direct API Access: http://localhost:5001/api/...

## Common Issues and Solutions

- **Database Connection Error**: Ensure PostgreSQL is running and your connection string is correct
- **Template Not Found Error**: Use `flask_app.py` which has explicit template paths for Windows
- **Port In Use Error**: Check if another process is using port 5000 or 5001 with `netstat -ano | findstr :5000`
Weather Information Cloud Service - Test Suite
This directory contains comprehensive tests for the Weather Information Cloud Service application. The tests cover all core components of the system including API functionality, authentication, database operations, and performance metrics.

Test Structure
conftest.py: Common fixtures and test setup for all tests
test_api.py: Tests for API endpoints and request handling
test_auth.py: Tests for authentication and password handling
test_notification.py: Tests for the notification system
test_performance.py: Performance and load testing
test_queue_manager.py: Tests for the background processing queue
test_schemas.py: Tests for Pydantic schema validation
test_weather_service.py: Tests for weather data retrieval and processing
Running Tests
To run all tests:

pytest
To run tests with coverage report:

pytest --cov=./
To run a specific test file:

pytest tests/test_api.py
To run performance tests only:

pytest -m performance
Environment Setup
Before running tests, ensure you have the necessary environment variables set:

# For local development testing
export DATABASE_URL=sqlite:///:memory:  # Use in-memory SQLite for tests
export SECRET_KEY=test_secret_key
export WEATHER_API_KEY=your_api_key  # Required for integration tests with real API
Test Types
Unit Tests
Tests for individual functions and components in isolation. These tests use mock objects to avoid external dependencies.

Integration Tests
Tests that verify the interaction between different components of the system. These tests ensure that components work together correctly.

API Tests
Tests that verify the behavior of API endpoints, including request validation, response formatting, and error handling.

Performance Tests
Tests that measure the performance of the system under various conditions, including response time, throughput, and resource utilization.

Test Coverage
The test suite aims to maintain high code coverage across all critical components:

API endpoints: 95%+
Authentication: 98%+
Database operations: 90%+
Weather data processing: 85%+
Background tasks: 80%+
Adding New Tests
When adding new functionality to the application, follow these guidelines:

Create unit tests for new functions
Create integration tests for new component interactions
Update API tests for new endpoints
Run the full test suite to ensure no regressions
CI/CD Integration
These tests are integrated with the CI/CD pipeline and run automatically on:

Pull requests to main/develop branches
Pushes to main/develop branches
Scheduled daily runs for regression testing
