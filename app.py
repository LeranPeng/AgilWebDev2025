from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import csv
import io
import json
from models import db, User, Tournament, Player, Team, Match
from functools import wraps
from flask_wtf.csrf import CSRFProtect, generate_csrf

# Create the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'JESUS SECRET KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///badminton.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Configure CSRF protection
csrf = CSRFProtect(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the database with the app
db.init_app(app)

# Import analytics AFTER initializing db
from analytics import analytics

# Register the analytics blueprint
app.register_blueprint(analytics)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to find or create a player
def get_or_create_player(name):
    player = Player.query.filter_by(name=name.strip()).first()
    if not player:
        player = Player(name=name.strip())
        db.session.add(player)
        db.session.flush()  # Flush to get the ID without committing
    return player


# Helper function to process team names and create team
def process_team(team_names):
    players = [name.strip() for name in team_names.split(',')]
    player1 = get_or_create_player(players[0])

    player2 = None
    if len(players) > 1 and players[1]:
        player2 = get_or_create_player(players[1])

    # Check if this team already exists
    if player2:
        team = Team.query.filter(
            ((Team.player1_id == player1.id) & (Team.player2_id == player2.id)) |
            ((Team.player1_id == player2.id) & (Team.player2_id == player1.id))
        ).first()
    else:
        team = Team.query.filter_by(player1_id=player1.id, player2_id=None).first()

    if not team:
        team = Team(player1_id=player1.id, player2_id=player2.id if player2 else None)
        db.session.add(team)
        db.session.flush()  # Flush to get the ID without committing

    return team


# Routes
@app.route("/")
@app.route("/home")
def index():
    return render_template("html/homepage.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validation
        if not username or not email or not password:
            flash("All fields are required")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("signup"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken")
            return redirect(url_for("signup"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered")
            return redirect(url_for("signup"))

        # Create new user
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash("Account created successfully! Please log in.")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {str(e)}")
            return redirect(url_for("signup"))

    return render_template("html/Signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Username and password are required")
            return redirect(url_for("login"))

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
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")

    return render_template("html/Login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))

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


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("login"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))

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
                    return redirect(url_for("settings"))
                user.username = username
                session["username"] = username

            if email and email != user.email:
                if User.query.filter_by(email=email).first() and User.query.filter_by(
                        email=email).first().id != user.id:
                    flash("Email already registered")
                    return redirect(url_for("settings"))
                user.email = email

            # Update password if provided
            if current_password and new_password:
                if not user.check_password(current_password):
                    flash("Current password is incorrect")
                    return redirect(url_for("settings"))

                if new_password != confirm_password:
                    flash("New passwords do not match")
                    return redirect(url_for("settings"))

                user.set_password(new_password)

            db.session.commit()
            flash("Settings updated successfully!")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating settings: {str(e)}")

    # Create a hidden input field containing the CSRF token
    from flask_wtf.csrf import generate_csrf
    csrf_token_input = f'<input type="hidden" name="csrf_token" value="{generate_csrf()}">'

    return render_template("html/User_settings.html", user=user, csrf_token_input=csrf_token_input)


@app.route("/upload")
@login_required
def upload_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("html/upload.html")


@app.route("/input_form")
@login_required
def input_form():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("html/InputForm.html")


def validate_match_players(team1, team2):
    """Validate that no player appears on both sides of the match"""
    team1_players = {team1.player1_id}
    if team1.player2_id:
        team1_players.add(team1.player2_id)

    team2_players = {team2.player1_id}
    if team2.player2_id:
        team2_players.add(team2.player2_id)

    # Check for intersection between the two sets
    if team1_players.intersection(team2_players):
        return False  # Players appearing on both sides

    return True  # No duplicates

@app.route("/submit_results", methods=["POST"])
@login_required
def submit_results():
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        # Get tournament details
        tournament_name = request.form.get("tournament_name")
        tournament_date_str = request.form.get("tournament_date")
        location = request.form.get("location", "")

        if not tournament_name or not tournament_date_str:
            flash("Tournament name and date are required")
            return redirect(url_for("input_form"))

        tournament_date = datetime.strptime(tournament_date_str, '%Y-%m-%d').date()

        # Create tournament
        tournament = Tournament(
            name=tournament_name,
            date=tournament_date,
            location=location,
            user_id=session["user_id"]
        )
        db.session.add(tournament)
        db.session.flush()  # Get the tournament ID without committing yet

        # Process match data
        rounds = request.form.getlist("round[]")
        groups = request.form.getlist("group[]")
        team1_names = request.form.getlist("team1[]")
        team2_names = request.form.getlist("team2[]")
        score1_list = request.form.getlist("score1[]")
        score2_list = request.form.getlist("score2[]")
        match_types = request.form.getlist("match_type[]")

        for i in range(len(rounds)):
            if i < len(team1_names) and i < len(team2_names) and i < len(score1_list) and i < len(
                    score2_list) and i < len(match_types):
                # Process teams
                team1 = process_team(team1_names[i])
                team2 = process_team(team2_names[i])

                # Add validation to prevent players appearing on both sides in doubles
                if match_types[i].endswith('Doubles') and not validate_match_players(team1, team2):
                    flash(f"Error: A player cannot be on both sides of the match (in match #{i + 1})")
                    return redirect(url_for("input_form"))

                group_name = groups[i] if i < len(groups) else ""

                # Create match
                match = Match(
                    tournament_id=tournament.id,
                    round_name=rounds[i],
                    group_name=group_name,
                    team1_id=team1.id,
                    team2_id=team2.id,
                    score1=score1_list[i],
                    score2=score2_list[i],
                    match_type=match_types[i]
                )
                db.session.add(match)

        # Commit all database changes
        db.session.commit()

        flash("Tournament results submitted successfully!")
        return redirect(url_for("dashboard"))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error submitting results: {str(e)}")
        flash(f"Error submitting results: {str(e)}")
        return redirect(url_for("input_form"))




@app.route("/upload/pre", methods=["POST"])
@login_required
def upload_pre_tournament():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if 'pre_file' not in request.files:
        flash('No file part')
        return redirect(url_for("upload_page"))

    file = request.files['pre_file']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for("upload_page"))

    if file:
        # Process the CSV file
        try:
            # Read the CSV data
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_data = list(csv.reader(stream))

            # Validate and process data
            player_count = 0
            for row in csv_data[1:]:  # Skip header row
                if len(row) >= 1 and row[0]:
                    player = get_or_create_player(row[0])
                    player_count += 1

            db.session.commit()
            flash(f'Successfully imported {player_count} players!')
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}')

        return redirect(url_for('upload_page'))


@app.route("/upload/post", methods=["POST"])
@login_required
def upload_post_tournament():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if 'post_file' not in request.files:
        flash('No file part')
        return redirect(url_for("upload_page"))

    file = request.files['post_file']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for("upload_page"))

    if file:
        try:
            # Save the file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Read the CSV data
            with open(filepath, 'r') as f:
                csv_reader = csv.reader(f)
                headers = next(csv_reader)
                matches = list(csv_reader)

            # Fixed template path - without the html/ prefix since it's in the templates/ directory
            return render_template('review_results.html', headers=headers, matches=matches, filename=filename)

        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('upload_page'))

@app.route("/confirm_results/<filename>", methods=["POST"])
@login_required
def confirm_results(filename):
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        tournament_name = request.form.get("tournament_name", f"Tournament from {filename}")
        tournament_date = datetime.now().date()

        # Create tournament
        tournament = Tournament(
            name=tournament_name,
            date=tournament_date,
            location=request.form.get("location", ""),
            user_id=session["user_id"]
        )
        db.session.add(tournament)
        db.session.flush()

        # Process the CSV file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        with open(filepath, 'r') as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader)

            # Process each row in the CSV
            match_count = 0
            for row in csv_reader:
                if len(row) >= 4:  # Ensure row has enough data
                    try:
                        team1 = process_team(row[0])
                        team2 = process_team(row[1])

                        # Check if players appear on both sides
                        match_type = row[5] if len(row) > 5 else "Unknown"
                        if "Doubles" in match_type and not validate_match_players(team1, team2):
                            flash(
                                f"Error: In doubles matches, players cannot appear on both sides (in {row[0]} vs {row[1]})")
                            return redirect(url_for('upload_page'))

                        match = Match(
                            tournament_id=tournament.id,
                            round_name=row[4] if len(row) > 4 else "Unknown",
                            team1_id=team1.id,
                            team2_id=team2.id,
                            score1=row[2] if len(row) > 2 else "0-0",
                            score2=row[3] if len(row) > 3 else "0-0",
                            match_type=row[5] if len(row) > 5 else "Unknown"
                        )
                        db.session.add(match)
                        match_count += 1
                    except Exception as e:
                        app.logger.error(f"Error processing match row: {str(e)}")
                        continue

        db.session.commit()
        os.remove(filepath)  # Clean up the temporary file

        flash(f'Successfully imported tournament with {match_count} matches!')
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing results: {str(e)}')
        return redirect(url_for('upload_page'))


# Helper routes for AJAX
@app.route("/api/matches/<int:tournament_id>")
@login_required
def get_matches(tournament_id):
    if "user_id" not in session:
        return jsonify({"error": "Not authorized"}), 401

    tournament = Tournament.query.filter_by(id=tournament_id, user_id=session["user_id"]).first()
    if not tournament:
        return jsonify({"error": "Tournament not found"}), 404

    matches = Match.query.filter_by(tournament_id=tournament_id).all()
    results = []

    for match in matches:
        team1_name = match.team1.player1.name
        if match.team1.player2:
            team1_name += f", {match.team1.player2.name}"

        team2_name = match.team2.player1.name
        if match.team2.player2:
            team2_name += f", {match.team2.player2.name}"

        results.append({
            "id": match.id,
            "round": match.round_name,
            "group": match.group_name,
            "team1": team1_name,
            "team2": team2_name,
            "score1": match.score1,
            "score2": match.score2,
            "match_type": match.match_type,
            "date": match.timestamp.strftime("%Y-%m-%d")
        })

    return jsonify(results)

@app.route("/how-it-works")
def how_it_works():
    return render_template("html/how_it_works.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('html/404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('html/500.html'), 500

@app.errorhandler(400)
def bad_request(e):
    return render_template('html/400.html'), 400


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)