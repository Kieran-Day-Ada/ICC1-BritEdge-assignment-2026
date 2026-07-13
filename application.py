# application.py
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask

from config import Config
from extensions import login_manager

# Load environment variables from a local .env file, if present.
load_dotenv()

# Initialise Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Import the data layer *after* the app/config are set up: it reads
# Config.DB_MODE to decide which backend (SQL or NoSQL) to load, and
# registers Flask-Login's user_loader as a side effect of import.
import data  # noqa: E402  (must come after app.config.from_object)

login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Creates tables (SQL backend) or containers (NoSQL backend) if they don't
# already exist.
data.init_backend(app)

# Import routes after everything above is initialised, to avoid circular imports.
from routes import *  # noqa: E402,F401,F403


@app.context_processor
def inject_now():
    return {'now': datetime.now(timezone.utc)}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
