import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bolisaty.db")

WKHTMLTOPDF_PATH = os.getenv(
    "WKHTMLTOPDF_PATH",
    r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

LABELS_DIR = os.getenv("LABELS_DIR", "Labels")
QR_DIR = os.getenv("QR_DIR", "Assets/qr")
LOGOS_DIR = os.getenv("LOGOS_DIR", "Assets/logos")
LOGS_DIR = os.getenv("LOGS_DIR", "Logs")

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")