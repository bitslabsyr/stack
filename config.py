import os

# MONGODB CONFIG
USERNAME = 'USERNAME'
PASSWORD = 'PASSWORD'
# Directory structure config vars
BASEDIR = os.path.abspath(os.path.dirname(__file__))
LOGDIR = BASEDIR + '/out'
DATADIR = BASEDIR + '/data'

# Flask config vars
DEBUG = False
SECRET_KEY = 'This key will be replaced with a secure key in production.'
CSRF_ENABLED = True
CSRF_SECRET_KEY = 'willbereplacedinproduction'

# STACKS config info
VERSION = '2.0'
DESC = 'STACKS - Social Media Tracker, Aggregator, and Collector Kit'
DEFAULT_ROLE = 0  # by default, users aren't admins
NETWORKS = ['twitter', 'facebook']  # networks that STACKS is set to work for

# Celery config info - queues & routes are added dynamically
CELERY_BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp'
CELERY_QUEUES = ()
CELERY_ROUTES = {}
# CELERY_REDIRECT_STDOUTS = False  # We handle stdout/err/in logging ourselves, so don't want Celery taking over
