"""
Admin Initialization Script - Run this to set up admin users.
"""

# Import necessary libraries
import sys
import os
from flask import Flask
from werkzeug.security import generate_password_hash
from models import db, User
import getpass  # For securely entering passwords

# Create a minimal Flask app to access the database
app = Flask(__name__)
# Configure the database URI, using an environment variable or defaulting to SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///badminton.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking for performance
db.init_app(app)  # Initialize the database with the Flask app

def create_admin_user():
    """Create a new admin user with specified credentials."""
    print("=== Create New Admin User ===")
    username = input("Enter username: ")

    # Check if the user already exists in the database
    with app.app_context():
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists.")
            # Prompt to grant admin rights if the user exists but is not an admin
            make_admin = input(f"Make '{username}' an admin? (y/n): ").lower() == 'y'

            if make_admin:
                existing_user.is_admin = True
                db.session.commit()  # Update the database
                print(f"User '{username}' is now an admin.")
            return  # Exit function if user already exists

    # Gather user details for new admin account
    email = input("Enter email: ")
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    # Check if the entered passwords match
    if password != confirm_password:
        print("Passwords do not match. Please try again.")
        return

    # Create a new admin user
    with app.app_context():
        new_admin = User(username=username, email=email, is_admin=True)
        new_admin.set_password(password)  # Securely set the password

        db.session.add(new_admin)  # Add new admin to the database
        db.session.commit()  # Commit the transaction
        print(f"Admin user '{username}' created successfully!")

def grant_admin_to_existing():
    """Grant admin access to an existing non-admin user."""
    print("=== Grant Admin to Existing User ===")

    with app.app_context():
        # Retrieve all non-admin users from the database
        users = User.query.filter_by(is_admin=False).all()

        # Check if there are any non-admin users to promote
        if not users:
            print("No non-admin users found.")
            return

        # Display a list of non-admin users
        print("Available users:")
        for i, user in enumerate(users, 1):
            print(f"{i}. {user.username} ({user.email})")

        try:
            # Prompt user to select a user to grant admin rights
            selection = int(input("Enter user number to make admin (0 to cancel): "))
            if selection == 0:
                return

            # Grant admin rights to the selected user
            selected_user = users[selection - 1]
            selected_user.is_admin = True
            db.session.commit()
            print(f"User '{selected_user.username}' is now an admin.")

        except (ValueError, IndexError):
            print("Invalid selection.")  # Handle invalid input gracefully

def list_admin_users():
    """Display a list of all admin users."""
    print("=== Current Admin Users ===")

    with app.app_context():
        # Retrieve all admin users from the database
        admins = User.query.filter_by(is_admin=True).all()

        # Check if there are any admin users
        if not admins:
            print("No admin users found.")
            return

        # Display the list of admin users
        print("Admin users:")
        for i, admin in enumerate(admins, 1):
            print(f"{i}. {admin.username} ({admin.email})")

def revoke_admin():
    """Revoke admin access from an existing admin user."""
    print("=== Revoke Admin Access ===")

    with app.app_context():
        # Retrieve all admin users from the database
        admins = User.query.filter_by(is_admin=True).all()

        # Check if there are any admins to revoke
        if not admins:
            print("No admin users found.")
            return

        # Display the list of admin users
        print("Admin users:")
        for i, admin in enumerate(admins, 1):
            print(f"{i}. {admin.username} ({admin.email})")

        try:
            # Prompt user to select an admin to revoke rights
            selection = int(input("Enter user number to revoke admin (0 to cancel): "))
            if selection == 0:
                return

            selected_admin = admins[selection - 1]

            # Prevent revoking the last remaining admin user
            if len(admins) == 1:
                print("Cannot revoke the last admin user.")
                return

            # Revoke admin rights from the selected user
            selected_admin.is_admin = False
            db.session.commit()
            print(f"Admin access revoked for '{selected_admin.username}'.")

        except (ValueError, IndexError):
            print("Invalid selection.")  # Handle invalid input

def main_menu():
    """Display the main admin management menu."""
    while True:
        # Show menu options
        print("\n=== Admin Management ===")
        print("1. Create New Admin User")
        print("2. Grant Admin to Existing User")
        print("3. List Admin Users")
        print("4. Revoke Admin Access")
        print("5. Exit")

        # Read the user's menu choice
        choice = input("Enter your choice (1-5): ")

        # Call the appropriate function based on user input
        if choice == '1':
            create_admin_user()
        elif choice == '2':
            grant_admin_to_existing()
        elif choice == '3':
            list_admin_users()
        elif choice == '4':
            revoke_admin()
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 5.")

# Entry point for the script
if __name__ == "__main__":
    # Check if the database exists; create if not
    if not os.path.exists('badminton.db'):
        print("Database not found. Creating tables...")
        with app.app_context():
            db.create_all()

    # Check if there are any existing admin users; create one if none exist
    with app.app_context():
        admin_count = User.query.filter_by(is_admin=True).count()

        if admin_count == 0:
            print("No admin users found. Creating initial admin...")
            create_admin_user()

    # Display the admin management menu
    main_menu()
