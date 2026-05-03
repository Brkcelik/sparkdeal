import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "instance", "spark.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # ITAD API key — https://isthereanydeal.com/dev/ adresinden ücretsiz alın
    ITAD_API_KEY = os.environ.get('ITAD_API_KEY', '')
