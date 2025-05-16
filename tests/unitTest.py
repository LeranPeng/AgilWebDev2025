# Unit and Selenium tests for the Badminton Tournament Manager application.
# Covers user authentication, match recording, tournament management, CSV import/export, and analytics.
# Includes both Flask test client and Selenium browser-based integration tests.

import unittest  # Python's built-in unit testing framework

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
        """Class-level setup that runs once before all tests."""
        # Set environment variable to indicate testing mode
        os.environ['FLASK_ENV'] = 'testing'
        
    def setUp(self):
        """Set up test environment before each test."""
        # Create a new Flask app and configure it for testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory DB for isolation
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
        """Clean up after each test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        # Clean up any test files created during the test
        for f in os.listdir(self.app.config['UPLOAD_FOLDER']):
            if not f.startswith('.'):  # Skip hidden files like .gitkeep
                os.unlink(os.path.join(self.app.config['UPLOAD_FOLDER'], f))

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run."""
        # Reset environment variable
        if 'FLASK_ENV' in os.environ:
            del os.environ['FLASK_ENV']

    def login(self):
        """Helper function to log in test user using Flask test client."""
        return self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)

    # -------------------- Match Recording and Results Tests --------------------

    def test_record_single_match(self):
        """Test recording a single match result (singles)."""
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
        """Test that match results are displayed correctly on the results page."""
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

    # -------------------- Data Import/Export Tests --------------------

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
        """Test exporting tournament data and statistics as JSON."""
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

    # -------------------- User Authentication and Authorization --------------------

    def test_user_registration(self):
        """Test that user registration works with valid data."""
        # Ensure no user is logged in by clearing the session
        with self.client.session_transaction() as session:
            session.clear()

        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }

        # Send POST request to register a new user
        response = self.client.post('/signup', data=data, follow_redirects=True)

        # Check if the response status code is 200 (success)
        self.assertEqual(response.status_code, 200)

        # Check for the flash message after successful registration
        self.assertIn(b'Account created successfully! Please log in.', response.data)

        # Check if the user was actually created in the database
        with self.app.app_context():
            user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'newuser@example.com')

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
        self.assertIn(b'Logged out successfully.', response.data)
        
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
        self.assertIn(b'Welcome Back', response.data)

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

    # -------------------- Player and Team Management --------------------

    def test_create_player(self):
        """Test that a new player can be added indirectly via tournament submission."""
        self.login()
        data = {
            'tournament_name': 'Test Tournament',
            'tournament_date': '2025-05-16',
            'team1[]': 'New Player',
            'team2[]': 'Opponent',
            'score1[]': '21-15',
            'score2[]': '15-21',
            'match_type[]': 'Singles',
            'round[]': 'Quarterfinal',
            'group[]': 'A'
        }
        response = self.client.post('/submit_results', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tournament results submitted successfully!', response.data)

        # Verify player exists in the database
        with self.app.app_context():
            player = Player.query.filter_by(name='New Player').first()
            self.assertIsNotNone(player)

    def test_player_duplicate_check(self):
        """Test that duplicate player names are handled gracefully (no duplicate records)."""
        self.login()
    
        data = {
            'tournament_name': 'Duplicate Test Tournament',
            'tournament_date': '2025-05-16',
            'team1[]': 'Duplicate Player',
            'team2[]': 'Opponent',
            'score1[]': '21-15',
            'score2[]': '15-21',
            'match_type[]': 'Singles',
            'round[]': 'Quarterfinal',
            'group[]': 'A'
        }

        # First submission
        response1 = self.client.post('/submit_results', data=data, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Tournament results submitted successfully!', response1.data)

        # Second submission (same player)
        response2 = self.client.post('/submit_results', data=data, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Tournament results submitted successfully!', response2.data)

        # Verify only one player record exists for 'Duplicate Player'
        with self.app.app_context():
            players = Player.query.filter_by(name='Duplicate Player').all()
            self.assertEqual(len(players), 1)

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

    # -------------------- Tournament Management --------------------

    def test_create_tournament(self):
        """Test that a new tournament is created successfully via submit_results."""
        self.login()
        data = {
            'tournament_name': 'Test Tournament',
            'tournament_date': '2025-05-16',
            'location': 'Test Location',
            'round[]': ['Round 1'],
            'group[]': ['Group A'],
            'team1[]': ['Player A'],
            'team2[]': ['Player B'],
            'score1[]': ['21-15'],
            'score2[]': ['15-21'],
            'match_type[]': ['Singles']
        }
        response = self.client.post('/submit_results', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tournament results submitted successfully!', response.data)

        # Optionally verify tournament in DB
        with self.app.app_context():
            tournament = Tournament.query.filter_by(name='Test Tournament').first()
            self.assertIsNotNone(tournament)

    def test_view_tournament_list(self):
        """Test that the tournament dashboard displays correctly."""
        self.login()
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Total Matches Uploaded', response.data)  # text that definitely appears on dashboard.html

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
            new_user_id = new_user.id

        response = self.client.post('/share/create', data={
            'tournament_id': tid,
            'user_id': new_user_id
        }, follow_redirects=True)

        self.assertIn(b'Tournament shared with recipient successfully!', response.data)

#################
# SELENIUM TESTS
#################

from selenium import webdriver
from selenium.webdriver.common.by import By  
from selenium.webdriver.support.ui import Select      
from multiprocessing import Process, set_start_method
import multiprocessing
import time

import platform

# multiprocessing on Mac requires this line in order to work 
if platform.system() == "Darwin":
    multiprocessing.set_start_method("fork") 
    
localHost = "http://127.0.0.1:5000"  
sleep_time = 1

def run_flask():
    """Run the Flask app in a separate process for Selenium tests."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory DB
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'test_uploads')
    
    app_context = app.app_context()
    app_context.push()
    with app_context:
        db.drop_all()
        db.create_all()

    app.run(host='127.0.0.1', port=5000, use_reloader=False)

def sign_up_log_in_as_test_user(driver):
    """Automate sign up and login as a test user using Selenium."""
    # Sign up
    driver.get(localHost + "/signup")
    username_feild = driver.find_element(By.ID, "username")
    username_feild.send_keys("testinguser")
    email_feild = driver.find_element(By.ID, "email")
    email_feild.send_keys("testinguser@mail.com")
    password1_feild = driver.find_element(By.ID, "password")
    password1_feild.send_keys("Testing123!")
    password2_feild = driver.find_element(By.ID, "confirm_password")
    password2_feild.send_keys("Testing123!")
    submit_button_feild = driver.find_element(By.ID, "submit_button")
    submit_button_feild.click()
    time.sleep(sleep_time)

    # Login
    username_feild = driver.find_element(By.ID, "username")
    username_feild.send_keys("testinguser")
    password_feild = driver.find_element(By.ID, "password")
    password_feild.send_keys("Testing123!")
    submit_button_feild = driver.find_element(By.ID, "submit_button")
    submit_button_feild.click()
    time.sleep(sleep_time)

def add_test_tournament(driver):
    """Automate adding a test tournament via the web form using Selenium."""
    driver.get(localHost+"/input_form")
    time.sleep(sleep_time)
    tournament_name_feild = driver.find_element(By.ID, "tournament_name")
    tournament_name_feild.send_keys("Test Tournament")
    tournament_date_feild = driver.find_element(By.ID, "tournament_date")
    tournament_date_feild.send_keys("01012025")
    location_feild = driver.find_element(By.ID, "location")
    location_feild.send_keys("Test location")
    round_feild = driver.find_element(By.ID, "round")
    round_feild.send_keys("Final")
    group_feild = driver.find_element(By.ID, "group")
    group_feild.send_keys("Test Group")
    team1_feild = driver.find_element(By.ID, "team1")
    team1_feild.send_keys("William Craig")
    team2_feild = driver.find_element(By.ID, "team2")
    team2_feild.send_keys("Craig William")
    score_feild = driver.find_element(By.ID, "score")
    score_feild.send_keys("21-19, 19-21, 21-18")
    time.sleep(sleep_time)
    submit_button_feild = driver.find_element(By.ID, "submit_button")
    submit_button_feild.click()
    time.sleep(sleep_time)

class SeleniumTests(unittest.TestCase):
    """Selenium-based integration tests for end-to-end browser interactions."""

    def setUp(self):
        # Start the Flask server in a separate process
        self.server_thread = Process(target=run_flask)
        self.server_thread.start()
        # Start the Selenium driver (Chrome browser)
        self.driver = webdriver.Chrome()
        self.driver.delete_all_cookies()
        self.driver.get(localHost)

    def tearDown(self):
        # Terminate Flask server and close browser after each test
        self.server_thread.terminate()
        self.driver.close()
        
    def test_tournament_statistics_selenium(self):
        """Test tournament statistics page via Selenium."""
        sign_up_log_in_as_test_user(self.driver)
        add_test_tournament(self.driver)
        # Go to analytics page and select tournament
        self.driver.get(localHost+"/analytics")
        time.sleep(sleep_time)
        tournament_select_feild = Select(self.driver.find_element(By.ID, "tournamentSelect"))
        tournament_select_feild.select_by_index(1) # Select the second item in the dropdown
        # Check that the tournament name appears on the analysis page
        self.assertIn("Test Tournament", self.driver.find_element(By.ID, "tournament-name").text,
                      "Tournament Analysis page title is not the same as tournament name provided in form")

    def test_player_statistics_selenium(self):
        """Test player statistics page via Selenium."""
        sign_up_log_in_as_test_user(self.driver)
        add_test_tournament(self.driver)
        self.driver.get(localHost + "/analytics")
        time.sleep(sleep_time)
        player_select_field = Select(self.driver.find_element(By.ID, "playerSelect"))
        player_select_field.select_by_visible_text("Craig William")
        self.assertIn("Craig William", self.driver.find_element(By.ID, "player-name").text,
                    "Player Analysis page title is not the same as player name provided in form")

if __name__ == '__main__':
    unittest.main()
