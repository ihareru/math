from flask import Flask
from config import Config
from app.settings_manager import load_settings
from app.utils import resource_path
from app.database import db
from flask_migrate import Migrate


app = Flask(
    __name__,
    template_folder=resource_path("app/templates"),
    static_folder=resource_path("app/static")
)

app.config.from_object(Config)

db.init_app(app)

migrate = Migrate(app, db)


@app.context_processor
def inject_settings():
    return dict(settings=load_settings())


from app import models
from app import routes
