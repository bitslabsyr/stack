import sys, time, os
import importlib
from bson.objectid import ObjectId

from models import DB
from app import app, celery

# TODO - dynamic import
from twitter import ThreadedCollector, preprocess, mongoBatchInsert

wd = BASEDIR + '/app'

class Worker(object):
    """
    Worker - A class for creating / controlling STACK Celery workers

    Worker.start(), Worker.stop(), Worker.restart():
    >> Set database flags and init processes from network submodules
    >> Start / stop Celery workers for the given processes

    Worker.run()
    >> A Celery task that async. runs the network process
    """

    def __init__(self):
        pass

    def start(self):
        """
        Sets flags and creates the Celery worker
        """

    def stop(self):
        """
        Sets flags and stops the Celery worker
        """

    def restart(self):
        """
        Calls start, then stop

        TODO - Update without fully stopping the collector
        """

    @celery.task
    def _run(self):
        """
        Runs the process async
        """

class Controller(object):
    """
    Controller - A class for controlling STACK processes. Calls Worker() to
    instantiate processes.
    """

    def __init__(self, process, cmdline=False, **kwargs):
        self.db = DB()
        self.process = process
        self.usage_message = 'controller collect|process|insert start|stop|restart project_id collector_id'

        if cmdline is False:
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
            self.process_name = self.project_name + '-' + self.collector_name + '-' + self.process + '-' + self.module + '-' + self.api + '-' + self.collector_id

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
        Worker = self._create()

        # Makes sure the command is relevant
        if self.cmdline and cmd not in ['start', 'stop', 'restart']:
            print 'Invalid command: %s' % cmd
            print ''
            print 'USAGE: python %s %s' % (sys.argv[0], self.usage_message)
            sys.exit(1)
        elif cmd == 'start':
            Worker.start(self.api)
        elif cmd == 'stop':
            Worker.stop()
        elif cmd == 'restart':
            Worker.stop()
            Worker.start(self.api)
        else:
            print 'USAGE: python %s %s' % (sys.argv[0], self.usage_message)
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
        archdir = app.config['DATADIR'] + '/' + self.project_name + '-' + self.project_id + '/' + self.module + '/archive'
        insertdir = app.config['DATADIR'] + '/' + self.project_name + '-' + self.project_id + '/' + self.module + '/insert_queue'

        # Creates dirs if they don't already exist
        if not os.path.exists(piddir)       : os.makedirs(piddir)
        if not os.path.exists(logdir)       : os.makedirs(logdir)
        if not os.path.exists(stddir)       : os.makedirs(stddir)
        if not os.path.exists(rawdir)       : os.makedirs(rawdir)
        if not os.path.exists(archdir)      : os.makedirs(archdir)
        if not os.path.exists(insertdir)    : os.makedirs(insertdir)

        # Sets outfiles
        pidfile = piddir + '/' + self.process_name + '-worker.pid'
        logfile = logdir + '/' + self.process_name + '-log.out'
        stdfile = stddir + '/' + self.process_name + '-stdout.txt'

        # TODO - datafile format based on Mongo stored rollover rate
        # datafile = rawdir + '/' + timestr + '-' + self.process_name + ...

        # Creates outfiles
        if not os.path.isfile(pidfile):
            create_file = open(pidfile, 'w')
            create_file.close()
        if not os.path.isfile(logfile):
            create_file = open(logfile, 'w')
            create_file.close()
        if not os.path.isfile(stdfile):
            create_file = open(stdfile, 'w')
            create_file.close()

        # Creates Worker object
        Worker = Worker(
            name=self.process_name,
            process=self.process,
            pidfile=pidfile,
            logfile=logfile,
            stdfile=stdfile
        )

        return Worker
