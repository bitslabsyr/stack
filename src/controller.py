"""
TODO
    -Mongo wrapper to work w/ Controller._check_flag()
    -Use Mongo wrapper to set flags to start/stop threads
    -Use Mongo wrapper to work w/ Controller._collect()
"""

import sys, time, os, atexit, signal
import importlib

from pymongo import MongoClient

wd = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(wd)

# TODO - (temp) remove & replace w/ Mongo wrapper
connection = MongoClient()
db = connection.config
mongo_config = db.config

class ProcessDaemon(object):

    def __init__(self, module, process, script, pidfile, stdin, stdout, stderr, home_dir='.', umask=022, verbose=1):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.home_dir = home_dir
        self.verbose = verbose
        self.umask = umask
        self.daemon_alive = True

        self.module = module
        self.process = process
        self.script = script

        try:
            self.scriptd = importlib.import_module('%s.%s' % (self.module, self.script))
        except ImportError, error:
            print 'ImportError: %s' % error
            sys.exit(1)

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
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

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

    def start(self, api=None):
        """
        Start the daemon
        """
        print 'Initializing...'
        mongo_config.update({'module': 'collector-follow'},
            {'$set': {'run': 1, 'collect': 1}})

        print 'Flags set. Now starting daemon...'

        pid = self.get_pid()
        if pid:
            message = "pidfile %s already exists. Is it already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run(api)

    def stop(self):
        """
        Stop the daemon
        """
        mongo_config.update({'module': 'collector-follow'},
            {'$set': {'run': 0, 'collect': 0}})
        mconf = mongo_config.find_one({'module': 'collector-follow'})
        status = mconf['active']

        print 'Stop flags set. Waiting for thread termination.'

        wait_count = 0
        while status == 1:
            wait_count += 1
            mconf = mongo_config.find_one({'module': 'collector-follow'})
            status = mconf['active']

            if wait_count > 20:
                break

            time.sleep(wait_count)

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

        print 'Daemon still running w/ loose thread. Stopping now...'
        print 'Stopped.'

    def restart(self, *args, **kwargs):
        """
        Restart the daemon
        """
        self.stop()
        self.start(*args, **kwargs)

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

    # TODO - Use w/ Mongo wrapper
    #      - use the username + module + api to reference DB
    # For now done in the start() as manual example
    def set_flag(self):
        pass

    def run(self, api):
        if self.process in ['process', 'insert']:
            self.scriptd.start()
        elif self.process == 'run':
            self.scriptd.start(api)
        elif self.process == 'collect':
            self.scriptd.collect()
        else:
            print 'Unrecognized process type!'
            sys.exit(1)

class Controller():

    def __init__(self, module, api, collector, processor, inserter):
        # TODO - replace w/ login creds; refer to Mongo collection for DB ref.
        self.user = None

        self.module = module
        self.api = api

        self.collector = collector
        self.processor = processor
        self.inserter = inserter

        self.usage_message = '[network-module] run|collect|process|insert start|stop|restart'

    def run(self, process, command):
        if process == 'run'     : self.initiate(command)
        if process == 'collect' : self.collect()
        if process == 'process' : self.process(command)
        if process == 'insert'  : self.insert(command)

    def check_flag(self, module):
        exception = None
        try:
            mongoConfigs = mongo_config.find_one({"module" : module})
            run_flag = mongoConfigs['run']

            if module in ['collector-follow', 'collector-track']:
                collect_flag = mongoConfigs['collect']
                update_flag = mongoConfigs['update']
            else:
                collect_flag = 0
                update_flag = 0
        except Exception, exception:
            logger.info('Mongo connection refused with exception: %s' % exception)

        return run_flag, collect_flag, update_flag

    # Initiates the collector script for the given network API
    def initiate(self, command):
        pidfile = '/tmp/' + self.module + '-' + self.api + '-collector-daemon.pid'
        stdout = wd + '/out/' + self.module + '-' + self.api + '-collector-out.txt'
        stdin = wd + '/out/' + self.module + '-' + self.api + '-collector-in.txt'
        stderr = wd + '/out/' + self.module + '-' + self.api + '-collector-err.txt'

        rund = ProcessDaemon(module=self.module,
            process='run',
            script=self.collector,
            pidfile=pidfile,
            stdout=stdout,
            stdin=stdin,
            stderr=stderr
        )

        if not os.path.isfile(stdout):
            create_file = open(stdout, 'w')
            create_file.close()
        if not os.path.isfile(stdin):
            create_file = open(stdin, 'w')
            create_file.close()
        if not os.path.isfile(stderr):
            create_file = open(stderr, 'w')
            create_file.close()

        if command not in ['start', 'stop', 'restart']:
            print 'Invalid command: %s' % command
            print 'USAGE: python %s %s' % (sys.argv[0], self.usage_message)
        elif command == 'start':
            rund.start(self.api)
        elif command == 'stop':
            rund.stop()
        elif command == 'restart':
            rund.restart(self.api)
        else:
            print 'USAGE: %s %s' % (sys.argv[0], self.usage_message)

    def collect(self):
        """
        Work w/ Mongo flag to start collection thread
        """

    def process(self, command):
        pidfile = '/tmp/' + self.module + '-' + self.api + '-processor-daemon.pid'
        stdout = wd + '/out/' + self.module + '-' + self.api + '-processor-out.txt'
        stdin = wd + '/out/' + self.module + '-' + self.api + '-processor-in.txt'
        stderr = wd + '/out/' + self.module + '-' + self.api + '-processor-err.txt'

        processd = ProcessDaemon(module=self.module,
            process='process',
            script=self.processor,
            pidfile=pidfile,
            stdout=stdout,
            stdin=stdin,
            stderr=stderr
        )

        if not os.path.isfile(stdout):
            create_file = open(stdout, 'w')
            create_file.close()
        if not os.path.isfile(stdin):
            create_file = open(stdin, 'w')
            create_file.close()
        if not os.path.isfile(stderr):
            create_file = open(stderr, 'w')
            create_file.close()

        if command not in ['start', 'stop', 'restart']:
            print 'Invalid command: %s' % command
            print 'USAGE: %s %s' % (sys.argv[0], self.usage_message)
        elif command == 'start':
            processd.start()
        elif command == 'stop':
            processd.stop()
        elif command == 'restart':
            processd.restart()
        else:
            print 'USAGE: %s %s' % (sys.argv[0], self.usage_message)

    def insert(self, command):
        pidfile = '/tmp/' + self.module + '-' + self.api + '-inserter-daemon.pid'
        stdout = wd + '/out/' + self.module + '-' + self.api + '-inserter-out.txt'
        stdin = wd + '/out/' + self.module + '-' + self.api + '-inserter-in.txt'
        stderr = wd + '/out/' + self.module + '-' + self.api + '-inserter-err.txt'

        insertd = ProcessDaemon(module=self.module,
            process='process',
            script=self.inserter,
            pidfile=pidfile,
            stdout=stdout,
            stdin=stdin,
            stderr=stderr
        )

        if not os.path.isfile(stdout):
            create_file = open(stdout, 'w')
            create_file.close()
        if not os.path.isfile(stdin):
            create_file = open(stdin, 'w')
            create_file.close()
        if not os.path.isfile(stderr):
            create_file = open(stderr, 'w')
            create_file.close()

        if command not in ['start', 'stop', 'restart']:
            print 'Invalid command: %s' % command
            print 'USAGE: %s %s' % (sys.argv[0], self.usage_message)
        elif command == 'start':
            insertd.start()
        elif command == 'stop':
            insertd.stop()
        elif command == 'restart':
            insertd.restart()
        else:
            print 'USAGE: %s %s' % (sys.argv[0], self.usage_message)
