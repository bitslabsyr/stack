"""
TODO

-Abstract away work w/ flags, but still use for status
"""

import sys, time, os
import importlib

from daemon import Daemon

wd = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(wd)

class Process(Daemon):

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
        self.module = module
        self.api = api

        self.collector = collector
        self.processor = processor
        self.inserter = inserter

        self.usage_message = '[network-module] run|collect|process|insert start|stop|restart'

    def run(self, process, command):
        if process == 'run': self.initiate(command)
        if process == 'collect': self.collect()
        if process == 'process': self.process(command)
        if process == 'insert': self.insert(command)

    # Initiates the collector script for the given network API
    def initiate(self, command):
        pidfile = '/tmp/' + self.module + '-' + self.api + '-collector-daemon.pid'
        stdout = wd + '/out/' + self.module + '-' + self.api + '-collector-out.txt'
        stdin = wd + '/out/' + self.module + '-' + self.api + '-collector-in.txt'
        stderr = wd + '/out/' + self.module + '-' + self.api + '-collector-err.txt'

        rund = Process(module=self.module,
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

        processd = Process(module=self.module,
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

        insertd = Process(module=self.module,
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
