import os
import subprocess
from app import celery, app
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


def start_workers():
    """
    Starts two Celery workers on app spin up

    -- 1) Handles starting of all STACK processes
    -- 2) Handles stoping of all STACK processes
    """
    base_command = 'celery multi start '

    # Worker names
    start_worker = 'stack-start'
    stop_worker = 'stack-stop'

    # Directories for log and pid information
    outdir = app.config['LOGDIR'] + '/app'
    piddir = outdir + '/pid'
    logdir = outdir + '/log'

    # Filenames
    start_logfile = logdir + '/%s.log' % start_worker
    stop_logfile = logdir + '/%s.log' % stop_worker
    start_pidfile = piddir + '/%s.pid' % start_worker
    stop_pidfile = piddir + '/%s.pid' % stop_worker

    # Creates directories if they don't exist
    if not os.path.exists(piddir):
        os.makedirs(piddir)
    if not os.path.exists(logdir):
        os.makedirs(logdir)

    start_pid = get_pid(start_pidfile)
    stop_pid = get_pid(stop_pidfile)

    # Completes the command syntax to spin up the workers
    if not start_pid:
        start_worker_cmd = base_command + '%s-worker -A app.celery -l info -Q %s --logfile=%s --pidfile=%s' % \
                                          (start_worker, start_worker, start_logfile, start_pidfile)
        subprocess.call(start_worker_cmd.split(' '))

    if not stop_pid:
        stop_worker_cmd = base_command + '%s-worker -A app.celery -l info -Q %s --logfile=%s --pidfile=%s' % \
                                        (stop_worker, stop_worker, stop_logfile, stop_pidfile)
        subprocess.call(stop_worker_cmd.split(' '))


def get_pid(pidfile):
    try:
        pf = file(pidfile, 'r')
        pid = int(pf.read().strip())
        pf.close()
    except IOError:
        pid = None
    except SystemExit:
        pid = None
    return pid