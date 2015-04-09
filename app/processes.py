import os
import logging
import time
import json
import threading

from bson.objectid import ObjectId

from models import DB
from app import app


class BaseCollector(object):
    """
    Extensible base class for all STACK collectors
    """

    def __init__(self, project_id, collector_id, process_name):
        self.project_id = project_id
        self.collector_id = collector_id
        self.process_name = process_name

        # Sets up connection w/ project config DB & loads in collector info
        self.db = DB()

    def setup(self):
        """
        Called by the controller to start the Collector - called by go()
        """
        project = self.db.get_project_detail(self.project_id)
        if project['status']:
            self.project_name = project['project_name']

            configdb = project['project_config_db']
            self.project_db = configdb.config

        resp = self.db.get_collector_detail(self.project_id, self.collector_id)
        if resp['status']:
            collector_info = resp['collector']

            # Load in collector info
            self.collector_name = collector_info['collector_name']
            self.network = collector_info['network']
            self.api = collector_info['api']
            self.collection_type = collector_info['collection_type']
            self.terms_list = collector_info['terms_list']
            self.languages = collector_info['languages']
            self.locations = collector_info['location']
            self.auth = collector_info['api_auth']
            # TODO - file format to Mongo
            # TODO - less then hour = warning
            self.file_format = '%Y%m%d-%H'

        # If this is a streaming collector
        if self.collection_type == 'realtime':
            self.project_db.update({'_id': ObjectId(self.collector_id)}, {'$set': {'stream_limits': []}})

        # Sets up logdir and logging
        logdir = app.config['LOGDIR'] + '/' + self.project_name + '-' + self.project_id + '/logs'
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        # Sets logger w/ name collector_name and level INFO
        self.logger = logging.getLogger(self.collector_name)
        self.logger.setLevel(logging.INFO)

        # Sets up logging file handler
        logfile = logdir + '/%s.log' % self.process_name
        # TODO - logging params
        # TODO - port logging rotation params to Mongo for user control later / these default values good
        handler = logging.handlers.TimedRotatingFileHandler(logfile, when='D', backupCount=30)
        handler.setLevel(logging.INFO)
        # Formats
        format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        dateformat = '%m-%d %H:%M'
        formatter = logging.Formatter(format, dateformat)
        handler.setFormatter(formatter)
        # Adds handler to logger to finish
        self.logger.addHandler(handler)

        self.log('STACK collector %s initiated.' % self.collector_name)

        # Sets up rawdir
        self.rawdir = app.config['DATADIR'] + '/' + self.project_name + '-' + self.project_id + '/' + self.network + '/raw'
        if not os.path.exists(self.rawdir):
            os.makedirs(self.rawdir)

        self.log('All raw files and directories set. Now starting collector...')

    def go(self):
        """
        Starts and maintains the loop that monitors the collection thread.
        Threads are maintained in the extended versions of the class
        """
        # First, set things up
        self.setup()

        # Checks if we're supposed to be running
        self.run_flag = self.check_flags()['run']
        self.collect_flag = 0
        self.update_flag = 0

        if self.run_flag:
            self.log('Starting Facebook collector %s with signal %d' % (self.process_name, self.run_flag))
        self.collecting_data = False

        thread_counter = 0

        # If run_flag is set - begin the loop
        while self.run_flag:
            try:
                flags = self.check_flags()
                self.run_flag = flags['run']
                self.collect_flag = flags['collect']
                self.update_flag = flags['update']
            except Exception as e:
                self.log('Mongo connection refused with exception: %s' % e, level='warn')

            # If we've been flagged to stop or update and we're collecting - shut it down
            if self.collecting_data and (self.update_flag or not self.collect_flag or not self.run_flag):
                self.stop_thread()

            # If we've been flagged to start and we're not collecting - start it up
            if self.collect_flag and threading.activeCount() == 1:
                self.start_thread()

            time.sleep(2)

        self.log('Exiting Facebook collection.')
        self.set_active(0)

    def write(self, data):
        """
        Called to write raw data to raw file - handles rotation
        """
        timestr = time.strftime(self.file_format)
        filename = self.rawdir + timestr + '-' + self.collector_name + '-' + self.collector_id + '-out.json'
        if not os.path.isfile(filename):
            self.log('Creating new raw file: %s' % filename)

        with open(filename, 'a') as rawfile:
            rawfile.write(json.dumps(data).encode('utf-8'))
            rawfile.write('\n')

    def log(self, message, level='info', thread='MAIN:'):
        """
        Logs messages to process logfile
        """
        if level == 'warn':
            self.logger.warning(thread + ' ' + message)
        elif level == 'error':
            self.logger.error(thread + ' ' + message)
        else:
            self.logger.info(thread + ' ' + message)

    def check_flags(self):
        """
        Quick method to grab and return all Mongo flags for given Collector instance
        """

        resp = self.db.get_collector_detail(self.project_id, self.collector_id)
        collector = resp['collector']

        return {
            'run': collector['collector']['run'],
            'collect': collector['collector']['collect'],
            'update': collector['collector']['update'],
            'active': collector['active']
        }

    def set_active(self, active):
        """
        Quick method to set the active flag to 1 or 0
        """
        self.project_db.update({'_id': ObjectId(self.collector_id)}, {'set': {'active': 0}})

    def start_thread(self):
        """
        Modify this method when extending the class to manage the actual collection thread
        """

    def stop_thread(self):
        """
        Modify this method when extending the class to stop the collection thread
        """


class BaseProcessor(object):
    pass
    # TODO - zip up archived raw files


class BaseInserter(object):
    pass
