import subprocess
import sys
import logging
import os

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/stack/")

from app import app

app.secret_key = os.urandom(24)

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

    # Completes the command syntax to spin up the workers
    start_worker_cmd = base_command + '%s-worker -A app.celery -l info -Q %s --logfile=%s --pidfile=%s' % \
                                      (start_worker, start_worker, start_logfile, start_pidfile)
    stop_worker_cmd = base_command + '%s-worker -A app.celery -l info -Q %s --logfile=%s --pidfile=%s' % \
                                      (stop_worker, stop_worker, stop_logfile, stop_pidfile)

    # Makes the call to start the workers
    subprocess.call(start_worker_cmd.split(' '))
    subprocess.call(stop_worker_cmd.split(' '))