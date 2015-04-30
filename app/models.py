import json
from datetime import datetime
from bson.objectid import ObjectId
from pymongo import MongoClient
from werkzeug import check_password_hash
from app import app

class DB(object):
    """
    A STACK wrapper to handle recurring interactions with MongoDB
    """
    def __init__(self):
        # Class instance connection to Mongo
        self.connection = MongoClient()

        # App-wide config file for project info access
        self.config_db = self.connection.config
        self.stack_config = self.config_db.config

    def create(self, project_name, password, hashed_password, description=None, admin=False):
        """
        Creates a project account with given name, password, and description
        """
        # Creates base STACK info (if doesn't exist)
        resp = self.stack_config.find_one({'module': 'info'})
        if resp is not None:
            doc = {'module': 'info', 'app': 'STACK', 'version': app.config['VERSION']}
            self.stack_config.insert(doc)

        status = 0
        message = None

        # Checks to see if project already exists
        resp = self.stack_config.find_one({'project_name': project_name})
        if resp:
            status = 0
            message = 'The project name %s is already taken. Please try again!' % project_name

        # If not, creates project
        else:
            # Creates an admin project login if creating an admin account
            if admin:
                project_doc = {
                    'project_name': project_name,
                    'password': hashed_password,
                    'description': description,
                    'configdb': None,
                    'collectors': None,
                    'admin': 1
                }
            # Creates a regular project account otherwise
            else:
                configdb = project_name + 'Config'

                project_doc = {
                    'project_name': project_name,
                    'password': hashed_password,
                    'description': description,
                    'collectors': [],
                    'configdb': configdb,
                    'admin': 0
                }

            # Try to insert project account doc; returns a failure if Mongo insert doesn't work
            try:
                self.stack_config.insert(project_doc)

                if admin:
                    status = 1
                    message = 'Admin account created successfully!'

            except:
                status = 0
                message = 'Project creation failed!'
                resp = self._generate_response(status, message)
                return resp

            # Creates account info for network modules if not an admin account
            if admin is False:
                resp = self.auth(project_name, password)
                if not resp['status']:
                    status = 0
                    message = 'Could not load new project info. Setup failed.'

                    resp = {'status': status, 'message': message}
                    return resp
                else:
                    # Creates a doc for each network
                    networks = app.config['NETWORKS']
                    for network in networks:
                        project_config_db = self.connection[configdb]
                        coll = project_config_db.config

                        doc = {
                            'module'            : network,
                            'processor'         : {'run': 0, 'restart': 0},
                            'inserter'          : {'run': 0, 'restart': 0},
                            'processor_active'  : 0,
                            'inserter_active'   : 0
                        }

                        try:
                            coll.insert(doc)
                            status = 1
                            message = 'Project account successfully created!'
                        except Exception as e:
                            status = 0
                            message = 'Network module setup failed for project! Try again.'

        resp = self._generate_response(status, message)
        return resp

    def auth(self, project_name, password):
        """
        Project auth function
        """
        auth = self.stack_config.find_one({'project_name': project_name})

        if auth and check_password_hash(auth['password'], password):
            status = 1
            project_id = str(auth['_id'])
            admin = auth['admin']
            message = 'Success'
        else:
            status = 0
            project_id = None
            admin = None
            message = 'Failed'

        resp = {'status': status, 'message': message, 'project_id': project_id, 'admin': admin}

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
                'project_config_db'     : configdb,
                'admin'                 : project['admin']
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

    def set_collector_detail(self, project_id, collector_name, network, collection_type, api_credentials_dict,
                             terms_list, api=None, languages=None, location=None, start_date=None, end_date=None):
        """
        Sets up config collection for a project collector
        """
        resp = self.stack_config.find_one({'_id': ObjectId(project_id)})
        project_name = resp['project_name']
        configdb = resp['configdb']

        if terms_list:
            terms = []
            for term in terms_list:
                # Sets term type based on network and api filter
                term_type = 'term'
                if network == 'twitter' and api == 'follow':
                    term_type = 'handle'
                elif network == 'twitter' and api == 'track':
                    term_type = 'term'
                elif network == 'facebook':
                    term_type = 'page'

                # Sets first history tracker
                history = {
                    'start_date': datetime.date(datetime.now()).isoformat(),
                    'end_date': 'current'
                }

                # Adds term to full list
                terms.append({'term': term, 'collect': 1, 'type': term_type, 'id': None, 'history': [history]})
        else:
            terms = None

        # Sets additional parameters - right now only used for Facebook
        params = {}
        if network == 'facebook':
            params['last'] = None
            # Set since param
            if start_date:
                params['since'] = start_date
            else:
                params['since'] = None
            # Set until param
            if end_date:
                params['until'] = end_date
            else:
                params['until'] = None


        # Creates full Mongo doc
        doc = {
            'project_id'        : project_id,
            'project_name'      : project_name,
            'collector_name'    : collector_name,
            'network'           : network,
            'collection_type'   : collection_type,
            'api'               : api,
            'api_auth'          : api_credentials_dict,
            'terms_list'        : terms,
            'params'            : params,
            'collector'         : {'run': 0, 'collect': 0, 'update': 0},
            'active'            : 0,
            'languages'         : languages,
            'location'          : location,
            'rate_limits'       : [],
            'error_codes'       : []
        }

        project_config_db = self.connection[configdb]
        coll = project_config_db.config

        # If collector already exists, warns the user
        resp = coll.find_one({'collector_name': collector_name})
        if resp is not None:
            status = 0
            message = 'Collector already exists. Please try again or update this collector!'
        else:
            try:
                coll.insert(doc)

                resp = coll.find_one({'collector_name': collector_name})
                collector_id = str(resp['_id'])

                self.stack_config.update({'_id': ObjectId(project_id)}, {'$push': {'collectors': {
                    'name': collector_name, 'collector_id': collector_id, 'active': 0}}})
                status = 1
                message = 'Collector created successfully!'
            except:
                status = 0
                message = 'Collector creation failed!'

        resp = self._generate_response(status, message)
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
        message = None

        if process:
            try:
                coll.update({'module': network},
                    {'$set': {'processor.run': run}})
                status = 1
                message = 'Success'
            except:
                message = 'Failed'
        if insert:
            try:
                coll.update({'module': network},
                    {'$set': {'inserter.run': run}})
                status = 1
                message = 'Success'
            except:
                message = 'Failed'

        resp = self._generate_response(status, message)
        return resp

    def set_collector_status(self, project_id, collector_id, collector_status=0, update_status=0):
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
            except Exception as e:
                message = e
        elif update_status:
            try:
                coll.update({'_id': ObjectId(collector_id)},
                    {'$set': {'collector': {'run': 1, 'collect': 1, 'update': 1}}})
                status = 1
                message = 'Success'
            except Exception as e:
                message = e
        else:
            try:
                coll.update({'_id': ObjectId(collector_id)},
                    {'$set': {'collector': {'run': 0, 'collect': 0, 'update': 0}}})
                status = 1
                message = 'Success'
            except Exception as e:
                message = e

        resp = {'status': status, 'message': message}

        return resp

    def check_process_status(self, project_id, process, collector_id=None, module=None):
        """
        Checks Mongo to see if a referenced collector/processor/inserter is actively running

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

        # Grabs active flag from Mongo collector module
        if process == 'collect':
            collector = coll.find_one({'_id': ObjectId(collector_id)})

            active = collector['active']
            if active:
                message = 'active'
        else:
            network_mod = coll.find_one({'module': module})

            # Grabs the active flag from Mongo network module
            if process == 'process':
                active = network_mod['processor_active']
            else:
                active = network_mod['inserter_active']

            if active:
                message = 'active'


        resp = {'status': status, 'message': message}
        return resp

    def get_storage_counts(self, project_id, network):
        """
        Grabs the count of stored documents in Mongo for the given project and network

        :param project_id:
        :param network:

        :return: count
        """
        # Loads the storage DB
        storagedb = self._load_project_storage_db(project_id)

        # Initiates storage count
        count = 0

        if network == 'twitter':
            count = storagedb.tweets.count()
        elif network == 'facebook':
            count = storagedb.facebook.count()

        return count

    def _load_project_config_db(self, project_id):
        """
        Utility method to load a project account's config DB

        :param project_id:

        :return: project_config_db connection
        """
        # Finds project db
        project_info = self.get_project_detail(project_id)
        configdb = project_info['project_config_db']

        # Makes a connection to the config db
        project_config_db = self.connection[configdb]

        return project_config_db

    def _load_project_storage_db(self, project_id):
        """
        Utility method to load a project account's storage DB

        :param project_id:

        :return: project_storage_db connection
        """
        # Finds project db
        project_info = self.get_project_detail(project_id)

        # Connects to the storage DB
        db_name = project_info['project_name'] + '_' + project_id
        project_storage_db = self.connection[db_name]

        return project_storage_db

    def _generate_response(self, status, message, content=None):
        """
        Utility message to generate a request response in a standardized format

        :param status - status code
        :param message - message to send w/ status code
        :param content - response content | None

        :return: resp = { 'status': 1|0, 'message':'message-text-here', 'content': ... }
        """
        return {
            'status': status,
            'message': message,
            'content': content
        }