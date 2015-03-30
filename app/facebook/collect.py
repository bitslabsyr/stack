import threading

from app.processes import BaseCollector

e = threading.Event()


class CollectionThread(object):
    """
    Class to handle the connection to the Facebook API
    """
    def __init__(self, Collector):
        self.c = Collector


class Collector(BaseCollector):
    """
    Extension of the STACK Collector for Facebook
    """
    def __init__(self, project_id, collector_id, process_name):
        BaseCollector.__init__(self, project_id, collector_id, process_name)

    def go(self):
        """
        Function to be called by the Controller to start the threaded collection. go() in turn
        uses processes.Collector to initiate, log, write, etc.
        """
        # Checks if we're supposed to be running
        run_flag = self.check_flag()['run']
        if run_flag:
            self.log('Starting Facebook collector %s with signal %d' % (self.process_name, run_flag))
        collecting_data = False

        thread_counter = 0

        # If run_flag is set - begin the loop
        while run_flag:
            pass

        self.log('Exiting Facebook collection.')
        self.set_active(0)