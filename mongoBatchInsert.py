#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      jhemsley
#
# Created:     09/10/2013
# Copyright:   (c) jhemsley 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------


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
from pymongo import Connection
from email.utils import parsedate_tz
from collections import defaultdict
import sys
import traceback
import string


PLATFORM_CONFIG_FILE = 'platform.ini'
BATCH_INSERT_SIZE = 1000

connection = Connection()
db = connection.config
mongo_config = db.config

# function goes out and gets a list of raw tweet data files
def get_processed_tweet_file_queue(Config):

    insert_queue_path = Config.get('files', 'tweet_insert_queue', 0)
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
def insert_tweet_list(mongoCollection, tweets_list, line_number, processedTweetsFile):

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

    return inserted_ids_list

# Parse Twitter created_at datestring and turn it into
def to_datetime(datestring):
    time_tuple = parsedate_tz(datestring.strip())
    dt = datetime(*time_tuple[:6])
    return dt

if __name__ == '__main__':

    Config = ConfigParser.ConfigParser()
    Config.read(PLATFORM_CONFIG_FILE)

    logDir = Config.get('files', 'log_dir', 0)
    logConfigFile = Config.get('files', 'log_config_file', 0)
    logging.config.fileConfig(logConfigFile)
    logging.addLevelName('root', 'mongo_insert')
    logger = logging.getLogger('mongo_insert')

    logger.info('Starting process to insert processed tweets in mongo')

    collectionName = Config.get('collection', 'name', 0)
    dbName = Config.get('collection', 'db_name', 0)
    dbCollectionName = Config.get('collection', 'collection_name', 0)

    # this is the mongo db we will store data in
    data_db = connection[dbName]
    mongoCollection = data_db[dbCollectionName]

    #connection = Connection()
    #db = connection.config
    #mongo_config = db.config

    mongoConfigs = mongo_config.find_one({"module" : "inserter"})
    runMongoInsert = mongoConfigs['run']

    while runMongoInsert:
        queued_tweets_file_list = get_processed_tweet_file_queue(Config)
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

            # lame workaround, but for now we assume it will take less than a minute to
            # copy a file so this next sleep is here to wait for a copy to finish on the
            # off chance that we happy to see it just as it is being copied to the directory
            time.sleep( 60 )

            with open(processedTweetsFile) as f:
                for line in f:

                    try:
                        line_number += 1
                        line = line.strip()

                        # print line_number

                        tweet = simplejson.loads(line)

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
                        print traceback.format_exc()
                        pass
                    except TypeError, e:
                        lost_tweets += 1
                        print "TypeError while converting date. tweet not processed: %d (%s)" % (line_number, processedTweetsFile)
                        logger.warning("TypeError while converting date. tweet not processed: %d (%s)" % (line_number, processedTweetsFile))
                        logging.exception(e)
                        print traceback.format_exc()
                        pass
                    except KeyError, e:
                        lost_tweets += 1
                        print "KeyError while converting date. tweet not processed: %d (%s)" % (line_number, processedTweetsFile)
                        logger.warning("KeyError while converting date. tweet not processed: %d (%s)" % (line_number, processedTweetsFile))
                        logging.exception(e)
                        print traceback.format_exc()
                        pass

                    if len(tweets_list) == BATCH_INSERT_SIZE:

                        print 'Inserting batch at file line %d' % line_number
                        inserted_ids_list = insert_tweet_list(mongoCollection, tweets_list, line_number, processedTweetsFile)

                        failed_insert_count = BATCH_INSERT_SIZE - len(inserted_ids_list)
                        logger.info('Batch of size %d had %d failed tweet inserts' % (BATCH_INSERT_SIZE, failed_insert_count))
                        tweets_list = []

                        lost_tweets = lost_tweets + failed_insert_count
                        tweet_total += len(inserted_ids_list)
        				#print "inserting 5k tweets - %i total" % tweet_total

            # make sure we clean up after ourselves
            f.close()
            os.remove(processedTweetsFile)

            if len(tweets_list) > 0:

                print 'Inserting last set of %d tweets at file line %d' % (len(tweets_list), line_number)
                inserted_ids_list = insert_tweet_list(mongoCollection, tweets_list, line_number, processedTweetsFile)

                failed_insert_count = len(tweets_list) - len(inserted_ids_list)
                logger.info('Insert set of size %d had %d failed tweet inserts' % (len(tweets_list), failed_insert_count) )
                tweets_list = []

                lost_tweets = lost_tweets + failed_insert_count
                tweet_total += len(inserted_ids_list)

            logger.info('Read %d lines, inserted %d tweets, lost %d tweets for file %s' % (line_number, tweet_total, lost_tweets, processedTweetsFile))


        mongoConfigs = mongo_config.find_one({"module" : "inserter"})
        runMongoInsert = mongoConfigs['run']
        # end run loop

    logger.info('Exiting MongoBatchInsert Program...')
    print 'Exiting MongoBatchInsert Program...'
