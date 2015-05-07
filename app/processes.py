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
        self.collecting_data = False

        # Sets up connection w/ project config DB & loads in collector info
        self.db = DB()

        project = self.db.get_project_detail(self.project_id)
        if project['status']:
            self.project_name = project['project_name']

            configdb = project['project_config_db']
            project_db = self.db.connection[configdb]
            self.project_db = project_db.config

        resp = self.db.get_collector_detail(self.project_id, self.collector_id)
        if resp['status']:
            collector_info = resp['collector']

            # Load in collector info
            self.collector_name = collector_info['collector_name']
            self.network = collector_info['network']
            self.api = collector_info['api']
            self.collection_type = collector_info['collection_type']
            self.params = collector_info['params']
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
        # Checks if we're supposed to be running
        self.run_flag = self.check_flags()['run']
        self.collect_flag = 0
        self.update_flag = 0

        if self.run_flag:
            self.log('Starting Facebook collector %s with signal %d' % (self.process_name, self.run_flag))
            self.set_active(1)

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
        filename = self.rawdir + '/' + timestr + '-' + self.collector_name + '-' + self.collector_id + '-out.json'
        if not os.path.isfile(filename):
            self.log('Creating new raw file: %s' % filename)

        with open(filename, 'a') as rawfile:
            rawfile.write(json.dumps(data).encode('utf-8'))
            rawfile.write('\n')

    def log(self, message, level='info', thread='MAIN:'):
        """
        Logs messages to process logfile
        """
        message = str(message)
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
        self.project_db.update({'_id': ObjectId(self.collector_id)}, {'$set': {'active': active}})

    def start_thread(self):
        """
        Modify this method when extending the class to manage the actual collection thread
        """

    def stop_thread(self):
        """
        Modify this method when extending the class to stop the collection thread
        """


class BaseProcessor(object):
    """
    Extensible base class for all STACK processors

    NOTE - when extending, must initiate connections to network specific data directories!
    """

    def __init__(self, project_id, process_name, network):
        self.project_id = project_id
        self.process_name = process_name
        self.network = network

        # Sets up connection w/ project config DB & loads in collector info
        self.db = DB()

        project = self.db.get_project_detail(self.project_id)
        self.project_name = project['project_name']

        configdb = project['project_config_db']
        project_db = self.db.connection[configdb]
        self.project_db = project_db.config

        # Sets up logdir and logging
        logdir = app.config['LOGDIR'] + '/' + self.project_name + '-' + self.project_id + '/logs'
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        # Sets logger w/ name collector_name and level INFO
        self.logger = logging.getLogger('Processor')
        self.logger.setLevel(logging.INFO)

        # Sets up logging file handler
        logfile = logdir + '/%s.log' % self.process_name
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

        self.log('STACK processor for project %s initiated.' % self.project_name)

        # Sets up data directory
        self.datadir = app.config['DATADIR'] + '/' + self.project_name + '-' + self.project_id

        # Establish connections to data directories
        self.raw = self.datadir + '/' + self.network + '/raw'
        self.archive = self.datadir + '/' + self.network + '/archive'
        self.queue = self.datadir + '/' + self.network + '/queue'
        self.error = self.datadir + '/' + self.network + '/error'

        if not os.path.exists(self.raw):
            os.makedirs(self.raw)
        if not os.path.exists(self.archive):
            os.makedirs(self.archive)
        if not os.path.exists(self.queue):
            os.makedirs(self.queue)
        if not os.path.exists(self.error):
            os.makedirs(self.error)

        self.log('STACK processor setup completed. Now starting...')

    def go(self):
        """
        Runs the processor
        """
        self.run_flag = self.check_flags()['run']
        self.restart_flag = 0

        if self.run_flag:
            self.log('Starting processor %s with signal %d' % (self.process_name, self.run_flag))
            self.set_active(1)

        while self.run_flag:
            # Call function to process files
            self.process()

            # Lastly, see if the run status has changed
            try:
                flags = self.check_flags()
                self.run_flag = flags['run']
                self.restart_flag = flags['restart']
            except Exception as e:
                self.log('Mongo connection refused with exception when attempting to check flags: %s' % e, level='warn')
                self.log('Will keep running the processing until reconnect is established.', level='warn')

        # Clean up upon run loop conclude
        self.log('Exiting processor.')
        self.set_active(0)

    def log(self, message, level='info', thread='MAIN:'):
        """
        Logs messages to process logfile
        """
        message = str(message)
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
        resp = self.project_db.find_one({'module': self.network})

        return {
            'run': resp['processor']['run'],
            'restart': resp['processor']['restart']
        }

    def set_active(self, active):
        """
        Quick method to set the active flag to 1 or 0
        """
        self.project_db.update({'module': self.network}, {'$set': {'processor_active': active}})

    def process(self):
        """
        Extend this function to implement your custom processing schemes
        """

class BaseInserter(object):
    """
    Extensible base class for all STACK processors

    NOTE - when extending, must initiate connections to network specific data directories!
    """

    def __init__(self, project_id, process_name, network):
        self.project_id = project_id
        self.process_name = process_name
        self.network = network

        # Sets up connection w/ project config DB & loads in collector info
        self.db = DB()

        project = self.db.get_project_detail(self.project_id)
        self.project_name = project['project_name']

        # Grabs connection to project config DB
        configdb = project['project_config_db']
        project_db = self.db.connection[configdb]
        self.project_db = project_db.config

        # Grabs connection to insertion DB
        # NOTE - on init, need to connect to appropriate network collection
        db_name = self.project_name + '_' + self.project_id
        self.insert_db = self.db.connection[db_name]

        # Sets up logdir and logging
        logdir = app.config['LOGDIR'] + '/' + self.project_name + '-' + self.project_id + '/logs'
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        # Sets logger w/ name collector_name and level INFO
        self.logger = logging.getLogger('Inserter')
        self.logger.setLevel(logging.INFO)

        # Sets up logging file handler
        logfile = logdir + '/%s.log' % self.process_name
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

        self.log('STACK inserter for project %s initiated.' % self.project_name)

        # Sets up data directory
        self.datadir = app.config['DATADIR'] + '/' + self.project_name + '-' + self.project_id

        # Establish connections to data directories
        self.raw = self.datadir + '/' + self.network + '/raw'
        self.archive = self.datadir + '/' + self.network + '/archive'
        self.queue = self.datadir + '/' + self.network + '/queue'
        self.error = self.datadir + '/' + self.network + '/error'

        if not os.path.exists(self.raw):
            os.makedirs(self.raw)
        if not os.path.exists(self.archive):
            os.makedirs(self.archive)
        if not os.path.exists(self.queue):
            os.makedirs(self.queue)
        if not os.path.exists(self.error):
            os.makedirs(self.error)

        self.log('STACK processor setup completed. Now starting...')

    def go(self):
        """
        Runs the processor
        """
        self.run_flag = self.check_flags()['run']
        self.restart_flag = 0

        if self.run_flag:
            self.log('Starting inserter %s with signal %d' % (self.process_name, self.run_flag))
            self.set_active(1)

        while self.run_flag:
            # Call function to process files
            self.insert()

            # Lastly, see if the run status has changed
            try:
                flags = self.check_flags()
                self.run_flag = flags['run']
                self.restart_flag = flags['restart']
            except Exception as e:
                self.log('Mongo connection refused with exception when attempting to check flags: %s' % e, level='warn')
                self.log('Will keep running the processing until reconnect is established.', level='warn')

        # Clean up upon run loop conclude
        self.log('Exiting inserter.')
        self.set_active(0)

    def log(self, message, level='info', thread='MAIN:'):
        """
        Logs messages to process logfile
        """
        message = str(message)
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
        resp = self.project_db.find_one({'module': self.network})

        return {
            'run': resp['inserter']['run'],
            'restart': resp['inserter']['restart']
        }

    def set_active(self, active):
        """
        Quick method to set the active flag to 1 or 0
        """
        self.project_db.update({'module': self.network}, {'$set': {'inserter_active': active}})

    def insert(self):
        """
        Extend this function to implement your custom processing schemes
        """
