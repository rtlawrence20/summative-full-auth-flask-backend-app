from flask import Flask, jsonify
from flask_migrate import Migrate

from models import db, bcrypt
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


@app.route("/")
def index():
    return jsonify({"message": "API is running"}), 200


if __name__ == "__main__":
    app.run(port=5555, debug=True)
