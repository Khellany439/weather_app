#!/usr/bin/env python3
"""
WSGI adapter for FastAPI application.
This makes FastAPI work with Gunicorn's WSGI workers.
"""

from flask import Flask, request, Response, render_template, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import subprocess
import threading
import time
import os
import signal
import atexit
import json
import datetime
from datetime import datetime, timedelta
import secrets

from database import get_db
import models

# Create a simple Flask app that will forward requests to the FastAPI app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", secrets.token_hex(16))
csrf = CSRFProtect(app)

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Template filter for formatting dates
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    if fmt:
        return date.strftime(fmt)
    return date.strftime('%Y-%m-%d %H:%M:%S')

# Template filter for parsing JSON
@app.template_filter('fromjson')
def _jinja2_filter_fromjson(json_string):
    import json
    try:
        return json.loads(json_string)
    except:
        return {}

# Jinja helper functions
@app.context_processor
def utility_processor():
    def get_unread_notifications_count():
        if current_user.is_authenticated:
            with get_db() as db:
                count = db.query(models.Notification).filter_by(user_id=current_user.id, is_read=False).count()
                return count
        return 0
        
    return dict(unread_notifications_count=get_unread_notifications_count(), now=datetime.now)

# Define the URL where FastAPI is running on port 5001
FASTAPI_URL = "http://localhost:5001"

# Global variable to store the FastAPI process
fastapi_process = None

def start_fastapi_server():
    """Start the FastAPI server once"""
    global fastapi_process
    
    # Check if port 5001 is already in use
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port_in_use = sock.connect_ex(('localhost', 5001)) == 0
    sock.close()
    
    if not port_in_use and (fastapi_process is None or fastapi_process.poll() is not None):
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
    elif port_in_use:
        print("FastAPI server already running on port 5001")

def cleanup_process():
    """Clean up FastAPI process on exit"""
    global fastapi_process
    if fastapi_process:
        print("Terminating FastAPI process")
        try:
            fastapi_process.terminate()
            fastapi_process.wait(timeout=5)
        except:
            fastapi_process.kill()

# Register cleanup function to be called on exit
atexit.register(cleanup_process)

# Start FastAPI when this module is loaded
start_fastapi_server()

@login_manager.user_loader
def load_user(user_id):
    with get_db() as db:
        return db.query(models.User).filter(models.User.id == int(user_id)).first()

# API Proxy routes
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(path):
    """Forward API requests to the FastAPI app"""
    
    try:
        # Forward the request to FastAPI including query parameters
        url = f"{FASTAPI_URL}/api/{path}"
        resp = requests.request(
            method=request.method,
            url=url,
            params=request.args,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)
        
        # Create a Flask Response from the FastAPI response
        response = Response(resp.content, resp.status_code)
        response.headers.update({key: value for (key, value) in resp.headers.items()})
        return response
    except Exception as e:
        return {"error": str(e)}, 500

# Frontend routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Call the FastAPI login endpoint
        try:
            response = requests.post(
                f"{FASTAPI_URL}/api/users/token",
                data={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                # Get user details
                token_data = response.json()
                access_token = token_data.get("access_token")
                
                # Use the token to get user info
                user_response = requests.get(
                    f"{FASTAPI_URL}/api/users/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    
                    # Find or create the user in the Flask-Login system
                    with get_db() as db:
                        user = db.query(models.User).filter_by(username=username).first()
                        
                        if user:
                            # Save the access token in the session
                            session['access_token'] = access_token
                            login_user(user)
                            flash('Login successful!', 'success')
                            
                            # Redirect to the next page or dashboard
                            next_page = request.args.get('next')
                            return redirect(next_page or url_for('dashboard'))
                        else:
                            flash('User not found in the database.', 'danger')
                else:
                    flash('Failed to get user information.', 'danger')
            else:
                error_data = response.json()
                flash(f'Login failed: {error_data.get("detail", "Invalid credentials")}', 'danger')
                
        except Exception as e:
            flash(f'Error during login: {str(e)}', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
            
        # Call the FastAPI register endpoint
        try:
            response = requests.post(
                f"{FASTAPI_URL}/api/users/register",
                json={"username": username, "email": email, "password": password}
            )
            
            if response.status_code == 200:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                error_data = response.json()
                flash(f'Registration failed: {error_data.get("detail", "Error during registration")}', 'danger')
                
        except Exception as e:
            flash(f'Error during registration: {str(e)}', 'danger')
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('access_token', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get recent requests
    # Ensure we have a valid token
    if 'access_token' not in session:
        flash('Your session has expired. Please log in again.', 'warning')
        return redirect(url_for('login'))

    try:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.get(f"{FASTAPI_URL}/api/weather/requests?limit=5", headers=headers)
        
        # If unauthorized, try to refresh the token
        if response.status_code == 401:
            flash('Refreshing your session...', 'info')
            # Redirect to login to get a fresh token
            return redirect(url_for('login'))
            
        if response.status_code == 200:
            recent_requests = response.json()
        else:
            print(f"API error: {response.status_code} - {response.text}")
            recent_requests = []
            
    except Exception as e:
        print(f"Exception in dashboard: {str(e)}")
        recent_requests = []
        
    return render_template('dashboard.html', recent_requests=recent_requests)

@app.route('/weather/search', methods=['GET', 'POST'])
@login_required
def weather_search():
    result = None
    request_type = None
    credits_used = 0
    
    if request.method == 'POST':
        location = request.form.get('location')
        request_type = request.form.get('request_type')
        forecast_days = request.form.get('forecast_days', 5)
        historical_date = request.form.get('historical_date')
        
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        
        try:
            if request_type == 'current':
                response = requests.get(
                    f"{FASTAPI_URL}/api/weather/current?location={location}",
                    headers=headers
                )
                credits_used = 1
                
            elif request_type == 'forecast':
                response = requests.get(
                    f"{FASTAPI_URL}/api/weather/forecast?location={location}&days={forecast_days}",
                    headers=headers
                )
                credits_used = 2
                
            elif request_type == 'historical':
                response = requests.get(
                    f"{FASTAPI_URL}/api/weather/historical?location={location}&date={historical_date}",
                    headers=headers
                )
                credits_used = 3
                
            if response.status_code == 200:
                result = response.json()
                flash('Weather data retrieved successfully!', 'success')
            else:
                error_data = response.json()
                flash(f'Failed to get weather data: {error_data.get("detail", "Error")}', 'danger')
                
        except Exception as e:
            flash(f'Error retrieving weather data: {str(e)}', 'danger')
    
    return render_template('weather_search.html', result=result, request_type=request_type, credits_used=credits_used)

@app.route('/request/history')
@login_required
def request_history():
    page = request.args.get('page', 1, type=int)
    limit = 10
    
    # Ensure we have a valid token
    if 'access_token' not in session:
        flash('Your session has expired. Please log in again.', 'warning')
        return redirect(url_for('login'))
    
    try:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        print(f"Requesting history with page={page}, limit={limit}")
        response = requests.get(
            f"{FASTAPI_URL}/api/weather/requests?limit={limit}&page={page}",
            headers=headers,
            timeout=10  # Add timeout to prevent hanging
        )
        
        # Log the API response for debugging
        print(f"API Response Status: {response.status_code}")
        
        # If unauthorized, try to refresh the token
        if response.status_code == 401:
            print("Unauthorized access, token might be expired")
            flash('Your session has expired. Please log in again.', 'warning')
            # Clear the invalid token
            session.pop('access_token', None)
            return redirect(url_for('login'))
            
        if response.status_code != 200:
            print(f"API Error: {response.text}")
            
        if response.status_code == 200:
            requests_data = response.json()
            print(f"Retrieved {len(requests_data)} weather requests")
            
            # Get the total count (we'll use a fixed value for now, could be improved later)
            total_count = 20  # Assume we have at least 20 records total
            if len(requests_data) < limit:
                # If we received fewer results than requested, we're on the last page
                total_count = (page - 1) * limit + len(requests_data)
            
            pages = max(1, (total_count + limit - 1) // limit)  # Ceil division with minimum of 1 page
        else:
            # Handle error responses
            error_msg = f"Error fetching request history: {response.status_code} - {response.text}"
            print(error_msg)
            flash(error_msg, 'danger')
            requests_data = []
            pages = 1
            
    except Exception as e:
        error_msg = f'Error retrieving request history: {str(e)}'
        print(f"Exception: {error_msg}")
        flash(error_msg, 'danger')
        requests_data = []
        pages = 1
        
    return render_template('request_history.html', requests=requests_data, page=page, pages=pages)

@app.route('/request/<int:request_id>')
@login_required
def view_request(request_id):
    try:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.get(
            f"{FASTAPI_URL}/api/weather/requests/{request_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            request_data = response.json()
        else:
            flash('Request not found or access denied.', 'danger')
            return redirect(url_for('request_history'))
            
    except Exception as e:
        flash(f'Error retrieving request details: {str(e)}', 'danger')
        return redirect(url_for('request_history'))
        
    return render_template('view_request.html', request=request_data)

@app.route('/credits')
@login_required
def credits():
    page = request.args.get('page', 1, type=int)
    limit = 10
    
    try:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.get(
            f"{FASTAPI_URL}/api/credits/transactions?limit={limit}&page={page}",
            headers=headers
        )
        
        if response.status_code == 200:
            transactions = response.json()
            # Calculate total pages
            total_count = len(transactions)  # In a real app, you'd get this from API
            pages = (total_count + limit - 1) // limit  # Ceil division
        else:
            transactions = []
            pages = 1
            
    except Exception as e:
        flash(f'Error retrieving credit transactions: {str(e)}', 'danger')
        transactions = []
        pages = 1
        
    return render_template('credits.html', transactions=transactions, page=page, pages=pages)

@app.route('/credits/purchase', methods=['POST'])
@login_required
def purchase_credits():
    amount = request.form.get('amount', type=int)
    
    if not amount or amount <= 0:
        flash('Invalid credit amount.', 'danger')
        return redirect(url_for('credits'))
        
    try:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.post(
            f"{FASTAPI_URL}/api/credits/purchase",
            json={"amount": amount},
            headers=headers
        )
        
        if response.status_code == 200:
            flash(f'Successfully purchased {amount} credits!', 'success')
        else:
            error_data = response.json()
            flash(f'Failed to purchase credits: {error_data.get("detail", "Error")}', 'danger')
            
    except Exception as e:
        flash(f'Error during credit purchase: {str(e)}', 'danger')
        
    return redirect(url_for('credits'))

@app.route('/credits/redeem', methods=['POST'])
@login_required
def redeem_promo():
    promo_code = request.form.get('promo_code')
    
    if not promo_code:
        flash('Promo code is required.', 'danger')
        return redirect(url_for('credits'))
        
    try:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.post(
            f"{FASTAPI_URL}/api/credits/redeem/{promo_code}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            flash(f'Successfully redeemed promo code for {result.get("credits_added", 0)} credits!', 'success')
        else:
            error_data = response.json()
            flash(f'Failed to redeem promo code: {error_data.get("detail", "Invalid or expired code")}', 'danger')
            
    except Exception as e:
        flash(f'Error redeeming promo code: {str(e)}', 'danger')
        
    return redirect(url_for('credits'))

@app.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    limit = 10
    
    try:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.get(
            f"{FASTAPI_URL}/api/users/notifications",
            headers=headers
        )
        
        if response.status_code == 200:
            notifications_data = response.json()
            # Calculate total pages
            total_count = len(notifications_data)
            pages = (total_count + limit - 1) // limit  # Ceil division
        else:
            notifications_data = []
            pages = 1
            
    except Exception as e:
        flash(f'Error retrieving notifications: {str(e)}', 'danger')
        notifications_data = []
        pages = 1
        
    return render_template('notifications.html', notifications=notifications_data, page=page, pages=pages)

@app.route('/notifications/update/<int:notification_id>', methods=['POST'])
@login_required
def update_notification(notification_id):
    is_read = request.form.get('is_read') == 'True'
    
    try:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.put(
            f"{FASTAPI_URL}/api/users/notifications/{notification_id}",
            json={"is_read": is_read},
            headers=headers
        )
        
        if response.status_code == 200:
            if is_read:
                flash('Notification marked as read.', 'success')
            else:
                flash('Notification marked as unread.', 'info')
        else:
            flash('Failed to update notification.', 'danger')
            
    except Exception as e:
        flash(f'Error updating notification: {str(e)}', 'danger')
        
    return redirect(url_for('notifications'))

@app.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    try:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        # This would require an endpoint in FastAPI to mark all as read
        # For now, we'll manually update each notification
        
        response = requests.get(
            f"{FASTAPI_URL}/api/users/notifications?unread_only=true",
            headers=headers
        )
        
        if response.status_code == 200:
            unread_notifications = response.json()
            
            for notification in unread_notifications:
                requests.put(
                    f"{FASTAPI_URL}/api/users/notifications/{notification['id']}",
                    json={"is_read": True},
                    headers=headers
                )
                
            flash('All notifications marked as read.', 'success')
        else:
            flash('Failed to mark notifications as read.', 'danger')
            
    except Exception as e:
        flash(f'Error updating notifications: {str(e)}', 'danger')
        
    return redirect(url_for('notifications'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    email = request.form.get('email')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    try:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        data = {"email": email}
        
        # Include password data only if trying to change password
        if current_password and new_password:
            data["current_password"] = current_password
            data["new_password"] = new_password
            
        response = requests.put(
            f"{FASTAPI_URL}/api/users/me",
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            flash('Profile updated successfully!', 'success')
        else:
            error_data = response.json()
            flash(f'Failed to update profile: {error_data.get("detail", "Error")}', 'danger')
            
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'danger')
        
    return redirect(url_for('profile'))

@app.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    try:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.delete(
            f"{FASTAPI_URL}/api/users/me",
            headers=headers
        )
        
        if response.status_code == 200:
            logout_user()
            session.pop('access_token', None)
            flash('Your account has been deleted.', 'info')
            return redirect(url_for('index'))
        else:
            error_data = response.json()
            flash(f'Failed to delete account: {error_data.get("detail", "Error")}', 'danger')
            
    except Exception as e:
        flash(f'Error deleting account: {str(e)}', 'danger')
        
    return redirect(url_for('profile'))

@app.route('/api-docs')
def api_docs():
    return render_template('api_docs.html')

@app.route('/swagger-ui')
def swagger_ui():
    return redirect(f"{FASTAPI_URL}/docs")

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error_code=500, error_message="Internal server error"), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
