from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy.ext.hybrid import hybrid_property

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    """
    User model

    - username is unique & required
    - password is stored as a secure hash in _password_hash
    - use the 'password' write-only property to set it
    - authenticate() classmethod handles login checks
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    _password_hash = db.Column(db.String(128), nullable=False)

    # One-to-many: User -> Notes
    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")

    @hybrid_property
    def password_hash(self):
        return self._password_hash

    # Make "password" write-only
    @hybrid_property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, plain_text_password: str):
        """
        Set a new password, storing only a secure hash.
        """
        if not plain_text_password:
            raise ValueError("Password cannot be empty.")

        hashed = bcrypt.generate_password_hash(plain_text_password).decode("utf-8")
        self._password_hash = hashed

    def check_password(self, plain_text_password: str) -> bool:
        """
        Return True if the given password matches the stored hash.
        """
        if not self._password_hash:
            return False

        return bcrypt.check_password_hash(self._password_hash, plain_text_password)

    @classmethod
    def authenticate(cls, username: str, plain_text_password: str):
        """
        Classmethod used in /login:
        - look up by username
        - check the password
        - return the user if valid, else None
        """
        user = cls.query.filter_by(username=username).first()
        if user and user.check_password(plain_text_password):
            return user
        return None

    def to_dict(self):
        """
        Minimal representation to send back to the frontend.
        """
        return {
            "id": self.id,
            "username": self.username,
        }

    def __repr__(self):
        return f"<User id={self.id} username={self.username!r}>"


class Note(db.Model):
    """
    User-owned resource model: Note

    Requirements:
    - id (primary key)
    - at least 2 other fields (title, content, plus timestamps here)
    - foreign key to user_id, linking to the owning User
    """

    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)

    # non-FK fields
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # FK field
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # relationship back to User
    user = db.relationship("User", back_populates="notes")

    def to_dict(self):
        """
        Representation for API responses.
        """
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id": self.user_id,
        }

    def __repr__(self):
        return f"<Note id={self.id} title={self.title!r} user_id={self.user_id}>"
