from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(255))

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def __repr__(self):
        return f"<User {self.full_name}>"


class RecipeRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    title = db.Column(db.String(355), nullable=True)
    ingredients = db.Column(db.JSON)
    description = db.Column(db.String(2000), nullable=True)
    youtube_link = db.Column(db.String(255), nullable=True)


class RecipeString(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset = db.Column(db.String(2000), nullable=False)
