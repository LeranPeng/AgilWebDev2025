from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Tournament, User, Match, Team, SharedTournament
from utils import login_required

# Create blueprint
sharing_bp = Blueprint('sharing', __name__)

@sharing_bp.route("/share")
@login_required
def share_page():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Get tournaments created by the current user
    user_id = session.get("user_id")
    my_tournaments = Tournament.query.filter_by(user_id=user_id).all()

    # Get all other users (potential recipients)
    other_users = User.query.filter(User.id != user_id).all()

    # Get existing shares
    existing_shares = SharedTournament.query.filter_by(owner_id=user_id).all()

    # Create a dictionary for quick lookup of shares
    shares_by_tournament = {}
    for share in existing_shares:
        if share.tournament_id not in shares_by_tournament:
            shares_by_tournament[share.tournament_id] = []
        shares_by_tournament[share.tournament_id].append(share.shared_with_id)

    return render_template(
        "share.html",
        tournaments=my_tournaments,
        users=other_users,
        shares=shares_by_tournament
    )

@sharing_bp.route("/share/create", methods=["POST"])
@login_required
def create_share():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    owner_id = session.get("user_id")
    tournament_id = request.form.get("tournament_id", type=int)
    shared_with_id = request.form.get("user_id", type=int)

    # Validate input
    if not tournament_id or not shared_with_id:
        flash("Missing required information")
        return redirect(url_for("sharing.share_page"))

    # Verify the tournament belongs to the current user
    tournament = Tournament.query.filter_by(id=tournament_id, user_id=owner_id).first()
    if not tournament:
        flash("Tournament not found or you don't have permission to share it")
        return redirect(url_for("sharing.share_page"))

    # Verify the target user exists
    target_user = User.query.get(shared_with_id)
    if not target_user:
        flash("Target user not found")
        return redirect(url_for("sharing.share_page"))

    # Check if already shared
    existing_share = SharedTournament.query.filter_by(
        tournament_id=tournament_id,
        owner_id=owner_id,
        shared_with_id=shared_with_id
    ).first()

    if existing_share:
        flash(f"Tournament already shared with {target_user.username}")
        return redirect(url_for("sharing.share_page"))

    # Create the share
    try:
        share = SharedTournament(
            tournament_id=tournament_id,
            owner_id=owner_id,
            shared_with_id=shared_with_id
        )
        db.session.add(share)
        db.session.commit()
        flash(f"Tournament shared with {target_user.username} successfully!")
    except Exception as e:
        db.session.rollback()
        flash(f"Error sharing tournament: {str(e)}")

    return redirect(url_for("sharing.share_page"))

@sharing_bp.route("/share/delete", methods=["POST"])
@login_required
def delete_share():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    owner_id = session.get("user_id")
    tournament_id = request.form.get("tournament_id", type=int)
    shared_with_id = request.form.get("user_id", type=int)

    # Validate input
    if not tournament_id or not shared_with_id:
        flash("Missing required information")
        return redirect(url_for("sharing.share_page"))

    # Find the sharing relationship
    share = SharedTournament.query.filter_by(
        tournament_id=tournament_id,
        owner_id=owner_id,
        shared_with_id=shared_with_id
    ).first()

    if not share:
        flash("Sharing relationship not found")
        return redirect(url_for("sharing.share_page"))

    # Delete the share
    try:
        username = User.query.get(shared_with_id).username
        db.session.delete(share)
        db.session.commit()
        flash(f"Stopped sharing tournament with {username}")
    except Exception as e:
        db.session.rollback()
        flash(f"Error removing sharing relationship: {str(e)}")

    return redirect(url_for("sharing.share_page"))

@sharing_bp.route("/shared-with-me")
@login_required
def shared_with_me():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")

    # Get tournaments shared with the current user
    shared_tournaments = SharedTournament.query.filter_by(shared_with_id=user_id).all()

    return render_template(
        "shared_with_me.html",
        shared_tournaments=shared_tournaments
    )

@sharing_bp.route("/shared-with-me/<int:tournament_id>")
@login_required
def view_shared_tournament(tournament_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session.get("user_id")

    # Check if the tournament is shared with the current user
    share = SharedTournament.query.filter_by(
        tournament_id=tournament_id,
        shared_with_id=user_id
    ).first()

    if not share:
        flash("You don't have access to this tournament")
        return redirect(url_for("sharing.shared_with_me"))

    # Get tournament details
    tournament = Tournament.query.get(tournament_id)
    if not tournament:
        flash("Tournament not found")
        return redirect(url_for("sharing.shared_with_me"))

    # Get matches for this tournament
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
        "view_shared_tournament.html",
        tournament=tournament,
        matches=match_data,
        owner=User.query.get(tournament.user_id),
        shared_by=User.query.get(share.owner_id)
    )