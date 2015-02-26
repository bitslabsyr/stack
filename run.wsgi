import sys
import logging
import os
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/stack/")

from app import app as application
application.secret_key = os.urandom(24)