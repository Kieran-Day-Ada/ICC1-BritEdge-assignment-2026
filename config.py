import os


class Config:
    # Secret key for Flask sessions and CSRF protection.
    # IMPORTANT: In production this should be a strong, randomly generated
    # string loaded from an environment variable or a secure secret store.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess-this-secret-key-for-development'

    # --- Database backend selection --------------------------------------
    # If COSMOS_ENDPOINT is set, the app stores data as documents in Azure
    # Cosmos DB (NoSQL API). Otherwise it uses SQLAlchemy: DATABASE_URL for
    # a real SQL database (e.g. Azure Database for PostgreSQL), or the
    # built-in SQLite database if DATABASE_URL isn't set either - so the app
    # works out of the box with no configuration at all.
    COSMOS_ENDPOINT = os.environ.get('COSMOS_ENDPOINT')
    DATABASE_URL = os.environ.get('DATABASE_URL')

    DB_MODE = 'nosql' if COSMOS_ENDPOINT else 'sql'

    # Only used when DB_MODE == 'sql'.
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
