from app import celery
from controller import Controller

@celery.task()
def start_daemon(process, project, collector_id=None, network=None):
    """
    Calls a Controller to daemonize and start a STACK process
    """
    if process == 'collect':
        c = Controller(
            process=process,
            project=project,
            collector_id=collector_id
        )
    else:
        c = Controller(
            process=process,
            project=project,
            network=network
        )

    c.process_command('start')

@celery.task()
def stop_daemon(process, project, collector_id=None, network=None):
    """
    Calls a Controller to stop a daemonized STACK process
    """
    if process == 'collect':
        c = Controller(
            process=process,
            project=project,
            collector_id=collector_id
        )
    else:
        c = Controller(
            process=process,
            project=project,
            network=network
        )

    c.process_command('stop')

@celery.task()
def restart_daemon(process, project, collector_id=None, network=None):
    """
    Calls a Controller to restart a daemonized STACK process
    """
    if process == 'collect':
        c = Controller(
            process=process,
            project=project,
            collector_id=collector_id
        )
    else:
        c = Controller(
            process=process,
            project=project,
            network=network
        )

    c.process_command('restart')
