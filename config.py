import os
from urllib.parse import quote_plus


class Config:
    # Secret key for Flask sessions and CSRF protection.
    # IMPORTANT: In production this should be a strong, randomly generated
    # string loaded from an environment variable or a secure secret store.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess-this-secret-key-for-development'

    # --- Database backend selection --------------------------------------
    # If COSMOS_ENDPOINT is set, the app stores data as documents in Azure
    # Cosmos DB (NoSQL API). Otherwise it uses SQLAlchemy, choosing in order:
    # 1) Azure SQL from AZURE_SQL_* variables
    # 2) PostgreSQL from PG_* variables
    # 3) Built-in SQLite if neither SQL option is configured.
    COSMOS_ENDPOINT = os.environ.get('COSMOS_ENDPOINT')

    AZURE_SQL_SERVER = os.environ.get('AZURE_SQL_SERVER')
    AZURE_SQL_USER = os.environ.get('AZURE_SQL_USER')
    AZURE_SQL_PASSWORD = os.environ.get('AZURE_SQL_PASSWORD')
    AZURE_SQL_PORT = os.environ.get('AZURE_SQL_PORT', '1433')
    AZURE_SQL_DATABASE = os.environ.get('AZURE_SQL_DATABASE', 'master')
    AZURE_SQL_DRIVER = os.environ.get('AZURE_SQL_DRIVER', 'ODBC Driver 18 for SQL Server')

    if any((AZURE_SQL_SERVER, AZURE_SQL_USER, AZURE_SQL_PASSWORD)) and not all((AZURE_SQL_SERVER, AZURE_SQL_USER, AZURE_SQL_PASSWORD)):
        raise ValueError('AZURE_SQL_SERVER, AZURE_SQL_USER and AZURE_SQL_PASSWORD must all be set together.')

    PG_HOST = os.environ.get('PG_HOST')
    PG_USER = os.environ.get('PG_USER')
    PG_PASSWORD = os.environ.get('PG_PASSWORD')
    PG_PORT = os.environ.get('PG_PORT', '5432')
    PG_DATABASE = os.environ.get('PG_DATABASE', 'postgres')

    if any((PG_HOST, PG_USER, PG_PASSWORD)) and not all((PG_HOST, PG_USER, PG_PASSWORD)):
        raise ValueError('PG_HOST, PG_USER and PG_PASSWORD must all be set together.')

    DATABASE_URL = None
    if all((AZURE_SQL_SERVER, AZURE_SQL_USER, AZURE_SQL_PASSWORD)):
        # ODBC connection string for Azure SQL Database.
        azure_sql_odbc_connect = quote_plus(
            f"Driver={{{AZURE_SQL_DRIVER}}};"
            f"Server=tcp:{AZURE_SQL_SERVER},{AZURE_SQL_PORT};"
            f"Database={AZURE_SQL_DATABASE};"
            f"Uid={AZURE_SQL_USER};"
            f"Pwd={AZURE_SQL_PASSWORD};"
            f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
        DATABASE_URL = f'mssql+pyodbc:///?odbc_connect={azure_sql_odbc_connect}'
    elif all((PG_HOST, PG_USER, PG_PASSWORD)):
        encoded_user = quote_plus(PG_USER) # pyright: ignore[reportArgumentType, reportCallIssue]
        encoded_password = quote_plus(PG_PASSWORD) # pyright: ignore[reportArgumentType, reportCallIssue]
        DATABASE_URL = (
            f'postgresql://{encoded_user}:{encoded_password}'
            f'@{PG_HOST}:{PG_PORT}/{PG_DATABASE}'
        )

    DB_MODE = 'nosql' if COSMOS_ENDPOINT else 'sql'

    # Only used when DB_MODE == 'sql'.
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
