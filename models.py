from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    last_login = db.Column(db.DateTime, default=db.func.current_timestamp())
    tournaments = db.relationship('Tournament', backref='organizer', lazy=True)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    matches = db.relationship('Match', backref='tournament', lazy=True, cascade="all, delete-orphan")


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    # Players can be part of multiple teams
    teams_as_player1 = db.relationship('Team', foreign_keys='Team.player1_id', backref='player1', lazy=True)
    teams_as_player2 = db.relationship('Team', foreign_keys='Team.player2_id', backref='player2', lazy=True)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)  # Nullable for singles matches
    # Teams can participate in multiple matches
    matches_as_team1 = db.relationship('Match', foreign_keys='Match.team1_id', backref='team1', lazy=True)
    matches_as_team2 = db.relationship('Match', foreign_keys='Match.team2_id', backref='team2', lazy=True)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    round_name = db.Column(db.String(100), nullable=False)
    group_name = db.Column(db.String(100))  # Optional group name
    team1_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team2_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    score1 = db.Column(db.String(100), nullable=False)  # e.g., "21-19, 19-21, 21-18"
    score2 = db.Column(db.String(100), nullable=False)  # e.g., "19-21, 21-19, 18-21"
    match_type = db.Column(db.String(50), nullable=False)  # e.g., "Men's Singles"
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def get_winner(self):
        """Determine the winner of the match based on scores"""
        score1_sets = self.score1.split(', ')
        score2_sets = self.score2.split(', ')

        team1_wins = 0
        team2_wins = 0

        for i in range(min(len(score1_sets), len(score2_sets))):
            try:
                score1_points = int(score1_sets[i].split('-')[0])
                score2_points = int(score2_sets[i].split('-')[0])
                if score1_points > score2_points:
                    team1_wins += 1
                else:
                    team2_wins += 1
            except (ValueError, IndexError):
                # If there's an error parsing scores, skip this set
                continue

        if team1_wins > team2_wins:
            return self.team1
        else:
            return self.team2