from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from models import db, User
from utils import validate_password

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validation
        if not username or not email or not password:
            flash("All fields are required")
            return redirect(url_for("auth.signup"))

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("auth.signup"))

        # Password strength validation
        is_valid, error_message = validate_password(password)
        if not is_valid:
            flash(error_message)
            return redirect(url_for("auth.signup"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken")
            return redirect(url_for("auth.signup"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered")
            return redirect(url_for("auth.signup"))

        # Create new user
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash("Account created successfully! Please log in.")
            # Use an absolute URL for the redirect to ensure it works
            return redirect(url_for("auth.login", _external=True))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {str(e)}")
            return redirect(url_for("auth.signup"))

    return render_template("html/Signup.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Username and password are required")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session.permanent = True
            session["user_id"] = user.id
            session["username"] = user.username

            # Save previous login to session before updating it
            session["last_login"] = user.last_login.strftime('%Y-%m-%dT%H:%M:%SZ') if user.last_login else None

            # Update login time
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash("Login successful!")
            return redirect(url_for("user.dashboard"))
        else:
            flash("Invalid username or password")

    return render_template("html/Login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("auth.login"))