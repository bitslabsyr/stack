from functools import wraps
from flask import g, flash, redirect, url_for, request

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.project is None:
            flash(u'You need to login to view this page!')
            redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function
