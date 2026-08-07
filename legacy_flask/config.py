import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://"
        f"{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}?charset=utf8mb4"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
    SMTP_LOGIN = os.getenv("SMTP_LOGIN")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL")