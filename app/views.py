from flask import render_template, request, flash, g, session, redirect, url_for
# TODO - hash project account passwords
# from werkzeug import check_password_hash, generate_password_hash

from app import app
from decorators import login_required
from db import DB

"""
TODO - Doesn't work w/out SQLAlchemy collection
@app.before_request()
def before_request():
    # Loads user information before every logged-in connection
    g.project = None
    if 'project_id' in session:
        db = DB()
        resp = db.get_project_detail(session['project_id'])
        if resp['status']:
            g.project = resp
"""

@app.route('/')
@app.route('/index')
def index():
    """
    Loads the STACK homepage w/ list of project accounts
    """
    db = DB()
    project_list = None
    resp = db.get_project_list()
    if resp and resp['project_list']:
        project_list = resp['project_list']
    return render_template('index.html', project_list=project_list)

@app.route('/login')
def login():
    """
    Handles project account authentication
    """
    pass

@app.route('/create')
def create():
    """
    Page to create a new project account
    """
    pass

@app.route('/<project_name>/home')
@login_required
def home(project_name):
    """
    Renders a project account's homepage
    """
    return render_template('home.html', project_detail=g.project)

@app.route('/<project_name>/<collector_id>')
@login_required
def collector(project_name, collector_id):
    """
    Loads the detail / control page for a collector
    """
    pass
