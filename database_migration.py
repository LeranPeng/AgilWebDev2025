"""
Migration script to add the SharedTournament table to the database
Run this after modifying models.py to include the SharedTournament model
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, db
from models import SharedTournament  # Import the model to ensure it's registered

def migrate_database():
    """Check if SharedTournament table exists, create it if not"""
    with app.app_context():
        try:
            # Check if the table exists by performing a simple query
            SharedTournament.query.first()
            print("SharedTournament table already exists")
        except Exception as e:
            if "no such table" in str(e).lower():
                print("Creating SharedTournament table...")
                # Create the table
                SharedTournament.__table__.create(db.engine)
                print("SharedTournament table created successfully")
            else:
                print(f"Error checking SharedTournament table: {str(e)}")

if __name__ == "__main__":
    migrate_database()