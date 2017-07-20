import sys
import os
import json

from werkzeug import generate_password_hash

from app.controller import Controller
from app.models import DB

basedir = os.getcwd()

if __name__ == "__main__":

    USAGE = 'USAGE: python __main__.py db|controller {db_method}|{controller_method} {params}'

    db_methods = [
        'create_project',
        'auth',
        'get_project_list',
        'get_project_detail',
        'get_collector_detail',
        'get_network_detail',
        'set_collector_detail',
        'set_network_status',
        'set_collector_status',
        'get_collector_ids',
        'update_collector_detail'
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

        if method == 'create_project':
            """
            python __main__.py db create_project
            """

            print
            print 'Welcome to STACKS! Please fill out the following information \
                   to get started:'
            print
            print 'Project Name - one word, NO hyphens (-), underscores (_), or \
                   spaces'
            print
            print 'Email - one or more email(s) used for status reports and \
                   issue notices.'
            print
            print 'Password - used for validation down the road'
            print
            print 'Description - a quick description about your project'

            project_name = raw_input('Project Name: ')
            password = raw_input('Password: ')
            hashed_password = generate_password_hash(password)

            cont = True
            email = []
            while cont:
                inut_email = raw_input('Email: ')
                email.append(inut_email)

                add_more = raw_input('Add Another Email [y/n]: ')
                if add_more is not 'y':
                    cont = False

            description = raw_input('Description: ')

            resp = db.create(project_name, password, hashed_password, description=description, email=email)
            print json.dumps(resp, indent=1)

        elif method == 'auth':
            """
            python __main__.py db auth project_name password
            """
            project_name = sys.argv[3]
            password = sys.argv[4]
            resp = db.auth(project_name, password)
            print json.dumps(resp, indent=1)

        elif method == 'get_project_list':
            """
            python __main__.py db get_project_list
            """
            resp = db.get_project_list()
            print json.dumps(resp, indent=1)

        elif method == 'get_collector_ids':
            """
            python __main__.py db get_collector_ids project_id
            """
            project_id = sys.argv[3]
            resp = db.get_collector_ids(project_id)
            print json.dumps(resp, indent=1)
        elif method == 'get_project_detail':
            """
            python __main__.py db get_project_detail project_id
            """
            project_id = sys.argv[3]
            resp = db.get_project_detail(project_id)
            print json.dumps(resp, indent=1)
        elif method == 'get_collector_detail':
            """
            python __main__.py db get_collector_detail project_id collector_id
            """
            project_id = sys.argv[3]
            collector_id = sys.argv[4]
            resp = db.get_collector_detail(project_id, collector_id)
            print json.dumps(resp, indent=1)
        elif method == 'get_network_detail':
            """
            python __main__.py db get_network_detail project_id network
            """
            project_id = sys.argv[3]
            network = sys.argv[4]
            resp = db.get_network_detail(project_id, network)
            print json.dumps(resp, indent=1)
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
            print '------'
            print 'languages = list, of, codes | none'
            print 'Ex. = pr, en'
            print ''
            print 'locations = list, of, location, points | none'
            print 'Ex. = -74, 40, -73, 41'
            print ''
            print 'terms = list,of,terms | none'
            print 'Ex. = social,media'
            print ''
            print 'If you creating a Facebook collector, please specify the "collection_type", "start_date" and "end_date" fields:'
            print '------'
            print 'collection_type = realtime | historical'
            print ''
            print 'start_date = 2015-04-01 | none'
            print 'end_date = 2014-04-01 | none'
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
            network = raw_input('Network: ').lower()

            terms_list = raw_input('Terms: ')
            if terms_list == 'none':
                terms_list = None
            else:
                terms_list = terms_list.split(',')

            languages = None
            locations = None
            api = None
            start_date = None
            end_date = None

            if network == 'twitter':
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

                collection_type = None

                api = raw_input('API: ')

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

            elif network == 'facebook':
                collection_type = raw_input('Collection Type: ')
                start_date = raw_input('Start Date: ')
                end_date = raw_input('End Date: ')

                # TODO - start and end date reqs for historical
                if start_date == 'none':
                    start_date = None
                if end_date == 'none':
                    end_date = None

                client_id = raw_input('Client ID: ')
                client_secret = raw_input('Client Secret: ')

                api_credentials_dict = {'client_id': client_id, 'client_secret': client_secret}

            resp = db.set_collector_detail(project_id, collector_name, network, collection_type, api_credentials_dict,
                                           terms_list, api=api, languages=languages, location=locations,
                                           start_date=start_date, end_date=end_date)

            print json.dumps(resp, indent=1)

        elif method == 'update_collector_detail':
            """
            Calls db.update_collector_detail
            Can only update a single collector param at a time

            FOR TERMS - must provide term and collection status (1 or 0)
            FOR API AUTH CREDS - must provide full list, even if updating one
            """
            update_params_list = [
                'collector_name',
                'api',
                'auth',
                'terms',
                'languages',
                'locations',
                'collection_type',
                'start_date',
                'end_date'
            ]

            update_param = sys.argv[3]
            if update_param not in update_params_list:
                print 'Invalid update paramter. Please try again.'
                print 'Valid update params: collector_name, api, auth, terms, \
                       languages, locations, collection_type, start_date, \
                       end_date.'
                sys.exit(1)

            print 'Collector update function called.'
            print ''
            print 'FOR TERMS - must provide term value and collection status.'
            print '     1 = collect | 0 = do not collect'
            print ''
            print 'FOR OAUTH CREDS - must provide full list'
            print ''
            print 'FOR languages and locations - must provide full new list of codes. Update will overwrite.'
            print ''
            print 'languages = list, of, codes | none'
            print 'Ex. = pr, en'
            print ''
            print 'locations = list, of, location, points | none'
            print 'Ex. = -74, 40, -73, 41'
            print ''
            print 'FOR start & end dates for Facebook, please use the following format:'
            print 'YYYY-MM-DD | none'
            print ''
            print 'FOR collection_type for Facebook: historical | realtime'
            print ''
            print 'Updating for param: %s' % update_param
            print ''

            project_name = raw_input('Project Name: ')
            password = raw_input('Password: ')

            resp = db.auth(project_name, password)
            if resp['status']:
                project_id = resp['project_id']
            else:
                print 'Invalid Project! Please try again.'
                sys.exit(0)

            collector_id = raw_input('Collector ID: ')
            resp = db.get_collector_detail(project_id, collector_id)
            resp = resp['collector']

            params = {}

            # First, do network-wide updates
            if update_param == 'collector_name':
                params['collector_name'] = raw_input('New Collector Name: ')
            elif update_param == 'terms':
                # Sets term type value based on collector API
                if resp['network'] == 'facebook':
                    term_type = 'page'
                elif resp['api'] == 'follow':
                    term_type = 'handle'
                else:
                    term_type = 'term'

                # Adds term dict to the params dict based on info provided, will be parsed by update method
                cont = True
                params['terms_list'] = []
                while cont:
                    new_term = raw_input('Term: ')
                    collect_status = int(raw_input('Collect: '))

                    if collect_status not in [1, 0]:
                        print 'Invalid collect status. Must be 1 or 0.'
                        sys.exit(0)

                    params['terms_list'].append({
                        'term': new_term,
                        'collect': collect_status,
                        'type': term_type,
                        'id': None
                    })

                    cont_ask = raw_input('Continue? [y/n]: ')
                    cont_ask = cont_ask.lower()
                    if cont_ask == 'y':
                        cont = True
                    else:
                        cont = False

            # Next, network specific updates
            if resp['network'] == 'twitter':
                if update_param == 'api':
                    params['api'] = raw_input('New API Filter: ')

                elif update_param == 'languages':
                    languages = raw_input('New Language Codes List: ')

                    if languages == 'none':
                        languages = None
                    else:
                        languages = languages.replace(' ', '')
                        languages = languages.split(',')

                    params['languages'] = languages

                elif update_param == 'locations':
                    locations = raw_input('New Location Codes List: ')

                    if locations == 'none':
                        locations = None
                    else:
                        locations = locations.replace(' ', '')
                        locations = locations.split(',')

                    params['location'] = locations

                elif update_param == 'auth':
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
                    params['api_auth'] = api_credentials_dict

            # Now, Facebook params
            elif resp['network'] == 'facebook':
                if update_param == 'collection_type':
                    params['collection_type'] = raw_input('Collection Type: ')
                elif update_param == 'start_date':
                    start_date = raw_input('Start Date: ')
                    if start_date == 'none':
                        params['start_date'] = None
                    else:
                        params['start_date'] = start_date

                elif update_param == 'end_date':
                    end_date = raw_input('End Date: ')
                    if end_date == 'none':
                        params['end_date'] = None
                    else:
                        params['end_date'] = end_date

                elif update_param == 'auth':
                    client_id = raw_input('Client ID: ')
                    client_secret = raw_input('Client Secret: ')

                    api_credentials_dict = {
                        'client_id' : client_id,
                        'client_secret': client_secret
                    }
                    params['api_auth'] = api_credentials_dict

            resp = db.update_collector_detail(project_id, collector_id, **params)
            print json.dumps(resp, indent=1)

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
            c = Controller(cmdline=True, project_id=project_id, process=method, collector_id=collector_id)
        else:
            network = sys.argv[5]
            c = Controller(cmdline=True, project_id=project_id, process=method, network=network)

        command = sys.argv[3]
        if command in controller_commands:
            c.process_command(command)
        else:
            print 'USAGE: python __main__.py controller collect|process|insert start|stop|restart project_id {collector_id|network}'

    else:
        print 'Please try again!'
        sys.exit()
