import sys, time, os

from daemon import Daemon

wd = os.getcwd()

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
            scriptd = __import__('%s.%s' % (self.module, self.script),
                fromlist='.')
        except ImportError:
            print 'Failed to import modules.'
            sys.exit(1)

    def run(self, *args, **kwargs):
        if process in ['run', 'process', 'insert']:
            self.scriptd.start(*args, **kwargs)
        elif process == 'collect':
            self.scriptd.collect(*args, **kwargs)
        else:
            print 'Unrecognized process type!'
            sys.exit(1)

class Controller():

    def __init__(self, module, run_script, process_script, insert_script, **kwargs):
        self.module = module
        self.run_script = run_script
        self.process_script = process_script
        self.insert_script = insert_script

        self.kwargs = kwargs

        self.usage_message = '[network-module] run|collect|process|insert start|stop|restart'

    def run(self, command):
        rund = Process(module=self.module,
            process='run',
            script=self.run_script,
            pidfile=wd + '/tmp/' + self.module + '-run-daemon.pid',
            stdout=wd + '/out/' + self.module + '-run-out.txt',
            stdin=wd + '/out/' + self.module + '-run-in.txt',
            stderr=wd + '/out/' + self.module + '-run-err.txt'
        )

        if command not in ['start', 'stop', 'restart']:
            print 'Invalid command: %s' % command
            print 'USAGE: %s %s' % (sys.argv[0], self.usage_message)
        elif command == 'start':
            rund.start(self.kwargs)
        elif command == 'stop':
            rund.stop()
        elif command == 'restart':
            rund.restart()
        else:
            print 'USAGE: %s %s' % (sys.argv[0], self.usage_message)

    def collect(self):
        """
        Work w/ Mongo flag to start collection thread
        """

    def process(self, command):
        processd = Process(module=self.module,
            process='process',
            script=self.run_script,
            pidfile=wd + '/tmp/' + self.module + '-process-daemon.pid',
            stdout=wd + '/out/' + self.module + '-process-out.txt',
            stdin=wd + '/out/' + self.module + '-process-in.txt',
            stderr=wd + '/out/' + self.module + '-process-err.txt'
        )

        if command not in ['start', 'stop', 'restart']:
            print 'Invalid command: %s' % command
            print 'USAGE: %s %s' % (sys.argv[0], self.usage_message)
        elif command == 'start':
            rund.start(self.kwargs)
        elif command == 'stop':
            rund.stop()
        elif command == 'restart':
            rund.restart()
        else:
            print 'USAGE: %s %s' % (sys.argv[0], self.usage_message)

    def insert(self, command):
        insertd = Process(module=self.module,
            process='process',
            script=self.run_script,
            pidfile=wd + '/tmp/' + self.module + '-process-daemon.pid',
            stdout=wd + '/out/' + self.module + '-process-out.txt',
            stdin=wd + '/out/' + self.module + '-process-in.txt',
            stderr=wd + '/out/' + self.module + '-process-err.txt'
        )

        if command not in ['start', 'stop', 'restart']:
            print 'Invalid command: %s' % command
            print 'USAGE: %s %s' % (sys.argv[0], self.usage_message)
        elif command == 'start':
            rund.start(self.kwargs)
        elif command == 'stop':
            rund.stop()
        elif command == 'restart':
            rund.restart()
        else:
            print 'USAGE: %s %s' % (sys.argv[0], self.usage_message)
