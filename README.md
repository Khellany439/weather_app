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
