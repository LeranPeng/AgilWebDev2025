"""
Admin Initialization Script - Run this to set up admin users
"""

import sys
import os
from flask import Flask
from werkzeug.security import generate_password_hash
from models import db, User
import getpass

# Create a minimal Flask app for db access
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///badminton.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def create_admin_user():
    """Create a new admin user"""
    print("=== Create New Admin User ===")
    username = input("Enter username: ")

    # Check if user already exists
    with app.app_context():
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User '{username}' already exists.")
            make_admin = input(f"Make '{username}' an admin? (y/n): ").lower() == 'y'

            if make_admin:
                existing_user.is_admin = True
                db.session.commit()
                print(f"User '{username}' is now an admin.")
            return

    email = input("Enter email: ")
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if password != confirm_password:
        print("Passwords do not match. Please try again.")
        return

    # Create new admin user
    with app.app_context():
        new_admin = User(username=username, email=email, is_admin=True)
        new_admin.set_password(password)

        db.session.add(new_admin)
        db.session.commit()
        print(f"Admin user '{username}' created successfully!")


def grant_admin_to_existing():
    """Grant admin access to an existing user"""
    print("=== Grant Admin to Existing User ===")

    with app.app_context():
        # List all non-admin users
        users = User.query.filter_by(is_admin=False).all()

        if not users:
            print("No non-admin users found.")
            return

        print("Available users:")
        for i, user in enumerate(users, 1):
            print(f"{i}. {user.username} ({user.email})")

        try:
            selection = int(input("Enter user number to make admin (0 to cancel): "))
            if selection == 0:
                return

            selected_user = users[selection - 1]
            selected_user.is_admin = True
            db.session.commit()
            print(f"User '{selected_user.username}' is now an admin.")

        except (ValueError, IndexError):
            print("Invalid selection.")


def list_admin_users():
    """List all admin users in the system"""
    print("=== Current Admin Users ===")

    with app.app_context():
        admins = User.query.filter_by(is_admin=True).all()

        if not admins:
            print("No admin users found.")
            return

        print("Admin users:")
        for i, admin in enumerate(admins, 1):
            print(f"{i}. {admin.username} ({admin.email})")


def revoke_admin():
    """Revoke admin access from a user"""
    print("=== Revoke Admin Access ===")

    with app.app_context():
        # List all admin users
        admins = User.query.filter_by(is_admin=True).all()

        if not admins:
            print("No admin users found.")
            return

        print("Admin users:")
        for i, admin in enumerate(admins, 1):
            print(f"{i}. {admin.username} ({admin.email})")

        try:
            selection = int(input("Enter user number to revoke admin (0 to cancel): "))
            if selection == 0:
                return

            selected_admin = admins[selection - 1]

            # Don't allow revoking the last admin
            if len(admins) == 1:
                print("Cannot revoke the last admin user.")
                return

            selected_admin.is_admin = False
            db.session.commit()
            print(f"Admin access revoked for '{selected_admin.username}'.")

        except (ValueError, IndexError):
            print("Invalid selection.")


def main_menu():
    """Display the main menu"""
    while True:
        print("\n=== Admin Management ===")
        print("1. Create New Admin User")
        print("2. Grant Admin to Existing User")
        print("3. List Admin Users")
        print("4. Revoke Admin Access")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ")

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


if __name__ == "__main__":
    # Check if database exists
    if not os.path.exists('badminton.db'):
        print("Database not found. Creating tables...")
        with app.app_context():
            db.create_all()

    # Check if there are any existing admin users
    with app.app_context():
        admin_count = User.query.filter_by(is_admin=True).count()

        if admin_count == 0:
            print("No admin users found. Creating initial admin...")
            create_admin_user()

    main_menu()