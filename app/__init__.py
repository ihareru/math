from flask import Flask
from config import Config
from app.settings_manager import load_settings
from app.utils import resource_path


app = Flask(__name__, template_folder=resource_path("app/templates"),
            static_folder=resource_path("app/static"))
app.config.from_object(Config)


@app.context_processor
def inject_settings():
    return dict(
        settings=load_settings()
    )


from app import routes
