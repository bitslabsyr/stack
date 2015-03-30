import os
import logging
import time
import json

from bson.objectid import ObjectId

from models import DB
from app import app


class Collector(object):
    """
    Base class for all STACK collectors
    """

    def __init__(self, project_id, collector_id, process_name):
        self.project_id = project_id
        self.collector_id = collector_id
        self.process_name = process_name

        # Sets up connection w/ project config DB & loads in collector info
        self.db = DB()

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

        self.log('All raw files and directories set.')

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

    def log(self, message, level='info'):
        """
        Logs messages to process logfile
        """
        if level is not 'INFO' and level == 'warn':
            self.logger.warning(message)
        elif level is not 'INFO' and level == 'error':
            self.logger.error(message)
        else:
            self.logger.info(message)

    def check_flag(self):
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

    def go(self):
        """
        If extending Collector class, use go() to start & manage the collection
        """


class Processor(object):
    pass


class Inserter(object):
    pass
