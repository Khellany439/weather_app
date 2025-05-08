from fastapi_app import app

# This module exposes the ASGI application for use with Gunicorn
# Run with: gunicorn -k uvicorn.workers.UvicornWorker asgi:app