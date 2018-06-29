# This script queries tweet objects from MongoDB *without conditions* and writes to a CSV file
# The script reads the settings from config.py
# Output: All ID fields are prepended with ID_
#         Array fields are | separated
#         If keys do not exist, write NULL
# By Sikana Tanupabrungsun. March 16, 2018

# Query conditions:
# tweet_id=[id_1, id_2]
# user_id=[user_id_1, user_id_2]
# screen_name=[name_1, name_2]
# created_at_from=datetime(YYYY, M, D, H)
# created_at_to=datetime(YYYY, M, D, H)
# retweet_included=True|False

# encoding=utf8
import os
import csv
import sys
import pymongo
import ConfigCond as cfg
from datetime import datetime

reload(sys)
sys.setdefaultencoding('utf8')


def query_conditions(tweet_id=None, reply_to_id=None
                     user_id=None, screen_name=None, 
                     created_at_from=None, created_at_to=None, 
                     retweet_included=True):
    
    query = {}
    if tweet_id is not None and len(tweet_id) > 0:
        tweet_id = [long(id) for id in tweet_id]
        query['id'] = {'$in': tweet_id}
    if reply_to_id is not None and len(reply_to_id) > 0:
        reply_to_id = [long(id) for id in reply_to_id]
        query['in_reply_to_status_id'] = {'$in': reply_to_id}
    if user_id is not None and len(user_id) > 0:
        user_id = [long(id) for id in user_id]
        query['user.id'] = {'$in': user_id}
    if screen_name is not None and len(screen_name) > 0:
        query['user.screen_name'] = {'$in': screen_name}
    if created_at_from or created_at_to:
        query['created_ts'] = {'$gte': created_at_from,
                               '$lte': created_at_to}
    if retweet_included is not None:
        if retweet_included == False:
            query['retweeted_status'] = {'$ne': None}

    return query

if __name__ == "__main__":
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
        print('%s already exists' % (outfilename))
        overwrite = raw_input("Replace the file [y/n]?").lower()
        if overwrite <> 'y':
            sys.exit(0)
    
    dirname = os.path.dirname(outfilename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    
    outcsvfile = open(outfilename, 'w')
    outfile = csv.writer(outcsvfile)
    outfile.writerow(keys)
    
    print('Query data from DB: %s Collection: %s' % (cfg.DB['DB_NAME'], cfg.DB['COL_NAME']))
    print('Output file: %s' % (outfilename))
    print('Output headers: %s' % (','.join(keys)))
    
    # Conditions
    tweet_id=cfg.CONDITIONS['tweet_id']
    
    if tweet_id is not None and os.path.isfile(tweet_id):
        incsvfile = open(tweet_id, 'rb')
        infile = csv.DictReader(incsvfile)
        tweet_id = []
        for row in infile:
            tweet_id.append(row['tweet_id'].replace('ID_', ''))
            
    reply_to_id=cfg.CONDITIONS['reply_to_id']
    if reply_to_id is not None and os.path.isfile(reply_to_id):
        incsvfile = open(reply_to_id, 'rb')
        infile = csv.DictReader(incsvfile)
        reply_to_id = []
        for row in infile:
            reply_to_id.append(row['reply_to_id'.replace('ID_', ''))
        
    user_id=cfg.CONDITIONS['user_id']
    if user_id is not None and os.path.isfile(user_id):
        incsvfile = open(user_id, 'rb')
        infile = csv.DictReader(incsvfile)
        user_id = []
        for row in infile:
            user_id.append(row['user_id'].replace('ID_', ''))
    
    screen_name=cfg.CONDITIONS['screen_name']
    if screen_name is not None and os.path.isfile(screen_name):
        incsvfile = open(screen_name, 'rb')
        infile = csv.DictReader(incsvfile)
        screen_name = []
        for row in infile:
            screen_name.append(row['screen_name'].strip())
    
    query = query_conditions(tweet_id=tweet_id,
                             reply_to_id=reply_to_id,
                             user_id=cfg.CONDITIONS['user_id'],
                             screen_name=cfg.CONDITIONS['screen_name'],
                             created_at_from=cfg.CONDITIONS['created_at_from'],
                             created_at_to=cfg.CONDITIONS['created_at_to'],
                             retweet_included=cfg.CONDITIONS['retweet_included'])
                            
    print('Query conditions: %s' % (query))
    tweets = db.find(query)
    
    print('Total tweets: %d' % (tweets.count()))
    
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
                    my_val = datetime.fromtimestamp(int(my_val)/1000).strftime('%a %b %d %X %z %Y')
                elif last_key.endswith('id') and my_val is not None:
                    my_val = 'ID_' + str(my_val)
                
                out.append(my_val)
            except:
                out.append(None)
        
        outfile.writerow(out)
    
