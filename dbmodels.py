from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'  # Change to a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use SQLite for simplicity
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# To Define a User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

# To Define a model for the metadata table
class FileMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(50), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    url_link_s3 = db.Column(db.String(255), nullable=False)
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Create the database
with app.app_context():
    db.create_all()