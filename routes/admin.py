from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from sqlalchemy import func, desc
from datetime import datetime
from models import db, User, Tournament, Player, Team, Match
from utils import admin_required

# Create blueprint with proper URL prefix
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin Dashboard
@admin_bp.route('/')
@admin_required
def admin_dashboard():
    # Get summary statistics
    user_count = User.query.count()
    tournament_count = Tournament.query.count()
    match_count = Match.query.count()
    player_count = Player.query.count()

    # Get recent activity
    recent_users = User.query.order_by(User.last_login.desc()).limit(5).all()
    recent_tournaments = Tournament.query.order_by(Tournament.created_at.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        user_count=user_count,
        tournament_count=tournament_count,
        match_count=match_count,
        player_count=player_count,
        recent_users=recent_users,
        recent_tournaments=recent_tournaments
    )


# User Management
@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template("admin/users.html", users=users)


@admin_bp.route('/users/<int:user_id>', methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        is_admin = 'is_admin' in request.form

        # Validate unique username and email
        username_exists = User.query.filter(User.username == username, User.id != user_id).first()
        email_exists = User.query.filter(User.email == email, User.id != user_id).first()

        if username_exists:
            flash("Username already taken")
            return redirect(url_for("admin.edit_user", user_id=user_id))

        if email_exists:
            flash("Email already registered")
            return redirect(url_for("admin.edit_user", user_id=user_id))

        # Update user
        user.username = username
        user.email = email
        user.is_admin = is_admin

        # Update password if provided
        new_password = request.form.get("new_password")
        if new_password:
            user.set_password(new_password)

        db.session.commit()
        flash("User updated successfully")
        return redirect(url_for("admin.manage_users"))

    return render_template("admin/edit_user.html", user=user)


@admin_bp.route('/users/create', methods=["GET", "POST"])
@admin_required
def create_user():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        is_admin = 'is_admin' in request.form

        # Validation
        if not username or not email or not password:
            flash("All fields are required")
            return redirect(url_for("admin.create_user"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken")
            return redirect(url_for("admin.create_user"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered")
            return redirect(url_for("admin.create_user"))

        # Create new user
        new_user = User(username=username, email=email, is_admin=is_admin)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("User created successfully")
        return redirect(url_for("admin.manage_users"))

    return render_template("admin/create_user.html")


@admin_bp.route('/users/<int:user_id>/delete', methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # Don't allow deleting your own account
    if user.id == session.get('user_id'):
        flash("You cannot delete your own account")
        return redirect(url_for("admin.manage_users"))

    # Check if user has associated tournaments
    tournaments = Tournament.query.filter_by(user_id=user.id).all()
    if tournaments:
        flash(f"Cannot delete user with {len(tournaments)} associated tournaments")
        return redirect(url_for("admin.manage_users"))

    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully")
    return redirect(url_for("admin.manage_users"))


# Tournament Management
@admin_bp.route('/tournaments')
@admin_required
def manage_tournaments():
    tournaments = Tournament.query.all()
    return render_template("admin/tournaments.html", tournaments=tournaments)


@admin_bp.route('/tournaments/<int:tournament_id>')
@admin_required
def view_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    matches = Match.query.filter_by(tournament_id=tournament_id).all()

    match_data = []
    for match in matches:
        team1 = Team.query.get(match.team1_id)
        team2 = Team.query.get(match.team2_id)

        team1_players = [team1.player1.name]
        if team1.player2:
            team1_players.append(team1.player2.name)

        team2_players = [team2.player1.name]
        if team2.player2:
            team2_players.append(team2.player2.name)

        winner = match.get_winner()

        match_data.append({
            'id': match.id,
            'round': match.round_name,
            'group': match.group_name,
            'team1': ', '.join(team1_players),
            'team2': ', '.join(team2_players),
            'score1': match.score1,
            'score2': match.score2,
            'match_type': match.match_type,
            'date': match.timestamp.strftime('%Y-%m-%d'),
            'winner': ', '.join(team1_players) if winner.id == team1.id else ', '.join(team2_players)
        })

    return render_template(
        "admin/view.html",
        tournament=tournament,
        matches=match_data,
        organizer=User.query.get(tournament.user_id)
    )


@admin_bp.route('/tournaments/<int:tournament_id>/delete', methods=["POST"])
@admin_required
def delete_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)

    # Delete associated matches
    Match.query.filter_by(tournament_id=tournament_id).delete()

    # Delete the tournament
    db.session.delete(tournament)
    db.session.commit()

    flash("Tournament and all associated matches deleted successfully")
    return redirect(url_for("admin.manage_tournaments"))


# Player Management
@admin_bp.route('/players')
@admin_required
def manage_players():
    players = Player.query.all()
    return render_template("admin/players.html", players=players)


@admin_bp.route('/players/<int:player_id>')
@admin_required
def view_player(player_id):
    player = Player.query.get_or_404(player_id)

    # Count matches
    singles_matches = db.session.query(Match).join(
        Team, ((Match.team1_id == Team.id) | (Match.team2_id == Team.id))
    ).filter(
        (Team.player1_id == player.id) & (Team.player2_id == None)
    ).count()

    doubles_matches = db.session.query(Match).join(
        Team, ((Match.team1_id == Team.id) | (Match.team2_id == Team.id))
    ).filter(
        ((Team.player1_id == player.id) | (Team.player2_id == player.id)) &
        (Team.player2_id != None)
    ).count()

    # Get recent matches
    recent_matches = []
    teams = Team.query.filter((Team.player1_id == player.id) | (Team.player2_id == player.id)).all()
    team_ids = [team.id for team in teams]

    if team_ids:
        matches = Match.query.filter(
            (Match.team1_id.in_(team_ids)) | (Match.team2_id.in_(team_ids))
        ).order_by(Match.timestamp.desc()).limit(10).all()

        for match in matches:
            tournament = Tournament.query.get(match.tournament_id)
            team1 = Team.query.get(match.team1_id)
            team2 = Team.query.get(match.team2_id)

            is_team1 = match.team1_id in team_ids

            team1_players = [team1.player1.name]
            if team1.player2:
                team1_players.append(team1.player2.name)

            team2_players = [team2.player1.name]
            if team2.player2:
                team2_players.append(team2.player2.name)

            winner = match.get_winner()
            is_winner = (is_team1 and winner.id == team1.id) or (not is_team1 and winner.id == team2.id)

            recent_matches.append({
                'id': match.id,
                'tournament': tournament.name,
                'date': match.timestamp.strftime('%Y-%m-%d'),
                'opponent': ', '.join(team2_players) if is_team1 else ', '.join(team1_players),
                'result': 'Win' if is_winner else 'Loss',
                'score': match.score1 if is_team1 else match.score2
            })

    return render_template(
        "admin/view_player.html",
        player=player,
        singles_matches=singles_matches,
        doubles_matches=doubles_matches,
        recent_matches=recent_matches
    )


@admin_bp.route('/players/<int:player_id>/merge', methods=["GET", "POST"])
@admin_required
def merge_player(player_id):
    player = Player.query.get_or_404(player_id)

    if request.method == "POST":
        merge_with_id = request.form.get("merge_with_id", type=int)

        if not merge_with_id:
            flash("No player selected to merge with")
            return redirect(url_for("admin.merge_player", player_id=player_id))

        merge_with = Player.query.get_or_404(merge_with_id)

        # Update all teams where the merge_with player is player1
        teams_p1 = Team.query.filter_by(player1_id=merge_with.id).all()
        for team in teams_p1:
            team.player1_id = player.id

        # Update all teams where the merge_with player is player2
        teams_p2 = Team.query.filter_by(player2_id=merge_with.id).all()
        for team in teams_p2:
            team.player2_id = player.id

        # Delete the merged player
        db.session.delete(merge_with)
        db.session.commit()

        flash(f"Successfully merged player {merge_with.name} into {player.name}")
        return redirect(url_for("admin.view_player", player_id=player_id))

    # Get potential duplicate players (same or similar names)
    potential_duplicates = Player.query.filter(
        Player.id != player_id,
        Player.name.like(f"%{player.name.split()[0]}%")  # Match on first name
    ).all()

    return render_template(
        "admin/merge_player.html",
        player=player,
        potential_duplicates=potential_duplicates
    )


# System Stats & Maintenance
@admin_bp.route('/stats')
@admin_required
def system_stats():
    # Get overall statistics
    user_count = User.query.count()
    admin_count = User.query.filter_by(is_admin=True).count()
    tournament_count = Tournament.query.count()
    match_count = Match.query.count()
    player_count = Player.query.count()
    team_count = Team.query.count()

    # Get activity over time
    tournaments_by_month = db.session.query(
        func.strftime('%Y-%m', Tournament.date).label('month'),
        func.count(Tournament.id).label('count')
    ).group_by('month').order_by('month').all()

    matches_by_month = db.session.query(
        func.strftime('%Y-%m', Match.timestamp).label('month'),
        func.count(Match.id).label('count')
    ).group_by('month').order_by('month').all()

    # Most active users
    active_users = db.session.query(
        User.id, User.username,
        func.count(Tournament.id).label('tournament_count')
    ).join(Tournament).group_by(User.id).order_by(desc('tournament_count')).limit(10).all()

    # Popular match types
    match_types = db.session.query(
        Match.match_type,
        func.count(Match.id).label('count')
    ).group_by(Match.match_type).order_by(desc('count')).all()

    return render_template(
        "admin/stats.html",
        user_count=user_count,
        admin_count=admin_count,
        tournament_count=tournament_count,
        match_count=match_count,
        player_count=player_count,
        team_count=team_count,
        tournaments_by_month=tournaments_by_month,
        matches_by_month=matches_by_month,
        active_users=active_users,
        match_types=match_types
    )


# Database Maintenance
@admin_bp.route('/maintenance')
@admin_required
def database_maintenance():
    # Identify orphaned records
    orphaned_teams = Team.query.filter(
        ~Team.matches_as_team1.any() & ~Team.matches_as_team2.any()
    ).count()

    # Players with no matches
    inactive_players = Player.query.filter(
        ~Player.teams_as_player1.any() & ~Player.teams_as_player2.any()
    ).count()

    # Users with no tournaments
    users_without_tournaments = User.query.filter(
        ~User.tournaments.any()
    ).count()

    # Tournaments with no matches
    empty_tournaments = Tournament.query.filter(
        ~Tournament.matches.any()
    ).count()

    return render_template(
        "admin/maintenance.html",
        orphaned_teams=orphaned_teams,
        inactive_players=inactive_players,
        users_without_tournaments=users_without_tournaments,
        empty_tournaments=empty_tournaments
    )


@admin_bp.route('/maintenance/cleanup', methods=["POST"])
@admin_required
def perform_cleanup():
    action = request.form.get("action")

    if action == "orphaned_teams":
        # Delete teams without matches
        teams = Team.query.filter(
            ~Team.matches_as_team1.any() & ~Team.matches_as_team2.any()
        ).all()

        for team in teams:
            db.session.delete(team)

        db.session.commit()
        flash(f"Deleted {len(teams)} orphaned teams")

    elif action == "inactive_players":
        # Delete players without teams
        players = Player.query.filter(
            ~Player.teams_as_player1.any() & ~Player.teams_as_player2.any()
        ).all()

        for player in players:
            db.session.delete(player)

        db.session.commit()
        flash(f"Deleted {len(players)} inactive players")

    elif action == "empty_tournaments":
        # Delete tournaments without matches
        tournaments = Tournament.query.filter(
            ~Tournament.matches.any()
        ).all()

        for tournament in tournaments:
            db.session.delete(tournament)

        db.session.commit()
        flash(f"Deleted {len(tournaments)} empty tournaments")

    return redirect(url_for("admin.database_maintenance"))