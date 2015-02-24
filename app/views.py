from subprocess import call

from flask import render_template, request, flash, g, session, redirect, url_for
from werkzeug import generate_password_hash, check_password_hash

from app import app
from decorators import login_required, load_project
from models import DB
from controller import Controller
from forms import LoginForm, CreateForm, NewCollectorForm, CollectorControlForm

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
            flash(resp['message'])
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

@app.route('/create', methods=['GET', 'POST'])
@load_project
def create():
    """
    Page to create a new project account
    """
    form = CreateForm(request.form)
    if form.validate_on_submit():
        # On submit, grab form information
        project_name = form.project_name.data
        password = form.password.data
        hashed_password = generate_password_hash(password)
        description = form.description.data

        # Create the account
        db = DB()
        resp = db.create(project_name, password, hashed_password, description)
        if resp['status']:
            flash(u'Project successfully created!')
            return redirect(url_for('login'))
        else:
            flash(resp['message'])
    return render_template('create.html', form=form)

@app.route('/<project_name>/home')
@load_project
@login_required
def home(project_name):
    """
    Renders a project account's homepage
    """
    return render_template('home.html', project_detail=g.project)

@app.route('/new_collector', methods=['GET', 'POST'])
@load_project
@login_required
def new_collector():
    """
    Route for a project account to create a new STACK collector
    """
    form = NewCollectorForm(request.form)
    if form.validate_on_submit():
        # On submit, grab form info
        collector_name = form.collector_name.data
        network = form.network.data
        api = form.api.data

        oauth_dict = {
            'consumer_key': form.consumer_key.data,
            'consumer_secret': form.consumer_secret.data,
            'access_token': form.access_token.data,
            'access_token_secret': form.access_token_secret.data
        }

        # Optional form values are assigned 'None' if not filled out
        languages = form.languages.data
        if not languages:
            languages = None

        locations = form.locations.data
        if not locations:
            locations = None

        terms = form.terms.data
        if not terms:
            terms = None
        # TODO - need to coerce term format better
        else:
            terms = terms.split('\r\n')

        # Create collector w/ form data
        db = DB()
        resp = db.set_collector_detail(
            g.project['project_id'],
            network,
            api,
            collector_name,
            oauth_dict,
            terms,
            languages=languages,
            location=locations
        )
        # If successful, redirect to collector page
        if resp['status']:
            project_config_db = db.connection[g.project['project_config_db']]
            coll = project_config_db.config
            try:
                collector = coll.find_one({'collector_name': collector_name})
                collector_id = str(collector['_id'])
                return redirect(url_for('collector',
                    project_name=g.project['project_name'],
                    collector_id=collector_id
                ))
            except:
                flash('Collector created, but cannot redirect to collector page!')
                return redirect(url_for('home', project_name=g.project['project_name']))
        else:
            flash(resp['message'])

    return render_template('new_collector.html', form=form)

@app.route('/<project_name>/<collector_id>', methods=['GET', 'POST'])
@load_project
@login_required
def collector(project_name, collector_id):
    """
    Loads the detail / control page for a collector
    """
    form = CollectorControlForm(request.form)

    # Loads collector info for the page
    db = DB()
    resp = db.get_collector_detail(g.project['project_id'], collector_id)
    collector = resp['collector']

    # On form submit controls the collector
    if form.validate_on_submit():
        command = request.form['control']
        c = Controller(
            process='collect',
            project=g.project,
            collector_id=collector_id
        )
        c.run(command)

    return render_template('collector.html',
        collector=collector,
        form=form
    )
