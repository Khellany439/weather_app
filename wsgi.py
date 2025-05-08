# This file is to support WSGI servers like gunicorn
# for an ASGI application like FastAPI, we need a special setup

import os
import subprocess
import threading
import time

# Import our Flask app with explicit template paths
from flask_app import app as flask_app
from asgi import app as asgi_app

# Start FastAPI in the background
def start_fastapi_server():
    """Start the FastAPI server once"""
    # Check if port 5001 is already in use
    import socket
    port_in_use = False  # Default if we can't check
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port_in_use = sock.connect_ex(('localhost', 5001)) == 0
        sock.close()
    except Exception as e:
        print(f"Socket error: {e}")
    
    if not port_in_use:
        print("Starting FastAPI server on port 5001")
        # Start the FastAPI server using uvicorn directly
        fastapi_process = subprocess.Popen([
            "python", "-m", "uvicorn", 
            "fastapi_app:app", 
            "--host", "0.0.0.0", 
            "--port", "5001"
        ])
        # Give FastAPI a moment to start
        time.sleep(2)
    else:
        print("FastAPI server already running on port 5001")

# Start FastAPI server
try:
    start_fastapi_server()
except Exception as e:
    print(f"Warning: Failed to start FastAPI server: {e}")

# This variable is what WSGI servers like gunicorn look for by default
app = flask_app