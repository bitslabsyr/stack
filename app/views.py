from flask import render_template, request, flash, g, session, redirect, url_for
# TODO - hash project account passwords
# from werkzeug import check_password_hash, generate_password_hash

from app import app
from decorators import login_required, load_project
from models import DB
from forms import LoginForm

@app.route('/')
@app.route('/index')
@load_project
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

@app.route('/login', methods=['GET', 'POST'])
@load_project
def login():
    """
    Handles project account authentication
    """
    form = LoginForm(request.form)
    if form.validate_on_submit():
        # On submit, grab name & password
        project_name = form.project_name.data
        password = form.password.data

        # Try login
        db = DB()
        resp = db.auth(project_name, password)
        if resp['status']:
            session['project_id'] = resp['project_id']

            project_detail = db.get_project_detail(session['project_id'])
            project_name = project_detail['project_name']

            flash('Welcome, %s!' % project_name)
            return redirect(url_for('home', project_name=project_name))
        else:
            flash('Invalid login, try again!')
    return render_template('login.html', form=form)

@app.route('/logout')
@load_project
def logout():
    """
    Logs a project account out
    """
    g.project = None
    if 'project_id' in session:
        session.pop('project_id', None)
    return redirect(url_for('index'))

@app.route('/create')
def create():
    """
    Page to create a new project account
    """
    pass

@app.route('/<project_name>/home')
@load_project
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
