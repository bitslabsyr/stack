#!env/bin/python

import sys
import os
import json

from stack.controller import Controller
from stack.db import DB

basedir = os.getcwd()

if __name__ == "__main__":
    c = Controller('5480c355eb8f8008ac260335', '5480c378eb8f8008b34fbc2f')

    c.run('collect', 'start')

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

    """
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
            project_list = json.loads(sys.argv[3])
            db.setup(project_list)

        elif method == 'auth':
            project_name = sys.argv[3]
            password = sys.argv[4]
            resp = db.auth(project_name, password)
            print resp
    else:
        print 'Please try again! Proper db methods:'
        for method in db_methods:
            print method + '\n'
        sys.exit()
    """
