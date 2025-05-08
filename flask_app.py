#!/usr/bin/env python3
"""
Flask application with explicit template path configuration for Windows compatibility.
"""

import os
from flask import Flask, request, Response, render_template, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import subprocess
import threading
import time
import secrets
import json
import datetime
from datetime import datetime, timedelta

from database import get_db
import models

# Get the absolute path to the templates directory
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

# Create Flask app with explicit template and static folders
app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=static_dir)
            
app.secret_key = os.environ.get("SESSION_SECRET", secrets.token_hex(16))
csrf = CSRFProtect(app)

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import all routes and configurations from main.py
from main import _jinja2_filter_datetime, _jinja2_filter_fromjson, utility_processor, load_user
from main import index, login, register, logout, dashboard, weather_search
from main import request_history, view_request, credits, purchase_credits, redeem_promo
from main import notifications, update_notification, mark_all_read, profile, update_profile
from main import delete_account, api_docs, swagger_ui, api_proxy, page_not_found, server_error

# Template filter for formatting dates
app.template_filter('strftime')(_jinja2_filter_datetime)
app.template_filter('fromjson')(_jinja2_filter_fromjson)

# Register utility processor
app.context_processor(utility_processor)

# Register error handlers
app.register_error_handler(404, page_not_found)
app.register_error_handler(500, server_error)

# Register the load_user function with LoginManager
login_manager.user_loader(load_user)

# Start FastAPI in the background
def start_fastapi_server():
    """Start the FastAPI server once"""
    # Check if port 5001 is already in use
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port_in_use = sock.connect_ex(('localhost', 5001)) == 0
    sock.close()
    
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

if __name__ == "__main__":
    # Start FastAPI in the background
    start_fastapi_server()
    
    # Run Flask on port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)