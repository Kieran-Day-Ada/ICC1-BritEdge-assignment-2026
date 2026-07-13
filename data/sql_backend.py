"""SQL backend: SQLAlchemy models and data-access functions.

Used for both the local SQLite database (default, zero config) and a real
SQL database such as Azure Database for PostgreSQL, selected via the
DATABASE_URL environment variable. See data/__init__.py for backend
selection.
"""
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(db.Model, UserMixin):
    """User model for authentication and job ownership."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    jobs = db.relationship('Job', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Job(db.Model):
    """Job model to store details about various jobs (deliveries, engineering jobs)."""

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Job('{self.title}', '{self.date_posted}', 'Completed: {self.is_completed}')"


def init_backend(app):
    """Wire SQLAlchemy up to the Flask app and create tables if needed."""
    db.init_app(app)
    with app.app_context():
        db.create_all()


# --- Data-access functions (same signatures as the NoSQL backend) --------

def get_all_jobs():
    jobs = Job.query.order_by(Job.date_posted.desc()).all()
    for job in jobs:
        job.formatted_date = job.date_posted.strftime('%Y-%m-%d')
    return jobs


def get_job(job_id):
    # job_id arrives as a string from the URL route; the NoSQL backend needs
    # strings (UUIDs), so routes.py always passes strings here too.
    try:
        return Job.query.get(int(job_id))
    except (TypeError, ValueError):
        return None


def create_job(title, description, user):
    job = Job(title=title, description=description, author=user)
    db.session.add(job)
    db.session.commit()
    return job


def update_job(job, title, description, is_completed):
    job.title = title
    job.description = description
    job.is_completed = is_completed
    db.session.commit()
    return job


def delete_job(job):
    db.session.delete(job)
    db.session.commit()


def rollback():
    db.session.rollback()


def get_user_by_id(user_id):
    return User.query.get(int(user_id))


def get_user_by_username(username):
    return User.query.filter_by(username=username).first()


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def create_user(username, email, password):
    user = User(username=username, email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return user
