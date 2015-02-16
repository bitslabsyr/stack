import os

# Directory structure config vars
BASEDIR = os.path.abspath(os.path.dirname(__file__))
LOGDIR = BASEDIR + '/out'
DATADIR = BASEDIR + '/data'

# Flask config vars
DEBUG = False
SECRET_KEY = 'This key will be replaced with a secure key in production.'
CSRF_ENABLED = True
CSRF_SECRET_KEY = 'willbereplacedinproduction'

# STACK config info
VERSION = '2.0'
DESC = 'STACK - Social Media Tracker, Aggregator, and Collector Kit'

# Celery config info - queues & routes are added dynamically
CELERY_BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp'
CELERY_QUEUES = ()
CELERY_ROUTES = {}
