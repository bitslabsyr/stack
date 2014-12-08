#!env/bin/python

import sys
import os
import json

from stack.controller import Controller
from stack.db import DB

db = DB()

test_projects = []
goji = {'project_name': 'goji', 'password': 'XXXX', 'description': 'What the hell is a goji?'}
billy = {'project_name': 'billy', 'password': 'XXXX', 'description': 'I wrote this!'}
test_projects.append(goji)
test_projects.append(billy)

oauth_follow = {
    'consumer_key': 'XXXX',
    'consumer_secret': 'XXXX',
    'access_token': 'XXXX',
    'access_token_secret': 'XXXX'
}

oauth_track = {
    'consumer_key': 'XXXX',
    'consumer_secret': 'XXXX',
    'access_token': 'XXXX',
    'access_token_secret': 'XXXX'
}

if __name__ == '__main__':
    if sys.argv[1] == 'setup':
        """
        1. Setup
            -new projects
            -existing projects
        """
        param = sys.argv[2]
        if param == 'new':
            resp = db.setup(test_projects)
        else:
            resp = db.setup([goji])

        print json.dumps(resp, indent=1)

    if sys.argv[1] == 'auth':
        """
        2. Auth
            -correct combo
            -bad password
            -bad username
        """
        param = sys.argv[2]
        if param == 'correct':
            resp = db.auth('goji', 'SU2orange!')
        elif param == 'pass':
            resp = db.auth('goji', 'xxxx')
        else:
            resp = db.auth('b', 'SU2orange!')

        print json.dumps(resp, indent=1)

    if sys.argv[1] == 'get_project_list':
        """
        3. get_project_list()
        """
        resp = db.get_project_list()
        print json.dumps(resp, indent=1)

    if sys.argv[1] == 'get_project_detail':
        """
        4. get_project_detail()
            -valid _id
            -invalid _id
        """
        auth = db.auth('goji', 'SU2orange!')
        project_id = auth['project_id']

        param = sys.argv[2]
        if param == 'valid':
            resp = db.get_project_detail(project_id)
        else:
            resp = db.get_project_detail('xxx')

        print json.dumps(resp, indent=1)

    if sys.argv[1] == 'set_collector_detail':
        """
        7. set_collector_detail()
            -project info
        """
        auth = db.auth('goji', 'SU2orange!')
        project_id_follow = auth['project_id']

        auth = db.auth('billy', 'SU2orange!')
        project_id_track = auth['project_id']

        param = sys.argv[2]
        if param == 'follow':
            resp = db.set_collector_detail(project_id_follow, 'twitter', 'follow', 'goji_follow', oauth_follow, ['ceskavich'])
        elif param == 'track':
            resp = db.set_collector_detail(project_id_track, 'twitter', 'track', 'billy_track', oauth_track, ['ceskavich'])

        print json.dumps(resp, indent=1)

    if sys.argv[1] == 'get_collector_detail':
        """
        5. get_collector_detail()
            -valid project_id
            -invalid project_id
            -valid collector_id
            -invalid collector_id
        """
        auth = db.auth('goji', 'SU2orange!')
        project_id = auth['project_id']

        detail = db.get_project_detail(project_id)
        collector_id = detail['collectors'][0]['_id']

        param = sys.argv[2]
        if param == 'valid':
            resp = db.get_collector_detail(project_id, collector_id)
        elif param == 'invalidc':
            resp = db.get_collector_detail(project_id, '123')
        elif param == 'invalidp':
            resp = db.get_collector_detail('123', collector_id)

        print json.dumps(resp, indent=1)

    if sys.argv[1] == 'get_network_detail':
        """
        6. get_network_detail()
            -valid project_id
            -invalid project_id
            -valid / invalid network
        """
        auth = db.auth('goji', 'SU2orange!')
        project_id = auth['project_id']

        param = sys.argv[2]
        if param == 'valid':
            resp = db.get_network_detail(project_id, 'twitter')
        elif param == 'invalidp':
            resp = db.get_network_detail('123', 'twitter')
        elif param == 'invalidn':
            resp = db.get_network_detail(project_id, 'facebook')

        print json.dumps(resp, indent=1)

    if sys.argv[1] == 'controller':
        """
        8. Controller.run()
            -valid / invalid project_id
            -valid / invalid collector_id
            -collect: start / stop / restart
            -process: start / stop / restart
            -insert: start / stop / restart
        """
        valid = sys.argv[2]

        auth = db.auth('goji', 'SU2orange!')
        project_id = auth['project_id']

        detail = db.get_project_detail(project_id)
        collector_id = detail['collectors'][0]['_id']

        if valid == 'valid':
            process = sys.argv[3]
            command = sys.argv[4]

            if process == 'collect':
                c = Controller(project_id, process, collector_id=collector_id)
                c.run(command)
            elif process == 'process':
                c = Controller(project_id, process, network='twitter')
                c.run(command)
            elif process == 'insert':
                c = Controller(project_id, process, network='twitter')
                c.run(command)
        else:
            c = Controller(project_id, '123')
            c.run('collect', 'start')
