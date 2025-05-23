# 🏸 Badminton Tournament Manager - Badminton MASTER

A comprehensive web application for organizing badminton tournaments, tracking player statistics, and analyzing game results.

Developer: Leran Peng(23909531), Andrew Mekhail (23775973), Dennis Chuo (23863534), Will Craig (23180621)
## 📋 Overview

Badminton MASTER allows tournament organizers to easily analyse and calculate key data of their hosted tournaments. 

Users can upload match data via CSV or input results through the web interface, then access analytics to track player performance, view match statistics, and share tournament data with other users.

## ✨ Features

### For Tournament Organizers
- **Player Management**: Register and manage player profiles
- **Tournament Creation**: Set up new tournaments with customizable settings
- **Match Recording**: Input match results with flexible scoring formats
- **Data Import/Export**: Upload and download tournament data via CSV
- **Results Sharing**: Share tournament results with other user accounts

### For Players and Spectators
- **Player Statistics**: View detailed performance metrics and match history
- **Tournament Standings**: Access tournament brackets and results
- **Head-to-Head Analysis**: Compare performance between any two players
- **Match History**: Review past match details and outcomes

### Technical Highlights
- **Beautiful Frontend**: Modern UI with Bootstrap framework
- **Server-side Rendering**: Fast performance with Flask and Jinja templates
- **Robust Backend**: Python with Flask for reliable processing
- **Secure Authentication**: User account system with password protection
- **Admin Controls**: Special admin accounts for system management

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Pip package manager
- SQLite (included with Python)

### Installation

<details>
<summary>View detailed installation instructions</summary>

1. Clone the repository:
```bash
git clone https://github.com/LeranPeng/AgilWebDev2025.git
cd AgilWebDev2025
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the admin user(optional):
```bash
python admin_init.py
```
We have an admin panel to manage all matches, users, and tournaments. But it's fine to sign up as an user.

5. Run the application:
```bash
python app.py
```

6. Access the application in your browser at `http://localhost:5000`
</details>


## 📊 Using the Application

### Uploading Tournament Data

1. **Manual Data Entry**:
   - Use the Input Form to add tournament details and match results
   - Specify match types (Singles, Doubles, Mixed)
   - Enter scores in standard format (e.g., "21-19, 19-21, 21-18")

2. **Post-Tournament Results**:
   - Upload match results using CSV with required columns:
     - Team 1, Team 2, Score 1, Score 2, Round, Match Type
   - For doubles matches, separate player names with commas

3. **Pre-Tournament Setup**:
   - Upload player list using CSV format
   - Player names must be in the first column


### Analyzing Results

- **Player Analytics**: View detailed statistics for individual players
- **Tournament Analytics**: Analyze tournaments by match types, rounds, and more
- **Head-to-Head**: Compare any two players' performance against each other
- **Overall Analysis**: View system-wide statistics across all tournaments

## 🧩 Project Structure

```
badminton-tournament-manager/
├── app.py              # Main Flask application
├── admin_init.py       # Admin Initialization Script 
├── admin.py            # Admin account functions
├── analytics.py        # Analytics module
├── models.py           # Database models
├── requirements.txt    # Project dependencies
├── static/             # Static files (CSS, JS, images)
├── routes/             # Python Flask backend logic for the sub pages
|   ├── admin.py        # functions for admin panel
│   ├── analytics.py    # functions for data analysis
│   ├── auth.py         # functions for login and signup
│   ├── match.py        # functions for matches 
│   ├── sharing.py      # functions for information sharing
│   ├── tournament.py   # functions for tournament logic
│   ├── user.py         # functionality for user settings
├── tests/
│   ├── test_uploads/   # directory for unittests testing uploads
│   ├── systemtests.py  # System Tests
│   ├── unittest.py     # Unittests 
├── templates/          # HTML templates
│   ├── layout.html     # Base template
│   ├── analytics.html
│   ├── overall_analysis.html
│   ├── head_to_head.html
│   ├── player_analytics.html
│   ├── review_results.html
│   ├── tournament_analytics.html
│   └── html/           # HTML templates for main pages
│       ├── 404.html
│       ├── 500.html
│       ├── dashboard.html
│       ├── homepage.html
│       ├── InputForm.html
│       ├── Login.html
│       ├── Signup.html
│       ├── upload.html
│       └── User_settings.html
├── README.md
└── uploads/            # Directory for uploaded files 
```

## 🔒 Security Implementation

Application security features:
- Login required for all protected routes (everything other than "/" and "/home")
- Admin user accounts with additional protected permissions  
- Session management with configurable timeout
- Password hashing and validation
- CSRF protection for all forms
- User login input data validation and sanitization

## 💾 Database

This project uses SQLite for simplicity and easy deployment. The database file is `badminton.db`.

### Key Models
- **User**: Stores user accounts and authentication data
- **Tournament**: Stores tournament details and metadata
- **Player**: Represents individual players in the system
- **Team**: Represents singles or doubles teams (links to players)
- **Match**: Stores match details, scores, and results
- **SharedTournament**: Manages tournament sharing between users

## 👨‍💻 Admin Account Guide

Admin accounts provide extended capabilities for managing the entire system, availiable at 

http://your-domain/admin

<details>
<summary>View admin setup instructions</summary>

### Setup

#### Database Schema

The admin functionality requires an `is_admin` field in the User model:

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    last_login = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_admin = db.Column(db.Boolean, default=False)  # Admin status field
    tournaments = db.relationship('Tournament', backref='organizer', lazy=True)
```

#### Creating the Initial Admin User

For new installations, run the `admin_init.py` script:

```bash
python admin_init.py
```

Follow the prompts to create a new admin user or grant admin privileges to an existing user.
</details>

<details>
<summary>View admin features</summary>

### Admin Dashboard Features

- **User Management**: Create, edit, and delete users
- **Tournament Management**: Manage all tournaments in the system
- **Player Management**: Track player statistics and merge duplicates
- **System Statistics**: Monitor platform usage and activity
- **Database Maintenance**: Clean up and optimize the database

### Accessing the Admin Interface

Once logged in as an admin, visit:
```
http://your-domain/admin
```
</details>

## 🔍 Troubleshooting

<details>
<summary>Common issues and solutions</summary>

### Installation Issues

- **Dependency errors**: Make sure you're using Python 3.8+ and have updated pip
  ```bash
  python -m pip install --upgrade pip
  ```

- **Database initialization fails**: Remove the existing database file and try again
  ```bash
  rm badminton.db
  ```

### Runtime Issues

- **Login issues**: If you can't log in, you may need to clear browser cookies or reset your password

- **CSV import errors**: Ensure your CSV files match the expected format with correct column headers

- **Page not found errors**: Check that you're accessing the correct URL and are logged in
</details>

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## Commitments

**This file is fully generated by AI**
