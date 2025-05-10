from functools import wraps
from flask import session, redirect, url_for, flash
import re
from models import db, Player, Team

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('auth.login'))

        from models import User
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('You do not have permission to access this page')
            return redirect(url_for('user.dashboard'))

        return f(*args, **kwargs)
    return decorated_function

def validate_password(password):
    """
    Validate password strength
    Returns a tuple (is_valid, error_message)
    """
    # Check length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    # Check for digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"

    # Common passwords check
    common_passwords = ['password', 'password123', '12345678', 'qwerty123']
    if password.lower() in common_passwords:
        return False, "This password is too common. Please choose a stronger password"

    return True, "Password is strong"

def get_or_create_player(name):
    """Find or create a player by name"""
    player = Player.query.filter_by(name=name.strip()).first()
    if not player:
        player = Player(name=name.strip())
        db.session.add(player)
        db.session.flush()  # Flush to get the ID without committing
    return player

def process_team(team_names):
    """Process team names and create team"""
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