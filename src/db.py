from pymongo import MongoClient

"""
TODO
----

Init - setup connection to be used throughout class
Setup - setup script username/password combos

auth - login, logout

get_project_list - list of project accounts, running collector count, description
get_project_detail - list of running collectors & details

set_collector_detail - setup of a collector config

WORK w/ CONTROLLER
set_network_status - process & insert flags at network level
set_collector_status - collector at network level
"""

class DB(object):

    def __init__(self):
        self.connection = MongoClient()

        self.config_db = self.connection.config
        self.stack_config = self.config_db.config

    def setup(self, project_list):
        """
        Initial app-wide config setup for project_users
        Should pass a list of project_name, password, description params:
        [{project_name: name, password: string, description: string}]
        """
        for item in project_list:
            self.stack_config.insert(item)

    def auth(self, project_name, password):
        auth = self.stack_config.find_one({
            'project_name'  : project_name,
            'password'      : password})

        if auth:
            status = 1
            project_id = auth['_id']
        else:
            status = 0
            project_id = None

        return [status, project_id]

    def get_project_list(self):
        pass

    def get_project_detail(self):
        pass

    def set_collector_detail(self):
        pass

    def set_network_status(self):
        pass

    def set_collector_status(self):
        pass

if __name__ == '__main__':
    Test = DB()

    db = Test.connection.config
    app_config = db.config

    test = app_config.find_one({'module': 'processor'})
    test_id = test['_id']
    test = app_config.find_one({'_id': test_id})
    print test

