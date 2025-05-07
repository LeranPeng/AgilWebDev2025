# 🏸Badminton Tournament Manager - Badminton MASTER

A web application for analysing badminton tournaments, tracking player statistics, and viewing game results.

Users are able to upload a .csv file or complete a form with the results of their own self hosted Badminton tournament and use Badminton MASTER to view ther overall results and ranking of players, compare two players, and share the data with other user accounts. 

![](/static/homepage.png)

## ✨Product Features
- **Player Management**: Register and manage players
- **Tournament Organization**: Create tournaments and organize matches
- **Match Recording**: Record match results and scores
- **Statistics & Analytics**: View detailed player and tournament statistics
- **Data Import/Export**: Upload and download tournament data via CSV
- **Admin Accounts**: Use Admin accounts to control your installation

## 🚀PROJECT Features
- **Beautiful Frontend**: Using the Bootstrap framework 
- **Serverside Rendering**: Using Flask and Jinja templates 
- **Simple backend**: Written in Python with Flask
- **Simple Database structure**: Using SQLite, interfaced using the SQAlchemy python package

![](/static/analysispage.png)

## ⬇️Installation Instructions
<details>
<summary>View Installation instructions</summary>

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
</details>

## 🗂️Project Structure

```
badminton-tournament-manager/
├── app.py              # Main Flask application
├── admin_init.py       # Admin Initialization Script 
├── admin.py            # Admin account functions
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
├── README.md
└── uploads/            # Directory for uploaded files 
```


## 🔒Security Implementation

The application includes security features:
- Login required for all protected routes (everything other than "/" and "/home")
- Admin user accounts with additional protected functionality and database editing functions
- Session management
- Password hashing

## 💾Database

This project uses SQLite for simplicity. The database file is `badminton.db`.


# 👨🏻‍💻Admin Account Guide
This project has "admin" account functionality, "admin" accounts are user accounts with additional privelidges and functionality over the data and accounts in your Badminton MASTER installation. 

## Main features of the admin accounts:
- **Admin Dashboard page**: The admin dashboard at `/admin`
- **User Management**: Create, edit, and delete user accounts
- **Tournament Management**: View and manage all tournaments in the system
- **Player Management**: View player statistics, merge duplicate players
- **System Statistics**: Get insights into system usage and activity
- **Database Maintenance**: Clean up orphaned records and optimize the database

## Admin Account Documentation
<details>
<summary>Setup</summary>

### Setup

### Database Schema Update

The admin functionality requires adding an `is_admin` field to the User model. This change has been implemented in the updated `models.py` file:

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    last_login = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_admin = db.Column(db.Boolean, default=False)  # New field for admin status
    tournaments = db.relationship('Tournament', backref='organizer', lazy=True)
```


### Creating the Initial Admin User

When upgrading an existing installation, you'll need to run the `admin_init.py` script to create the first admin user or grant admin privileges to an existing user:

1. Ensure you have the latest code with the admin functionality
2. Run `python admin_init.py`
3. Follow the prompts to create a new admin user or update an existing one

For new installations, an admin user will be created automatically when the application starts for the first time.
</details>


<details>
<summary>User management </summary>

### User Management
The user management interface allows administrators to:

- View all registered users
- Create new user accounts
- Edit existing user information, including passwords
- Grant or revoke admin privileges
- Delete user accounts (if they have no associated tournaments)


#### Admin Privileges
Users with admin status have access to:

- The admin dashboard at `/admin`
- All user, tournament, player, and system data regardless of ownership
- Special maintenance and system management features
</details>


<details>
<summary>Tournament management</summary>

### Tournament Management
The tournament management interface allows administrators to:

- View all tournaments in the system
- See detailed tournament information
- View all matches within a tournament
- Delete tournaments and their associated matches
</details>


<details>
<summary>Player management</summary>

### Player Management
The player management interface provides:

- A list of all players in the system
- Detailed player statistics and performance metrics
- Tools for identifying and merging duplicate player records
- Player activity tracking

#### Merging Duplicate Players

One common issue in tournament management is duplicate player records due to different spellings or typos. The admin interface provides a tool to merge these records:

1. Navigate to Player Management
2. Find the player you want to keep
3. Click "Merge Player"
4. Select the duplicate player record to merge
5. Confirm the merge

This process will:
- Transfer all teams from the duplicate to the target player
- Update all matches accordingly
- Delete the duplicate player record
</details>


<details>
<summary>System management</summary>

### System Statistics
The statistics dashboard provides insights into system usage:

- User, tournament, match, and player counts
- Activity trends over time
- Match type distribution
- Most active users
- System health metrics
</details>


<details>
<summary>Database Maintenance</summary>

### Database Maintenance
The maintenance tools help keep the database clean and optimized:

- Remove orphaned teams (teams with no associated matches)
- Remove inactive players (players not associated with any teams)
- Delete empty tournaments (tournaments with no matches)
- Back up the database
</details>


<details>
<summary>Security Considerations</summary>

### Security Considerations
When implementing the admin functionality, consider the following security best practices:

1. **Change the default admin password immediately** after installation
2. Use strong, unique passwords for all admin accounts
3. Limit the number of admin users
4. Regularly review the admin user list
5. Consider implementing additional authentication measures for admin access
6. Implement proper input validation on all admin forms
7. Log all administrative actions
8. Regularly back up your database
</details>


<details>
<summary>Accessing the Admin Interface</summary>

### Accessing the Admin Interface
Once logged in as an admin user, you can access the admin dashboard at:

```
http://your-domain/admin
```

From there, you can navigate to all the admin features described in this guide.
</details>

## License

This project is licensed under the MIT License - see the LICENSE file for details.