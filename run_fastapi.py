#!/usr/bin/env python3
"""
Start the FastAPI application on port 5001.
This will be called by the Flask proxy in main.py.
"""

import uvicorn

if __name__ == "__main__":
    # Run FastAPI on port 5001 to avoid conflict with the Flask proxy on port 5000
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=5001)