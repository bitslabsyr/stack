import threading

from app.processes import Collector

e = threading.Event()


class CollectionThread(object):
    pass


def go(project_id, collector_id, process_name):
    """
    Function to be called by the Controller to start the threaded collection. go() in turn
    uses processes.Collector to initiate, log, write, etc.
    """
    c = Collector(project_id, collector_id, process_name)

    # Checks if we're supposed to be running
    run_flag = c.check_flag()['run']
    if run_flag:
        c.log('Starting Facebook collector %s with signal %d' % (process_name, run_flag))
    collecting_data = False

    thread_counter = 0

    # If run_flag is set - begin the loop
    while run_flag:
        pass

    c.log('Exiting Facebook collection.')
    c.set_active(0)