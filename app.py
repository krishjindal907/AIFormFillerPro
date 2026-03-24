import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request
from models import db, User
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-123-v2'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        return response

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from routes.auth import auth_bp
    from routes.core import core_bp
    from routes.profile import profile_bp
    from routes.analyze import analyze_bp
    from routes.autofill import autofill_bp
    from routes.parsing import parsing_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(analyze_bp)
    app.register_blueprint(autofill_bp)
    app.register_blueprint(parsing_bp)

    with app.app_context():
        # Create database tables if they do not exist
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    # Binds to 0.0.0.0 to allow Local Network / Smartphone Access
    app.run(debug=True, host='0.0.0.0')
