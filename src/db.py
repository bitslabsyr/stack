import json
from bson.objectid import ObjectId

from pymongo import MongoClient

"""
TODO
----
get_project_detail - list of running collectors & details

WORK w/ CONTROLLER
set_network_status - process & insert flags at network level
set_collector_status - collector at network level
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
                print 'Project "%s" already exists!' % item['project_name']

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
                    'module'    : 'twitter',
                    'processor' : {'active': 0, 'run': 0},
                    'inserter'  : {'active': 0, 'run': 0}
                }

                project_config_db = self.connection[configdb]
                coll = project_config_db.config

                coll.insert(doc)

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
            project_id = auth['_id']
        else:
            status = 0
            project_id = None

        resp = {'status': status, 'project_id': project_id}

        return resp

    def get_project_list(self):
        """
        Generic function that return list of all projects in stack config DB
        """
        projects = self.stack_config.find()

        if projects:
            status = 1
            project_count = self.stack_config.count()
            project_list = [item for item in projects]
            resp = {'status': status, 'project_count': project_count, 'project_list': project_list}
        else:
            status = 0
            resp = {'status': status}

        return resp

    # TODO - review collector storage process
    def get_project_detail(self, project_id):
        """
        When passed a project_id, returns that project's account info along
        with it's list of collectors
        """
        project = self.stack_config.find_one({'_id': ObjectId(project_id)})

        if not project:
            resp = {'status': 0}
            return resp

        configdb = project['configdb']

        resp = {
            'project_id'            : project['_id'],
            'project_name'          : project['project_name'],
            'project_description'   : project['description'],
            'project_config_db'     : configdb
        }

        if not project['collectors']:
            resp['collectors'] = []
        else:
            project_config_db = self.connection[configdb]
            coll = project_config_db.config

            collectors = []
            for item in project['collectors']:
                collector_id = item['collector_id']
                collector = coll.find_one({'_id': collector_id})

                collectors.append(collector)

            resp['collectors'] = collectors

        return resp

    # TODO - enforce unique project names
    def set_collector_detail(self, project_id, network, api, collector_name, api_credentials_dict, terms_list):
        """
        Sets up config collection for a project collector
        """
        resp = self.stack_config.find_one({'_id': ObjectId(project_id)})
        project_name = resp['project_name']
        configdb = resp['configdb']

        terms = []
        for term in terms_list:
            terms.append({'term': term, 'collect': 1})

        doc = {
            'project_id'    : project_id,
            'project_name'  : project_name,
            'collector_name': collector_name,
            'network'       : network,
            'api'           : api,
            'api_auth'      : api_credentials_dict,
            'terms_list'    : terms,
            'collector'     : {'active': 0, 'run': 0, 'collect': 0, 'update': 0}
        }

        project_config_db = self.connection[configdb]
        coll = project_config_db.config

        try:
            coll.insert(doc)

            resp = coll.find_one({'collector_name': collector_name})
            collector_id = resp['_id']

            self.stack_config.update({'_id': ObjectId(project_id)}, {'$push': {'collectors': {'name': collector_name, 'collector_id': collector_id, 'active': 0}}})
            status = 1
        except:
            status = 0

        return status

    def update_collector_detail(self, collector_id, **kwargs):
        pass

    def set_network_status(self, run=0, process=None, insert=None):
        """
        Start / Stop preprocessor & inserter for a series of network
        collections
        """

    def set_collector_status(self, collector_id, run=0):
        """
        Start / Stop an individual collector
        """

if __name__ == '__main__':
    projects = [
        {
            'project_name': 'billy',
            'password': 'SU2orange!',
            'description': 'I like comfy socks and toasty coffee.'
        },
        {
            'project_name': 'goji',
            'password': 'SU2orange!',
            'description': "What's a goji?"
        }
    ]

    test_db = DB()

    # test_db.setup(projects)
    # resp = test_db.get_project_list()
    # resp = test_db.get_project_detail('54806f73eb8f800351de5ca3')

    """
    api_credentials = {}
    terms_list = ['billy']

    resp = test_db.set_collector_detail('54806f73eb8f800351de5ca3', 'twitter', 'track', 'goji_track', api_credentials, terms_list)
    """

    # print resp
