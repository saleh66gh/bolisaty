import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bolisaty.db")

WKHTMLTOPDF_PATH = os.getenv(
    "WKHTMLTOPDF_PATH",
     "/usr/local/bin/wkhtmltopdf"
)

LABELS_DIR = os.getenv("LABELS_DIR", "Labels")
QR_DIR = os.getenv("QR_DIR", "Assets/qr")
LOGOS_DIR = os.getenv("LOGOS_DIR", "Assets/logos")
LOGS_DIR = os.getenv("LOGS_DIR", "Logs")

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")