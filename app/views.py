import sys

from flask import render_template, request, flash, g, session, redirect, url_for
from werkzeug.security import generate_password_hash

from app import app, celery
from app.decorators import login_required, admin_required, load_project, load_admin
from app.models import DB
from app.forms import LoginForm, CreateForm, NewCollectorForm, ProcessControlForm, SetupForm, UpdateCollectorForm, \
    UpdateCollectorTermsForm
from app.tasks import start_daemon, stop_daemon, restart_daemon, start_workers


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
            flash('Project successfully created!')
            return redirect(url_for('index'))
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
    start_workers()

    db = DB()
    resp = db.get_project_list()

    project_list = None
    admins = None

    if resp and resp['project_list']:
        project_list = resp['project_list']
        admins = [project for project in project_list if 'admin' in list(project.keys()) and project['admin'] == 1]

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
    if g.project is not None:
        return redirect(url_for('home', project_name=g.project['project_name']))

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

            return redirect(url_for('home', project_name=project_name))
        else:
            flash(resp['message'])
    return render_template('login.html', form=form)


@app.route('/admin_login', methods=['GET', 'POST'])
@load_admin
def admin_login():
    """
    Login for an admin account
    """
    if g.admin is not None:
        return redirect(url_for('admin_home', admin_id=g.admin['project_id']))

    form = LoginForm(request.form)
    if form.validate_on_submit():
        # On submit, grab name & password
        project_name = form.project_name.data
        password = form.password.data

        # Try login
        db = DB()
        resp = db.auth(project_name, password)
        if resp['status'] and resp['admin']:
            session['admin_project_id'] = resp['project_id']

            admin_detail = db.get_project_detail(session['admin_project_id'])
            admin_id = admin_detail['project_id']

            return redirect(url_for('admin_home', admin_id=admin_id))
        elif not resp['admin']:
            flash('Invalid admin account!')
        else:
            flash(resp['message'])
    return render_template('admin_login.html', form=form)


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
@load_admin
@admin_required
def create():
    """
    Page to create a new project account
    """
    form = CreateForm(request.form)
    if form.validate_on_submit():
        # On submit, grab form information
        project_name = form.project_name.data
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password)
        description = form.description.data

        # Create the account
        db = DB()
        resp = db.create(project_name, password, hashed_password, description=description, email=email)
        if resp['status']:
            flash('Project successfully created!')
            return redirect(url_for('admin_home', admin_id=g.admin['project_id']))
        else:
            flash(resp['message'])

    return render_template('create.html', form=form)


@app.route('/admin/<admin_id>')
@load_admin
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
            if 'admin' in list(project.keys()) and not project['admin']:
                project_list.append(project)



    return render_template('admin_home.html', admin_detail=g.admin, project_list=project_list)


@app.route('/<project_name>/home/', methods=['GET', 'POST'])
@app.route('/<project_name>/home/<task_id>', methods=['GET', 'POST'])
@load_project
@load_admin
@login_required
def home(project_name, task_id=None):
    """
    Renders a project account's homepage
    """
    # Loads project details if an admin
    if g.admin is not None:
        _aload_project(project_name)

    # Loads in terms # count for panel
    project_detail = g.project
    if project_detail['collectors']:
        project_detail['num_collectors'] = len(project_detail['collectors'])

        for collector in project_detail['collectors']:
            collector['num_terms'] = 0

            if collector['terms_list'] is not None:
                collector['num_terms'] = len(collector['terms_list'])
    else:
        project_detail['num_collectors'] = 0

    return render_template('home.html', project_detail=project_detail)


@app.route('/<project_name>/<network>/', methods=['GET', 'POST'])
@app.route('/<project_name>/<network>/<task_id>', methods=['GET', 'POST'])
@load_project
@load_admin
@login_required
def network_home(project_name, network, task_id=None):
    """
    Renders a project account's homepage
    """
    # Loads project details if an admin
    if g.admin is not None:
        _aload_project(project_name)

    # Grabs collectors for the given network
    if not g.project['collectors']:
        collectors = None
    else:
        collectors = [c for c in g.project['collectors'] if c['network'] == network]
        for collector in collectors:
            collector['num_terms'] = 0

            if collector['terms_list'] is not None:
                collector['num_terms'] = len(collector['terms_list'])

        g.project['num_collectors'] = len(collectors)

    processor_form = ProcessControlForm(request.form)
    inserter_form = ProcessControlForm(request.form)

    # Loads processor active status
    db = DB()
    resp = db.check_process_status(g.project['project_id'], 'process', module=network)
    processor_active_status = resp['message']

    # Loads inserter active status
    resp = db.check_process_status(g.project['project_id'], 'insert', module=network)
    inserter_active_status = resp['message']

    # Loads count of tweets in the storage DB
    count = db.get_storage_counts(g.project['project_id'], network)

    # If a start/stop/restart is in progress, display the status
    task_status = None
    if task_id:
        resp = celery.AsyncResult(task_id)
        if resp.state == 'PENDING':
            processor_task_status = 'Processor/Inserter start/shutdown still in progress...'
        else:
            processor_task_status = 'Processor/Inserter start/shutdown completed.'

    return render_template('network_home.html',
                           network=network,
                           collectors=collectors,
                           project_detail=g.project,
                           processor_active_status=processor_active_status,
                           inserter_active_status=inserter_active_status,
                           task_status=task_status,
                           count=count,
                           processor_form=processor_form,
                           inserter_form=inserter_form)


@app.route('/new_collector', methods=['GET', 'POST'])
@load_project
@load_admin
@login_required
def new_collector():
    """
    Route for a project account to create a new STACK collector
    """
    # Redirects an admin back to the homepage b/c nothing is loaded into the session yet
    if g.project is None:
        flash('Please navigate to the New Collector page from your homepage panel.')
        return redirect(url_for('index'))

    form = NewCollectorForm(request.form)

    # On submit, get info which varies by network
    if request.method == 'POST' and form.validate():
        collector_name = form.collector_name.data
        network = form.network.data

        api = None
        languages = None
        locations = None
        start_date = None
        end_date = None

        # TODO - historical for Twitter as well
        collection_type = 'realtime'

        if network == 'twitter':
            api = form.api.data
            oauth_dict = {
                'consumer_key': form.consumer_key.data,
                'consumer_secret': form.consumer_secret.data,
                'access_token': form.access_token.data,
                'access_token_secret': form.access_token_secret.data
            }

            # Optional form values are assigned 'None' if not filled out
            languages = form.languages.data
            if not languages or languages == '':
                languages = None
            else:
                languages = languages.split('\r\n')

            locations = form.locations.data
            if not locations or languages == '':
                locations = None
            else:
                locations = locations.replace('\r\n', ',').split(',')
                if len(locations) % 4 is not 0:
                    flash('Location coordinates should be entered in pairs of 4. Please try again')
                    return redirect(url_for('new_collector'))

            terms = form.twitter_terms.data
            if not terms or terms == '':
                terms = None
            else:
                terms = terms.split('\r\n')

        elif network == 'facebook':
            collection_type = form.collection_type.data
            oauth_dict = {
                'client_id': form.client_id.data,
                'client_secret': form.client_secret.data
            }

            # Optional start & end date params
            start_date = form.start_date.data
            if not start_date or start_date == '':
                start_date = None
            else:
                start_date = str(start_date)

            end_date = form.end_date.data
            if not end_date or end_date == '':
                end_date = None
            else:
                end_date = str(end_date)

            terms = form.facebook_terms.data
            terms = terms.split('\r\n')

        # Create collector w/ form data
        db = DB()
        resp = db.set_collector_detail(
            g.project['project_id'],
            collector_name,
            network,
            collection_type,
            oauth_dict,
            terms,
            api=api,
            languages=languages,
            location=locations,
            start_date=start_date,
            end_date=end_date
        )

        # If successful, redirect to collector page
        if resp['status']:
            project_config_db = db.connection[g.project['project_config_db']]
            coll = project_config_db.config
            try:
                collector = coll.find_one({'collector_name': collector_name})
                collector_id = str(collector['_id'])
                network = str(collector['network'])

                return redirect(url_for(
                    'collector',
                    project_name=g.project['project_name'],
                    network=network,
                    collector_id=collector_id
                ))
            except:
                flash('Collector created, but cannot redirect to collector page!')
                return redirect(url_for('home', project_name=g.project['project_name']))
        else:
            flash(resp['message'])

    return render_template('new_collector.html', form=form)


@app.route('/<collector_id>/update_collector', methods=['GET', 'POST'])
@load_project
@load_admin
@login_required
def update_collector(collector_id):
    """
    Used to update a collector details form the front-end

    TODO - Terms & start / end dates
    """
    db = DB()
    resp = db.get_collector_detail(g.project['project_id'], collector_id)
    collector = resp['collector']

    # First, populate the main form w/ info
    form_params = {
        'collector_name': collector['collector_name']
    }

    if collector['network'] == 'twitter':
        form_params['api'] = collector['api']
        form_params['consumer_key'] = collector['api_auth']['consumer_key']
        form_params['consumer_secret'] = collector['api_auth']['consumer_secret']
        form_params['access_token'] = collector['api_auth']['access_token']
        form_params['access_token_secret'] = collector['api_auth']['access_token_secret']

        if collector['languages']:
            languages = '\r\n'.join(collector['languages'])
            form_params['languages'] = languages
        if collector['location']:
            loc_string = ''
            r = 1
            c = 1
            for loc in collector['location']:
                if c == 1 and r > 1:
                    loc_string = loc_string + '\r\n' + loc + ','
                else:
                    if c != 4:
                        loc_string = loc_string + loc + ','
                    else:
                        loc_string = loc_string + loc

                if c == 4:
                    c = 1
                    r += 1
                else:
                    c += 1

            form_params['locations'] = loc_string

    elif collector['network'] == 'facebook':
        form_params['collection_type'] = collector['collection_type']
        form_params['client_id'] = collector['api_auth']['client_id']
        form_params['client_secret'] = collector['api_auth']['client_secret']

        # TODO - start & end dates

    form = UpdateCollectorForm(**form_params)

    # Next, create a form for each term -- if no terms, one form is needed & it's empty
    terms = collector['terms_list']
    terms_forms = []
    if terms:
        for term in terms:
            # Load form & set defaults
            form_params = {
                'term': term['term'],
                'collect': int(term['collect']),
            }
            tform = UpdateCollectorTermsForm(prefx=term['term'], **form_params)
            terms_forms.append(tform)

    # Finally, update on submission
    if request.method == 'POST':
        # Loads in the data from the form & sets initial param dict
        form_data = request.get_json()
        params = {}

        if form_data['collector_name'] != collector['collector_name']:
            params['collector_name'] = form_data['collector_name']

        # Twitter data
        if collector['network'] == 'twitter':
            if form_data['api'] != collector['api']:
                params['api'] = form_data['api']
            # If one auth param is updated, assume all are
            if form_data['consumer_key'] != collector['api_auth']['consumer_key']:
                params['api_auth'] = {
                    'consumer_key': form_data['consumer_key'],
                    'consumer_secret': form_data['consumer_secret'],
                    'access_token': form_data['access_token'],
                    'access_token_secret': form_data['access_token_secret']
                }

            languages = form_data['languages']
            if not languages or languages == '':
                languages = None
            else:
                languages = languages.split('\r\n')

            if languages != collector['languages']:
                params['languages'] = languages

            locations = form_data['locations']
            if not locations or languages == '':
                locations = None
            else:
                locations = locations.replace('\r\n', ',').split(',')
                if len(locations) % 4 is not 0:
                    flash('Location coordinates should be entered in pairs of 4. Please try again')
                    return redirect(url_for('update_collector', collector_id=collector_id))

            if locations != collector['location']:
                params['location'] = locations

        # Facebook Data
        elif collector['network'] == 'facebook':
            if form_data['collection_type'] != collector['collection_type']:
                params['collection_type'] = form.collection_type.data
            if form_data['client_id'] != collector['api_auth']['client_id']:
                params['api_auth'] = {
                    'client_id': form_data['client_id'],
                    'client_secret': form_data['client_secret']
                }

            # TODO - start and end dates

        # Final terms dict
        params['terms_list'] = []

        # Term type value
        if collector['network'] == 'twitter':
            if collector['api'] == 'follow':
                term_type = 'handle'
            else:
                term_type = 'term'
        else:
            term_type = 'page'

        # New terms (if any)
        terms = form_data['new_terms']
        if terms and terms != '':
            terms = terms.split('\r\n')
            for t in terms:
                params['terms_list'].append({
                    'term': t,
                    'collect': 1,
                    'type': term_type,
                    'id': None
                })

        # Updated terms (if any)
        current_terms = form_data['terms']
        while current_terms:
            params['terms_list'].append({
                'term': current_terms.pop(0),
                'collect': int(current_terms.pop(0)),
                'type': term_type,
                'id': None
            })

        # Now, try updating
        resp = db.update_collector_detail(g.project['project_id'], collector_id, **params)
        if resp['status']:
            flash('Collector updated successfully!')
            return redirect(url_for('collector', project_name=g.project['project_name'], network=collector['network'],
                                    collector_id=collector_id))
        else:
            flash(resp['message'])
            return redirect(url_for('update_collector', collector_id=collector_id))

    return render_template('update_collector.html', collector=collector, form=form, terms_forms=terms_forms)


@app.route('/<project_name>/<network>/<collector_id>/', methods=['GET', 'POST'])
@app.route('/<project_name>/<network>/<collector_id>/<task_id>', methods=['GET', 'POST'])
@load_project
@load_admin
@login_required
def collector(project_name, network, collector_id, task_id=None):
    """
    Loads the detail / control page for a collector
    """
    # Redirects an admin back to the homepage b/c nothing is loaded into the session yet
    if g.project is None:
        flash('Please navigate to the New Collector page from your homepage panel.')
        return redirect(url_for('index'))

    form = ProcessControlForm(request.form)

    # Loads collector info for the page
    db = DB()
    resp = db.get_collector_detail(g.project['project_id'], collector_id)
    collector = resp['collector']

    # Loads active status
    resp = db.check_process_status(g.project['project_id'], 'collect', collector_id=collector_id)
    active_status = resp['message']

    # If a start/stop/restart is in progress, display the status
    task_status = None
    if task_id:
        resp = celery.AsyncResult(task_id)
        if resp.state == 'PENDING':
            task_status = 'Collector start/shutdown still in progress...'
        else:
            task_status = 'Collector start/shutdown completed.'

    return render_template(
        'collector.html',
        collector=collector,
        active_status=active_status,
        form=form,
        task_status=task_status
    )


@app.route('/collector_control/<collector_id>', methods=['POST'])
@load_project
@load_admin
def collector_control(collector_id):
    """
    POST control route for collector forms
    """
    collector_form = ProcessControlForm(request.form)
    task = None

    # On form submit controls the processor
    if request.method == 'POST' and collector_form.validate():
        command = request.form['control'].lower()

        task_args = {
            'process': 'collect',
            'project': g.project,
            'collector_id': collector_id
        }

        db = DB()
        collector = db.get_collector_detail(g.project['project_id'], collector_id)
        network = collector['collector']['network']

        if command == 'start':
            task = start_daemon.apply_async(kwargs=task_args, queue='stack-start')
        elif command == 'stop':
            task = stop_daemon.apply_async(kwargs=task_args, queue='stack-stop')
        elif command == 'restart':
            task = restart_daemon.apply_async(kwargs=task_args, queue='stack-start')

        return redirect(url_for('collector',
                                project_name=g.project['project_name'],
                                network=network,
                                collector_id=collector_id,
                                task_id=task.task_id))


@app.route('/processor_control/<network>', methods=['POST'])
@load_project
@load_admin
def processor_control(network):
    """
    POST control route for processor forms
    """
    processor_form = ProcessControlForm(request.form)
    task = None

    # On form submit controls the processor
    if request.method == 'POST' and processor_form.validate():
        command = request.form['control'].lower()

        task_args = {
            'process': 'process',
            'project': g.project,
            'network': network
        }

        if command == 'start':
            task = start_daemon.apply_async(kwargs=task_args, queue='stack-start')
        elif command == 'stop':
            task = stop_daemon.apply_async(kwargs=task_args, queue='stack-stop')
        elif command == 'restart':
            task = restart_daemon.apply_async(kwargs=task_args, queue='stack-start')

    return redirect(url_for('network_home',
                            project_name=g.project['project_name'],
                            network=network,
                            processor_task_id=task.task_id))


@app.route('/inserter_control/<network>', methods=['POST'])
@load_project
@load_admin
def inserter_control(network):
    """
    POST control route for inserter forms
    """
    inserter_form = ProcessControlForm(request.form)
    task = None

    # On form submit controls the processor
    if request.method == 'POST' and inserter_form.validate():
        command = request.form['control'].lower()

        task_args = {
            'process': 'insert',
            'project': g.project,
            'network': network
        }

        if command == 'start':
            task = start_daemon.apply_async(kwargs=task_args, queue='stack-start')
        elif command == 'stop':
            task = stop_daemon.apply_async(kwargs=task_args, queue='stack-stop')
        elif command == 'restart':
            task = restart_daemon.apply_async(kwargs=task_args, queue='stack-start')

    return redirect(url_for('network_home',
                            project_name=g.project['project_name'],
                            network=network,
                            inserter_task_id=task.task_id))


def _aload_project(project_name):
    """
    Utility method to load an admin project detail if an admin is viewing their control page
    """
    db = DB()
    resp = db.stack_config.find_one({'project_name': project_name})
    g.project = db.get_project_detail(str(resp['_id']))

    session['project_id'] = str(resp['_id'])
