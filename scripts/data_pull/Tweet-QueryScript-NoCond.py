# This script queries tweet objects from MongoDB *without conditions* and writes to a CSV file
# The script reads the settings from config.py
# Output: All ID fields are prepended with ID_
#         Array fields are | separated
#         If keys do not exist, write NULL
# By Sikana Tanupabrungsun. March 16, 2018

# encoding=utf8
import os
import csv
import sys
import pymongo
import scripts.data_pull.ConfigCond as cfg
from datetime import datetime
import importlib

importlib.reload(sys)
sys.setdefaultencoding('utf8')

connection = pymongo.MongoClient()

# Check if DB is password protected
if cfg.DB_AUTH['DB_IS_AUTH']:
    connection.admin.authenticate(cfg.DB_AUTH['DB_USERNAME'], cfg.DB_AUTH['DB_PASSWORD'])

db = connection[cfg.DB['DB_NAME']][cfg.DB['COL_NAME']]

# Get keys
keys = cfg.OUTPUT['HEADER']

# Outfile Handling #
outfilename = cfg.OUTPUT['OUT_FILENAME']
if os.path.exists(outfilename):
    print(('%s already exists' % (outfilename)))
    overwrite = input("Replace the file [y/n]?").lower()
    if overwrite != 'y':
        sys.exit(0)

dirname = os.path.dirname(outfilename)
if not os.path.exists(dirname):
    os.makedirs(dirname)

outcsvfile = open(outfilename, 'w')
outfile = csv.writer(outcsvfile)
outfile.writerow(keys)

print(('Query data from DB: %s Collection: %s' % (cfg.DB['DB_NAME'], cfg.DB['COL_NAME'])))
print(('Output file: %s' % (outfilename)))
print(('Output headers: %s' % (','.join(keys))))

tweets = db.find()

print(('Total tweets: %d' % (tweets.count())))

for tweet in tweets:
    out = []
    for key in keys:
        key_arr = key.split('.')
        last_key = None
        try:
            if len(key_arr) == 3:
                my_val = tweet[key_arr[0]][key_arr[1]][key_arr[2]]
                last_key = key_arr[2]
            elif len(key_arr) == 2:
                my_val = tweet[key_arr[0]][key_arr[1]]
                last_key = key_arr[1]
            else:
                my_val = tweet[key]
                last_key = key

            if isinstance(my_val, list):
                my_val = '|'.join(my_val)
            elif last_key == 'created_at':
                my_val = datetime.fromtimestamp(int(my_val) / 1000).strftime('%a %b %d %X %z %Y')
            elif last_key.endswith('id') and my_val is not None:
                my_val = 'ID_' + str(my_val)

            out.append(my_val)
        except:
            out.append(None)

    outfile.writerow(out)