import json
import subprocess

from pymongo import MongoClient
from bson.objectid import ObjectId
from check_collectors import get_collector_status
from notifier import process_and_notify

def get_mongo_docs():
    connection = MongoClient()
    config_db = connection.config.config

    projects = []
    for project in config_db.find():
        # TODO - Change to admin
        if 'project_name' in project.keys() and ('admin' not in project.keys() or not project['admin']):
            project['_id'] = str(project['_id'])

            projects.append({
                'id': str(project['_id']),
                'project_name': project['project_name'],
                'configdb': project['configdb'],
                # 'email': project['email'],
                'collectors': project['collectors']
            })

    for project in projects:
        project_db = connection[project['configdb']].config

        collectors = project['collectors']
        project['collectors'] = []

        for collector in collectors:
            cid = collector['collector_id']
            cdoc = project_db.find_one(ObjectId(cid))

            # Only want twitter collectors that track the listener thread
            if (cdoc['network'] == 'twitter' and 'listener_running' in cdoc.keys()) or cdoc['network'] != 'twitter':
                project['collectors'].append({
                    'id': str(cdoc['_id']),
                    'collector_name': cdoc['collector_name'],
                    # 'start_time': cdoc['start_time'],
                    # 'end_time': cdoc['end_time'],
                    'active': cdoc['active'],
                    'flags': cdoc['collector'],
                    'network': cdoc['network']
                })

    return projects

def check_diskspace():
    df = subprocess.Popen(['df', '-h'], stdout=subprocess.PIPE)
    avail = int(df.communicate()[0].split('\n')[1].split()[3].split('G')[0])

    return avail

def check_mongo_status():
    pgrep = subprocess.Popen(['pgrep', 'mongo'], stdout=subprocess.PIPE)
    status = pgrep.communicate()[0]

    if status:
        return True
    else:
        return False

def main():
    # Dict to be used for storing status info
    status_dict = {}

    # Part 1 - System status
    status_dict['system'] = {
        'avail_space': check_diskspace(),
        'mongo_running': check_mongo_status(),
    }

    # Part 2 - Status for each project & its given processes
    projects = get_mongo_docs()
    if projects:
        for project in projects:
            for collector in project['collectors']:
               collector = get_collector_status(project, collector)

        status_dict['projects'] = projects
        for project in status_dict['projects']:
            process_and_notify(status_dict['system'], project)

if __name__ == '__main__':
    main()
