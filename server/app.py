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


# ---------- Notes CRUD Routes ---------- #


@app.get("/notes")
@login_required
def get_notes(current_user):
    """
    List notes for the current user with pagination.

    Query params:
      ?page=<int> (default: 1)
      ?per_page=<int> (default: 10, max: 50)

    Response:
      200 OK + {
        "items": [ {note}, ... ],
        "page": 1,
        "per_page": 10,
        "total": 25,
        "pages": 3
      }
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Enforce max per_page
    if per_page > 50:
        per_page = 50

    query = Note.query.filter_by(user_id=current_user.id).order_by(
        Note.created_at.desc()
    )

    pagination = db.paginate(
        query,
        page=page,
        per_page=per_page,
        error_out=False,
    )

    items = [note.to_dict() for note in pagination.items]

    return (
        jsonify(
            {
                "items": items,
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            }
        ),
        200,
    )


@app.post("/notes")
@login_required
def create_note(current_user):
    """
    Create a new note belonging to the current user.

    Expected JSON:
    {
      "title": "string",
      "content": "string"
    }

    Responses:
      201 Created + note JSON on success
      400 Bad Request + {"errors": [...]} on validation error
    """
    data = request.get_json() or {}

    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()

    errors = []
    if not title:
        errors.append("Title is required.")
    if not content:
        errors.append("Content is required.")

    if errors:
        return jsonify({"errors": errors}), 400

    note = Note(
        title=title,
        content=content,
        user_id=current_user.id,
    )

    db.session.add(note)
    db.session.commit()

    return jsonify(note.to_dict()), 201


@app.patch("/notes/<int:note_id>")
@login_required
def update_note(note_id, current_user):
    """
    Update an existing note belonging to the current user.

    Expected JSON (any subset):
    {
      "title": "new title",
      "content": "new content"
    }

    Responses:
      200 OK + note JSON on success
      404 Not Found + {"error": "Note not found"} if note doesn't exist or belongs to another user
    """
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    data = request.get_json() or {}

    if "title" in data and data["title"] is not None:
        note.title = data["title"].strip()

    if "content" in data and data["content"] is not None:
        note.content = data["content"].strip()

    db.session.commit()

    return jsonify(note.to_dict()), 200


@app.delete("/notes/<int:note_id>")
@login_required
def delete_note(note_id, current_user):
    """
    Delete an existing note belonging to the current user.

    Responses:
      204 No Content on success
      404 Not Found + {"error": "Note not found"} if note doesn't exist or belongs to another user
    """
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    db.session.delete(note)
    db.session.commit()

    return "", 204


if __name__ == "__main__":
    app.run(port=5555, debug=True)
