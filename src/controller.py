import sys, time

from twitter import ThreadedCollector
from daemon import Daemon

class MyDaemon(Daemon):

    def __init__(self, script_type, script, pidfile, stdin, stdout, stderr,
        home_dir='.', umask=022, verbose=1):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.home_dir = home_dir
        self.verbose = verbose
        self.umask = umask
        self.daemon_alive = True

        self.script_type = script_type
        self.script = script

    def run(self):
        if script_type in ['run', 'process', 'collect']:
            self.script.start()
        elif script_type == 'collect':
            self.script.collect()
        else:
            print 'Unrecognized process type!'
            sys.exit(1)

class Controller():

    def __init__(self, module, run_script, process_script, insert_script):
        self.module = module
        self.run_script = run_script
        self.collect_script = run_script
        self.process_script = process_script
        self.insert_script = insert_script

    def run():
        rund = MyDaemon(script_type='run',
            script=self.run_script,
            pidfile='/tmp/daemon-example.pid',
            stdout='/Users/Billy/BITS/SoMeToolkit/src/out/out.txt',
            stdin='/Users/Billy/BITS/SoMeToolkit/src/out/in.txt',
            stderr='/Users/Billy/BITS/SoMeToolkit/src/out/err.txt')

        if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                rund.start()
            elif 'stop' == sys.argv[1]:
                rund.stop()
            elif 'restart' == sys.argv[1]:
                rund.restart()
            else:
                print 'Unknown command!'
                sys.exit(2)
            sys.exit(0)
        else:
            print 'usage: %s start|stop|restart' % sys.argv[0]
            sys.exit(2)

    def collect(self):
        collectd = MyDaemon(script_type='collect',
            script=self.collect_script,
            pidfile='/tmp/daemon-example.pid',
            stdout='/Users/Billy/BITS/SoMeToolkit/src/out/out.txt',
            stdin='/Users/Billy/BITS/SoMeToolkit/src/out/in.txt',
            stderr='/Users/Billy/BITS/SoMeToolkit/src/out/err.txt')

        if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                collectd.start()
            elif 'stop' == sys.argv[1]:
                collectd.stop()
            elif 'restart' == sys.argv[1]:
                collectd.restart()
            else:
                print 'Unknown command!'
                sys.exit(2)
            sys.exit(0)
        else:
            print 'usage: %s start|stop|restart' % sys.argv[0]
            sys.exit(2)

    def process(self):
        processd = MyDaemon(script_type='process',
            script=self.process_script,
            pidfile='/tmp/daemon-example.pid',
            stdout='/Users/Billy/BITS/SoMeToolkit/src/out/out.txt',
            stdin='/Users/Billy/BITS/SoMeToolkit/src/out/in.txt',
            stderr='/Users/Billy/BITS/SoMeToolkit/src/out/err.txt')

        if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                processd.start()
            elif 'stop' == sys.argv[1]:
                processd.stop()
            elif 'restart' == sys.argv[1]:
                processd.restart()
            else:
                print 'Unknown command!'
                sys.exit(2)
            sys.exit(0)
        else:
            print 'usage: %s start|stop|restart' % sys.argv[0]
            sys.exit(2)

    def insert(self):
        insertd = MyDaemon(script_type='insert',
            script=self.insert_script,
            pidfile='/tmp/daemon-example.pid',
            stdout='/Users/Billy/BITS/SoMeToolkit/src/out/out.txt',
            stdin='/Users/Billy/BITS/SoMeToolkit/src/out/in.txt',
            stderr='/Users/Billy/BITS/SoMeToolkit/src/out/err.txt')

        if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                insertd.start()
            elif 'stop' == sys.argv[1]:
                insertd.stop()
            elif 'restart' == sys.argv[1]:
                insertd.restart()
            else:
                print 'Unknown command!'
                sys.exit(2)
            sys.exit(0)
        else:
            print 'usage: %s start|stop|restart' % sys.argv[0]
            sys.exit(2)
