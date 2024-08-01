from flask import Flask
from app.views import main as main_blueprint
from app.models import db, User
from flask_migrate import Migrate
from flask_login import LoginManager


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate = Migrate(app, db)

    app.register_blueprint(main_blueprint)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
