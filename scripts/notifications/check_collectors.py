import os

from check_processes import check_process_pid

def get_collector_status(project, collector):
    base_dir = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
    pid_dir = base_dir\
        + '/out/'\
        + project['project_name']\
        + '-'\
        + project['id']\
        + '/pid'

    process_name = project['project_name']\
        + '-'\
        + collector['collector_name']\
        + '-collect-'\
        + collector['network']\
        + '-'\
        + collector['id']

    pidfile = pid_dir + '/' + process_name + '.pid'
    collector['daemon_running'] = check_process_pid(pidfile)

    return collector
