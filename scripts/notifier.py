import os

from pymongo import MongoClient
from bson.objectid import ObjectId
from sendgrid import SendGridClient, Mail, SendGridError, SendGridClientError, SendGridServerError
from jinja2 import Environment, FileSystemLoader

# TODO - Set as os.environ var
API_KEY = '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'

def get_previous_report(project_id):
    connection = MongoClient()
    config_db = connection.config.config

    project = config_db.find_one(ObjectId(project_id))
    if 'status_report' in project.keys():
        return project['status_report']
    else:
        # If we haven't loaded a status report into Mongo yet, create one
        report = {
            'system': {
                'total': 0,
                'critical': None,
                'total_critical': 0,
                'warn': None,
                'total_warn': 0,
                'info': None,
                'total_info': 0
            },
            'project': {
                'collectors': {
                    'total': 0,
                    'critical': None,
                    'total_critical': 0,
                    'warn': None,
                    'total_warn': 0,
                    'info': None,
                    'total_info': 0
                }
            }
        }
        config_db.update({'_id': ObjectId(project_id)}, {
            '$set': { 'status_report': report }
        })
        return report

def process_system_stats(system_stats):
    stats = {
        'total': 0,
        'critical': None,
        'total_critical': 0,
        'warn': None,
        'total_warn': 0,
        'info': None,
        'total_info': 0,
    }

    # A) Critical
    critical = []
    if system_stats['avail_space'] < 20:
        critical.append({
            'title': 'Storage Space Low - %d' % system_stats['avail_space'],
            'message': 'System storage space is below 20GB, now at %dGB' % system_stats['avail_space'],
        })

    if not system_stats['mongo_running']:
        critical.append({
            'title': 'Mongo Error',
            'message': 'MongoDB has stopped running on the server!',
        })

    stats['critical'] = critical if critical else None

    # TODO B & C - warn & info
    warn = []
    info = []

    # D) Counts
    stats['total_critical'] = len(critical)
    stats['total_warn'] = len(warn)
    stats['total_info'] = len(info)
    stats['total'] = stats['total_critical'] + stats['total_warn'] + stats['total_info']

    return stats

def process_project_stats(project_stats):
    stats = {
        'collectors': {
            'total': 0,
            'critical': None,
            'total_critical': 0,
            'warn': None,
            'total_warn': 0,
            'info': None,
            'total_info': 0,
        }
    }

    # If no project stats b/c Mongo is down, just return
    if not project_stats:
        return stats

    # A) Critical
    critical = []
    for collector in project_stats['collectors']:
        if collector['flags']['run'] and not collector['daemon_running']:
            critical.append({
                'title': 'Unexpected process termination',
                'message': 'Collector "%s" has stopped without being flagged to do so.' % collector['collector_name'],
            })

        if collector['flags']['collect'] and collector['network'] == 'twitter' and not collector['listener_running']:
            critical.append({
                'title': 'Collector running without listener',
                'message': 'Collector "%s" is running without a connection to the Streaming API' % collector['collector_name'],
            })

    stats['collectors']['critical'] = critical if critical else None
    stats['collectors']['total_critical'] = len(critical)
    stats['collectors']['total'] = len(critical)

    # TODO in future - warn & info
    # TODO in future - stats for processor & inserter

    return stats

def new_issues(report, previous_report):
    counts = [
        report['system']['total'],
        report['project']['collectors']['total']
    ]
    previous_counts = [
        previous_report['system']['total'],
        previous_report['project']['collectors']['total']
    ]

    return counts[0] > previous_counts[0] or counts[1] > previous_counts[1]

def generate_email_text(report):
    loader = FileSystemLoader(os.path.abspath(os.path.dirname(__file__)) + '/templates')
    env = Environment(loader=loader)

    return env.get_template('status_email.html').render(report=report)

def send_email(report, title):
    sg = SendGridClient(API_KEY, raise_errors=True)

    # Backwards compatability for emails stored as strings, not lists
    emails = report['project_details']['email']
    if type(emails) is not list:
        emails = [emails]

    for address in emails:
        message = Mail()
        message.add_to(address)
        message.set_subject(title)
        message.set_html(generate_email_text(report))
        message.set_from('STACKS <noreply@bits.ischool.syr.edu>')

        try:
            sg.send(message)
        except SendGridError as e:
            print e
        except SendGridClientError as e:
            print e
        except SendGridServerError as e:
            print e

def process_and_notify(system_stats, project_stats, report_type):
    # Create the new report
    report = {}
    report['system'] = process_system_stats(system_stats)
    report['project'] = process_project_stats(project_stats)
    report['project_details'] = {
        'project_name': project_stats['project_name'] if project_stats else 'Full System',
        'email': project_stats['email'] if project_stats else 'bceskavich@gmail.com'
    }

    # If this is a standard check, store. Send a notification is new issues
    previous_report = get_previous_report(project_stats['id'])
    if report_type == 'system_check':
        if new_issues(report, previous_report):
            send_email(report, 'STACKS Issue!')

        connection = MongoClient()
        config_db = connection.config.config
        config_db.update({'_id': ObjectId(project_stats['id'])}, {
            '$set': { 'status_report': report }
        })
    elif report_type == 'report':
        # Otherwise, send our daily report regardless if there are new issues
        send_email(report, 'STACKS Daily Status Update')
