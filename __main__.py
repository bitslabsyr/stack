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
    controller_commands = ['start', 'stop', 'restart']

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
        elif method == 'get_collector_ids':
            """
            python __main__.py db get_collector_ids project_id
            """
            project_id = sys.argv[3]
            resp = db.get_collector_ids(project_id)
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
            python __main__.py db set_collector_detail

            INPUT FORMATTING

            terms_list = '["your", "array", "of", "terms"]' | none
            languages = '["array", "of", "BPR-47 language codes"]' | none
            location = '["array", "of", "location", "points"]' | none

            Can be used to both create and update a collector's details
            """

            print ''
            print 'To create a collector, please fill in the fields when asked.'
            print ''
            print 'For the fields "languages", "locations", and "terms" please fill in either a command separated list, or "none":'
            print ''
            print 'languages = list, of, codes | none'
            print 'Ex. = pr, en'
            print ''
            print 'locations = list, of, location, points | none'
            print 'Ex. = -74, 40, -73, 41'
            print ''
            print 'terms = list, of, terms | none'
            print 'Ex. = social, media'
            print ''

            project_name = raw_input('Project Name: ')
            password = raw_input('Password: ')

            resp = db.auth(project_name, password)
            if resp['status']:
                project_id = resp['project_id']
            else:
                print 'Invalid Project! Please try again.'
                sys.exit(0)

            collector_name = raw_input('Collector Name: ')

            languages = raw_input('Languages: ')
            if languages == 'none':
                languages = None
            else:
                languages = languages.replace(' ', '')
                languages = languages.split(',')

            locations = raw_input('Locations: ')
            if locations == 'none':
                locations = None
            else:
                locations = locations.replace(' ', '')
                locations = locations.split(',')

                if len(locations) % 4 is not 0:
                    print 'The number of location coordinates need to be in pairs of four. Please consult the Twitter docs and try again.'
                    sys.exit(0)

            terms_list = raw_input('Terms: ')
            if terms_list == 'none':
                terms_list = None
            else:
                terms_list = terms_list.replace(' ', '')
                terms_list = terms_list.split(',')

            api = raw_input('API: ')
            network = 'twitter'

            consumer_key = raw_input('Consumer Key: ')
            consumer_secret = raw_input('Consumer Secret: ')
            access_token = raw_input('Access Token: ')
            access_token_secret = raw_input('Access Token Secret: ')

            api_credentials_dict = {
                'consumer_key'          : consumer_key,
                'consumer_secret'       : consumer_secret,
                'access_token'          : access_token,
                'access_token_secret'   : access_token_secret
            }

            resp = db.set_collector_detail(project_id, network, api, collector_name, api_credentials_dict, terms_list, languages=languages, location=locations)
            print json.dumps(resp)
    elif wrapper == 'controller' and method in controller_processes:
        """
        python __main__.py controller collect|process|insert start|stop|restart project_id {collector_id|network}

        WHERE

        collector_id - optional, only needed for a collection controller
        network - optional, needed for processor or inserter controllers
        """
        project_id = sys.argv[4]

        if method == 'collect':
            collector_id = sys.argv[5]
            c = Controller(project_id, method, collector_id=collector_id)
        else:
            network = sys.argv[5]
            c = Controller(project_id, method, network=network)

        command = sys.argv[3]
        if command in controller_commands:
            c.run(command)
        else:
            print 'USAGE: python __main__.py controller collect|process|insert start|stop|restart project_id {collector_id|network}'

    else:
        print 'Please try again!'
        sys.exit()
