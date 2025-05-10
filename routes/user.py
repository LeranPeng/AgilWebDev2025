from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import generate_csrf
from models import db, User, Tournament, Match
from utils import login_required

# Create blueprint
user_bp = Blueprint('user', __name__)

@user_bp.route("/")
@user_bp.route("/home")
def index():
    return render_template("html/homepage.html")

@user_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    tournament_count = Tournament.query.filter_by(user_id=user.id).count()
    latest_tournament = Tournament.query.filter_by(user_id=user.id).order_by(Tournament.created_at.desc()).first()
    latest_date = latest_tournament.date.strftime("%b %d, %Y") if latest_tournament else "No tournaments yet"

    recent_matches = []
    matches = Match.query.join(Tournament).filter(Tournament.user_id == user.id).order_by(Match.timestamp.desc()).limit(5).all()

    for match in matches:
        team1_players = [match.team1.player1.name]
        if match.team1.player2:
            team1_players.append(match.team1.player2.name)
        team2_players = [match.team2.player1.name]
        if match.team2.player2:
            team2_players.append(match.team2.player2.name)
        winner = match.get_winner()
        is_winner_team1 = winner.id == match.team1.id
        recent_matches.append({
            "team1": " vs ".join(team1_players),
            "team2": " vs ".join(team2_players),
            "score": f"{match.score1} · {match.timestamp.strftime('%Y-%m-%d')}",
            "is_winner": is_winner_team1,
            "match_date": match.timestamp.strftime('%Y-%m-%d')
        })

    last_login = session.get("last_login")

    return render_template(
        "html/dashboard.html",
        user=user,
        username=user.username,
        email=user.email,
        last_login=last_login,  # Send ISO string to HTML
        tournament_count=tournament_count,
        latest_upload=latest_date,
        upcoming_matches=3,
        recent_matches=recent_matches
    )

@user_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        current_password = request.form.get("currentPassword")
        new_password = request.form.get("newPassword")
        confirm_password = request.form.get("confirmPassword")

        try:
            # Update username and email
            if username and username != user.username:
                if User.query.filter_by(username=username).first() and User.query.filter_by(
                        username=username).first().id != user.id:
                    flash("Username already taken")
                    return redirect(url_for("user.settings"))
                user.username = username
                session["username"] = username

            if email and email != user.email:
                if User.query.filter_by(email=email).first() and User.query.filter_by(
                        email=email).first().id != user.id:
                    flash("Email already registered")
                    return redirect(url_for("user.settings"))
                user.email = email

            # Update password if provided
            if current_password and new_password:
                if not user.check_password(current_password):
                    flash("Current password is incorrect")
                    return redirect(url_for("user.settings"))

                if new_password != confirm_password:
                    flash("New passwords do not match")
                    return redirect(url_for("user.settings"))

                user.set_password(new_password)

            db.session.commit()
            flash("Settings updated successfully!")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating settings: {str(e)}")

    # Create a hidden input field containing the CSRF token
    csrf_token_input = f'<input type="hidden" name="csrf_token" value="{generate_csrf()}">'

    return render_template("html/User_settings.html", user=user, csrf_token_input=csrf_token_input)

@user_bp.route("/how-it-works")
def how_it_works():
    return render_template("html/how_it_works.html")