# app/__init__.py
import os
from flask import Flask
from app.routes import lti  # uses the Blueprint created in app/routes/__init__.py

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # minimal config (override with env vars in real deployments)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

    # Register the LTI/Grader blueprint at root (so routes are /grader, /grader-base, etc.)
    app.register_blueprint(lti, url_prefix="")

    return app

# WSGI convenience (so `gunicorn 'app:create_app()'` works or flask picks up `app`)
app = create_app()
