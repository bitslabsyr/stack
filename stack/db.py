import json
from bson.objectid import ObjectId

from pymongo import MongoClient

"""
MongoDB wrapper for STACK
"""

class DB(object):

    def __init__(self):
        # Class instance connection to Mongo
        self.connection = MongoClient()

        # App-wide config file for project info access
        self.config_db = self.connection.config
        self.stack_config = self.config_db.config

    def setup(self, project_list):
        """
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

        # Loops through each given project & sets up info
        for item in project_list:
            # Checks to see if project already exists
            resp = self.auth(item['project_name'], item['password'])
            if resp['status']:
                fail_count += 1
                status = 0

            # Creates master config entry for project
            else:
                item['collectors'] = []
                configdb = item['project_name'] + 'Config'
                item['configdb'] = configdb
                self.stack_config.insert(item)

                # Also creates network-wide flag modules
                # TODO - this should be more dynamic in future versions
                #      - (i.e. Create from a network list)
                doc = {
                    'module'            : 'twitter',
                    'collection_script' : 'ThreadedCollector',
                    'processor_script'  : 'preprocess',
                    'insertion_script'  : 'mongoBatchInsert',
                    'processor'         : {'run': 0},
                    'inserter'          : {'run': 0},
                    'processor_active'  : 0,
                    'inserter_active'   : 0
                }

                project_config_db = self.connection[configdb]
                coll = project_config_db.config

                try:
                    coll.insert(doc)
                    success_count += 1
                    status = 1
                except:
                    status = 0

        message = '%d successful project creations. %d duplicates failed.' % (success_count, fail_count)

        resp = {'status': status, 'message': message}

        return resp

    def auth(self, project_name, password):
        """
        Project auth function
        """
        # TODO - Flag issue that we know it's insecure & needs fix
        auth = self.stack_config.find_one({
            'project_name'  : project_name,
            'password'      : password})

        if auth:
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
                project_list.append(project)

            resp = {'status': status, 'message': 'Success', 'project_count': project_count, 'project_list': project_list}
        else:
            status = 0
            resp = {'status': status, 'message': 'Failed'}

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
                resp['collectors'] = []
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

    # TODO - Create more dynamic update that allows for active/inactive terms
    def set_collector_detail(self, project_id, network, api, collector_name, api_credentials_dict, terms_list):
        """
        Sets up config collection for a project collector
        """
        resp = self.stack_config.find_one({'_id': ObjectId(project_id)})
        project_name = resp['project_name']
        configdb = resp['configdb']

        terms = []
        for term in terms_list:
            if api == 'track':
                term_type = 'term'
            else:
                term_type = 'handle'
            terms.append({'term': term, 'collect': 1, 'type': term_type, 'id': None})

        doc = {
            'project_id'    : project_id,
            'project_name'  : project_name,
            'collector_name': collector_name,
            'network'       : network,
            'api'           : api,
            'api_auth'      : api_credentials_dict,
            'terms_list'    : terms,
            'collector'     : {'run': 0, 'collect': 0, 'update': 0},
            'active'        : 0
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
