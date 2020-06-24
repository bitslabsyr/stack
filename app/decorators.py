from functools import wraps
from flask import g, flash, redirect, url_for, request, session
from app.models import DB


# Used to divert users from account-only STACK pages
# Admins are able to access protected pages
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.project is None:
            if g.admin is None:
                flash('You need to login to view this page!')
                return redirect(url_for('index', next=request.path))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.admin is None:
            flash('You need to be an admin to view this page!')
            return redirect(url_for('index', next=request.path))
        return f(*args, **kwargs)

    return decorated_function


# Used to load project info into the session if not there
def load_project(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.project = None
        if 'project_id' in session:
            db = DB()
            resp = db.get_project_detail(session['project_id'])
            if resp['status']:
                g.project = resp
        return f(*args, **kwargs)

    return decorated_function


# Used to load admin info into the session
def load_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.admin = None
        if 'admin_project_id' in session:
            db = DB()
            resp = db.get_project_detail(session['admin_project_id'])
            if resp['status']:
                g.admin = resp
        return f(*args, **kwargs)

    return decorated_function

