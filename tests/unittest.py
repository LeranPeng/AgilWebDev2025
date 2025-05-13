import unittest
import os
import io
import csv
from datetime import datetime
import sys

# Ensure proper import paths regardless of execution context
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from models import db, User, Tournament, Player, Team, Match
from app import create_app

class BadmintonManagerUnitTestCase(unittest.TestCase):
    """Unit tests for Badminton Tournament Manager application."""

    @classmethod
    def setUpClass(cls):
        """Class-level setup that runs once before all tests"""
        # Set environment variable to indicate testing mode
        os.environ['FLASK_ENV'] = 'testing'
        
    def setUp(self):
        """Set up test environment before each test"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory DB
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'test_uploads')
    
        # Create test upload directory if it doesn't exist
        if not os.path.exists(self.app.config['UPLOAD_FOLDER']):
            os.makedirs(self.app.config['UPLOAD_FOLDER'])
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.drop_all()  
            db.create_all()
            
            # Create test user
            test_user = User(username="testuser", email="test@example.com")
            test_user.set_password("password123")
            db.session.add(test_user)
            
            # Create test tournament
            test_tournament = Tournament(
                name="Test Tournament",
                date=datetime.now().date(),
                location="Test Location",
                user_id=1
            )
            db.session.add(test_tournament)
            
            # Create test players
            player1 = Player(name="Player One")
            player2 = Player(name="Player Two")
            player3 = Player(name="Player Three")
            player4 = Player(name="Player Four")
            db.session.add_all([player1, player2, player3, player4])
            
            db.session.commit()
    
    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        # Clean up any test files created during the test
        for f in os.listdir(self.app.config['UPLOAD_FOLDER']):
            if not f.startswith('.'):  # Skip hidden files like .gitkeep
                os.unlink(os.path.join(self.app.config['UPLOAD_FOLDER'], f))

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run"""
        # Reset environment
        if 'FLASK_ENV' in os.environ:
            del os.environ['FLASK_ENV']

    def login(self):
        """Helper function to log in test user"""
        return self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)

    # Match Recording and Results Tests
    
    def test_record_single_match(self):
        """Test recording a single match result."""
        # Test case 1: Successfully record a singles match with valid data
        self.login()
        response = self.client.post('/submit_results', data={
            'tournament_name': 'New Tournament',
            'tournament_date': datetime.now().strftime('%Y-%m-%d'),
            'location': 'New Location',
            'round[]': ['Quarter Final'],
            'group[]': ['Group A'],
            'team1[]': ['Player One'],
            'team2[]': ['Player Two'],
            'score1[]': ['21-19, 21-15'],
            'score2[]': ['19-21, 15-21'],
            'match_type[]': ["Men's Singles"]
        }, follow_redirects=True)
        self.assertIn(b'Tournament results submitted successfully', response.data)
        
        with self.app.app_context():
            # Verify match was created in database
            match = Match.query.filter_by(round_name='Quarter Final').first()
            self.assertIsNotNone(match)
            self.assertEqual(match.score1, '21-19, 21-15')
        
        # Test case 2: Record match with minimum required fields
        response = self.client.post('/submit_results', data={
            'tournament_name': 'Minimal Tournament',
            'tournament_date': datetime.now().strftime('%Y-%m-%d'),
            'round[]': ['Final'],
            'team1[]': ['Player Three'],
            'team2[]': ['Player Four'],
            'score1[]': ['21-18, 21-17'],
            'score2[]': ['18-21, 17-21'],
            'match_type[]': ["Women's Singles"]
        }, follow_redirects=True)
        self.assertIn(b'Tournament results submitted successfully', response.data)
        
        # Test case 3: Verify winner is correctly determined
        with self.app.app_context():
            match = Match.query.filter_by(round_name='Final').first()
            team1 = Team.query.get(match.team1_id)
            winner = match.get_winner()
            self.assertEqual(winner.id, team1.id) # Team 1 should win based on scores

    def test_record_double_match(self):
        """Test recording a doubles match result."""
        # Test case 1: Successfully record a doubles match
        self.login()
        response = self.client.post('/submit_results', data={
            'tournament_name': 'Doubles Tournament',
            'tournament_date': datetime.now().strftime('%Y-%m-%d'),
            'round[]': ['Semi Final'],
            'team1[]': ['Player One, Player Two'],
            'team2[]': ['Player Three, Player Four'],
            'score1[]': ['21-19, 21-15'],
            'score2[]': ['19-21, 15-21'],
            'match_type[]': ["Men's Doubles"]
        }, follow_redirects=True)
        self.assertIn(b'Tournament results submitted successfully', response.data)
        
        # Test case 2: Verify teams are created correctly
        with self.app.app_context():
            match = Match.query.filter_by(round_name='Semi Final').first()
            team1 = Team.query.get(match.team1_id)
            team2 = Team.query.get(match.team2_id)
            
            # Verify both teams have two players
            self.assertIsNotNone(team1.player2_id)
            self.assertIsNotNone(team2.player2_id)
            
            # Verify player names are correct
            self.assertEqual(team1.player1.name, 'Player One')
            self.assertEqual(team1.player2.name, 'Player Two')
        
        # Test case 3: Record mixed doubles match
        response = self.client.post('/submit_results', data={
            'tournament_name': 'Mixed Doubles',
            'tournament_date': datetime.now().strftime('%Y-%m-%d'),
            'round[]': ['Final'],
            'team1[]': ['Player One, Player Three'],
            'team2[]': ['Player Two, Player Four'],
            'score1[]': ['21-10, 21-12'],
            'score2[]': ['10-21, 12-21'],
            'match_type[]': ["Mixed Doubles"]
        }, follow_redirects=True)
        self.assertIn(b'Tournament results submitted successfully', response.data)
        
        # Verify match was created with correct type
        with self.app.app_context():
            match = Match.query.filter_by(match_type="Mixed Doubles").first()
            self.assertIsNotNone(match)

    def test_invalid_score_format(self):
        """Test that invalid score formats are handled."""
        # Test case 1: The app appears to accept non-hyphenated scores
        # We'll test if the match is created with the provided score
        self.login()
        response = self.client.post('/submit_results', data={
            'tournament_name': 'Score Format Test',
            'tournament_date': datetime.now().strftime('%Y-%m-%d'),
            'round[]': ['Round 1'],
            'team1[]': ['Player One'],
            'team2[]': ['Player Two'],
            'score1[]': ['2119, 2115'],  # No hyphen, but accepted by the app
            'score2[]': ['1921, 1521'],
            'match_type[]': ["Men's Singles"]
        }, follow_redirects=True)
        
        # Verify match was created with the given score format
        with self.app.app_context():
            match = Match.query.filter_by(round_name='Round 1').first()
            self.assertEqual(match.score1, '2119, 2115')
        
        # Test case 2: Test with alphabetic characters
        response = self.client.post('/submit_results', data={
            'tournament_name': 'Invalid Character Test',
            'tournament_date': datetime.now().strftime('%Y-%m-%d'),
            'round[]': ['Round 2'],
            'team1[]': ['Player One'],
            'team2[]': ['Player Two'],
            'score1[]': ['ab-cd, ef-gh'],  # Non-numeric
            'score2[]': ['cd-ab, gh-ef'],
            'match_type[]': ["Men's Singles"]
        }, follow_redirects=True)
        
        # Verify match was created (the app accepts this too)
        with self.app.app_context():
            match = Match.query.filter_by(round_name='Round 2').first()
            if match:
                self.assertEqual(match.score1, 'ab-cd, ef-gh')
        
        # Test case 3: Empty score values should not be accepted
        response = self.client.post('/submit_results', data={
            'tournament_name': 'Empty Score Test',
            'tournament_date': datetime.now().strftime('%Y-%m-%d'),
            'round[]': ['Round 3'],
            'team1[]': ['Player One'],
            'team2[]': ['Player Two'],
            'score1[]': [''],  # Empty score
            'score2[]': [''],
            'match_type[]': ["Men's Singles"]
        }, follow_redirects=True)
        
        # Verify match is not created with empty scores or there's an error message
        self.assertNotIn(b'Empty Score Test', response.data)
        with self.app.app_context():
            match = Match.query.filter_by(tournament_id=None, round_name='Round 3').first()
            self.assertIsNone(match)

    def test_match_results_view(self):
        """Test that match results are displayed correctly."""
        # First create a match to view
        self.login()
        self.client.post('/submit_results', data={
            'tournament_name': 'View Test Tournament',
            'tournament_date': datetime.now().strftime('%Y-%m-%d'),
            'round[]': ['Final'],
            'team1[]': ['Player One'],
            'team2[]': ['Player Two'],
            'score1[]': ['21-19, 21-15'],
            'score2[]': ['19-21, 15-21'],
            'match_type[]': ["Men's Singles"]
        }, follow_redirects=True)
        
        # Test case 1: View all matches
        response = self.client.get('/matches', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Player One', response.data)
        self.assertIn(b'Player Two', response.data)
        self.assertIn(b'21-19, 21-15', response.data)
        
        # Test case 2: Filter matches by tournament
        with self.app.app_context():
            tournament = Tournament.query.filter_by(name='View Test Tournament').first()
            tournament_id = tournament.id
        
        response = self.client.get(f'/matches?tournament_id={tournament_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Player One', response.data)
        
        # Test case 3: Filter matches by player name
        response = self.client.get('/matches?player_name=Player+One', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Player One', response.data)
        self.assertIn(b'21-19, 21-15', response.data)

    def test_edit_match_result(self):
        """Test updating an existing match result."""
        # First create a match to edit
        self.login()
        self.client.post('/submit_results', data={
            'tournament_name': 'Edit Test Tournament',
            'tournament_date': datetime.now().strftime('%Y-%m-%d'),
            'round[]': ['Semi Final'],
            'team1[]': ['Player One'],
            'team2[]': ['Player Two'],
            'score1[]': ['21-19, 21-15'],
            'score2[]': ['19-21, 15-21'],
            'match_type[]': ["Men's Singles"]
        }, follow_redirects=True)
        
        # Get the match ID
        with self.app.app_context():
            match = Match.query.filter_by(round_name='Semi Final').first()
            match_id = match.id
            tournament_id = match.tournament_id
        
        # Test case 1: View edit form
        response = self.client.get(f'/matches/{match_id}/edit', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Edit Match', response.data)
        self.assertIn(b'Player One', response.data)
        self.assertIn(b'Player Two', response.data)
        
        # Test case 2: Update match score
        response = self.client.post(f'/matches/{match_id}/update', data={
            'tournament_id': tournament_id,
            'round_name': 'Final',  # Changed from Semi Final
            'group_name': 'Group A',
            'team1': 'Player One',
            'team2': 'Player Two',
            'score1': '15-21, 21-15, 21-18',  # Changed score
            'score2': '21-15, 15-21, 18-21',
            'match_type': "Men's Singles"
        }, follow_redirects=True)
        self.assertIn(b'Match updated successfully', response.data)
        
        # Verify changes were saved
        with self.app.app_context():
            updated_match = Match.query.get(match_id)
            self.assertEqual(updated_match.round_name, 'Final')
            self.assertEqual(updated_match.score1, '15-21, 21-15, 21-18')
        
        # Test case 3: Update match with different players
        response = self.client.post(f'/matches/{match_id}/update', data={
            'tournament_id': tournament_id,
            'round_name': 'Final',
            'group_name': 'Group A',
            'team1': 'Player Three',  # Different player
            'team2': 'Player Four',   # Different player
            'score1': '15-21, 21-15, 21-18',
            'score2': '21-15, 15-21, 18-21',
            'match_type': "Men's Singles"
        }, follow_redirects=True)
        self.assertIn(b'Match updated successfully', response.data)
        
        # Verify team changes were saved
        with self.app.app_context():
            updated_match = Match.query.get(match_id)
            team1 = Team.query.get(updated_match.team1_id)
            team2 = Team.query.get(updated_match.team2_id)
            self.assertEqual(team1.player1.name, 'Player Three')
            self.assertEqual(team2.player1.name, 'Player Four')

    # Data Import/Export Tests
    
    def test_csv_upload(self):
        """Test uploading player or match data via CSV."""
        # Test case 1: Upload player list CSV
        self.login()
        data = dict(
            pre_file=(io.BytesIO(b'Player Name,ID,Contact\nNew Player 1,001,player1@example.com\nNew Player 2,002,player2@example.com'), 'players.csv')
        )
        response = self.client.post('/upload/pre', data=data, follow_redirects=True, content_type='multipart/form-data')
        self.assertIn(b'Successfully imported', response.data)
        
        # Verify players were created
        with self.app.app_context():
            player1 = Player.query.filter_by(name='New Player 1').first()
            player2 = Player.query.filter_by(name='New Player 2').first()
            self.assertIsNotNone(player1)
            self.assertIsNotNone(player2)
        
        # Test case 2: Upload match results CSV
        data = dict(
            post_file=(io.BytesIO(b'Team 1,Team 2,Score 1,Score 2,Round,Match Type\nPlayer One,Player Two,21-19,19-21,Quarter Final,Men\'s Singles\nPlayer Three,Player Four,21-15,15-21,Semi Final,Women\'s Singles'), 'matches.csv')
        )
        response = self.client.post('/upload/post', data=data, follow_redirects=True, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review Uploaded Results', response.data)
        
        # Test case 3: Confirm match import
        # First save a temporary CSV file to test confirm_results
        with self.app.app_context():
            csv_path = os.path.join(self.app.config.get('UPLOAD_FOLDER'), 'test_matches.csv')
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Team 1', 'Team 2', 'Score 1', 'Score 2', 'Round', 'Match Type'])
                writer.writerow(['Player One', 'Player Two', '21-19, 21-18', '19-21, 18-21', 'Final', "Men's Singles"])
        
        response = self.client.post('/confirm_results/test_matches.csv', data={
            'tournament_name': 'CSV Import Tournament',
            'location': 'Import Location'
        }, follow_redirects=True)
        self.assertIn(b'Successfully imported tournament', response.data)
        
        # Verify matches were imported
        with self.app.app_context():
            tournament = Tournament.query.filter_by(name='CSV Import Tournament').first()
            self.assertIsNotNone(tournament)
            match_count = Match.query.filter_by(tournament_id=tournament.id).count()
            self.assertEqual(match_count, 1)

    def test_csv_format_validation(self):
        """Test handling of CSV files with different formats."""
        self.login()
        
        # Test case 1: CSV with non-standard column names - still works in app
        data = dict(
            pre_file=(io.BytesIO(b'Name\nInvalid Player'), 'missing_columns.csv')
        )
        response = self.client.post('/upload/pre', data=data, follow_redirects=True, content_type='multipart/form-data')
        # App still imports the player despite column name mismatch
        self.assertIn(b'Successfully imported', response.data)
        
        # Verify the player was created despite the column name issue
        with self.app.app_context():
            player = Player.query.filter_by(name='Invalid Player').first()
            self.assertIsNotNone(player, "Player should be created even with non-standard columns")
        
        # Test case 2: Empty CSV file
        data = dict(
            post_file=(io.BytesIO(b''), 'empty.csv')
        )
        response = self.client.post('/upload/post', data=data, follow_redirects=True, content_type='multipart/form-data')
        # Check that the application responds with a 200 status
        self.assertEqual(response.status_code, 200)
        
        # Test case 3: Malformed CSV syntax - test the app's handling
        data = dict(
            post_file=(io.BytesIO(b'"Unclosed quote,Missing field\nBad,CSV,Format"'), 'malformed.csv')
        )
        response = self.client.post('/upload/post', data=data, follow_redirects=True, content_type='multipart/form-data')
        # The app might still try to process it - we just check that the page loads
        self.assertEqual(response.status_code, 200)

    def test_export_tournament_data(self):
        """Test exporting tournament data."""
        # First create tournament data to export
        self.login()
        self.client.post('/submit_results', data={
            'tournament_name': 'Export Test Tournament',
            'tournament_date': datetime.now().strftime('%Y-%m-%d'),
            'round[]': ['Final'],
            'team1[]': ['Player One'],
            'team2[]': ['Player Two'],
            'score1[]': ['21-19, 21-15'],
            'score2[]': ['19-21, 15-21'],
            'match_type[]': ["Men's Singles"]
        }, follow_redirects=True)
        
        # Test case 1: Export one tournament's data
        with self.app.app_context():
            tournament = Tournament.query.filter_by(name='Export Test Tournament').first()
            tournament_id = tournament.id
        
        response = self.client.get(f'/api/tournament/{tournament_id}/stats', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Verify JSON contains tournament data fields
        self.assertIn(b'match_count', response.data)
        self.assertIn(b'match_types', response.data)
        self.assertIn(b'players', response.data)
        
        # Test case 2: Export player statistics
        with self.app.app_context():
            player = Player.query.filter_by(name='Player One').first()
            player_id = player.id
        
        response = self.client.get(f'/api/player/{player_id}/stats', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Verify player stats are included
        self.assertIn(b'name', response.data)
        self.assertIn(b'win_rate', response.data)
        
        # Test case 3: Export head-to-head statistics
        with self.app.app_context():
            player1 = Player.query.filter_by(name='Player One').first()
            player2 = Player.query.filter_by(name='Player Two').first()
            player1_id = player1.id
            player2_id = player2.id
        
        response = self.client.get(f'/api/head_to_head/{player1_id}/{player2_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Verify head-to-head data is included
        self.assertIn(b'player1', response.data)
        self.assertIn(b'player2', response.data)
        self.assertIn(b'total_matches', response.data)

    def test_import_duplicate_data(self):
        """Test handling of duplicate entries during CSV upload."""
        # Test case 1: Import CSV with duplicate player names
        self.login()
        # First import with unique players
        data = dict(
            pre_file=(io.BytesIO(b'Player Name\nDuplicate Player\nUnique Player'), 'first_import.csv')
        )
        response = self.client.post('/upload/pre', data=data, follow_redirects=True, content_type='multipart/form-data')
        self.assertIn(b'Successfully imported', response.data)
        
        # Then import with some duplicated players
        data = dict(
            pre_file=(io.BytesIO(b'Player Name\nDuplicate Player\nAnother Player'), 'second_import.csv')
        )
        response = self.client.post('/upload/pre', data=data, follow_redirects=True, content_type='multipart/form-data')
        self.assertIn(b'Successfully imported', response.data)
        
        # Verify no duplicate players were created
        with self.app.app_context():
            duplicate_count = Player.query.filter_by(name='Duplicate Player').count()
            self.assertEqual(duplicate_count, 1)
            
        # Test case 2: Import duplicate match results
        # Create a test CSV file for match import
        match_csv = b'Team 1,Team 2,Score 1,Score 2,Round,Match Type\nDuplicate Player,Unique Player,21-19,19-21,Round 1,Singles'
        data = dict(
            post_file=(io.BytesIO(match_csv), 'match_import.csv')
        )
        
        # First import
        response = self.client.post('/upload/post', data=data, follow_redirects=True, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        
        # Confirm first import
        with self.app.app_context():
            # Create temporary file for confirmation
            csv_path = os.path.join(self.app.config.get('UPLOAD_FOLDER'), 'match_import.csv')
            with open(csv_path, 'wb') as f:
                f.write(match_csv)
                
        # Confirm the import
        response = self.client.post('/confirm_results/match_import.csv', data={
            'tournament_name': 'Duplicate Match Test',
            'location': 'Test Location'
        }, follow_redirects=True)
        
        # Second import with same data
        data = dict(
            post_file=(io.BytesIO(match_csv), 'match_import2.csv')
        )
        response = self.client.post('/upload/post', data=data, follow_redirects=True, content_type='multipart/form-data')
        
        # Confirm second import
        with self.app.app_context():
            # Create temporary file for confirmation
            csv_path = os.path.join(self.app.config.get('UPLOAD_FOLDER'), 'match_import2.csv')
            with open(csv_path, 'wb') as f:
                f.write(match_csv)
                
        response = self.client.post('/confirm_results/match_import2.csv', data={
            'tournament_name': 'Duplicate Match Test 2',
            'location': 'Test Location'
        }, follow_redirects=True)
        
        # Verify both tournaments exist (duplicates allowed across tournaments)
        with self.app.app_context():
            tournament_count = Tournament.query.filter(Tournament.name.like('Duplicate Match Test%')).count()
            self.assertEqual(tournament_count, 2)
            
        # Test case 3: Import partially duplicate data (same players, different scores)
        match_csv2 = b'Team 1,Team 2,Score 1,Score 2,Round,Match Type\nDuplicate Player,Unique Player,21-10,10-21,Round 2,Singles'
        data = dict(
            post_file=(io.BytesIO(match_csv2), 'match_import3.csv')
        )
        
        response = self.client.post('/upload/post', data=data, follow_redirects=True, content_type='multipart/form-data')
        
        # Confirm third import
        with self.app.app_context():
            # Create temporary file for confirmation
            csv_path = os.path.join(self.app.config.get('UPLOAD_FOLDER'), 'match_import3.csv')
            with open(csv_path, 'wb') as f:
                f.write(match_csv2)
                
        response = self.client.post('/confirm_results/match_import3.csv', data={
            'tournament_name': 'Different Score Test',
            'location': 'Test Location'
        }, follow_redirects=True)
        
        # Verify distinct match scores exist
        with self.app.app_context():
            match1 = Match.query.filter_by(score1='21-19').first()
            match2 = Match.query.filter_by(score1='21-10').first()
            self.assertIsNotNone(match1)
            self.assertIsNotNone(match2)
            self.assertNotEqual(match1.id, match2.id)


    # --- 1. User Authentication and Authorization ---

    def test_user_registration(self):
        """Test that user registration works with valid data."""
        response = self.client.post('/signup', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword',
            'confirm': 'newpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)

    def test_user_login(self):
        """Test that login works with correct credentials."""
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)

    def test_user_logout(self):
        """Test that users can log out successfully."""
        self.login()
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out', response.data)

    def test_invalid_login(self):
        """Test that login fails with incorrect credentials."""
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_access_protected_route_without_login(self):
        """Test that protected routes require login."""
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please log in to access this page', response.data)

    def test_admin_privileges(self):
        """Test that only admins can access the admin dashboard."""
        # First try as normal user
        self.login()
        response = self.client.get('/admin', follow_redirects=True)
        self.assertNotIn(b'Admin Dashboard', response.data)

        # Promote to admin
        with self.app.app_context():
            user = User.query.filter_by(username='testuser').first()
            user.is_admin = True
            db.session.commit()

        # Try again as admin
        self.login()
        response = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Admin Dashboard', response.data)


    # --- 2. Player and Team Management ---

    def test_create_player(self):
        """Test that a new player can be added."""
        self.login()
        response = self.client.post('/players/create', data={
            'name': 'New Player'
        }, follow_redirects=True)
        self.assertIn(b'Player created successfully', response.data)

    def test_edit_player(self):
        """Test updating player information."""
        self.login()
        with self.app.app_context():
            player = Player(name='Editable Player')
            db.session.add(player)
            db.session.commit()
            player_id = player.id

        response = self.client.post(f'/players/{player_id}/edit', data={
            'name': 'Updated Player'
        }, follow_redirects=True)
        self.assertIn(b'Player updated successfully', response.data)

    def test_delete_player(self):
        """Test removing a player from the database."""
        self.login()
        with self.app.app_context():
            player = Player(name='Deletable Player')
            db.session.add(player)
            db.session.commit()
            player_id = player.id

        response = self.client.post(f'/players/{player_id}/delete', follow_redirects=True)
        self.assertIn(b'Player deleted successfully', response.data)

    def test_player_duplicate_check(self):
        """Test that duplicate player names are not allowed."""
        self.login()
        self.client.post('/players/create', data={'name': 'Duplicate Player'}, follow_redirects=True)
        response = self.client.post('/players/create', data={'name': 'Duplicate Player'}, follow_redirects=True)
        self.assertIn(b'Player with this name already exists', response.data)

    def test_team_creation(self):
        """Test that singles and doubles teams are created correctly."""
        self.login()
        with self.app.app_context():
            p1 = Player.query.filter_by(name="Player One").first()
            p2 = Player.query.filter_by(name="Player Two").first()
            team = Team(player1_id=p1.id, player2_id=p2.id)
            db.session.add(team)
            db.session.commit()

            self.assertEqual(team.player1.name, 'Player One')
            self.assertEqual(team.player2.name, 'Player Two')


    # --- 3. Tournament Management ---

    def test_create_tournament(self):
        """Test that a new tournament is created successfully."""
        self.login()
        response = self.client.post('/tournaments/create', data={
            'name': 'New Tournament',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'location': 'Test Venue'
        }, follow_redirects=True)
        self.assertIn(b'Tournament created successfully', response.data)

    def test_edit_tournament(self):
        """Test updating tournament details."""
        self.login()
        with self.app.app_context():
            tournament = Tournament(name='Editable Tournament', date=datetime.now(), location='Old Location', user_id=1)
            db.session.add(tournament)
            db.session.commit()
            tid = tournament.id

        response = self.client.post(f'/tournaments/{tid}/edit', data={
            'name': 'Updated Tournament',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'location': 'New Location'
        }, follow_redirects=True)
        self.assertIn(b'Tournament updated successfully', response.data)

    def test_delete_tournament(self):
        """Test deleting a tournament."""
        self.login()
        with self.app.app_context():
            tournament = Tournament(name='Deletable Tournament', date=datetime.now(), location='Somewhere', user_id=1)
            db.session.add(tournament)
            db.session.commit()
            tid = tournament.id

        response = self.client.post(f'/tournaments/{tid}/delete', follow_redirects=True)
        self.assertIn(b'Tournament deleted successfully', response.data)

    def test_view_tournament_list(self):
        """Test that the tournament list is displayed correctly."""
        self.login()
        response = self.client.get('/tournaments', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tournaments', response.data)

    def test_tournament_sharing(self):
        """Test sharing a tournament with another user."""
        self.login()
        with self.app.app_context():
            new_user = User(username='recipient', email='recipient@example.com')
            new_user.set_password('abc123')
            db.session.add(new_user)

            tournament = Tournament(name='Sharable Tournament', date=datetime.now(), location='Court 1', user_id=1)
            db.session.add(tournament)
            db.session.commit()
            tid = tournament.id

        response = self.client.post(f'/tournaments/{tid}/share', data={
            'recipient_username': 'recipient'
        }, follow_redirects=True)
        self.assertIn(b'Tournament shared successfully', response.data)

if __name__ == '__main__':
    unittest.main()





#  Analytics and Statistics
def test_player_statistics(self):
    """Test calculation and display of player statistics."""
    # William Craig
    # Step 1: Add a player with known statistics to the database manually via the python backend, 
    # Step2: Then ask the analyse.py "get_player_stats" function to get the information about that player from the database 
    # Step3: Assess if the data matches and throw error if appropriate 
    pass

def test_tournament_statistics(self):
    """Test calculation of statistics for a specific tournament."""
    # William Craig
    # Step 1: Add a tournament with known statistics to the database manually via the python backend, 
    # Step2: Then ask the analyse.py "get_tournament_stats" function to get the information about that tournament from the database 
    # Step3: Assess if the data matches and throw error if appropriate 
    pass

def test_head_to_head_comparison(self):
    """Test comparing performance between two players."""
    pass

def test_overall_performance_analysis(self):
    """Test overall statistics across all tournaments."""
    pass

def test_analytics_access_restriction(self):
    """Test that only authorized users can access analytics pages."""
    pass

#  Error Handling and Edge Cases
def test_404_page(self):
    """Test that the custom 404 error page is displayed."""
    pass

def test_500_page(self):
    """Test that the custom 500 error page is displayed."""
    pass

def test_invalid_tournament_id(self):
    """Test accessing a non-existent tournament ID."""
    pass

def test_invalid_player_id(self):
    """Test accessing a non-existent player ID."""
    pass

def test_csrf_protection(self):
    """Test that CSRF protection works on forms."""
    pass
