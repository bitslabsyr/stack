import sys, time

from pythondaemon import Daemon

class MyDaemon(Daemon):

    def run(self):
        i = 0
        while i < 100:
            print 'Round %d' % i
            i += 1
            time.sleep(i)

def run():
    daemon = MyDaemon('/tmp/daemon-example.pid', stdout='/Users/Billy/test')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print 'Unknown command!'
            sys.exit(2)
        sys.exit(0)
    else:
        print 'usage: %s start|stop|restart' % sys.argv[0]
        sys.exit(2)
