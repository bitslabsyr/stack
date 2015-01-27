import os

basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = False

SECRET_KEY = 'This key will be replaced with a secure key in production.'
CSRF_ENABLED = True
CSRF_SECRET_KEY = 'willbereplacedinproduction'
