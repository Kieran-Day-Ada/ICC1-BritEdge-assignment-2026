# routes.py
from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

import data
from application import app


@app.route("/")
@app.route("/home")
def home():
    """Home page route. Displays all jobs."""
    jobs = data.get_all_jobs()
    return render_template('index.html', jobs=jobs)


@app.route("/register", methods=['GET', 'POST'])
def register():
    """User registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password or not confirm_password:
            flash('All fields are required!', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        if data.get_user_by_username(username):
            flash('Username already taken. Please choose a different one.', 'danger')
            return render_template('register.html')
        if data.get_user_by_email(email):
            flash('Email already registered. Please use a different email or login.', 'danger')
            return render_template('register.html')

        try:
            data.create_user(username, email, password)
            flash('Your account has been created! You are now able to log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            data.rollback()
            flash(f'An error occurred during registration: {e}', 'danger')
            print(f"Error during registration: {e}")
            return render_template('register.html')

    return render_template('register.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = data.get_user_by_email(email)

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')

    return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
    """Log the current user out."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route("/job/new", methods=['GET', 'POST'])
@login_required
def new_job():
    """Create a new job."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        if not title or not description:
            flash('Title and Description are required for the job.', 'danger')
            return render_template('create_job.html', title='New Job')

        try:
            data.create_job(title, description, current_user)
            flash('Your job has been created!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            data.rollback()
            flash(f'An error occurred while creating the job: {e}', 'danger')
            print(f"Error creating job: {e}")
            return render_template('create_job.html', title='New Job')

    return render_template('create_job.html', title='New Job')


@app.route("/job/<job_id>")
def job_detail(job_id):
    """View details of a specific job."""
    job = data.get_job(job_id)
    if job is None:
        abort(404)
    return render_template('job_detail.html', title=job.title, job=job)


@app.route("/job/<job_id>/update", methods=['GET', 'POST'])
@login_required
def update_job(job_id):
    """Update an existing job. Only the author may update it."""
    job = data.get_job(job_id)
    if job is None:
        abort(404)
    if job.user_id != current_user.id:
        flash('You are not authorised to update this job.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        is_completed = True if request.form.get('is_completed') == 'on' else False

        if not title or not description:
            flash('Title and Description are required for the job.', 'danger')
            return render_template('create_job.html', title='Update Job', job=job)

        try:
            job = data.update_job(job, title, description, is_completed)
            flash('Your job has been updated!', 'success')
            return redirect(url_for('job_detail', job_id=job.id))
        except Exception as e:
            data.rollback()
            flash(f'An error occurred while updating the job: {e}', 'danger')
            print(f"Error updating job: {e}")
            return render_template('create_job.html', title='Update Job', job=job)

    return render_template('create_job.html', title='Update Job', job=job)


@app.route("/job/<job_id>/delete", methods=['POST'])
@login_required
def delete_job(job_id):
    """Delete an existing job. Only the author may delete it."""
    job = data.get_job(job_id)
    if job is None:
        abort(404)
    if job.user_id != current_user.id:
        flash('You are not authorised to delete this job.', 'danger')
        return redirect(url_for('home'))

    try:
        data.delete_job(job)
        flash('Your job has been deleted!', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        data.rollback()
        flash(f'An error occurred while deleting the job: {e}', 'danger')
        print(f"Error deleting job: {e}")
        return redirect(url_for('job_detail', job_id=job.id))
