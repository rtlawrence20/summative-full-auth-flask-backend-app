from flask import (
    Flask,
    jsonify,
    request,
    session,
)
from flask_migrate import Migrate
from functools import wraps

from models import db, bcrypt, User, Note
import os

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "app.db")
app.config["SQLALCHEMY_TRACKING_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "dev-secret-key"

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)


# ---------- Helper utilities ---------- #


def get_current_user():
    """
    Look up the current logged-in user using session['user_id'].
    Returns a User instance or None.
    """
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required(fn):
    """
    Decorator for custom resource routes to ensure the user is logged in.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        # store user on the function object so the route can use it
        return fn(*args, current_user=user, **kwargs)

    return wrapper


# ---------- Basic check ---------- #


@app.route("/")
def index():
    return jsonify({"message": "API is running"}), 200


# ---------- Auth Routes ---------- #


@app.post("/signup")
def signup():
    """
    Create a new user, start a session.
    Expected JSON:
    {
      "username": "string",
      "password": "string",
      "password_confirmation": "string"
    }

    On success:
      201 + user JSON
    On validation error:
      422 + {"errors": [ ... ]}
    """
    data = request.get_json() or {}

    username = (data.get("username") or "").strip()
    password = data.get("password")
    password_confirmation = data.get("password_confirmation")

    errors = []

    # Validation
    if not username:
        errors.append("Username is required.")
    if not password:
        errors.append("Password is required.")
    if password != password_confirmation:
        errors.append("Passwords do not match.")

    # Uniqueness check
    if username:
        existing = User.query.filter_by(username=username).first()
        if existing:
            errors.append("Username already taken.")

    if errors:
        # Report validation errors
        return jsonify({"errors": errors}), 422

    # Create user
    user = User(username=username)
    user.password = password  # triggers hashing in models.User.password setter

    db.session.add(user)
    db.session.commit()

    # Start session
    session["user_id"] = user.id

    return jsonify(user.to_dict()), 201


@app.post("/login")
def login():
    """
    Log in an existing user.

    Expected JSON:
    {
      "username": "string",
      "password": "string"
    }

    On success:
      200 + user JSON
    On failure:
      401 + {"error": "Invalid username or password"}
    """
    data = request.get_json() or {}

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        # Treat missing fields as invalid credentials
        return jsonify({"error": "Invalid username or password"}), 401

    user = User.authenticate(username, password)
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    session["user_id"] = user.id

    return jsonify(user.to_dict()), 200


@app.get("/check_session")
def check_session():
    """
    Check if a user is logged in.

    If logged in:
      200 + user JSON
    If not:
      200 + {}   (frontend expectation)
    """
    user = get_current_user()
    if not user:
        return jsonify({}), 200

    return jsonify(user.to_dict()), 200


@app.delete("/logout")
def logout():
    """
    Log out the current user.

    On success:
      204 No Content
    """
    session.pop("user_id", None)
    return "", 204


if __name__ == "__main__":
    app.run(port=5555, debug=True)
