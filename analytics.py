"""
Data Analysis Module - Provides data analysis functionality for the badminton tournament management system
"""

from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json

# Import database models
from app import db, Tournament, Match, Team, Player

# Create blueprint
analytics = Blueprint('analytics', __name__)

def get_player_stats(player_id=None, user_id=None):
    """Get player statistics"""

    # Base query - all matches
    query = db.session.query(
        Match, Tournament
    ).join(
        Tournament, Match.tournament_id == Tournament.id
    )

    # If user ID is specified, only query that user's matches
    if user_id:
        query = query.filter(Tournament.user_id == user_id)

    # Get all relevant matches
    matches = query.all()

    # Player statistics
    player_stats = {}

    for match, tournament in matches:
        # Process team 1
        team1 = match.team1
        team1_players = [team1.player1]
        if team1.player2:
            team1_players.append(team1.player2)

        # Process team 2
        team2 = match.team2
        team2_players = [team2.player1]
        if team2.player2:
            team2_players.append(team2.player2)

        # Determine match winner
        winner = match.get_winner()
        is_team1_winner = (winner.id == team1.id)

        # Update statistics for each player
        for player in team1_players:
            if player.id not in player_stats:
                player_stats[player.id] = {
                    'id': player.id,
                    'name': player.name,
                    'matches': 0,
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0,
                    'points_scored': 0,
                    'points_conceded': 0,
                    'match_types': {},
                    'recent_matches': []
                }

            player_stats[player.id]['matches'] += 1
            if is_team1_winner:
                player_stats[player.id]['wins'] += 1
            else:
                player_stats[player.id]['losses'] += 1

            # Update match type statistics
            match_type = match.match_type
            if match_type not in player_stats[player.id]['match_types']:
                player_stats[player.id]['match_types'][match_type] = {'matches': 0, 'wins': 0}

            player_stats[player.id]['match_types'][match_type]['matches'] += 1
            if is_team1_winner:
                player_stats[player.id]['match_types'][match_type]['wins'] += 1

            # Calculate points scored and conceded
            score1_sets = match.score1.split(', ')
            score2_sets = match.score2.split(', ')

            points_scored = 0
            points_conceded = 0

            for i in range(min(len(score1_sets), len(score2_sets))):
                try:
                    score1_points = int(score1_sets[i].split('-')[0])
                    score2_points = int(score2_sets[i].split('-')[1])
                    points_scored += score1_points
                    points_conceded += score2_points
                except (ValueError, IndexError):
                    # Handle malformed scores
                    pass

            player_stats[player.id]['points_scored'] += points_scored
            player_stats[player.id]['points_conceded'] += points_conceded

            # Add to recent matches
            match_info = {
                'id': match.id,
                'tournament': tournament.name,
                'date': match.timestamp.strftime('%Y-%m-%d'),
                'opponent': ', '.join([p.name for p in team2_players]),
                'result': 'Win' if is_team1_winner else 'Loss',
                'score': match.score1
            }
            player_stats[player.id]['recent_matches'].append(match_info)

        # Do the same for team 2 players
        for player in team2_players:
            if player.id not in player_stats:
                player_stats[player.id] = {
                    'id': player.id,
                    'name': player.name,
                    'matches': 0,
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0,
                    'points_scored': 0,
                    'points_conceded': 0,
                    'match_types': {},
                    'recent_matches': []
                }

            player_stats[player.id]['matches'] += 1
            if not is_team1_winner:
                player_stats[player.id]['wins'] += 1
            else:
                player_stats[player.id]['losses'] += 1

            # Update match type statistics
            match_type = match.match_type
            if match_type not in player_stats[player.id]['match_types']:
                player_stats[player.id]['match_types'][match_type] = {'matches': 0, 'wins': 0}

            player_stats[player.id]['match_types'][match_type]['matches'] += 1
            if not is_team1_winner:
                player_stats[player.id]['match_types'][match_type]['wins'] += 1

            # Calculate points scored and conceded
            score1_sets = match.score1.split(', ')
            score2_sets = match.score2.split(', ')

            points_scored = 0
            points_conceded = 0

            for i in range(min(len(score1_sets), len(score2_sets))):
                try:
                    score1_points = int(score1_sets[i].split('-')[0])
                    score2_points = int(score2_sets[i].split('-')[1])
                    points_scored += score2_points
                    points_conceded += score1_points
                except (ValueError, IndexError):
                    # Handle malformed scores
                    pass

            player_stats[player.id]['points_scored'] += points_scored
            player_stats[player.id]['points_conceded'] += points_conceded

            # Add to recent matches
            match_info = {
                'id': match.id,
                'tournament': tournament.name,
                'date': match.timestamp.strftime('%Y-%m-%d'),
                'opponent': ', '.join([p.name for p in team1_players]),
                'result': 'Win' if not is_team1_winner else 'Loss',
                'score': match.score2
            }
            player_stats[player.id]['recent_matches'].append(match_info)

    # Calculate win rates and keep only the most recent 5 matches
    for player_id, stats in player_stats.items():
        if stats['matches'] > 0:
            stats['win_rate'] = round((stats['wins'] / stats['matches']) * 100, 1)
            stats['recent_matches'] = sorted(stats['recent_matches'], key=lambda x: x['date'], reverse=True)[:5]

            # Calculate win rate for each match type
            for match_type, type_stats in stats['match_types'].items():
                if type_stats['matches'] > 0:
                    type_stats['win_rate'] = round((type_stats['wins'] / type_stats['matches']) * 100, 1)

    # If a player ID is specified, only return that player's stats
    if player_id and player_id in player_stats:
        return player_stats[player_id]

    # Otherwise return all player stats, sorted by win rate
    return sorted(list(player_stats.values()), key=lambda x: x['win_rate'], reverse=True)

def get_tournament_stats(tournament_id=None, user_id=None):
    """Get tournament statistics"""

    # Base query
    query = Tournament.query

    # If user ID is specified
    if user_id:
        query = query.filter_by(user_id=user_id)

    # If tournament ID is specified
    if tournament_id:
        query = query.filter_by(id=tournament_id)

    tournaments = query.all()
    tournament_stats = []

    for tournament in tournaments:
        matches = Match.query.filter_by(tournament_id=tournament.id).all()

        # Basic statistics
        stats = {
            'id': tournament.id,
            'name': tournament.name,
            'date': tournament.date.strftime('%Y-%m-%d'),
            'location': tournament.location,
            'match_count': len(matches),
            'player_count': 0,
            'match_types': {},
            'players': [],
            'rounds': {},
            'longest_match': None,
            'highest_score': None
        }

        # Collect all players and match types
        players = set()
        longest_sets = 0
        highest_points = 0
        highest_score_match = None
        longest_match = None

        for match in matches:
            # Add team 1 players
            players.add(match.team1.player1.id)
            if match.team1.player2:
                players.add(match.team1.player2.id)

            # Add team 2 players
            players.add(match.team2.player1.id)
            if match.team2.player2:
                players.add(match.team2.player2.id)

            # Match type statistics
            if match.match_type not in stats['match_types']:
                stats['match_types'][match.match_type] = 0
            stats['match_types'][match.match_type] += 1

            # Round statistics
            if match.round_name not in stats['rounds']:
                stats['rounds'][match.round_name] = 0
            stats['rounds'][match.round_name] += 1

            # Check for longest match (by number of sets)
            score1_sets = match.score1.split(', ')
            current_sets = len(score1_sets)
            if current_sets > longest_sets:
                longest_sets = current_sets
                longest_match = match

            # Check for highest scoring match
            total_points = 0
            for i in range(len(score1_sets)):
                try:
                    set_parts = score1_sets[i].split('-')
                    if len(set_parts) == 2:
                        total_points += int(set_parts[0]) + int(set_parts[1])
                except (ValueError, IndexError):
                    pass

            if total_points > highest_points:
                highest_points = total_points
                highest_score_match = match

        # Update player count
        stats['player_count'] = len(players)

        # Add longest match info
        if longest_match:
            team1_names = [longest_match.team1.player1.name]
            if longest_match.team1.player2:
                team1_names.append(longest_match.team1.player2.name)

            team2_names = [longest_match.team2.player1.name]
            if longest_match.team2.player2:
                team2_names.append(longest_match.team2.player2.name)

            stats['longest_match'] = {
                'team1': ', '.join(team1_names),
                'team2': ', '.join(team2_names),
                'score1': longest_match.score1,
                'score2': longest_match.score2,
                'sets': longest_sets,
                'match_type': longest_match.match_type
            }

        # Add highest score match info
        if highest_score_match:
            team1_names = [highest_score_match.team1.player1.name]
            if highest_score_match.team1.player2:
                team1_names.append(highest_score_match.team1.player2.name)

            team2_names = [highest_score_match.team2.player1.name]
            if highest_score_match.team2.player2:
                team2_names.append(highest_score_match.team2.player2.name)

            stats['highest_score'] = {
                'team1': ', '.join(team1_names),
                'team2': ', '.join(team2_names),
                'score1': highest_score_match.score1,
                'score2': highest_score_match.score2,
                'total_points': highest_points,
                'match_type': highest_score_match.match_type
            }

        # Add all players' basic info
        for player_id in players:
            player = Player.query.get(player_id)
            if player:
                stats['players'].append({
                    'id': player.id,
                    'name': player.name
                })

        tournament_stats.append(stats)

    # If a tournament ID is specified and a matching tournament is found
    if tournament_id and tournament_stats:
        return tournament_stats[0]

    # Sort by date
    return sorted(tournament_stats, key=lambda x: x['date'], reverse=True)

def get_head_to_head(player1_id, player2_id):
    """Get head-to-head data between two players"""

    # Find matches where both players participated
    # This query is complex as players could be in different teams
    player1_team_ids = db.session.query(Team.id).filter(
        (Team.player1_id == player1_id) | (Team.player2_id == player1_id)
    ).all()
    player1_team_ids = [t[0] for t in player1_team_ids]

    player2_team_ids = db.session.query(Team.id).filter(
        (Team.player1_id == player2_id) | (Team.player2_id == player2_id)
    ).all()
    player2_team_ids = [t[0] for t in player2_team_ids]

    # Find matches where they faced each other
    versus_matches = Match.query.filter(
        ((Match.team1_id.in_(player1_team_ids)) & (Match.team2_id.in_(player2_team_ids))) |
        ((Match.team1_id.in_(player2_team_ids)) & (Match.team2_id.in_(player1_team_ids)))
    ).all()

    player1 = Player.query.get(player1_id)
    player2 = Player.query.get(player2_id)

    # Match records
    head_to_head = {
        'player1': {
            'id': player1.id,
            'name': player1.name,
            'wins': 0
        },
        'player2': {
            'id': player2.id,
            'name': player2.name,
            'wins': 0
        },
        'matches': [],
        'total_matches': len(versus_matches)
    }

    for match in versus_matches:
        # Determine which team each player is on
        player1_in_team1 = match.team1.player1_id == player1.id or (match.team1.player2_id and match.team1.player2_id == player1.id)
        player2_in_team1 = match.team1.player1_id == player2.id or (match.team1.player2_id and match.team1.player2_id == player2.id)

        # Determine winning team
        winner = match.get_winner()
        winner_is_team1 = winner.id == match.team1.id

        # Record win/loss
        if (player1_in_team1 and winner_is_team1) or (not player1_in_team1 and not winner_is_team1):
            head_to_head['player1']['wins'] += 1
            winner_id = player1.id
        else:
            head_to_head['player2']['wins'] += 1
            winner_id = player2.id

        # Add match details
        tournament = Tournament.query.get(match.tournament_id)

        # Get team names
        team1_players = [match.team1.player1.name]
        if match.team1.player2:
            team1_players.append(match.team1.player2.name)

        team2_players = [match.team2.player1.name]
        if match.team2.player2:
            team2_players.append(match.team2.player2.name)

        match_info = {
            'id': match.id,
            'date': match.timestamp.strftime('%Y-%m-%d'),
            'tournament': tournament.name,
            'team1': ', '.join(team1_players),
            'team2': ', '.join(team2_players),
            'score1': match.score1,
            'score2': match.score2,
            'winner_id': winner_id,
            'match_type': match.match_type
        }
        head_to_head['matches'].append(match_info)

    # Sort by date
    head_to_head['matches'] = sorted(head_to_head['matches'], key=lambda x: x['date'], reverse=True)

    return head_to_head

def get_match_distribution_by_type(user_id=None):
    """Get match distribution by type"""

    # Base query
    query = db.session.query(
        Match.match_type,
        func.count(Match.id).label('count')
    )

    # If user ID is specified, only query that user's matches
    if user_id:
        query = query.join(Tournament, Match.tournament_id == Tournament.id)
        query = query.filter(Tournament.user_id == user_id)

    # Group and get results
    distribution = query.group_by(Match.match_type).all()

    # Format as dictionary
    result = {
        'labels': [],
        'data': []
    }

    for match_type, count in distribution:
        result['labels'].append(match_type)
        result['data'].append(count)

    return result

def get_win_rates_by_player(user_id=None, limit=10):
    """Get win rates by player"""

    # Get player statistics
    players = get_player_stats(user_id=user_id)

    # Sort by win rate and limit count
    players = sorted(players, key=lambda x: x['win_rate'], reverse=True)[:limit]

    # Format for chart data
    result = {
        'labels': [],
        'data': []
    }

    for player in players:
        result['labels'].append(player['name'])
        result['data'].append(player['win_rate'])

    return result

def get_points_stats_by_player(user_id=None, limit=10):
    """Get points statistics by player"""

    # Get player statistics
    players = get_player_stats(user_id=user_id)

    # Sort by average points per match
    for player in players:
        if player['matches'] > 0:
            player['avg_points_per_match'] = round(player['points_scored'] / player['matches'], 1)
        else:
            player['avg_points_per_match'] = 0

    players = sorted(players, key=lambda x: x['avg_points_per_match'], reverse=True)[:limit]

    # Format for chart data
    result = {
        'labels': [],
        'scored': [],
        'conceded': [],
        'avg_per_match': []
    }

    for player in players:
        result['labels'].append(player['name'])
        result['scored'].append(player['points_scored'])
        result['conceded'].append(player['points_conceded'])
        result['avg_per_match'].append(player['avg_points_per_match'])

    return result

def get_monthly_match_counts(user_id=None, months=12):
    """Get monthly match counts"""

    # Determine start date
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * months)

    # Base query
    query = db.session.query(
        func.strftime('%Y-%m', Match.timestamp).label('month'),
        func.count(Match.id).label('count')
    )

    # If user ID is specified, only query that user's matches
    if user_id:
        query = query.join(Tournament, Match.tournament_id == Tournament.id)
        query = query.filter(Tournament.user_id == user_id)

    # Limit date range
    query = query.filter(Match.timestamp >= start_date)

    # Group and get results
    monthly_counts = query.group_by('month').all()

    # Ensure all months have data
    result = {
        'labels': [],
        'data': []
    }

    # Create dictionary for all months
    all_months = {}
    current = start_date
    while current <= end_date:
        month_key = current.strftime('%Y-%m')
        all_months[month_key] = 0
        current = (current.replace(day=1) + timedelta(days=32)).replace(day=1)

    # Fill in query results
    for month, count in monthly_counts:
        all_months[month] = count

    # Convert to lists
    for month, count in sorted(all_months.items()):
        year, month_num = month.split('-')
        month_name = datetime(int(year), int(month_num), 1).strftime('%b %Y')
        result['labels'].append(month_name)
        result['data'].append(count)

    return result

@analytics.route('/analytics')
def analytics_dashboard():
    """Analytics dashboard view"""
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    # Get basic statistics
    match_distribution = get_match_distribution_by_type(user_id)
    player_win_rates = get_win_rates_by_player(user_id, limit=5)
    monthly_matches = get_monthly_match_counts(user_id, months=6)

    # Get all players list (for selection)
    players = Player.query.all()

    # Get all tournaments list (for selection)
    tournaments = Tournament.query.filter_by(user_id=user_id).all()

    return render_template(
        "html/analytics.html",
        match_distribution=json.dumps(match_distribution),
        player_win_rates=json.dumps(player_win_rates),
        monthly_matches=json.dumps(monthly_matches),
        players=players,
        tournaments=tournaments
    )

@analytics.route('/analytics/player/<int:player_id>')
def player_analytics(player_id):
    """Individual player analysis view"""
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    # Get player statistics
    player_stats = get_player_stats(player_id, user_id)

    # Get all players (for comparison)
    players = Player.query.all()

    return render_template(
        "html/player_analytics.html",
        player=player_stats,
        players=players
    )

@analytics.route('/analytics/tournament/<int:tournament_id>')
def tournament_analytics(tournament_id):
    """Tournament analysis view"""
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    # Get tournament statistics
    tournament_stats = get_tournament_stats(tournament_id, user_id)

    # If tournament not found or doesn't belong to current user
    if not tournament_stats:
        return redirect(url_for('analytics.analytics_dashboard'))

    return render_template(
        "html/tournament_analytics.html",
        tournament=tournament_stats
    )

@analytics.route('/analytics/head_to_head')
def head_to_head_view():
    """Head-to-head analysis view"""
    if "user_id" not in session:
        return redirect(url_for("login"))

    player1_id = request.args.get('player1', type=int)
    player2_id = request.args.get('player2', type=int)

    # Get all players (for selection)
    players = Player.query.all()

    # If two player IDs are provided
    head_to_head = None
    if player1_id and player2_id:
        head_to_head = get_head_to_head(player1_id, player2_id)

    return render_template(
        "html/head_to_head.html",
        players=players,
        head_to_head=head_to_head,
        player1_id=player1_id,
        player2_id=player2_id
    )

@analytics.route('/api/player/<int:player_id>/stats')
def api_player_stats(player_id):
    """Player statistics API"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session.get("user_id")
    stats = get_player_stats(player_id, user_id)

    return jsonify(stats)

@analytics.route('/api/tournament/<int:tournament_id>/stats')
def api_tournament_stats(tournament_id):
    """Tournament statistics API"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session.get("user_id")
    stats = get_tournament_stats(tournament_id, user_id)

    return jsonify(stats)

@analytics.route('/api/head_to_head/<int:player1_id>/<int:player2_id>')
def api_head_to_head(player1_id, player2_id):
    """Head-to-head statistics API"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    stats = get_head_to_head(player1_id, player2_id)

    return jsonify(stats)