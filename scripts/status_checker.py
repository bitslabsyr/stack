import sys
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
        if 'email' in project.keys() and ('admin' not in project.keys() or not project['admin']):
            projects.append({
                'id': str(project['_id']),
                'project_name': project['project_name'],
                'configdb': project['configdb'],
                'email': project['email'],
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

def main(report_type):
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
            process_and_notify(status_dict['system'], project, report_type)

if __name__ == '__main__':
    reports = [
        'system_check',
        'report'
    ]
    report_type = sys.argv[1]

    if report_type not in reports:
        print 'Report type {} not valid'.format(report_type)
        sys.exit(1)
    else:
        main(report_type)
