"""Unified data-access API.

routes.py and application.py only ever import from this package, never
from data.sql_backend or data.nosql_backend directly. Which backend is
actually used is decided once, here, based on Config.DB_MODE - everywhere
else in the app is backend-agnostic.
"""
from config import Config

if Config.DB_MODE == 'nosql':
    from data.nosql_backend import (
        create_job,
        create_user,
        delete_job,
        get_all_jobs,
        get_job,
        get_user_by_email,
        get_user_by_id,
        get_user_by_username,
        init_backend,
        rollback,
        update_job,
    )
else:
    from data.sql_backend import (
        create_job,
        create_user,
        delete_job,
        get_all_jobs,
        get_job,
        get_user_by_email,
        get_user_by_id,
        get_user_by_username,
        init_backend,
        rollback,
        update_job,
    )

from extensions import login_manager


@login_manager.user_loader
def load_user(user_id):
    """Required by Flask-Login to reload a user from the session on each request."""
    return get_user_by_id(user_id)
