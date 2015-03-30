import threading
import time

from app.processes import BaseCollector

e = threading.Event()


class CollectionListener(object):
    """
    Class to handle the connection to the Facebook API
    """
    def __init__(self, Collector):
        self.c = Collector

    def run(self):
        """
        Facebook listener loop
        """


class Collector(BaseCollector):
    """
    Extension of the STACK Collector for Facebook
    """
    def __init__(self, project_id, collector_id, process_name):
        BaseCollector.__init__(self, project_id, collector_id, process_name)
        self.thread_count = 0
        self.thread_name = ''

        self.l = None
        self.l_thread = None

    def start_thread(self):
        """
        Starts the CollectionThread()
        """
        self.thread_count += 1
        self.thread_name = self.collector_name + '-thread%d' % self.thread_count

        # TODO - Facebook terms handling

        # Sets up thread
        self.l = CollectionListener(self)
        self.l_thread = threading.Thread(name=self.thread_name, target=self.l.run)
        self.l_thread.start()

        self.collecting_data = True
        self.log('Started Facebook listener thread: %s' % self.thread_name)

    def stop_thread(self):
        """
        Stops the CollectionThread()
        """
        if self.update_flag:
            self.log('Received UPDATE signal. Attempting to restart collection thread.')
            self.db.set_collector_status(self.project_id, self.collector_id, update_status=1)
        if not self.collect_flag or not self.run_flag:
            self.log('Received STOP/EXIT signal. Attempting to stop collection thread.')
            self.db.set_colllector_status(self.project_id, self.collector_id, collector_status=0)
            self.collect_flag = 0

        e.set()
        wait_count = 0
        while self.l_thread.isAlive():
            wait_count += 1
            self.log('%d) Waiting on Facebook listener thread shutdown.' % wait_count)
            time.sleep(wait_count)

        self.collecting_data = False

        # TODO - Facebook count, limit, error logging