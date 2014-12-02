import json
from bson.objectid import ObjectId

from pymongo import MongoClient

"""
TODO
----

get_project_list - list of project accounts, running collector count, description
get_project_detail - list of running collectors & details

set_collector_detail - setup of a collector config

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
        for item in project_list:
            resp = self.auth(item['project_name'], item['password'])

            if resp['status']:
                print 'Project "%s" already exists!' % item['project_name']
            else:
                item['collectors'] = []
                self.stack_config.insert(item)

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

    def get_project_detail(self):
        pass

    # TODO - enforce unique project names
    def set_collector_detail(self, project_id, network, api, collector_name, api_credentials_dict, terms_list):
        """
        Sets up config collection for a project collector
        """
        resp = self.stack_config.find_one({'_id': ObjectId(project_id)})
        project_name = resp['project_name']

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
            'collector'     : {'active': 0, 'run': 0, 'collect': 0, 'update': 0},
            'processor'     : {'active': 0, 'run': 0},
            'inserter'      : {'active': 0, 'run': 0}
        }

        project_config_db = self.connection[project_name + 'Config']
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

    def set_network_status(self):
        pass

    def set_collector_status(self):
        pass

if __name__ == '__main__':
    projects = [
        {
            'project_name': 'ross',
            'password': '1111',
            'description': 'Test project three.'
        }
    ]

    test_db = DB()

    status = test_db.set_collector_detail('547e02e1eb8f8005abf243f2', 'twitter', 'track', 'govdata_track', {'application_key': '123'}, ['billy', 'ceskavich'])
    print status

