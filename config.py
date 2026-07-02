from dotenv import load_dotenv
import os


load_dotenv()


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

    SMTP_LOGIN = os.getenv("SMTP_LOGIN")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

    SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL")