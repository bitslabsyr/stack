import json
from bson.objectid import ObjectId
from pymongo import MongoClient
from werkzeug import check_password_hash
from app import app, celery

class DB(object):
    """
    A STACK wrapper to handle recurrant interactions with MongoDB
    """
    def __init__(self):
        # Class instance connection to Mongo
        self.connection = MongoClient()

        # App-wide config file for project info access
        self.config_db = self.connection.config
        self.stack_config = self.config_db.config

    def create(self, project_name, password, hashed_password, description):
        """
        Creates a project account with given name, password, and description
        """
        # Creates base STACK info (if doesn't exist)
        resp = self.stack_config.find_one({'module': 'info'})
        if resp is not None:
            doc = {'module': 'info', 'app': 'STACK', 'version': app.config['VERSION']}
            self.stack_config.insert(doc)

        # Checks to see if project already exists
        resp = self.stack_config.find_one({'project_name': project_name})
        if resp:
            status = 0
            message = 'Project already exists!'

        # If not, creates project
        else:
            configdb = project_name + 'Config'

            project_doc = {
                'project_name': project_name,
                'password': hashed_password,
                'description': description,
                'collectors': [],
                'configdb': configdb
            }
            try:
                self.stack_config.insert(project_doc)
            except:
                status = 0
                message = 'Project creation failed!'
                resp = {'status': status, 'message': message}
                return resp

            # Creates account info for network modules
            # TODO - this should be more dynamic in future versions
            #      - (i.e. Create from a network list)
            resp = self.auth(project_name, password)
            if not resp['status']:
                status = 0
                message = 'Could not load project info.'

                resp = {'status': status, 'message': message}
                return resp
            else:
                project_id = resp['project_id']

                raw_tweets_dir = '/raw_tweets_' + project_id + '/'
                tweet_archive = '/tweet_archive_' + project_id + '/'
                insert_queue = '/insert_queue_' + project_id + '/'

                doc = {
                    'module'            : 'twitter',
                    'collection_script' : 'ThreadedCollector',
                    'processor_script'  : 'preprocess',
                    'insertion_script'  : 'mongoBatchInsert',
                    'processor'         : {'run': 0, 'task_id': None},
                    'inserter'          : {'run': 0, 'task_id': None},
                    'processor_active'  : 0,
                    'inserter_active'   : 0,
                    'raw_tweets_dir'    : raw_tweets_dir,
                    'tweet_archive_dir' : tweet_archive,
                    'insert_queue_dir'  : insert_queue
                }

                try:
                    project_config_db = self.connection[configdb]
                    coll = project_config_db.config
                    coll.insert(doc)

                    status = 1
                    message = 'Project successfully created!'
                except:
                    status = 0
                    message = 'Network module setup failed for project! Try again.'

        resp = {'status': status, 'message': message}
        return resp

    def setup(self, project_list):
        """
        DEPRECATED in v2.0 / Replaced by create()

        Initial app-wide config setup for project_users
        Should pass a list of project_name, password, description params:

            [{
                project_name    : [project-name],
                password        : [project-password],
                description     : [project-description]
            }]
        """
        success_count = 0
        fail_count = 0

        # Creates base STACK info (if doesn't exist)
        resp = self.stack_config.find_one({'module': 'info'})
        if resp is not None:
            doc = {'module': 'info', 'app': 'STACK', 'version': '1.0'}
            self.stack_config.insert(doc)

        created_projects = []
        failed_projects = []

        # Loops through each given project & sets up info
        for item in project_list:
            # Checks to see if project already exists
            resp = self.get_project_list()
            project_names = [project['project_name'] for project in resp['project_list']]
            if item['project_name'] in project_names:
                failed_projects.append(item['project_name'])

                fail_count += 1
                status = 0

            # Creates master config entry for project
            else:
                item['collectors'] = []
                configdb = item['project_name'] + 'Config'
                item['configdb'] = configdb
                self.stack_config.insert(item)

                resp = self.auth(item['project_name'], item['password'])
                print resp
                project_id = resp['project_id']

                raw_tweets_dir = '/raw_tweets_' + project_id + '/'
                tweet_archive = '/tweet_archive_' + project_id + '/'
                insert_queue = '/insert_queue_' + project_id + '/'

                # Also creates network-wide flag modules
                # TODO - this should be more dynamic in future versions
                #      - (i.e. Create from a network list)
                doc = {
                    'module'            : 'twitter',
                    'collection_script' : 'ThreadedCollector',
                    'processor_script'  : 'preprocess',
                    'insertion_script'  : 'mongoBatchInsert',
                    'processor'         : {'run': 0, 'task_id': None},
                    'inserter'          : {'run': 0, 'task_id': None},
                    'processor_active'  : 0,
                    'inserter_active'   : 0,
                    'raw_tweets_dir'    : raw_tweets_dir,
                    'tweet_archive_dir' : tweet_archive,
                    'insert_queue_dir'  : insert_queue
                }

                project_config_db = self.connection[configdb]
                coll = project_config_db.config

                try:
                    coll.insert(doc)
                    resp = self.auth(item['project_name'], item['password'])
                    if resp['status']:
                        created_projects.append({'project_name': item['project_name'], 'project_id': resp['project_id']})

                        success_count += 1
                        status = 1
                except:
                    status = 0

        message = '%d successful project creations. %d duplicates failed.' % (success_count, fail_count)

        resp = {'status': status, 'message': message, 'created_projects': created_projects, 'failed_projects': failed_projects}

        return resp

    def auth(self, project_name, password):
        """
        Project auth function
        """
        auth = self.stack_config.find_one({'project_name': project_name})

        if auth and check_password_hash(auth['password'], password):
            status = 1
            project_id = str(auth['_id'])
            message = 'Success'
        else:
            status = 0
            project_id = None
            message = 'Failed'

        resp = {'status': status, 'message': message, 'project_id': project_id}

        return resp

    def get_project_list(self):
        """
        Generic function that return list of all projects in stack config DB
        """
        projects = self.stack_config.find()

        if projects:
            status = 1
            project_count = self.stack_config.count()
            project_list = []

            for project in projects:
                project['_id'] = str(project['_id'])

                tweets_db = self.connection[project['_id'] + '_' + project['project_name']]
                coll = tweets_db.tweets
                record_count = coll.count()

                project['record_count'] = record_count

                project_list.append(project)

            resp = {'status': status, 'message': 'Success', 'project_count': project_count, 'project_list': project_list}
        else:
            status = 0
            resp = {'status': status, 'message': 'Failed'}

        return resp

    def get_collector_ids(self, project_id):
        """
        When passed a project_id, will return a simple list of collectors and
        their corresponding IDs.
        """
        resp = self.get_project_detail(project_id)

        if not resp['status']:
            resp = {'status': 0, 'message': 'Project does not exist, please try again.'}
            return resp
        else:
            collectors = []
            project_name = resp['project_name']

            if resp['collectors']:
                for collector in resp['collectors']:
                    coll_info = {
                        'collector_name': collector['collector_name'],
                        'collector_id': collector['_id']
                    }
                    collectors.append(coll_info)

            resp = {
                'status': 1,
                'project_name': project_name,
                'collectors': collectors
            }
            return resp

    def get_project_detail(self, project_id):
        """
        When passed a project_id, returns that project's account info along
        with it's list of collectors
        """
        project = self.stack_config.find_one({'_id': ObjectId(project_id)})

        if not project:
            resp = {'status': 0, 'message': 'Failed'}
            return resp
        else:
            configdb = project['configdb']

            resp = {
                'status'                : 1,
                'message'               : 'Success',
                'project_id'            : str(project['_id']),
                'project_name'          : project['project_name'],
                'project_description'   : project['description'],
                'project_config_db'     : configdb
            }

            if project['collectors'] is None:
                resp['collectors'] = None
            else:
                project_config_db = self.connection[configdb]
                coll = project_config_db.config

                collectors = []
                for item in project['collectors']:
                    collector_id = item['collector_id']

                    collector = coll.find_one({'_id': ObjectId(collector_id)})
                    collector['_id'] = str(collector['_id'])

                    collectors.append(collector)

                resp['collectors'] = collectors

            return resp

    def get_collector_detail(self, project_id, collector_id):
        """
        When passed a collector_id, returns that collectors details
        """
        project = self.get_project_detail(project_id)

        if project['status']:
            configdb = project['project_config_db']

            project_config_db = self.connection[configdb]
            coll = project_config_db.config

            collector = coll.find_one({'_id': ObjectId(collector_id)})
            if collector:
                collector['_id'] = str(collector['_id'])
                resp = {'status': 1, 'message': 'Success', 'collector': collector}
            else:
                resp = {'status': 0, 'message': 'Failed'}
        else:
            resp = {'status': 0, 'message': 'Failed'}

        return resp

    def get_network_detail(self, project_id, network):
        """
        Returns details for a network module. To be used by the Controller.
        """
        project = self.get_project_detail(project_id)

        if project['status']:
            configdb = project['project_config_db']

            project_config_db = self.connection[configdb]
            coll = project_config_db.config

            network = coll.find_one({'module': network})
            if network:
                network['_id'] = str(network['_id'])
                resp = {'status': 1, 'message': 'Success', 'network': network}
            else:
                resp = {'status': 0, 'message': 'Failed'}
        else:
            resp = {'status': 0, 'message': 'Failed'}

        return resp

    def set_collector_detail(self, project_id, network, api, collector_name, api_credentials_dict, terms_list, languages=None, location=None):
        """
        Sets up config collection for a project collector
        """
        resp = self.stack_config.find_one({'_id': ObjectId(project_id)})
        project_name = resp['project_name']
        configdb = resp['configdb']

        if terms_list:
            terms = []
            for term in terms_list:
                if api == 'track':
                    term_type = 'term'
                else:
                    term_type = 'handle'
                terms.append({'term': term, 'collect': 1, 'type': term_type, 'id': None})
        else:
            terms = None

        if languages:
            lang_codes = languages
        else:
            lang_codes = None
        if location:
            loc_points = location
        else:
            loc_points = None

        doc = {
            'project_id'    : project_id,
            'project_name'  : project_name,
            'collector_name': collector_name,
            'network'       : network,
            'api'           : api,
            'api_auth'      : api_credentials_dict,
            'terms_list'    : terms,
            'collector'     : {'run': 0, 'collect': 0, 'update': 0},
            'active'        : 0,
            'languages'     : lang_codes,
            'location'      : loc_points,
            'task_id'       : None
        }

        project_config_db = self.connection[configdb]
        coll = project_config_db.config

        # If collector already exists, updates with document, or else creates
        resp = coll.find_one({'collector_name': collector_name})
        if resp is not None:
            collector_id = str(resp['_id'])
            run = resp['collector']['run']
            collect = resp['collector']['collect']

            coll.update({'_id': ObjectId(collector_id)}, {'$set': doc})
            coll.update({'_id': ObjectId(collector_id)}, {'$set': {'collector': {'run': run, 'collect': collect, 'update': 1}}})
            status = 1
            message = 'Success'
        else:
            try:
                coll.insert(doc)

                resp = coll.find_one({'collector_name': collector_name})
                collector_id = str(resp['_id'])

                self.stack_config.update({'_id': ObjectId(project_id)}, {'$push': {'collectors': {'name': collector_name, 'collector_id': collector_id, 'active': 0}}})
                status = 1
                message = 'Success'
            except:
                status = 0
                message = 'Failed'

        resp = {'status': status, 'message': message}

        return resp

    def update_collector_detail(self, project_id, collector_id, **kwargs):
        """
        Updates provided fields for the identified collector; responds w/ a
        failure if fields aren't valid
        """
        resp = self.stack_config.find_one({'_id': ObjectId(project_id)})
        project_name = resp['project_name']
        configdb = resp['configdb']

        project_config_db = self.connection[configdb]
        coll = project_config_db.config

        for key in kwargs.keys():
            if key not in ['collector_name', 'api', 'api_credentials', 'terms_list', 'languages', 'locations']:
                status = 0
                message = 'Invalid collector parameter. Please try again.'
            else:
                if key == 'collector_name':
                    coll.update({'_id': ObjectId(collector_id)},{
                        '$set': {'collector_name': kwargs['collector_name']}
                    })
                    status = 1
                    message = 'Collector name updated.'
                elif key == 'api':
                    coll.update({'_id': ObjectId(collector_id)},{
                        '$set': {'api': kwargs['api']}
                    })
                    status = 1
                    message = 'API updated.'
                elif key == 'languages':
                    coll.update({'_id': ObjectId(collector_id)},{
                        '$set': {'languages': kwargs['languages']}
                    })
                    status = 1
                    message = 'Languages updated.'
                elif key == 'locations':
                    coll.update({'_id': ObjectId(collector_id)},{
                        '$set': {'location': kwargs['locations']}
                    })
                    status = 1
                    message = 'Locations update.'
                elif key == 'api_credentials':
                    coll.update({'_id': ObjectId(collector_id)},{
                        '$set': {'api_auth': kwargs['api_credentials']}
                    })
                    status = 1
                    message = 'API authorization credentials updated.'
                elif key == 'terms_list':
                    collector = coll.find_one({'_id': ObjectId(collector_id)})
                    terms = collector['terms_list']

                    # If terms exist, update on a case by case
                    if terms:
                        for term in kwargs['terms_list']:
                            try:
                                i = next(i for (i, d) in enumerate(terms) if d['term'] == term['term'])
                                terms[i]['term'] = term['term']
                                terms[i]['collect'] = term['collect']
                            except:
                                terms.append(term)

                        coll.update({'_id': ObjectId(collector_id)},{
                            '$set': {'terms_list': terms}
                        })
                    # Otherwise, create new terms list array
                    else:
                        coll.update({'_id': ObjectId(collector_id)},{
                            '$set': {'terms_list': kwargs['terms_list']}
                        })

                    status = 1
                    message = 'Terms list updated.'

        resp = {'status': status, 'message': message}
        return resp

    def set_network_status(self, project_id, network, run=0, process=False, insert=False):
        """
        Start / Stop preprocessor & inserter for a series of network
        collections
        """

        # Finds project db w/ flags
        project_info = self.get_project_detail(project_id)
        configdb = project_info['project_config_db']

        # Makes collection connection
        project_config_db = self.connection[configdb]
        coll = project_config_db.config

        status = 0

        if process:
            try:
                coll.update({'module': network},
                    {'$set': {'processor': {'run': run}}})
                status = 1
                message = 'Success'
            except:
                message = 'Failed'
        if insert:
            try:
                coll.update({'module': network},
                    {'$set': {'inserter': {'run': run}}})
                status = 1
                message = 'Success'
            except:
                message = 'Failed'

        resp = {'status': status, 'message': message}

        return resp

    def set_collector_status(self, project_id, collector_id, collector_status=0):
        """
        Start / Stop an individual collector
        """

        # Finds project db w/ flags
        project_info = self.get_project_detail(project_id)
        configdb = project_info['project_config_db']

        # Makes collection connection
        project_config_db = self.connection[configdb]
        coll = project_config_db.config

        status = 0

        if collector_status:
            try:
                coll.update({'_id': ObjectId(collector_id)},
                    {'$set': {'collector': {'run': 1, 'collect': 1, 'update': 0}}})
                status = 1
                message = 'Success'
            except:
                message = 'Failed'
        else:
            try:
                coll.update({'_id': ObjectId(collector_id)},
                    {'$set': {'collector': {'run': 0, 'collect': 0, 'update': 0}}})
                status = 1
                message = 'Success'
            except:
                message = 'Failed'

        resp = {'status': status, 'message': message}

        return resp

    def check_worker_status(self, project_id, process, collector_id=None, module=None):
        """
        Checks Celery and Mongo to see if a referenced collector/processor/inserter is actively running

        :param project_id:
        :param process: 'collect' | 'process' | 'insert'
        :param collector_id: Only provided if referencing a collector
        :param module: For processor or inserters, which network module
        :return: {'status': 0|1, 'message': 'active'|'inactive'}
        """

        # Default status and message to be returned
        status = 0
        message = 'inactive'

        # Finds project db
        project_info = self.get_project_detail(project_id)
        configdb = project_info['project_config_db']

        # Makes collection connection
        project_config_db = self.connection[configdb]
        coll = project_config_db.config

        # References the collector control document if a collector is referenced
        if process == 'collect':
            collector = coll.find_one({'_id': ObjectId(collector_id)})

            # Grabs the task_id value. If None, nothing is running so it's inactive; otherwise, checks celery
            task_id = collector['task_id']
            if task_id:
                task = celery.AsyncResult(task_id)
                task_status = task.state
                if task_status == 'PENDING':
                    message = 'active'
        else:
            network_mod = coll.find_one({'module': module})

            # References appropriate task_id field for given process
            if process == 'process':
                task_id = network_mod['processor']['task_id']
            else:
                task_id = network_mod['inserter']['task_id']

            # Grabs the task_id value. If None, nothing is running so it's inactive; otherwise, checks celery
            if task_id:
                task = celery.AsyncResult(task_id)
                task_status = task.state
                if task_status == 'PENDING':
                    message = 'active'


        resp = {'status': status, 'message': message}
        return resp
