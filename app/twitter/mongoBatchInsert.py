#-----------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      jhemsley
#
# Created:     09/10/2013
# Copyright:   (c) jhemsley 2013
# Licence:     <your licence>
#-----------------------------------------------------------------------------


import os.path
#import json
import ConfigParser
#import datetime
from datetime import datetime, timedelta
import time
import logging
import logging.config
import time
import glob
import simplejson
from email.utils import parsedate_tz
from collections import defaultdict
import sys
import traceback
import string
import config
from pymongo import errors as PymongoErrors

from . import module_dir
from app.models import DB

PLATFORM_CONFIG_FILE = module_dir + '/platform.ini'
BATCH_INSERT_SIZE = 1000

db = DB()
db_central = DB(local=False)

# function goes out and gets a list of raw tweet data files
def get_processed_tweet_file_queue(Config, insertdir):

    insert_queue_path = insertdir + '/'
    if not os.path.exists(insert_queue_path):
        os.makedirs(insert_queue_path)

    tweetsOutFile = Config.get('files', 'tweets_file', 0)
    file_extension = os.path.splitext(tweetsOutFile)[1]
    tweetFileNamePattern = tweetsOutFile.replace(file_extension, '_processed' + file_extension)
    tweetFileNamePattern = insert_queue_path + '*' + tweetFileNamePattern

    # now get a list of the files in tweet dir that match the pattern
    insert_queue_file_list = glob.glob(tweetFileNamePattern)
    # note that the dir list may have '//' as dir separator and may not
    final_insert_queue_file_list = [s.replace('\\', '/') for s in insert_queue_file_list]

    return final_insert_queue_file_list


# function goes out and gets a list of raw tweet data files
    def insert_tweet_list(mongoCollection, tweets_list, line_number, processedTweetsFile, data_db, logger):

    inserted_ids_list = []
    # mongo_error_code = -1
    try:
        # this call returns a list of ids
        inserted_ids_list = mongoCollection.insert(tweets_list, continue_on_error=True)
        #mongo_error_code = mongoCollection.error()
        mongo_error_code = data_db.error()

        if mongo_error_code is not None:
            logger.warning("Error %d on mongo insert for (%s)" % (mongo_error_code, processedTweetsFile))

    except ValueError, e:
        print "Exception during mongo insert"
        logger.warning("Exception during mongo insert at or before file line number %d (%s)" % (line_number, processedTweetsFile))
        logging.exception(e)
        print traceback.format_exc()
        pass

    except PymongoErrors.DuplicateKeyError, e:
        print "Exception during mongo insert"
        logger.warning("Duplicate error during mongo insert at or before file line number %d (%s)" % (line_number, processedTweetsFile))
        logging.exception(e)
        print traceback.format_exc()
        pass
    
    return inserted_ids_list

# Parse Twitter created_at datestring and turn it into
def to_datetime(datestring):
    time_tuple = parsedate_tz(datestring.strip())
    dt = datetime(*time_tuple[:6])
    return dt

def go(project_id, rawdir, insertdir, logdir):
    # Connects to project account DB
    project = db.get_project_detail(project_id)
    project_name = project['project_name']

    configdb = project['project_config_db']
    conn = db.connection[configdb]
    project_config_db = conn.config

    # Reference for controller if script is active or not.
    project_config_db.update({'module': 'twitter'}, {'$set': {'inserter_active': 1}})

    Config = ConfigParser.ConfigParser()
    Config.read(PLATFORM_CONFIG_FILE)

    # Creates logger w/ level INFO
    logger = logging.getLogger('mongo_insert')
    logger.setLevel(logging.INFO)
    # Creates rotating file handler w/ level INFO
    fh = logging.handlers.TimedRotatingFileHandler(logdir + '/' + project_name + '-inserter-log-' + project_id + '.out', 'D', 1, 30, None, False, False)
    fh.setLevel(logging.INFO)
    # Creates formatter and applies to rotating handler
    format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    datefmt = '%m-%d %H:%M'
    formatter = logging.Formatter(format, datefmt)
    fh.setFormatter(formatter)
    # Finishes by adding the rotating, formatted handler
    logger.addHandler(fh)

    logger.info('Starting process to insert processed tweets in mongo')

    if not os.path.exists(rawdir + '/error_inserted_tweets/'):
        os.makedirs(rawdir + '/error_inserted_tweets/')

    error_tweet = open(rawdir + '/error_inserted_tweets/error_inserted_tweet-' + project_name + '-' + project_id + '.txt', 'a')

    db_name = project_name + '_' + project_id
    data_db = db.connection[db_name]
    insert_db = data_db.tweets
    
    data_db_central = db_central.connection[config.CT_DB_NAME]
    
    delete_db = db.connection[db_name + '_delete']
    deleteCollection = delete_db['tweets']

    module_config = project_config_db.find_one({'module': 'twitter'})
    runMongoInsert = module_config['inserter']['run']

    while runMongoInsert:
        queued_tweets_file_list = get_processed_tweet_file_queue(Config, insertdir)
        num_files_in_queue = len(queued_tweets_file_list)
        #logger.info('Queue length %d' % num_files_in_queue)

        # TODO - end on zero?
        if (num_files_in_queue == 0):
            time.sleep( 180 )
        else:

            processedTweetsFile = queued_tweets_file_list[0]
            logger.info('Mongo insert file found: %s' % processedTweetsFile)

            tweets_list = []
            tweet_total = 0
            lost_tweets = 0
            line_number = 0
            deleted_tweets = 0
            deleted_tweets_list = []
            stream_limit_notices = 0
            stream_limits_list = []

            # lame workaround, but for now we assume it will take less than a minute to
            # copy a file so this next sleep is here to wait for a copy to finish on the
            # off chance that we happy to see it just as it is being copied to the directory
            time.sleep( 60 )

            with open(processedTweetsFile) as f:
                logger.info(processedTweetsFile)
                for line in f:
                    if '-delete-' not in processedTweetsFile and '-streamlimits-' not in processedTweetsFile:
                        try:
                            line_number += 1
                            line = line.strip()

                            # print line_number

                            tweet = simplejson.loads(line)

                            # use tweet id as mongo id
                            #tweet['_id'] = tweet['id']

                            # now, when we did the process tweet step we already worked with
                            # these dates. If they failed before, they shouldn't file now, but
                            # if they do we are going to skip this tweet and go on to the next one
                            t = to_datetime(tweet['created_at'])
                            tweet['created_ts'] = t

                            t = to_datetime(tweet['user']['created_at'])
                            tweet['user']['created_ts'] = t

                            tweets_list.append(tweet)

                        except ValueError, e:
                            lost_tweets += 1
                            print "ValueError while converting date. tweet not processed: %d (%s)" % (line_number, processedTweetsFile)
                            logger.warning("ValueError while converting date. tweet not processed: %d (%s)" % (line_number, processedTweetsFile))
                            logging.exception(e)
                            error_tweet.write(line+"\n")
                            print traceback.format_exc()
                            pass
                        except TypeError, e:
                            lost_tweets += 1
                            print "TypeError while converting date. tweet not processed: %d (%s)" % (line_number, processedTweetsFile)
                            logger.warning("TypeError while converting date. tweet not processed: %d (%s)" % (line_number, processedTweetsFile))
                            logging.exception(e)
                            error_tweet.write(line+"\n")
                            print traceback.format_exc()
                            pass
                        except KeyError, e:
                            lost_tweets += 1
                            print "KeyError while converting date. tweet not processed: %d (%s)" % (line_number, processedTweetsFile)
                            logger.warning("KeyError while converting date. tweet not processed: %d (%s)" % (line_number, processedTweetsFile))
                            logging.exception(e)
                            error_tweet.write(line+"\n")
                            print traceback.format_exc()
                            pass

                        if len(tweets_list) == BATCH_INSERT_SIZE:

                            print 'Inserting batch at file line %d' % line_number
                            inserted_ids_list = insert_tweet_list(insert_db, tweets_list, line_number, processedTweetsFile, data_db, logger)

                            failed_insert_count = BATCH_INSERT_SIZE - len(inserted_ids_list)
                            logger.info('Batch of size %d had %d failed tweet inserts' % (BATCH_INSERT_SIZE, failed_insert_count))
                            tweets_list = []

                            lost_tweets = lost_tweets + failed_insert_count
                            tweet_total += len(inserted_ids_list)
            				#print "inserting 5k tweets - %i total" % tweet_total
                    elif '-delete-' in processedTweetsFile:
                        deleted_tweets += 1

                        line = line.strip()
                        tweet = simplejson.loads(line)
                        deleted_tweets_list.append(tweet)

                        inserted_ids_list = insert_tweet_list(deleteCollection, deleted_tweets_list, line_number, processedTweetsFile, delete_db, logger)
                        deleted_tweets_list = []
                    elif '-streamlimits-' in processedTweetsFile:
                        stream_limit_notices += 1

                        line = line.strip()
                        notice = simplejson.loads(line)
                        stream_limits_list.append(notice)

                        stream_limit_collection = data_db.limits
                        inserted_ids_list = insert_tweet_list(stream_limit_collection, stream_limits_list, line_number, processedTweetsFile, data_db, logger)
                        
                        # Also inserts to a central limits collection
                        stream_limit_collection_central = data_db_central.limits
                        inserted_ids_list_central = insert_tweet_list(stream_limit_collection_central, stream_limits_list, line_number, processedTweetsFile, data_db_central, logger)
                        
                        stream_limits_list = []

            if '-delete-' in processedTweetsFile:
                print 'Inserted %d delete statuses for file %s.' % (deleted_tweets, processedTweetsFile)
                logger.info('Inserted %d delete statuses for file %s.' % (deleted_tweets, processedTweetsFile))

            if '-streamlimits-' in processedTweetsFile:
                print 'Inserted %d stream limit statuses for file %s.' % (stream_limit_notices, processedTweetsFile)
                logger.info('Inserted %d stream limit statuses for file %s.' % (stream_limit_notices, processedTweetsFile))


            # make sure we clean up after ourselves
            f.close()
            os.remove(processedTweetsFile)

            if len(tweets_list) > 0:

                print 'Inserting last set of %d tweets at file line %d' % (len(tweets_list), line_number)
                inserted_ids_list = insert_tweet_list(insert_db, tweets_list, line_number, processedTweetsFile, data_db, logger)

                failed_insert_count = len(tweets_list) - len(inserted_ids_list)
                logger.info('Insert set of size %d had %d failed tweet inserts' % (len(tweets_list), failed_insert_count) )
                tweets_list = []

                lost_tweets = lost_tweets + failed_insert_count
                tweet_total += len(inserted_ids_list)

            logger.info('Read %d lines, inserted %d tweets, lost %d tweets for file %s' % (line_number, tweet_total, lost_tweets, processedTweetsFile))


        module_config = project_config_db.find_one({'module': 'twitter'})
        runMongoInsert = module_config['inserter']['run']
        # end run loop

    error_tweet.close()
    logger.info('Exiting MongoBatchInsert Program...')
    print 'Exiting MongoBatchInsert Program...'

    # Reference for controller if script is active or not.
    project_config_db.update({'module': 'twitter'}, {'$set': {'inserter_active': 0}})
