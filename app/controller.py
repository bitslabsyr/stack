import sys, time, os
import importlib
from subprocess import call

from bson.objectid import ObjectId
from celery.contrib.methods import task_method

from models import DB
from app import app, celery
from twitter import ThreadedCollector

# TODO - dynamic import
# from twitter import ThreadedCollector, preprocess, mongoBatchInsert

wd = app.config['BASEDIR'] + '/app'

# TODO - move raw file directories to Controller extensible base class
@celery.task()
def _run(api, process, project_id, collector_id=None, rawdir=None, archdir=None, insertdir=None, logdir=None):
    """
    Runs the process async
    """
    if process == 'collect':
        ThreadedCollector.go(api, project_id, collector_id, rawdir, logdir)


class Worker(object):
    """
    Worker - A class for creating / controlling STACK Celery workers

    Worker.start(), Worker.stop(), Worker.restart():
    >> Set database flags and init processes from network submodules
    >> Start / stop Celery workers for the given processes

    Worker.run()
    >> A Celery task that async. runs the network process
    """

    def __init__(self, name, module, process, pidfile, logfile, stdfile, rawdir, archdir, insertdir, logdir, project_id,
                 collector_id):
        # Worker info instance vars
        self.name = name  # Unique name (used here for the worker)
        self.module = module
        self.process = process
        self.project_id = project_id
        self.collector_id = collector_id

        # File info
        self.rawdir = rawdir
        self.archdir = archdir
        self.insertdir = insertdir
        self.logdir = logdir
        self.pidfile = pidfile
        self.logfile = logfile
        self.stdfile = stdfile

        # DB connection
        self.db = DB()

        # Project account DB connection
        project_info = self.db.get_project_detail(self.project_id)
        configdb = project_info['project_config_db']
        project_config_db = self.db.connection[configdb]
        self.projectdb = project_config_db.config

        # TODO - dynamic naming
        if self.process == 'collect':
            script = 'ThreadedCollector'
        elif self.process == 'process':
            script = 'preprocess'
        elif self.process == 'insert':
            script = 'mongoBatchInsert'

        # Import scripts
        # TODO - error logging
        try:
            self.worker_process = importlib.import_module('stack.app.%s.%s' % (self.module, script))
        except ImportError, error:
            print error

    def start(self, api=None):
        """
        Sets flags and creates the Celery worker
        """
        print 'Initializing the Celery worker: %s' % self.name

        # Sets flags for given process
        resp = ''
        if self.process == 'collect':
            resp = self.db.set_collector_status(self.project_id, self.collector_id, collector_status=1)
        elif self.process == 'process':
            resp = self.db.set_network_status(self.project_id, self.module, run=1, process=True)
        elif self.process == 'insert':
            resp = self.db.set_network_status(self.project_id, self.module, run=1, insert=True)

        if 'status' in resp and resp['status']:
            print 'Flags set. Now initializing Celery worker.'

            # Starts worker with name and queue based on project name
            # >> A Celery queue with name self.name will be created dynamically
            # >> So will a corresponding route upon a routed task
            start_command = 'celery multi start %s-worker -A app.celery -l info -Q %s --logfile=%s --pidfile=%s' % \
                            (self.name, self.name, self.stdfile, self.pidfile)

            print start_command
            call(start_command.split(' '))

            # Calls task to start
            # TODO - dynamic import
            task_args = {
                'api': api,
                'process': self.process,
                # 'worker_process': ThreadedCollector,
                'project_id': self.project_id,
                'collector_id': self.collector_id,
                'rawdir': self.rawdir,
                'archdir': self.archdir,
                'insertdir': self.insertdir,
                'logdir': self.logdir
            }
            task = _run.apply_async(kwargs=task_args, queue=self.name)

            # Records ID for state check
            # TODO - Mongo exceptions
            # TODO - IDs for non-collectors
            task_id = task.id
            if self.process == 'collect':
                self.projectdb.update({'_id': ObjectId(self.collector_id)}, {'$set': {'task_id': task_id}})
            elif self.process == 'process':
                self.projectdb.update({'module': self.module}, {'$set': {'processor': {'task_id': task_id}}})
            else:
                self.projectdb.update({'module': self.module}, {'$set': {'inserter': {'task_id': task_id}}})
        else:
            print 'Failed to successfully set flags, try again.'

    def stop(self):
        """
        Sets flags and stops the Celery worker

        """
        print 'Stop command received.'
        print 'Step 1) Setting flags on the STACK process to stop.'

        if self.process == 'collect':
            # Set flags for the STACK process to stop
            resp = self.db.set_collector_status(self.project_id, self.collector_id, collector_status=0)

            # Grab active flag from collector's Mongo document
            collector_conf = self.projectdb.find_one({'_id': ObjectId(self.collector_id)})
            active = collector_conf['active']
        else:
            module_conf = self.projectdb.find_one({'module': self.module})
            if self.process == 'process':
                resp = self.db.set_network_status(self.project_id, self.module, process=True)
                active = module_conf['processor_active']
            else:
                resp = self.db.set_network_status(self.project_id, self.module, insert=True)
                active = module_conf['inserter_active']

        # TODO - mongo error handling
        if resp['status']:
            print 'Step 1 complete.'

        # Step 2) Check for task / STACK process completion; loops through 20 times to check

        print 'Step 2) Check for STACK process completion and Celery task shutdown.'

        wait_count = 0
        while active == 1:
            wait_count += 1

            if self.process in ['process', 'insert']:
                module_conf = self.projectdb.find_one({'module': self.module})
                if self.process == 'process':
                    active = module_conf['processor_active']
                    task_id = module_conf['processor']['task_id']
                else:
                    active = module_conf['inserter_active']
                    task_id = module_conf['inserter']['task_id']
            else:
                collector_conf = self.projectdb.find_one({'_id': ObjectId(self.collector_id)})
                active = collector_conf['active']
                task_id = collector_conf['task_id']

            resp = celery.AsyncResult(task_id)

            print 'Mongo Active Status: %d' % active
            print 'Celery Task Status: %s' % resp.state

            print 'Trying again in %d seconds' % wait_count

            if wait_count > 20:
                break

            time.sleep(wait_count)

        # TODO - Kill if process hasn't stopped
        print 'Completed.'

        stop_command = 'celery multi stopwait %s-worker -A app.celery -l info -Q %s --pidfile=%s' % \
                            (self.name, self.name, self.pidfile)

        print stop_command
        call(stop_command.split(' '))

        # Reset task_id in Mongo now that we've terminated
        if self.process == 'collect':
                self.projectdb.update({'_id': ObjectId(self.collector_id)}, {'$set': {'task_id': None}})
        elif self.process == 'process':
            self.projectdb.update({'module': self.module}, {'$set': {'processor': {'task_id': None}}})
        else:
            self.projectdb.update({'module': self.module}, {'$set': {'inserter': {'task_id': None}}})

    def restart(self, api=None):
        """
        Calls start, then stop

        TODO - Update without fully stopping the collector
        """
        self.stop()
        self.start(api)


class Controller(object):
    """
    Controller - A class for controlling STACK processes. Calls Worker() to instantiate processes.
    """

    def __init__(self, process, cmdline=False, **kwargs):
        self.db = DB()
        self.process = process
        self.cmdline = cmdline
        self.usage_message = 'controller collect|process|insert start|stop|restart project_id collector_id'

        if self.cmdline is False:
            # Grab information from Flask user object
            self.project = kwargs['project']
            self.project_id = self.project['project_id']
            self.project_name = self.project['project_name']
        else:
            # Command is coming from the command line, look up info
            self.project_id = kwargs['project_id']

            resp = self.db.get_project_detail(self.project_id)
            if resp['status']:
                self.project_name = resp['project_name']
            else:
                print 'Project w/ ID %s not found!' % self.project_id
                print ''
                print 'USAGE: python %s %s' % (sys.argv[0], self.usage_message)
                sys.exit(1)

        # Loads info for process based on type: collector, processor, inserter
        if self.process in ['process', 'insert']:
            # Only module type needed for processor / inserter
            self.module = kwargs['network']
            self.collector_id = None
            # Set name for worker based on gathered info
            self.process_name = self.project_name + '-' + self.process + '-' + self.module + '-' + self.project_id
        elif process == 'collect':
            # For collectors, also grabs: collector_id, api, collector_name
            self.collector_id = kwargs['collector_id']

            resp = self.db.get_collector_detail(self.project_id, self.collector_id)
            if resp['status']:
                collector = resp['collector']
                self.module = collector['network']
                self.api = collector['api'].lower()
                self.collector_name = collector['collector_name']
            else:
                print 'Collector (ID: %s) not found!' % self.collector_id
                print ''
                print 'USAGE: python %s %s' % (sys.argv[0], self.usage_message)
                sys.exit(1)

            # Set name for worker based on gathered info
            self.process_name = self.project_name + '-' + self.collector_name + '-' + self.process + '-' + self.module +\
                '-' + self.api + '-' + self.collector_id

        # Grabs network module process scripts
        resp = self.db.get_network_detail(self.project_id, self.module)
        if resp['status']:
            network = resp['network']
            self.collector = network['collection_script']
            self.processor = network['processor_script']
            self.inserter = network['insertion_script']
        else:
            print 'Network %s not found!' % self.module
            print ''
            print 'USAGE: python %s %s' % (sys.argv[0], self.usage_message)
            sys.exit(1)

    def run(self, cmd):
        """
        Runs the Celery Worker init'd by _create()
        """
        # Creates the worker
        worker = self._create()

        # Makes sure the command is relevant
        if self.cmdline and cmd not in ['start', 'stop', 'restart']:
            print 'Invalid command: %s' % cmd
            print ''
            print 'USAGE: python %s %s' % (sys.argv[0], self.usage_message)
            sys.exit(1)
        elif cmd == 'start':
            worker.start(self.api)
        elif cmd == 'stop':
            worker.stop()
        elif cmd == 'restart':
            worker.restart(self.api)
        else:
            print 'USAGE: python %s %s' % (sys.argv[0], self.usage_message)
            if self.cmdline:
                sys.exit(1)

    def _create(self):
        """
        Creates process control object & Worker stdout paths, dirs
        """

        # Sets out directories
        piddir = app.config['LOGDIR'] + '/' + self.project_name + '-' + self.project_id + '/pid'
        logdir = app.config['LOGDIR'] + '/' + self.project_name + '-' + self.project_id + '/logs'
        stddir = app.config['LOGDIR'] + '/' + self.project_name + '-' + self.project_id + '/std'

        # Sets data dirs
        rawdir = app.config['DATADIR'] + '/' + self.project_name + '-' + self.project_id + '/' + self.module + '/raw'
        archdir = app.config['DATADIR'] + '/' + self.project_name + '-' + self.project_id + '/' + self.module + \
            '/archive'
        insertdir = app.config['DATADIR'] + '/' + self.project_name + '-' + self.project_id + '/' + self.module + \
            '/insert_queue'

        # Creates dirs if they don't already exist
        if not os.path.exists(piddir)       : os.makedirs(piddir)
        if not os.path.exists(logdir)       : os.makedirs(logdir)
        if not os.path.exists(stddir)       : os.makedirs(stddir)
        if not os.path.exists(rawdir)       : os.makedirs(rawdir)
        if not os.path.exists(archdir)      : os.makedirs(archdir)
        if not os.path.exists(insertdir)    : os.makedirs(insertdir)

        # Sets outfiles
        pidfile = piddir + '/%N.pid'
        logfile = logdir + '/' + self.process_name + '-log.out'
        stdfile = stddir + '/' + self.process_name + '-stdout.txt'

        # TODO - datafile format based on Mongo stored rollover rate
        # datafile = rawdir + '/' + timestr + '-' + self.process_name + ...

        # TODO: creates outfiles - not needed until Controller subclass
        """
        if not os.path.isfile(pidfile):
            create_file = open(pidfile, 'w')
            create_file.close()
        if not os.path.isfile(logfile):
            create_file = open(logfile, 'w')
            create_file.close()
        if not os.path.isfile(stdfile):
            create_file = open(stdfile, 'w')
            create_file.close()
        """

        # Creates Worker object
        worker = Worker(
            name=self.process_name,
            module=self.module,
            process=self.process,
            pidfile=pidfile,
            logfile=logfile,
            stdfile=stdfile,
            rawdir=rawdir,
            archdir=archdir,
            insertdir=insertdir,
            logdir=logdir,
            project_id=self.project_id,
            collector_id=self.collector_id
        )

        return worker
