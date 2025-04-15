# Badminton Tournament Manager
Author: Leran Peng, Dennis Chuo, Andrew Mekhail, William Craig
A Flask web application for managing badminton tournaments, tracking matches, and analyzing player performance.

## Features

- **User Authentication**: Secure signup, login, and account management
- **Tournament Management**: Create and manage badminton tournaments
- **Match Tracking**: Record match results with detailed scoring
- **Player Management**: Track players and their participation in matches
- **Data Upload**: Upload tournament data via forms or CSV files
- **Dashboard**: View tournament statistics and recent match history

## Technical Structure

### Models

- **User**: Stores user accounts with authentication information
- **Tournament**: Represents tournaments with dates, locations, and organizers
- **Player**: Individual players that can participate in matches
- **Team**: Can be single players or pairs for doubles matches
- **Match**: Records match details including scores, participants, and match types

### Routes

- Authentication routes (signup, login, logout)
- Dashboard and user settings management
- Tournament and match data submission
- CSV data import/export
- API endpoints for AJAX requests

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```
git clone <repository-url>
cd badminton-tournament-manager
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:
```
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///badminton.db
UPLOAD_FOLDER=uploads
```

5. Initialize the database:
```
flask db init
flask db migrate
flask db upgrade
```

### Running the Application

```
flask run
```

The application will be available at http://localhost:5000

## File Structure

```
badminton-tournament-manager/
├── app.py                  # Main application file
├── templates/              # HTML templates
│   ├── html/               # HTML templates from the project
│   │   ├── dashboard.html
│   │   ├── homepage.html
│   │   ├── InputForm.html
│   │   ├── Login.html
│   │   ├── Signup.html
│   │   ├── upload.html
│   │   └── User_settings.html
│   └── review_results.html # Additional template for reviewing uploaded results
├── static/                 # CSS, JS, and other static files
├── uploads/                # Directory for temporary file uploads
├── venv/                   # Virtual environment (not in version control)
├── .env                    # Environment variables (not in version control)
├── .gitignore
├── requirements.txt        # Project dependencies
└── README.md               # This file
```

## Dependencies

- Flask: Web framework
- Flask-SQLAlchemy: Database ORM
- Flask-WTF: Form handling and CSRF protection
- Werkzeug: Utilities including password hashing
- python-dotenv: Environment variable management

## Future Enhancements

- Advanced tournament creation with configurable formats
- Automatic group generation based on player skill levels
- Player rankings and statistics
- Schedule generation for tournaments
- PDF report generation for tournament results
- Email notifications for upcoming matches