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
import ConfigParser
from pymongo import Connection
import datetime
import logging
import logging.config
import sys
import time
from email.utils import parsedate_tz
import glob
import simplejson
import hashlib
import string
from collections import defaultdict
import re
import traceback
import shutil
import tweetprocessing

from . import module_dir

PLATFORM_CONFIG_FILE = module_dir + '/test.ini'
EXPAND_URLS = False

#connect to mongo
connection = Connection()
db = connection.config
mongo_config = db.config

# function goes out and gets a list of raw tweet data files
def get_tweet_file_queue(Config):

    tweetsOutFilePath = module_dir + Config.get('files', 'raw_tweets_file_path', 0)
    if not os.path.exists(tweetsOutFilePath):
        os.makedirs(tweetsOutFilePath)
    tweetsOutFileDateFrmt = Config.get('files', 'tweets_file_date_frmt', 0)
    tweetsOutFile = Config.get('files', 'tweets_file', 0)

    # make a pattern of the tweet files we hope to find
    tweetFileNamePattern = tweetsOutFilePath + '*' + tweetsOutFile
    #print tweetFileNamePattern

    # now get a list of the files in tweet dir that match the pattern
    tweetsFileList = glob.glob(tweetFileNamePattern)
    # note that the dir list may have '//' as dir separator and may not
    tweetsFileList = [s.replace('\\', '/') for s in tweetsFileList]

    # now we don't want a file in the list if it is the one tweets are being added too
    # this is a timestamp using the format in the platform config file. if a tweet file is
    # in use, we will remove it from the list

    # Remove by time now since we can run two collector threads
    timestr = time.strftime(tweetsOutFileDateFrmt)
    currentTweetFileNamePattern = tweetsOutFilePath + timestr + '*'
    currentTweetFileList = glob.glob(currentTweetFileNamePattern)
    currentTweetFileList = [s.replace('\\', '/') for s in currentTweetFileList]

    # this line removes the current live file from the list
    for item in currentTweetFileList:
        if item in tweetsFileList: tweetsFileList.remove(item)

    return tweetsFileList

def get_processed_tweets_file_name (Config, rawTweetsFile):

    tweetsOutFilePath = module_dir + Config.get('files', 'raw_tweets_file_path', 0)
    tweet_archive_dir = module_dir + Config.get('files', 'tweet_archive_dir', 0)
    if not os.path.exists(tweet_archive_dir):
        os.makedirs(tweet_archive_dir)

    processed_tweets_file = rawTweetsFile.replace(tweetsOutFilePath, tweet_archive_dir)
    file_extension = os.path.splitext(rawTweetsFile)[1]
    processed_tweets_file = processed_tweets_file.replace(file_extension, '_processed' + file_extension)

    return processed_tweets_file

def queue_up_processed_tweets (Config, processed_tweets_file, logger):

    tweet_archive_dir = module_dir + Config.get('files', 'tweet_archive_dir', 0)
    tweet_insert_queue_path = module_dir + Config.get('files', 'tweet_insert_queue', 0)
    if not os.path.exists(tweet_insert_queue_path):
        os.makedirs(tweet_insert_queue_path)

    queued_up_tweets_file = processed_tweets_file.replace(tweet_archive_dir, tweet_insert_queue_path)

    shutil.copyfile(processed_tweets_file, queued_up_tweets_file)

    #os.symlink(processed_tweets_file, queued_up_tweets_file)

    logger.info('Queued up %s to %s' % (processed_tweets_file, queued_up_tweets_file))

def archive_processed_file (Config, rawTweetsFile, logger):

    tweetsOutFilePath = module_dir + Config.get('files', 'raw_tweets_file_path', 0)
    tweet_archive_dir = module_dir + Config.get('files', 'tweet_archive_dir', 0)
    if not os.path.exists(tweet_archive_dir):
        os.makedirs(tweet_archive_dir)

    archive_raw_tweets_file = rawTweetsFile.replace(tweetsOutFilePath, tweet_archive_dir)

    shutil.move(rawTweetsFile, archive_raw_tweets_file)

    logger.info('Moved %s to %s' % (rawTweetsFile, archive_raw_tweets_file))


def start():
    Config = ConfigParser.ConfigParser()
    Config.read(PLATFORM_CONFIG_FILE)

    logDir = module_dir + Config.get('files', 'log_dir', 0)

     # Creates logger w/ level INFO
    logger = logging.getLogger('preprocess')
    logger.setLevel(logging.INFO)
    # Creates rotating file handler w/ level INFO
    fh = logging.handlers.TimedRotatingFileHandler(module_dir + '/logs/log-processor.out', 'D', 1, 30, None, False, False)
    fh.setLevel(logging.INFO)
    # Creates formatter and applies to rotating handler
    format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    datefmt = '%m-%d %H:%M'
    formatter = logging.Formatter(format, datefmt)
    fh.setFormatter(formatter)
    # Finishes by adding the rotating, formatted handler
    logger.addHandler(fh)

    """
    logConfigFile = Config.get('files', 'log_config_file', 0)
    logging.config.fileConfig(logConfigFile)
    logging.addLevelName('root', 'preprocess')
    logging.TimedRotatingFileHandler('.logs/log-processor.out', 'M', 1, 30, None, False, False)
    """

    logger = logging.getLogger('preprocess')

    logger.info('Starting preprocess system')

    error_tweet = open("error_tweet.txt", "a")
    # collectionName = Config.get('collection', 'name', 0)

    mongoConfigs = mongo_config.find_one({"module" : "processor"})
    runPreProcessor = mongoConfigs['run']
    #runPreProcessor = True

    if runPreProcessor:
        print 'Starting runPreProcessor'
        logger.info('Preprocess start signal')
    runLoopSleep = 0

    while runPreProcessor:

        termsListFile = module_dir + Config.get('files', 'terms_file', 0)
        with open(termsListFile) as f:
            track_list = f.read().splitlines()


        tweetsFileList = get_tweet_file_queue(Config)
        files_in_queue = len(tweetsFileList)

        # TODO - Confirm loop time for checking files
        # --Base off of hour format in log?
        if files_in_queue < 1:
            time.sleep( 180 )
        else:
            logger.info('Queue length is %d' % files_in_queue)
            rawTweetsFile = tweetsFileList[0]
            logger.info('Preprocess raw file: %s' % rawTweetsFile)

            processed_tweets_file = get_processed_tweets_file_name (Config, rawTweetsFile)

            # TODO - Dynamic copy time
            # lame workaround, but for now we assume it will take less than a minute to
            # copy a file so this next sleep is here to wait for a copy to finish on the
            # off chance that we happy to see it just as it is being copied to the directory
            time.sleep( 60 )

            f_out = open(processed_tweets_file,'w')

            tweets_list = []
            tweet_total = 0
            lost_tweets = 0
            line_number = 0

            with open(rawTweetsFile) as f:
                for line in f:

                    try:
                        line_number += 1
                        line = line.strip()

                        tweet_out_string = tweetprocessing.process_tweet(line, track_list, expand_url=EXPAND_URLS)
                        f_out.write(tweet_out_string)
                        tweet_total += 1
                        # print tweet_out_string

                    except ValueError, e:
                        lost_tweets += 1
                        print "ValueError. tweet not processed: %d (%s)" % (line_number, rawTweetsFile)
                        logger.warning("tweet not processed: %d (%s)" % (line_number, rawTweetsFile))
                        logging.exception(e)
                        error_tweet.write(line+"\n")
                        print traceback.format_exc()
                        pass
                    except TypeError, e:
                        lost_tweets += 1
                        print "TypeError. tweet not processed: %d (%s)" % (line_number, rawTweetsFile)
                        logger.warning("tweet not processed: %d (%s)" % (line_number, rawTweetsFile))
                        logging.exception(e)
                        error_tweet.write(line+"\n")
                        print traceback.format_exc()
                        pass
                    except KeyError, e:
                        lost_tweets += 1
                        print "KeyError. tweet not processed: %d (%s)" % (line_number, rawTweetsFile)
                        logger.warning("tweet not processed: %d (%s)" % (line_number, rawTweetsFile))
                        logging.exception(e)
                        error_tweet.write(line+"\n")
                        print traceback.format_exc()
                        pass

            f_out.close()
            f.close()

            logger.info('Tweets processed: %d, lost: %d' % (tweet_total, lost_tweets))

            archive_processed_file (Config, rawTweetsFile, logger)
            queue_up_processed_tweets (Config, processed_tweets_file, logger)

        exception = None
        try:
            mongoConfigs = mongo_config.find_one({"module" : "processor"})
            runPreProcessor = mongoConfigs['run']
        # If mongo is unavailable, decrement processing loop by 2 sec.
        # increments until connection is re-established.
        # TODO - need to make this more robust; will do for now.
        except Exception, exception:
            print 'Mongo connection for preprocessor refused with exception: %s' % exception
            logger.error('Mongo connection for preprocessor refused with exception: %s' % exception)
            runLoopSleep += 2
            time.sleep(runLoopSleep)

    error_tweet.close()
    logger.info('Exiting preprocessor Program...')
    print 'Exiting preprocessor Program...'

    #logging.shutdown()




