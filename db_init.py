#!/usr/bin/env python3
"""
Initialize the database with all the tables defined in the models.
This script should be run when the application starts for the first time
or when database migrations are needed.
"""

from database import engine
import models

# Create all tables in the database
def initialize_database():
    print("Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    initialize_database()