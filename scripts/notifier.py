def process_system_stats(system_stats):
    stats = {
        'critical': None,
        'warn': None,
        'info': None,
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

    # TODO in future - warn & info
    return stats

def process_project_stats(project_stats):
    stats = {
        'critical': None,
        'warn': None,
        'info': None,
    }

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

    stats['critical'] = critical if critical else None

    # TODO in future - warn & info
    # TODO in future - stats for processor & inserter
    return stats

def send_email(report):
    print report

def process_and_notify(system_stats, project_stats):
    report = {
        'CRITICAL': {
            'system': None,
            'project': None,
        },
        'WARN': {
            'system': None,
            'project': None,
        },
        'INFO': {
            'system': None,
            'project': None,
        },
    }

    system = process_system_stats(system_stats)
    report['CRITICAL']['system'] = system['critical']
    report['WARN']['system'] = system['warn']
    report['INFO']['system'] = system['info']

    project = process_project_stats(project_stats)
    report['CRITICAL']['project'] = project['critical']
    report['WARN']['project'] = project['warn']
    report['INFO']['project'] = project['info']

    send_email(report) #, project_stats['email'])
