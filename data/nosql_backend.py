"""NoSQL backend: Azure Cosmos DB for NoSQL (document) data-access functions.

Selected automatically when COSMOS_ENDPOINT is set - see data/__init__.py.
Users and Jobs are stored as documents in two Cosmos containers, each
partitioned on /id (simplest partitioning scheme, fine for a teaching app).
Unlike the SQL backend there are no foreign keys or joins: a Job document
stores its author's user_id, and get_all_jobs() looks the author up and
attaches it as a plain attribute so templates can still use job.author.username.
"""
import os
import uuid
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

_client = None
_users = None
_jobs = None


class NoSQLUser(UserMixin):
    """Lightweight stand-in for the SQL User model, backed by a Cosmos document."""

    def __init__(self, doc):
        self.id = doc['id']
        self.username = doc['username']
        self.email = doc['email']
        self.password_hash = doc['password_hash']

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class NoSQLJob:
    """Lightweight stand-in for the SQL Job model, backed by a Cosmos document."""

    def __init__(self, doc, author=None):
        self.id = doc['id']
        self.title = doc['title']
        self.description = doc['description']
        self.date_posted = datetime.fromisoformat(doc['date_posted'])
        self.is_completed = doc.get('is_completed', False)
        self.user_id = doc['user_id']
        self.author = author
        self.formatted_date = self.date_posted.strftime('%Y-%m-%d')

    def __repr__(self):
        return f"Job('{self.title}', '{self.date_posted}', 'Completed: {self.is_completed}')"


def init_backend(app):
    """Create the Cosmos client, database, and containers used by this backend."""
    global _client, _users, _jobs
    from azure.cosmos import CosmosClient, PartitionKey

    endpoint = os.environ.get('COSMOS_ENDPOINT')
    key = os.environ.get('COSMOS_KEY')
    db_name = os.environ.get('COSMOS_DB', 'BritEdgeDB')

    _client = CosmosClient(endpoint, key)
    database = _client.create_database_if_not_exists(id=db_name)
    _users = database.create_container_if_not_exists(
        id=os.environ.get('COSMOS_USERS_CONTAINER', 'users'),
        partition_key=PartitionKey(path='/id'),
    )
    _jobs = database.create_container_if_not_exists(
        id=os.environ.get('COSMOS_JOBS_CONTAINER', 'jobs'),
        partition_key=PartitionKey(path='/id'),
    )


def rollback():
    # No transaction/session concept for Cosmos in this simple app - nothing to do.
    pass


# --- Jobs ------------------------------------------------------------------

def get_all_jobs():
    items = list(_jobs.read_all_items())
    user_cache = {}
    jobs = []
    for doc in items:
        author = user_cache.get(doc['user_id'])
        if author is None:
            author = get_user_by_id(doc['user_id'])
            user_cache[doc['user_id']] = author
        jobs.append(NoSQLJob(doc, author=author))
    jobs.sort(key=lambda j: j.date_posted, reverse=True)
    return jobs


def get_job(job_id):
    from azure.cosmos.exceptions import CosmosResourceNotFoundError
    try:
        doc = _jobs.read_item(item=str(job_id), partition_key=str(job_id))
    except CosmosResourceNotFoundError:
        return None
    return NoSQLJob(doc, author=get_user_by_id(doc['user_id']))


def create_job(title, description, user):
    doc = {
        'id': str(uuid.uuid4()),
        'title': title,
        'description': description,
        'date_posted': datetime.now(timezone.utc).isoformat(),
        'is_completed': False,
        'user_id': user.id,
    }
    _jobs.upsert_item(doc)
    return NoSQLJob(doc, author=user)


def update_job(job, title, description, is_completed):
    doc = _jobs.read_item(item=str(job.id), partition_key=str(job.id))
    doc['title'] = title
    doc['description'] = description
    doc['is_completed'] = is_completed
    _jobs.upsert_item(doc)
    return NoSQLJob(doc, author=job.author)


def delete_job(job):
    _jobs.delete_item(item=str(job.id), partition_key=str(job.id))


# --- Users -------------------------------------------------------------

def get_user_by_id(user_id):
    from azure.cosmos.exceptions import CosmosResourceNotFoundError
    try:
        doc = _users.read_item(item=str(user_id), partition_key=str(user_id))
    except CosmosResourceNotFoundError:
        return None
    return NoSQLUser(doc)


def _query_one_user(query, param_name, value):
    params = [{'name': param_name, 'value': value}]
    items = list(_users.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    return NoSQLUser(items[0]) if items else None


def get_user_by_username(username):
    return _query_one_user('SELECT * FROM c WHERE c.username = @username', '@username', username)


def get_user_by_email(email):
    return _query_one_user('SELECT * FROM c WHERE c.email = @email', '@email', email)


def create_user(username, email, password):
    doc = {
        'id': str(uuid.uuid4()),
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
    }
    _users.upsert_item(doc)
    return NoSQLUser(doc)
