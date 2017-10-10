import sys
import time
import os
import signal
import atexit

from bson.objectid import ObjectId

from models import DB
from app import app

# TODO - dynamic import
from twitter import ThreadedCollector, preprocess, mongoBatchInsert

# wd is the directory used to generate filenames for the Controller / Worker
wd = app.config['BASEDIR'] + '/app'


class Controller(object):
    """
    Controller - A class for controlling STACK processes.
    Calls the Process() class to start and stop STACK processes.
    """

    def __init__(self, process, cmdline=False, home_dir='.', umask=022, verbose=1, **kwargs):

        self.process = process
        self.cmdline = cmdline
        self.usage_message = 'controller collect|process|insert start|stop|restart project_id collector_id'

        self.home_dir = home_dir
        self.umask = umask
        self.verbose = verbose


    def get_project_db(self):
        # Project account DB connection
        self.db = DB()
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

        project_info = self.db.get_project_detail(self.project_id)
        configdb = project_info['project_config_db']
        project_config_db = self.db.connection[configdb]
        self.projectdb = project_config_db.config

        # Loads info for process based on type: collector, processor, inserter
        if self.process in ['process', 'insert']:
            # Only module type needed for processor / inserter
            self.module = kwargs['network']
            self.collector_id = None
            # Set name for worker based on gathered info
            self.process_name = self.project_name + '-' + self.process + '-' + self.module + '-' + self.project_id
        elif self.process == 'collect':
            # For collectors, also grabs: collector_id, api, collector_name
            self.collector_id = kwargs['collector_id']

            resp = self.db.get_collector_detail(self.project_id, self.collector_id)
            if resp['status']:
                collector = resp['collector']
                self.module = collector['network']
                self.api = collector['api']
                self.collector_name = collector['collector_name']
            else:
                print 'Collector (ID: %s) not found!' % self.collector_id
                print ''
                print 'USAGE: python %s %s' % (sys.argv[0], self.usage_message)
                sys.exit(1)

            # Set name for worker based on gathered info
            self.process_name = self.project_name + '-' + self.collector_name + '-' + self.process + '-' + self.module + \
                                '-' + self.collector_id

        # Sets out directories
        self.piddir = app.config['LOGDIR'] + '/' + self.project_name + '-' + self.project_id + '/pid'
        self.logdir = app.config['LOGDIR'] + '/' + self.project_name + '-' + self.project_id + '/logs'
        self.stddir = app.config['LOGDIR'] + '/' + self.project_name + '-' + self.project_id + '/std'

        # Sets data dirs
        # TODO - deprecate w/ Facebook
        self.rawdir = app.config[
                          'DATADIR'] + '/' + self.project_name + '-' + self.project_id + '/' + self.module + '/raw'
        self.archdir = app.config['DATADIR'] + '/' + self.project_name + '-' + self.project_id + '/' + self.module + \
                       '/archive'
        self.insertdir = app.config['DATADIR'] + '/' + self.project_name + '-' + self.project_id + '/' + self.module + \
                         '/insert_queue'

        # Creates dirs if they don't already exist
        if not os.path.exists(self.piddir): os.makedirs(self.piddir)
        if not os.path.exists(self.stddir): os.makedirs(self.stddir)

        # These directories only need be created for Twitter
        # TODO - deprecate w/ Facebook
        if self.module == 'twitter':
            if not os.path.exists(self.logdir): os.makedirs(self.logdir)
            if not os.path.exists(self.rawdir): os.makedirs(self.rawdir)
            if not os.path.exists(self.archdir): os.makedirs(self.archdir)
            if not os.path.exists(self.insertdir): os.makedirs(self.insertdir)

        # Sets outfiles
        self.pidfile = self.piddir + '/%s.pid' % self.process_name
        self.stdout = self.stddir + '/%s-stdout.txt' % self.process_name
        self.stderr = self.stddir + '/%s-stderr.txt' % self.process_name
        self.stdin = self.stddir + '/%s-stdin.txt' % self.process_name

        # Creates the std files for the daemon
        if not os.path.isfile(self.stdout):
            create_file = open(self.stdout, 'w')
            create_file.close()
        if not os.path.isfile(self.stdin):
            create_file = open(self.stdin, 'w')
            create_file.close()
        if not os.path.isfile(self.stderr):
            create_file = open(self.stderr, 'w')
            create_file.close()

    def process_command(self, cmd):
        """
        Prases the passed command (start / stop / restart) and initiates daemonization
        """
        # Makes sure the command is relevant
        if self.cmdline and cmd not in ['start', 'stop', 'restart']:
            print 'Invalid command: %s' % cmd
            print ''
            print 'USAGE: python %s %s' % (sys.argv[0], self.usage_message)
            sys.exit(1)
        elif cmd == 'start':
            self.start()
        elif cmd == 'stop':
            self.stop()
        elif cmd == 'restart':
            self.restart()
        else:
            print 'USAGE: python %s %s' % (sys.argv[0], self.usage_message)
            if self.cmdline:
                sys.exit(1)

    def start(self):
        """
        Method that starts the daemon process
        """
        if 'status' in resp and resp['status']:
            print 'Flags set.'

            # Check to see if running based on pidfile
            pid = self.get_pid()
            if pid:
                message = "pidfile %s already exists. Is it already running?\n"
                sys.stderr.write(message % self.pidfile)
                sys.exit(1)

            # Start the daemon
            self.daemonize()
            self.run()
        else:
            print 'Failed to successfully set flags, try again.'

        get_project_db(self)
        print 'Initializing the STACK daemon: %s' % self.process_name

        # Sets flags for given process
        resp = ''
        if self.process == 'collect':
            resp = self.db.set_collector_status(self.project_id, self.collector_id, collector_status=1)
        elif self.process == 'process':
            resp = self.db.set_network_status(self.project_id, self.module, run=1, process=True)
        elif self.process == 'insert':
            resp = self.db.set_network_status(self.project_id, self.module, run=1, insert=True)



    def stop(self):
        """
        Method that sets flags and stops the daemon process
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
                resp = self.db.set_network_status(self.project_id, self.module, run=0, process=True)
                active = module_conf['processor_active']
            else:
                resp = self.db.set_network_status(self.project_id, self.module, run=0, insert=True)
                active = module_conf['inserter_active']

        # TODO - mongo error handling
        if resp['status']:
            print 'Step 1 complete.'

        # If the daemon has already stopped, then set flags and break
        pid = self.get_pid()
        if not pid:
            print "STACK daemon already terminated."

            # Extra clean up, just in case
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)

            if self.process in ['process', 'insert']:
                if self.process == 'process':
                    self.projectdb.update({'module': self.module}, {'$set': {'processor_active': 0}})
                else:
                    self.projectdb.update({'module': self.module}, {'$set': {'inserter_active': 0}})
            else:
                self.projectdb.update({'_id': ObjectId(self.collector_id)}, {'$set': {'active': 0}})

            return

        # Step 2) Check for task / STACK process completion; loops through 15 times to check

        print 'Step 2) Check for STACK process completion and shutdown the daemon.'

        wait_count = 0
        while active == 1:
            wait_count += 1

            if self.process in ['process', 'insert']:
                module_conf = self.projectdb.find_one({'module': self.module})
                if self.process == 'process':
                    active = module_conf['processor_active']
                else:
                    active = module_conf['inserter_active']
            else:
                collector_conf = self.projectdb.find_one({'_id': ObjectId(self.collector_id)})
                active = collector_conf['active']

            print 'Try %d / 15' % wait_count
            print 'Active Status: %d' % active
            print 'Trying again in 5 seconds.'
            print ''

            if wait_count > 15:
                break

            time.sleep(5)

        # Get the pid from the pidfile
        pid = self.get_pid()
        if not pid:
            print "Daemon successfully stopped via thread termination."

            # Just to be sure. A ValueError might occur if the PID file is
            # empty but does actually exist
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)

            return  # Not an error in a restart

        # Try killing the daemon process
        print 'Daemon still running w/ loose thread. Stopping now...'

        try:
            i = 0
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
                i = i + 1
                if i % 10 == 0:
                    os.kill(pid, signal.SIGHUP)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

        # Had to kill the daemon, so set the active status flag accordingly.
        if self.process in ['process', 'insert']:
            if self.process == 'process':
                self.projectdb.update({'module': self.module}, {'$set': {'processor_active': 0}})
            else:
                self.projectdb.update({'module': self.module}, {'$set': {'inserter_active': 0}})
        else:
            self.projectdb.update({'_id': ObjectId(self.collector_id)}, {'$set': {'active': 0}})

        print 'Stopped.'

    def restart(self):
        """
        Simple restart of the daemon
        """
        # TODO - restart w/out shutting down daemon as part of extensible processor modules
        self.stop()
        self.start()

    def run(self):
        """
        Calls the process logic scripts and runs
        """
        # Backwards compatibility for older Twitter scripts
        if self.module == 'twitter':
            if self.process == 'collect':
                ThreadedCollector.go(self.api, self.project_id, self.collector_id, self.rawdir, self.logdir)
            elif self.process == 'process':
                preprocess.go(self.project_id, self.rawdir, self.archdir, self.insertdir, self.logdir)
            elif self.process == 'insert':
                mongoBatchInsert.go(self.project_id, self.rawdir, self.insertdir, self.logdir)
        # New approach via extensible collectors
        else:
            # Dynamically import collect from
            os.chdir(app.config['BASEDIR'])

            if self.process == 'collect':
                _temp = __import__('app.%s.collect' % self.module, globals(), locals(), ['Collector'], -1)
                Collector = _temp.Collector

                c = Collector(self.project_id, self.collector_id, self.process_name)
                c.go()
            elif self.process == 'process':
                _temp = __import__('app.%s.process' % self.module, globals(), locals(), ['Processor'], -1)
                Processor = _temp.Processor

                c = Processor(self.project_id, self.process_name, self.module)
                c.go()
            elif self.process == 'insert':
                _temp = __import__('app.%s.insert' % self.module, globals(), locals(), ['Inserter'], -1)
                Inserter = _temp.Inserter

                c = Inserter(self.project_id, self.process_name, self.module)
                c.go()

    def daemonize(self):
        """
        Do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write(
                "fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # Decouple from parent environment
        os.chdir(self.home_dir)
        os.setsid()
        os.umask(self.umask)

        # Do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write(
                "fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r+')
        so = file(self.stdout, 'a+')
        if self.stderr:
            se = file(self.stderr, 'a+', 0)
        else:
            se = so

        if self.cmdline:
            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())

        sys.stderr.flush()
        sys.stdout.flush()

        def sigtermhandler(signum, frame):
            self.daemon_alive = False
            signal.signal(signal.SIGTERM, sigtermhandler)
            signal.signal(signal.SIGINT, sigtermhandler)

        if self.verbose >= 1:
            print "Started"

        # Write pidfile
        atexit.register(
            self.delpid)  # Make sure pid file is removed if we quit
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def get_pid(self):
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        except SystemExit:
            pid = None
        return pid