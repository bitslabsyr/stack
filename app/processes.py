import os
import logging
import time
import json

from models import DB
from app import app

"""
class BaseProcess(object):

    def __init__(self, project_id):
        self.project_id = project_id

        # Sets up connection to project config database
        self.db = DB()
        resp = self.db.get_project_detail(self.project_id)
        if resp['status']:
            configdb = resp['project_config_db']
            self.project_db = configdb.config
        else:
            # TODO - logging

        # Sets up logging
"""


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

        resp = self.db.get_collector_detail(self.project_id, self.collector_id)
        if resp['status']:
            collector_info = resp['collector']
            self.collector_name = collector_info['collector_name']
            self.network = collector_info['network']
            self.auth = collector_info['api_auth']
            # TODO - file format to Mongo
            self.file_format = '%Y%m%d-%H'

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

    def start(self):
        pass

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


class Processor(object):
    pass


class Inserter(object):
    pass
