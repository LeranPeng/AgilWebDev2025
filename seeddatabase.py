"""
Seed script to populate the database with initial data for testing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, db
from models import User, Tournament, Player, Team, Match
from datetime import datetime, timedelta
import random
import string

# Sample data - 20 distinctive players
player_names = [
    "James Wilson", "Michael Scott", "David Mitchell", "Robert Brown", "John Davis",
    "Thomas Anderson", "William Taylor", "Richard Moore", "Christopher White", "Andrew Clark",
    "Emma Johnson", "Olivia Williams", "Sarah Jones", "Jessica Smith", "Emily Thompson",
    "Sophie Harris", "Charlotte Martin", "Elizabeth Robinson", "Victoria Wright", "Amelia Walker"
]

match_types = [
    "Men's Singles", "Women's Singles", "Men's Doubles", "Women's Doubles", "Mixed Doubles"
]

tournament_names = [
    "Spring Championship", "Summer Open", "Fall Invitational", "Winter Classic",
    "National Cup", "Regional Series", "Elite Tournament", "Pro Circuit",
    "University Games", "Corporate Challenge", "City Championship", "State Tournament"
]

locations = [
    "University Sports Hall", "City Recreation Center", "Downtown Stadium", "Community Center",
    "Olympic Training Center", "Sports Academy", "Civic Auditorium", "Athletic Club"
]

rounds = [
    "Group Stage", "Round of 32", "Round of 16", "Quarterfinal", "Semifinal", "Final"
]


# Helper to validate match players (no player can appear on both sides)
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


def generate_match_scores():
    # Generate 2 or 3 sets for a match
    sets = 2 if random.random() < 0.7 else 3

    scores1 = []
    scores2 = []

    # First set
    if random.choice([True, False]):
        scores1.append("21-" + str(random.randint(10, 19)))
        scores2.append(str(random.randint(10, 19)) + "-21")
        set1_winner = 1
    else:
        scores1.append(str(random.randint(10, 19)) + "-21")
        scores2.append("21-" + str(random.randint(10, 19)))
        set1_winner = 2

    # Second set
    if random.choice([True, False]):
        scores1.append("21-" + str(random.randint(10, 19)))
        scores2.append(str(random.randint(10, 19)) + "-21")
        set2_winner = 1
    else:
        scores1.append(str(random.randint(10, 19)) + "-21")
        scores2.append("21-" + str(random.randint(10, 19)))
        set2_winner = 2

    # If tied, add a third set
    if set1_winner != set2_winner or sets == 3:
        if random.choice([True, False]):
            scores1.append("21-" + str(random.randint(10, 19)))
            scores2.append(str(random.randint(10, 19)) + "-21")
        else:
            scores1.append(str(random.randint(10, 19)) + "-21")
            scores2.append("21-" + str(random.randint(10, 19)))

    return ", ".join(scores1), ", ".join(scores2)


def create_seed_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        print("Creating users...")
        # Create users
        admin_user = User(username="admin", email="admin@example.com")
        admin_user.set_password("password")
        db.session.add(admin_user)

        test_user = User(username="testuser", email="test@example.com")
        test_user.set_password("password")
        db.session.add(test_user)

        db.session.commit()

        print("Creating players...")
        # Create exactly 20 players from the predefined list
        players = []
        for name in player_names:
            player = Player(name=name)
            players.append(player)
            db.session.add(player)

        db.session.commit()

        print("Creating teams...")
        # Create teams
        teams = []

        # Singles teams (one player)
        for player in players:
            team = Team(player1_id=player.id)
            teams.append(team)
            db.session.add(team)

        # Create all possible doubles combinations (without duplicates)
        for i in range(len(players)):
            for j in range(i+1, len(players)):
                # For men's and women's doubles, ensure same gender
                # For simplicity, assume first 10 are men, last 10 are women
                same_gender = (i < 10 and j < 10) or (i >= 10 and j >= 10)

                if same_gender or random.random() < 0.4:  # 40% chance for mixed doubles
                    team = Team(player1_id=players[i].id, player2_id=players[j].id)
                    teams.append(team)
                    db.session.add(team)

        db.session.commit()

        print("Creating tournaments...")
        # Create tournaments - 12 tournaments spanning over last year
        tournaments = []

        # Generate dates starting from a year ago up to now
        start_date = datetime.now().date() - timedelta(days=365)  # 1 year ago

        for i in range(12):
            # Distribute tournaments throughout the year (one per month)
            date_offset = int((i / 12) * 365)
            tournament_date = start_date + timedelta(days=date_offset)

            # Use a unique name by adding month and year
            tournament_name = random.choice(tournament_names)
            month = tournament_date.strftime("%B")
            year = tournament_date.year
            full_name = f"{tournament_name} {month} {year}"

            tournament = Tournament(
                name=full_name,
                date=tournament_date,
                location=random.choice(locations),
                user_id=test_user.id
            )
            tournaments.append(tournament)
            db.session.add(tournament)

        db.session.commit()

        print("Creating matches...")
        # Create approximately 500 matches
        match_count = 0
        target_match_count = 500
        max_attempts = 1000  # Prevent infinite loop
        attempts = 0

        # Function to get a random date within tournament dates
        def get_random_tournament_date(tournament):
            # Assume tournament spans 3 days
            start = tournament.date
            end = start + timedelta(days=2)

            # Random date within range
            days_diff = (end - start).days
            random_days = random.randint(0, days_diff)
            random_date = start + timedelta(days=random_days)

            # Random time between 9 AM and 7 PM
            random_hour = random.randint(9, 19)
            random_minute = random.choice([0, 15, 30, 45])

            return datetime.combine(random_date, datetime.min.time()) + timedelta(hours=random_hour, minutes=random_minute)

        # Create matches for each tournament
        for tournament in tournaments:
            # Each tournament has around 40-50 matches
            tournament_matches = random.randint(40, 50)

            for _ in range(tournament_matches):
                if match_count >= target_match_count or attempts >= max_attempts:
                    break

                attempts += 1

                # Determine match type
                match_type = random.choice(match_types)

                # Select appropriate teams based on match type
                if "Singles" in match_type:
                    # Filter players by gender for singles matches
                    if match_type == "Men's Singles":
                        valid_players = players[:10]  # First 10 are men
                    else:
                        valid_players = players[10:]  # Last 10 are women

                    # Get the corresponding singles teams
                    valid_team_ids = [team.id for team in teams if
                                      team.player2_id is None and
                                      any(p.id == team.player1_id for p in valid_players)]

                    if len(valid_team_ids) < 2:
                        continue

                    team1_id = random.choice(valid_team_ids)
                    team2_id = random.choice([tid for tid in valid_team_ids if tid != team1_id])

                    team1 = next(t for t in teams if t.id == team1_id)
                    team2 = next(t for t in teams if t.id == team2_id)

                elif "Doubles" in match_type:
                    # Filter doubles teams by type
                    if match_type == "Men's Doubles":
                        # Both players must be men (in the first 10)
                        valid_teams = [t for t in teams if
                                      t.player2_id is not None and
                                      any(p.id == t.player1_id for p in players[:10]) and
                                      any(p.id == t.player2_id for p in players[:10])]
                    elif match_type == "Women's Doubles":
                        # Both players must be women (in the last 10)
                        valid_teams = [t for t in teams if
                                      t.player2_id is not None and
                                      any(p.id == t.player1_id for p in players[10:]) and
                                      any(p.id == t.player2_id for p in players[10:])]
                    else:  # Mixed Doubles
                        # One player from each gender
                        valid_teams = [t for t in teams if
                                      t.player2_id is not None and
                                      ((any(p.id == t.player1_id for p in players[:10]) and
                                        any(p.id == t.player2_id for p in players[10:])) or
                                       (any(p.id == t.player1_id for p in players[10:]) and
                                        any(p.id == t.player2_id for p in players[:10])))]

                    if len(valid_teams) < 2:
                        continue

                    team1 = random.choice(valid_teams)

                    # Find a valid team2 that doesn't share players with team1
                    valid_team2_candidates = [t for t in valid_teams if
                                            t.id != team1.id and validate_match_players(team1, t)]

                    if not valid_team2_candidates:
                        continue

                    team2 = random.choice(valid_team2_candidates)

                # Generate scores
                score1, score2 = generate_match_scores()

                # Determine the round name
                round_name = random.choice(rounds)

                # Create group name for group stages
                group_name = None
                if round_name == "Group Stage":
                    group_name = f"Group {random.choice(string.ascii_uppercase[:4])}"

                # Create match
                match = Match(
                    tournament_id=tournament.id,
                    round_name=round_name,
                    group_name=group_name,
                    team1_id=team1.id,
                    team2_id=team2.id,
                    score1=score1,
                    score2=score2,
                    match_type=match_type,
                    timestamp=get_random_tournament_date(tournament)
                )
                db.session.add(match)
                match_count += 1

                # Commit in batches to improve performance
                if match_count % 50 == 0:
                    db.session.commit()
                    print(f"Created {match_count} matches so far...")

        db.session.commit()
        print(f"Database seeded successfully with {match_count} matches across 12 tournaments!")

        # Print some statistics about the players
        print("\nPlayer Statistics:")
        for i, player in enumerate(players):
            singles_count = Match.query.join(Team, Match.team1_id == Team.id).filter(
                Team.player1_id == player.id, Team.player2_id == None).count() + \
                Match.query.join(Team, Match.team2_id == Team.id).filter(
                Team.player1_id == player.id, Team.player2_id == None).count()

            doubles_count = db.session.query(Match).join(
                Team, ((Match.team1_id == Team.id) | (Match.team2_id == Team.id))
            ).filter(
                (Team.player1_id == player.id) | (Team.player2_id == player.id)
            ).filter(
                Team.player2_id != None
            ).count() - singles_count  # Adjust for possible double-counting

            print(f"{player.name}: {singles_count} singles matches, {doubles_count} doubles matches")


if __name__ == "__main__":
    create_seed_data()