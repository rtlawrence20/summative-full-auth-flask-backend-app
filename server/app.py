from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config")

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # Simple health-check route
    @app.route("/")
    def index():
        return jsonify({"message": "API is running"})

    return app


app = create_app()
