import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "instance", "spark.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # ITAD — https://isthereanydeal.com/dev/
    ITAD_API_KEY = os.environ.get('ITAD_API_KEY', '')
    ITAD_CLIENT_ID = os.environ.get('ITAD_CLIENT_ID', '')
    ITAD_CLIENT_SECRET = os.environ.get('ITAD_CLIENT_SECRET', '')
