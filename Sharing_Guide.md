# Tournament Sharing Feature Implementation Guide

This guide walks through implementing the tournament sharing feature that allows users to securely share tournament data with specific other users within the application.

## Overview

The sharing feature allows:
- User A to share tournament data with User B without User C having access
- User B to view tournaments shared with them
- User A to revoke access at any time
- All sharing happens within the application (not via links or file downloads)

## Implementation Steps

### 1. Database Updates

First, add the `SharedTournament` model to `models.py`:

```python
class SharedTournament(db.Model):
    """Model for tournament sharing between users"""
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id', ondelete='CASCADE'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    shared_with_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    shared_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Define relationships
    tournament = db.relationship('Tournament', backref='shared_tournaments')
    owner = db.relationship('User', foreign_keys=[owner_id], backref='tournaments_shared')
    shared_with = db.relationship('User', foreign_keys=[shared_with_id], backref='tournaments_shared_with_me')
    
    # Ensure a tournament is only shared once between same users
    __table_args__ = (
        db.UniqueConstraint('tournament_id', 'owner_id', 'shared_with_id', name='unique_tournament_sharing'),
    )
```

### 2. Create the Migration Script

Run the migration script (`migration.py`) to create the new table:

```python
"""
Migration script to add the SharedTournament table to the database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, db
from models import SharedTournament

def migrate_database():
    """Check if SharedTournament table exists, create it if not"""
    with app.app_context():
        try:
            # Check if the table exists by performing a simple query
            SharedTournament.query.first()
            print("SharedTournament table already exists")
        except Exception as e:
            if "no such table" in str(e).lower():
                print("Creating SharedTournament table...")
                # Create the table
                SharedTournament.__table__.create(db.engine)
                print("SharedTournament table created successfully")
            else:
                print(f"Error checking SharedTournament table: {str(e)}")

if __name__ == "__main__":
    migrate_database()
```

### 3. Add Routes to `app.py`

Add the following routes to handle sharing functionality:

```python
# Route to view your tournaments that you can share
@app.route("/share")
@login_required
def share_page():
    # Get tournaments created by the current user 
    # Get all other users (potential recipients)
    # Get existing shares
    # Render the share template
    ...

# Route to create a sharing relationship
@app.route("/share/create", methods=["POST"])
@login_required
def create_share():
    # Get form data
    # Validate tournament ownership and target user
    # Create the share record
    ...

# Route to remove a sharing relationship
@app.route("/share/delete", methods=["POST"])
@login_required
def delete_share():
    # Get form data
    # Find and delete the share record
    ...

# Route to view tournaments shared with you
@app.route("/shared-with-me")
@login_required
def shared_with_me():
    # Get tournaments shared with the current user
    # Render the shared_with_me template
    ...

# View a specific shared tournament
@app.route("/shared-with-me/<int:tournament_id>")
@login_required
def view_shared_tournament(tournament_id):
    # Check if the tournament is shared with the current user
    # Get tournament details and matches
    # Render the view_shared_tournament template
    ...
```

### 4. Create the Templates

Create the following templates:

1. `share.html` - For sharing your tournaments
2. `shared_with_me.html` - For viewing tournaments shared with you
3. `view_shared_tournament.html` - For viewing a specific shared tournament

### 5. Update Navigation

Add links to the new sharing features in the navigation menu:

```html
<a href="/share" class="px-3 hover:underline {% if request.path == '/share' %}font-semibold{% endif %}">Share</a>
<a href="/shared-with-me" class="px-3 hover:underline {% if request.path == '/shared-with-me' %}font-semibold{% endif %}">Shared With Me</a>
```

### 6. Update Dashboard

Add sharing buttons to the dashboard:

```html
<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
  <a href="/share" class="bg-indigo-600 text-white p-6 rounded-lg shadow hover:bg-indigo-700 transition">
    <h3 class="text-xl font-bold mb-2">🔄 Share Tournaments</h3>
    <p>Share your tournament data with other users.</p>
  </a>
  <a href="/shared-with-me" class="bg-teal-600 text-white p-6 rounded-lg shadow hover:bg-teal-700 transition">
    <h3 class="text-xl font-bold mb-2">📥 Shared With Me</h3>
    <p>View tournaments others have shared with you.</p>
  </a>
</div>
```

## Security Considerations

1. Always verify ownership before sharing (ensure the user owns the tournament they're sharing)
2. Always verify access before showing shared content (check if the current user has been granted access)
3. Use `CASCADE` in foreign keys to automatically remove shares if a tournament or user is deleted
4. Implement proper CSRF protection for all forms

## Testing

Test the following scenarios:
1. User A shares a tournament with User B
2. User B can view the shared tournament
3. User C cannot view the tournament (not shared with them)
4. User A revokes access from User B
5. User B can no longer view the tournament

This implementation provides selective sharing while maintaining data security within the application.