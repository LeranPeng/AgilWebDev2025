from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Tournament, Match, Player, Team
from utils import login_required, process_team, validate_match_players

# Create blueprint
match_bp = Blueprint('match', __name__)

@match_bp.route("/matches")
@login_required
def view_matches():
    """View all matches with edit/delete options"""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")

    # Get query parameters for filtering
    tournament_id = request.args.get('tournament_id', type=int)
    player_name = request.args.get('player_name', '')

    # Base query - join with Tournament to filter by user_id
    query = db.session.query(Match, Tournament).join(
        Tournament, Match.tournament_id == Tournament.id
    ).filter(Tournament.user_id == user_id)

    # Apply filters if provided
    if tournament_id:
        query = query.filter(Match.tournament_id == tournament_id)

    if player_name:
        # This is a more complex filter since players can be in either team
        player_matches = []
        player_ids = []

        # Find players with matching names
        players = Player.query.filter(Player.name.contains(player_name)).all()
        player_ids = [p.id for p in players]

        if player_ids:
            # Find teams containing these players
            team_ids = db.session.query(Team.id).filter(
                (Team.player1_id.in_(player_ids)) |
                (Team.player2_id.in_(player_ids))
            ).all()
            team_ids = [t[0] for t in team_ids]

            # Filter matches containing these teams
            query = query.filter(
                (Match.team1_id.in_(team_ids)) |
                (Match.team2_id.in_(team_ids))
            )

    # Get all tournaments for the filter dropdown
    tournaments = Tournament.query.filter_by(user_id=user_id).all()

    # Execute query and get results
    matches = query.order_by(Match.timestamp.desc()).all()

    # Prepare data for template
    match_data = []
    for match, tournament in matches:
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
            'tournament': tournament.name,
            'tournament_id': tournament.id,
            'date': match.timestamp.strftime('%Y-%m-%d'),
            'round': match.round_name,
            'group': match.group_name,
            'team1': ', '.join(team1_players),
            'team2': ', '.join(team2_players),
            'score1': match.score1,
            'score2': match.score2,
            'match_type': match.match_type,
            'winner': ', '.join(team1_players) if winner.id == team1.id else ', '.join(team2_players)
        })

    return render_template(
        "matches.html",
        matches=match_data,
        tournaments=tournaments,
        current_tournament=tournament_id,
        player_name=player_name
    )

@match_bp.route("/matches/<int:match_id>/edit", methods=["GET"])
@login_required
def edit_match(match_id):
    """Show form to edit a match"""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")

    # Get the match with validation that it belongs to the current user
    match = db.session.query(Match).join(
        Tournament, Match.tournament_id == Tournament.id
    ).filter(
        Match.id == match_id,
        Tournament.user_id == user_id
    ).first()

    if not match:
        flash("Match not found or you don't have permission to edit it")
        return redirect(url_for("match.view_matches"))

    # Get tournament, teams and players
    tournament = Tournament.query.get(match.tournament_id)
    team1 = Team.query.get(match.team1_id)
    team2 = Team.query.get(match.team2_id)

    # Get all tournament's that belong to user for potential tournament change
    tournaments = Tournament.query.filter_by(user_id=user_id).all()

    # Format team names for form display
    team1_name = team1.player1.name
    if team1.player2:
        team1_name += f", {team1.player2.name}"

    team2_name = team2.player1.name
    if team2.player2:
        team2_name += f", {team2.player2.name}"

    return render_template(
        "edit_match.html",
        match=match,
        tournament=tournament,
        tournaments=tournaments,
        team1_name=team1_name,
        team2_name=team2_name
    )

@match_bp.route("/matches/<int:match_id>/update", methods=["POST"])
@login_required
def update_match(match_id):
    """Process match update form"""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")

    # Get the match with validation that it belongs to the current user
    match = db.session.query(Match).join(
        Tournament, Match.tournament_id == Tournament.id
    ).filter(
        Match.id == match_id,
        Tournament.user_id == user_id
    ).first()

    if not match:
        flash("Match not found or you don't have permission to edit it")
        return redirect(url_for("match.view_matches"))

    try:
        # Get form data
        tournament_id = request.form.get("tournament_id", type=int)
        round_name = request.form.get("round_name")
        group_name = request.form.get("group_name", "")
        team1_name = request.form.get("team1")
        team2_name = request.form.get("team2")
        score1 = request.form.get("score1")
        score2 = request.form.get("score2")
        match_type = request.form.get("match_type")

        # Validate tournament is owned by user
        tournament = Tournament.query.filter_by(id=tournament_id, user_id=user_id).first()
        if not tournament:
            flash("Invalid tournament selection")
            return redirect(url_for("match.edit_match", match_id=match_id))

        # Process teams - either find existing teams or create new ones
        team1 = process_team(team1_name)
        team2 = process_team(team2_name)

        # Validate teams (ensure no player is on both sides in doubles)
        if match_type.endswith('Doubles') and not validate_match_players(team1, team2):
            flash("Error: A player cannot be on both sides of a doubles match")
            return redirect(url_for("match.edit_match", match_id=match_id))

        # Update match
        match.tournament_id = tournament_id
        match.round_name = round_name
        match.group_name = group_name
        match.team1_id = team1.id
        match.team2_id = team2.id
        match.score1 = score1
        match.score2 = score2
        match.match_type = match_type

        db.session.commit()
        flash("Match updated successfully!")
        return redirect(url_for("match.view_matches"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating match: {str(e)}")
        return redirect(url_for("match.edit_match", match_id=match_id))

@match_bp.route("/matches/<int:match_id>/delete", methods=["POST"])
@login_required
def delete_match(match_id):
    """Delete a match"""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")

    # Get the match with validation that it belongs to the current user
    match = db.session.query(Match).join(
        Tournament, Match.tournament_id == Tournament.id
    ).filter(
        Match.id == match_id,
        Tournament.user_id == user_id
    ).first()

    if not match:
        flash("Match not found or you don't have permission to delete it")
        return redirect(url_for("match.view_matches"))

    try:
        # Delete the match
        db.session.delete(match)
        db.session.commit()
        flash("Match deleted successfully!")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting match: {str(e)}")

    return redirect(url_for("match.view_matches"))