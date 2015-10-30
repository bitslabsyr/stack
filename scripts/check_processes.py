import os
import subprocess
import re

def pid_alive(pid):
    """
    Uses subprocess to check for active processes
    http://stackoverflow.com/questions/7647167/check-if-a-process-is-running-in-python-in-linux-unix
    """
    ps = subprocess.Popen('ps -ef | grep {}'.format(pid), shell=True, stdout=subprocess.PIPE)
    output = ps.stdout.read()
    ps.stdout.close()
    ps.wait()

    if re.search(str(pid), output) is None:
        return False
    else:
        return True

def check_process_pid(pidfile):
    """
    A) If the pidfile doesn't exist, return false
    B) If the pidfile exists, call pid_alive to check if process is actually running
    """
    try:
        pf = file(pidfile, 'r')
        pid = int(pf.read().strip())
        pf.close()
        print pid
        return pid_alive(pid)
    except IOError as e:
        print 'IOError on pidfile read'
        print e
        return False
    except SystemExit:
        return False
