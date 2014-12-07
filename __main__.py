#!env/bin/python

import sys
import os
import json

from stack.controller import Controller
from stack.db import DB

basedir = os.getcwd()

if __name__ == "__main__":

    USAGE = 'USAGE: python __main__.py db|controller {db_method}|{controller_method} {params}'

    db_methods = [
        'setup',
        'auth',
        'get_project_list',
        'get_project_detail',
        'get_collector_detail',
        'get_network_detail',
        'set_collector_detail',
        'set_network_status',
        'set_collector_status'
    ]

    controller_processes = ['collect', 'process', 'insert']

    try:
        wrapper = sys.argv[1]
    except:
        print USAGE
        sys.exit()
    try:
        method = sys.argv[2]
    except:
        print USAGE
        sys.exit()

    if wrapper not in ['db', 'controller']:
        print USAGE
        sys.exit()

    if wrapper == 'db' and method in db_methods:
        db = DB()

        if method == 'setup':
            """
            python __main__.py db setup [project_list]
            """
            project_list = json.loads(sys.argv[3])
            resp = db.setup(project_list)
            print json.dumps(resp)
        elif method == 'auth':
            """
            python __main__.py db auth project_name password
            """
            project_name = sys.argv[3]
            password = sys.argv[4]
            resp = db.auth(project_name, password)
            print json.dumps(resp)
        elif method == 'get_project_list':
            """
            python __main__.py db get_project_list
            """
            resp = db.get_project_list()
            print json.dumps(resp)
        elif method == 'get_project_detail':
            """
            python __main__.py db get_project_detail project_id
            """
            project_id = sys.argv[3]
            resp = db.get_project_detail(project_id)
            print json.dumps(resp)
        elif method == 'get_collector_detail':
            """
            python __main__.py db get_collector_detail project_id collector_id
            """
            project_id = sys.argv[3]
            collector_id = sys.argv[4]
            resp = db.get_collector_detail(project_id, collector_id)
            print json.dumps(resp)
        elif method == 'get_network_detail':
            """
            python __main__.py db get_network_detail project_id network
            """
            project_id = sys.argv[3]
            network = sys.argv[4]
            resp = db.get_network_detail(project_id, network)
            print json.dumps(resp)
        elif method == 'set_collector_detail':
            """
            python __main__.py db set_collector_detail project_id network api
            collector_name api_credentials_dict terms_list

            WHERE

            api_credentials_dict = {'access_token': 'xxxxx', 'etc.': 'etc.'}
            terms_list = ['your', 'array', 'of', 'terms']

            Can be used to both create and update a collector's details
            """
            project_id = sys.argv[3]
            network = sys.argv[4]
            api = sys.argv[5]
            collector_name = sys.argv[6]
            api_credentials_dict = json.loads(sys.argv[7])
            terms_list = json.loads(sys.argv[8])

            resp = db.set_collector_detail(project_id, network, api, collector_name, api_credentials_dict, terms_list)
            print json.dumps(resp)
    elif wrapper == 'controller' and method in controller_processes:
        """
        python __main__.py controller collect|process|insert start|stop|restart project_id collector_id
        """
        project_id = sys.argv[4]
        collector_id = sys.argv[5]

        c = Controller(project_id, collector_id)

        command = sys.argv[3]
        if command in controller_commands:
            c.run(method, command)
        else:
            print 'USAGE: python __main__.py controller collect|process|insert start|stop|restart project_id collector_id'

    else:
        print 'Please try again!'
        sys.exit()
