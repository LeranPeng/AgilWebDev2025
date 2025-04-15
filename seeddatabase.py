"""
Seed script to populate the database with initial data for testing
Run this after setting up the application but before using it
"""

from app import app, db, User, Tournament, Player, Team, Match
from datetime import datetime, timedelta
import random

# Sample data
player_names = [
    "Alice Chen", "Bob Smith", "Charlie Wong", "Dana Lee",
    "Ethan Park", "Fiona Johnson", "George Zhang", "Hannah Liu",
    "Ian Miller", "Jessica Wang", "Kevin Brown", "Linda Zhao"
]

match_types = [
    "Men's Singles", "Women's Singles", "Men's Doubles",
    "Women's Doubles", "Mixed Doubles"
]

tournament_names = [
    "Spring Championship", "Summer Open", "Fall Invitational", "Winter Classic"
]

locations = [
    "University Sports Hall", "City Recreation Center", "Downtown Stadium",
    "Community Center"
]

rounds = [
    "Group Stage", "Round of 16", "Quarterfinal", "Semifinal", "Final"
]


# Helper to generate random scores
def generate_score():
    # Generate a random badminton score
    # First player could win 21-x or lose x-21
    if random.choice([True, False]):
        score1 = 21
        score2 = random.randint(10, 19)
    else:
        score1 = random.randint(10, 19)
        score2 = 21

    return f"{score1}-{score2}"


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
        # Create players
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

        # Doubles teams (two players)
        for i in range(6):  # Create 6 doubles teams
            p1 = random.choice(players)
            p2 = random.choice([p for p in players if p.id != p1.id])
            team = Team(player1_id=p1.id, player2_id=p2.id)
            teams.append(team)
            db.session.add(team)

        db.session.commit()

        print("Creating tournaments...")
        # Create tournaments
        tournaments = []
        for i in range(3):  # Create 3 tournaments
            date = datetime.now().date() - timedelta(days=i * 30)
            tournament = Tournament(
                name=random.choice(tournament_names),
                date=date,
                location=random.choice(locations),
                user_id=test_user.id
            )
            tournaments.append(tournament)
            db.session.add(tournament)

        db.session.commit()

        print("Creating matches...")
        # Create matches
        for tournament in tournaments:
            # Create 8-12 matches per tournament
            for i in range(random.randint(8, 12)):
                team1 = random.choice(teams)
                team2 = random.choice([t for t in teams if t.id != team1.id])

                # Generate scores
                score1, score2 = generate_match_scores()

                # Determine match type based on team composition
                if team1.player2_id is None and team2.player2_id is None:
                    # Both singles
                    match_type = "Men's Singles" if random.random() < 0.6 else "Women's Singles"
                elif team1.player2_id is not None and team2.player2_id is not None:
                    # Both doubles
                    match_type = random.choice(["Men's Doubles", "Women's Doubles", "Mixed Doubles"])
                else:
                    # Mixed - shouldn't happen in real tournaments but just in case
                    match_type = "Exhibition Match"

                # Create match
                match = Match(
                    tournament_id=tournament.id,
                    round_name=random.choice(rounds),
                    group_name=f"Group {chr(65 + random.randint(0, 3))}" if random.random() < 0.7 else None,
                    team1_id=team1.id,
                    team2_id=team2.id,
                    score1=score1,
                    score2=score2,
                    match_type=match_type,
                    timestamp=datetime.combine(tournament.date, datetime.min.time()) + timedelta(
                        hours=random.randint(9, 17))
                )
                db.session.add(match)

        db.session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    create_seed_data()