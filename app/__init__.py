import os
from flask import Flask
from celery import Celery

# Init and config app
app = Flask(__name__)
app.config.from_object('config')

# Init and config celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

from app import views
