from functools import wraps
from flask import g, flash, redirect, url_for, request, session
from models import DB

# Used to divert users from account-only STACK pages
# Admins are able to access all login_required pages
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.admin is not None:
            pass
        elif g.project is None:
            flash(u'You need to login to view this page!')
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
            # First, make sure this isn't an admin, we don't want to load that info
            if resp['status'] and resp['admin']:
                pass
            elif resp['status']:
                g.project = resp
        return f(*args, **kwargs)
    return decorated_function

# Used on admin pages to load the admin into session storage
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.project = None
        if 'admin_project_id' in session:
            db = DB()
            resp = db.get_project_detail(session['admin_project_id'])
            if resp['status'] and resp['admin']:
                g.admin = resp
            elif resp['status'] and not resp['admin']:
                flash(u'You need to be an admin to view this page!')
                return redirect(url_for('index', next=request.path))
        return f(*args, **kwargs)
    return decorated_function