from subprocess import call

from flask import render_template, request, flash, g, session, redirect, url_for
from werkzeug import generate_password_hash, check_password_hash

from app import app
from decorators import login_required, load_project, admin_required
from models import DB
from controller import Controller
from forms import LoginForm, CreateForm, NewCollectorForm, ProcessControlForm, SetupForm

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """
    Called on a new install to setup an admin account
    """
    form = SetupForm(request.form)
    if form.validate_on_submit():
        # On submit, grab form information
        project_name = form.project_name.data
        password = form.password.data
        hashed_password = generate_password_hash(password)

        # Create the account
        db = DB()
        resp = db.create(project_name, password, hashed_password, admin=True)
        if resp['status']:
            flash(u'Project successfully created!')
            return redirect(url_for('admin_login'))
        else:
            flash(resp['message'])

    return render_template('setup.html', form=form)

@app.route('/')
@app.route('/index')
@load_project
def index():
    """
    Loads the STACK homepage w/ list of project accounts
    """
    db = DB()
    resp = db.get_project_list()

    project_list = None
    admins = None

    if resp and resp['project_list']:
        project_list = resp['project_list']
        admins = [project for project in project_list if 'admin' in project.keys() and project['admin'] == 1]

    # Renders index of at least one admin account exists, if not calls the new install setup
    if admins:
        return render_template('index.html', project_list=project_list)
    else:
        return redirect(url_for('setup'))

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

@app.route('/admin_login', methods=['GET', 'POST'])
@load_project
def admin_login():
    """
    Login for an admin account
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
            session['admin_project_id'] = resp['project_id']

            admin_detail = db.get_project_detail(session['project_id'])
            admin_id = admin_detail['project_id']

            return redirect(url_for('admin_home', admin_id=admin_id))
        elif not resp['admin']:
            flash(u'Invalid admin account!')
        else:
            flash(resp['message'])
    return render_template('login.html', form=form)

@app.route('/logout')
@load_project
def logout():
    """
    Logs out a project account or admin project account
    """
    g.project = None
    g.admin = None
    if 'project_id' in session:
        session.pop('project_id', None)
    if 'admin_project_id' in session:
        session.pop('admin_project_id', None)
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

@app.route('/admin/<admin_id>')
@admin_required
def admin_home(admin_id):
    """
    Homepage for an admin account
    """
    project_list = []

    db = DB()
    resp = db.get_project_list()

    if resp['status']:
        for project in resp['project_list']:
            if 'admin' in project.keys() and not project['admin']:
                project_list.append(project)

    return render_template('admin_home.html', admin_detail=g.admin, project_list=project_list)

@app.route('/transit')
@admin_required
def transit(project_id):
    """
    Loads specific project into session from admin homepage
    """
    if 'project_id' in session:
        session.pop('project_id', None)

    session['project_id'] = project_id

    db = DB()
    resp = db.get_project_detail(project_id)
    if resp['status']:
        g.project = resp
        return redirect(url_for('home', project_name=g.project['project_name']))
    else:
        flash(u'Invalid project!')
        return redirect(url_for('index'))

@app.route('/<project_name>/home', methods=['GET', 'POST'])
@load_project
@login_required
def home(project_name):
    """
    Renders a project account's homepage
    """
    processor_form = ProcessControlForm(request.form)
    inserter_form = ProcessControlForm(request.form)

    # On submit controls the inserter
    if request.method == 'POST' and inserter_form.validate():
        command = request.form['insert']
        c = Controller(
            process='insert',
            project=g.project,
            network='twitter'
        )
        c.run(command)

    # Loads processor active status
    db = DB()
    resp = db.check_worker_status(g.project['project_id'], 'process', module='twitter')
    processor_active_status = resp['message']

    # Loads inserter active status
    resp = db.check_worker_status(g.project['project_id'], 'insert', module='twitter')
    inserter_active_status = resp['message']

    # Loads count of tweets in the storage DB
    count = db.get_storage_counts(g.project['project_id'], 'twitter')

    return render_template('home.html',
                           project_detail=g.project,
                           processor_active_status=processor_active_status,
                           inserter_active_status=inserter_active_status,
                           count=count,
                           processor_form=processor_form,
                           inserter_form=inserter_form)


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
    form = ProcessControlForm(request.form)

    # Loads collector info for the page
    db = DB()
    resp = db.get_collector_detail(g.project['project_id'], collector_id)
    collector = resp['collector']

    # Loads active status
    resp = db.check_worker_status(g.project['project_id'], 'collect', collector_id=collector_id)
    active_status = resp['message']


    return render_template('collector.html',
        collector=collector,
        active_status=active_status,
        form=form
    )

@app.route('/collector_control/<collector_id>', methods=['POST'])
@load_project
def collector_control(collector_id):
    """
    POST control route for collector forms
    """
    collector_form = ProcessControlForm(request.form)

    # On form submit controls the processor
    if request.method == 'POST' and collector_form.validate():
        command = request.form['control']
        c = Controller(
            process='collect',
            project=g.project,
            collector_id=collector_id
        )
        c.run(command)

    return redirect(url_for('collector',
                            project_name=g.project['project_name'],
                            collector_id=collector_id))

@app.route('/processor_control', methods=['POST'])
@load_project
def processor_control():
    """
    POST control route for processor forms
    """
    processor_form = ProcessControlForm(request.form)

    # On form submit controls the processor
    if request.method == 'POST' and processor_form.validate():
        command = request.form['control']
        c = Controller(
            process='process',
            project=g.project,
            network='twitter'
        )
        c.run(command)

    return redirect(url_for('home', project_name=g.project['project_name']))

@app.route('/inserter_control', methods=['POST'])
@load_project
def inserter_control():
    """
    POST control route for inserter forms
    """
    inserter_form = ProcessControlForm(request.form)

    # On form submit controls the processor
    if request.method == 'POST' and inserter_form.validate():
        command = request.form['control']
        c = Controller(
            process='insert',
            project=g.project,
            network='twitter'
        )
        c.run(command)

    return redirect(url_for('home', project_name=g.project['project_name']))