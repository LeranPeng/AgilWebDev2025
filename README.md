# Badminton Tournament Management System

A Flask-based web application for managing badminton tournaments, tracking player statistics, and analyzing match data.

## Features

- User accounts and authentication
- Tournament creation and management
- Match recording and scoring
- Player statistics and analytics
- Head-to-head comparisons
- CSV data import/export

## Project Structure

```
badminton-manager/
├── app.py                  # Main application file
├── analytics.py            # Analytics module
├── models.py               # Database models
├── seeddatabase.py         # Script to populate sample data
├── uploads/                # Directory for uploaded CSV files
├── static/                 # Static assets (CSS, JS, images)
├── templates/              # Template files
│   ├── html/               # Main HTML templates
│   │   ├── 404.html
│   │   ├── 500.html
│   │   ├── dashboard.html
│   │   ├── homepage.html
│   │   ├── InputForm.html
│   │   ├── Login.html
│   │   ├── Signup.html
│   │   ├── upload.html
│   │   └── User_settings.html
│   ├── analytics.html      # Analytics dashboard
│   ├── head_to_head.html   # Head-to-head comparison
│   ├── player_analytics.html   # Individual player analysis
│   ├── review_results.html     # CSV review page
│   └── tournament_analytics.html   # Tournament analysis
└── README.md               # This file
```

## Template Structure

The application uses a specific template structure:

1. **Main UI templates**: Located in `templates/html/` directory
   - Referenced in code as `render_template("html/filename.html")`
   - Example: `render_template("html/homepage.html")`

2. **Analytics templates**: Located directly in the `templates/` directory
   - Referenced in code as `render_template("filename.html")`
   - Example: `render_template("analytics.html")`

## Setup and Installation

### Prerequisites

- Python 3.8+
- SQLite (included with Python)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd badminton-manager
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install flask flask-sqlalchemy
   ```

4. Initialize the database:
   ```
   python app.py
   ```

5. (Optional) Seed the database with sample data:
   ```
   python seeddatabase.py
   ```

## Running the Application

1. Start the Flask development server:
   ```
   python app.py
   ```

2. Access the application in your web browser:
   ```
   http://localhost:5000/
   ```

## Usage

1. **Sign up/Log in**: Create an account or log in with existing credentials
2. **Dashboard**: View tournament statistics and recent matches
3. **Upload**: Import player data or match results via CSV
4. **Manual Input**: Add tournament results manually via the form
5. **Analytics**: Explore statistics and visualizations of player/tournament data

## Important Notes on Template Paths

When adding new templates or routes, be aware of the template structure:

- If your template is a main UI page, place it in `templates/html/` and reference it as `html/filename.html`
- If your template is an analytics page, place it directly in `templates/` and reference it as `filename.html`

For example:
```python
# For main UI pages
@app.route("/example")
def example_page():
    return render_template("html/example.html")

# For analytics pages
@analytics.route("/analytics/example")
def analytics_example():
    return render_template("example.html")
```

Following this convention will prevent `TemplateNotFound` errors.

## Development Notes

### Database Models

The application uses SQLAlchemy with the following models:
- `User`: User accounts
- `Tournament`: Tournament records
- `Player`: Individual player records
- `Team`: Teams (composed of one or two players)
- `Match`: Match results linking teams in tournaments

### Authentication

The application uses Flask sessions for authentication. Protected routes check for `user_id` in the session.

## License

MIT License