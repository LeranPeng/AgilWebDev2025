import os
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from dotenv import load_dotenv

# Import models
from models import db

# Import routes
from routes.auth import auth_bp
from routes.user import user_bp
from routes.tournament import tournament_bp
from routes.match import match_bp
from routes.sharing import sharing_bp
from routes.analytics import analytics_bp
from routes.admin import admin_bp


def create_app():
    app = Flask(__name__)

    # Load environment variables
    load_dotenv("key.env")

    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    if not app.config['SECRET_KEY']:
        raise ValueError("No SECRET_KEY set for Flask application")

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///badminton.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    csrf = CSRFProtect(app)
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(tournament_bp)
    app.register_blueprint(match_bp)
    app.register_blueprint(sharing_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('html/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('html/500.html'), 500

    @app.errorhandler(400)
    def bad_request(e):
        return render_template('html/400.html'), 400

    return app


# Create the application instance
app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True, port=5000)