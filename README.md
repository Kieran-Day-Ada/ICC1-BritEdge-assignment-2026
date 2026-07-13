# ICC1-web-app-job-schedule (BritEdge Job Management)

## Purpose

This repository is used as a basis for the ICC1 module at Ada. BritEdge Job
Management is a Flask web application with user accounts (register/login)
and job entries (create, view, update, delete) - built to explore flexible
Azure hosting and database choices without changing a line of code.

The same codebase runs unmodified on:

- **A virtual machine** (with `uv run` or plain Python)
- **Azure App Service** (with gunicorn)

...and works with any of three database backends, selected purely through
environment variables:

- **Local**: the built-in SQLite database - zero configuration
- **SQL**: a real SQL database, e.g. Azure Database for PostgreSQL
- **NoSQL**: Azure Cosmos DB for NoSQL (documents)

## How the database is chosen

`config.py` picks a backend at startup, based on which environment variables
are set:

1. If `COSMOS_ENDPOINT` is set → **NoSQL** (Azure Cosmos DB for NoSQL, via `data/nosql_backend.py`)
2. Else if `DATABASE_URL` is set → **SQL** (SQLAlchemy, e.g. PostgreSQL, via `data/sql_backend.py`)
3. Else → **Local** SQLite (also via `data/sql_backend.py`, just with a `sqlite:///site.db` connection string)

`routes.py` never touches SQLAlchemy or the Cosmos SDK directly - it only
calls functions like `data.get_all_jobs()` or `data.create_job(...)`, and
`data/__init__.py` wires those up to whichever backend is active. That's
the whole trick that lets one codebase support all three databases.

## Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Running locally

**Recommended: uv**

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone <repo-url>
cd ICC1-web-app-job-schedule
uv run python3 application.py
```

`uv run` creates a `.venv` and installs everything from `uv.lock` automatically
the first time you run it - no separate install step.

**Fallback: pip + venv**

```sh
git clone <repo-url>
cd ICC1-web-app-job-schedule
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 application.py
```

By default (no `.env`, no environment variables set) the app uses SQLite and
is available at `http://127.0.0.1:8080`.

## Choosing a database

Copy the template and edit it:

```sh
cp .env.example .env
```

- Leave `DATABASE_URL` and `COSMOS_ENDPOINT` both commented out → **SQLite** (default)
- Set `DATABASE_URL` → **SQL** (e.g. Azure Database for PostgreSQL)
- Set `COSMOS_ENDPOINT` (and `COSMOS_KEY`) → **NoSQL** (Azure Cosmos DB for NoSQL). This takes priority over `DATABASE_URL` if both happen to be set.

`.env` is loaded automatically via `python-dotenv` and is already excluded
in `.gitignore`, so credentials never get committed.

## Hosting on a virtual machine

Same as the earlier labs in this module: clone the repo onto the VM, set
your chosen database's environment variables (or `.env`), and run:

```sh
uv run python3 application.py
```

The app listens on port 8080 by default (override with the `PORT` environment
variable).

## Hosting on Azure App Service

App Service expects a production WSGI server rather than Flask's built-in
development server, so this repo includes `gunicorn` for that. When you
create the App Service (Linux, Python runtime), set the **Startup Command**
to:

```sh
gunicorn --bind=0.0.0.0 --timeout 600 application:app
```

Then configure your chosen database's environment variables under
**Settings → Environment variables** (formerly Application Settings) -
exactly the same variable names as in `.env.example`. No code changes are
needed to move between a VM and App Service, or between database backends.

## Optional: Docker

```sh
docker build -t britedge-app .
docker run --env-file .env -p 8080:8080 britedge-app
```

This uses the same `gunicorn` startup as App Service, so it's a good way to
test your App Service configuration locally before deploying.

## Project structure

- `application.py` - creates the Flask app, loads config, initialises the active database backend
- `config.py` - reads environment variables and decides which database backend to use
- `extensions.py` - shared Flask extension instances (SQLAlchemy, Flask-Login)
- `routes.py` - all routes; talks only to the `data` package, never to a specific database
- `data/__init__.py` - picks the SQL or NoSQL backend and exposes one common API
- `data/sql_backend.py` - SQLAlchemy models and functions (SQLite and PostgreSQL)
- `data/nosql_backend.py` - Azure Cosmos DB for NoSQL functions (documents)
- `.env.example` - template for your local `.env` file (copy to `.env`, never commit the real one)
- `pyproject.toml` / `uv.lock` - dependency definition and locked versions for `uv`
- `requirements.txt` - plain pip fallback, kept in sync with `pyproject.toml`
- `Dockerfile` - optional container build, matches the App Service gunicorn startup
- `templates/` - HTML templates

## Key features

- User registration and login (Flask-Login, hashed passwords)
- Create, view, update, and delete job entries
- Track job completion status
- Same code, three database backends: SQLite, PostgreSQL, Cosmos DB for NoSQL
- Same code, two hosting targets: VM or Azure App Service

## License

This project is for educational purposes and is provided as-is.
