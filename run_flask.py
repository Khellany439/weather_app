#!/usr/bin/env python3
"""
Start the Flask frontend application on port 5000.
This should be run after starting the FastAPI backend on port 5001.
"""

from main import app

if __name__ == "__main__":
    # Run Flask on port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)