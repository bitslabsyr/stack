import os

def pid_alive(pid):
    """
    Uses OS Kill signal 0 to check if the process with given pid is running
    Via - http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid
    """
    try:
        os.kill(pid, 0)
    except OSError:
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
        return pid_alive(pid)
    except IOError:
        return False
    except SystemExit:
        return False
