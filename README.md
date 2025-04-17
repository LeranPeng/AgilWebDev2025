# Badminton Tournament Manager

A web application for organizing and managing badminton tournaments, tracking player statistics, and analyzing game results.

## Features

- **Player Management**: Register and manage players
- **Tournament Organization**: Create tournaments and organize matches
- **Match Recording**: Record match results and scores
- **Statistics & Analytics**: View detailed player and tournament statistics
- **Data Import/Export**: Upload and download tournament data via CSV

## Installation

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

4. Initialize the database:
```bash
python seeddatabase.py
```

5. Run the application:
```bash
python app.py
```

6. Access the application in your browser at `http://localhost:5000`

## Project Structure

```
badminton-tournament-manager/
├── app.py              # Main Flask application
├── analytics.py        # Analytics module
├── models.py           # Database models
├── seeddatabase.py     # Database initialization script
├── requirements.txt    # Project dependencies
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
│   ├── layout.html     # Base template
│   ├── analytics.html
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
└── uploads/            # Directory for uploaded files
```

## Template Rendering Issue Fix

If you're experiencing issues with template rendering (template code showing as raw text), try these fixes:

1. Make sure your `layout.html` is in the correct location (directly in the `templates` folder)

2. Add the following configuration to your Flask app to enable template auto-reloading:
```python
app.config['TEMPLATES_AUTO_RELOAD'] = True
```

3. Clear your browser cache or try in a private/incognito window

4. If using PyCharm, try invalidating caches: File > Invalidate Caches / Restart

5. Check that the Jinja2 environment is properly configured:
```python
# Add this to app.py
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}
```

## Security Implementation

The application includes security features:
- Login required for all protected routes
- Session management
- Password hashing

## Database

This project uses SQLite for simplicity. The database file is `badminton.db`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.