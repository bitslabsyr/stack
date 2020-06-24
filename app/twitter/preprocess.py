# -------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      jhemsley
#
# Created:     09/10/2013
# Copyright:   (c) jhemsley 2013
# Licence:     <your licence>
# -------------------------------------------------------------------------------
import os
import os.path
import configparser
from pymongo import MongoClient
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
from app.twitter import tweetprocessing

from . import module_dir
from app.models import DB

PLATFORM_CONFIG_FILE = module_dir + '/platform.ini'
EXPAND_URLS = False

# connect to mongo
db = DB()


# function goes out and gets a list of raw tweet data files
# TODO - by project
def get_tweet_file_queue(Config, rawdir):
    tweetsOutFilePath = rawdir + '/'
    if not os.path.exists(tweetsOutFilePath):
        os.makedirs(tweetsOutFilePath)
    tweetsOutFileDateFrmt = Config.get('files', 'tweets_file_date_frmt', 0)
    tweetsOutFile = Config.get('files', 'tweets_file', 0)

    # make a pattern of the tweet files we hope to find
    tweetFileNamePattern = tweetsOutFilePath + '*' + tweetsOutFile
    # print tweetFileNamePattern

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


def get_processed_tweets_file_name(Config, rawTweetsFile, rawdir, archdir):
    tweetsOutFilePath = rawdir + '/'
    tweet_archive_dir = archdir + '/'
    if not os.path.exists(tweet_archive_dir):
        os.makedirs(tweet_archive_dir)

    processed_tweets_file = rawTweetsFile.replace(tweetsOutFilePath, tweet_archive_dir)
    file_extension = os.path.splitext(rawTweetsFile)[1]
    processed_tweets_file = processed_tweets_file.replace(file_extension, '_processed' + file_extension)

    return processed_tweets_file


def queue_up_processed_tweets(Config, processed_tweets_file, logger, archdir, insertdir):
    tweet_archive_dir = archdir + '/'
    tweet_insert_queue_path = insertdir + '/'
    if not os.path.exists(tweet_insert_queue_path):
        os.makedirs(tweet_insert_queue_path)

    queued_up_tweets_file = processed_tweets_file.replace(tweet_archive_dir, tweet_insert_queue_path)

    shutil.copyfile(processed_tweets_file, queued_up_tweets_file)

    # os.symlink(processed_tweets_file, queued_up_tweets_file)

    logger.info('Queued up %s to %s' % (processed_tweets_file, queued_up_tweets_file))


def archive_processed_file(Config, rawTweetsFile, logger, rawdir, archdir):
    tweetsOutFilePath = rawdir + '/'
    tweet_archive_dir = archdir + '/'
    if not os.path.exists(tweet_archive_dir):
        os.makedirs(tweet_archive_dir)

    archive_raw_tweets_file = rawTweetsFile.replace(tweetsOutFilePath, tweet_archive_dir)

    shutil.move(rawTweetsFile, archive_raw_tweets_file)

    logger.info('Moved %s to %s' % (rawTweetsFile, archive_raw_tweets_file))


def go(project_id, rawdir, archdir, insertdir, logdir):
    # Connects to project account DB
    project = db.get_project_detail(project_id)
    project_name = project['project_name']

    configdb = project['project_config_db']
    conn = db.connection[configdb]
    project_config_db = conn.config

    # Reference for controller if script is active or not.
    project_config_db.update({'module': 'twitter'}, {'$set': {'processor_active': 1}})

    Config = configparser.ConfigParser()
    Config.read(PLATFORM_CONFIG_FILE)

    # Creates logger w/ level INFO
    logger = logging.getLogger('preprocess')
    logger.setLevel(logging.INFO)
    # Creates rotating file handler w/ level INFO
    fh = logging.handlers.TimedRotatingFileHandler(
        logdir + '/' + project_name + '-processor-log-' + project_id + '.out', 'D', 1, 30, None, False, False)
    fh.setLevel(logging.INFO)
    # Creates formatter and applies to rotating handler
    format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    datefmt = '%m-%d %H:%M'
    formatter = logging.Formatter(format, datefmt)
    fh.setFormatter(formatter)
    # Finishes by adding the rotating, formatted handler
    logger.addHandler(fh)

    logger = logging.getLogger('preprocess')
    logger.info('Starting preprocess system')

    if not os.path.exists(rawdir + '/error_tweets/'):
        os.makedirs(rawdir + '/error_tweets/')

    error_tweet = open(rawdir + '/error_tweets/error_tweet-' + project_name + '-' + project_id + '.txt', 'a')

    module_config = project_config_db.find_one({'module': 'twitter'})
    runPreProcessor = module_config['processor']['run']

    if runPreProcessor:
        print('Starting runPreProcessor')
        logger.info('Preprocess start signal')
    runLoopSleep = 0

    while runPreProcessor:

        # Get all terms for all collectors
        track_list = []
        for collector in project['collectors']:
            if collector['terms_list']:
                tmp_terms = [term['term'] for term in collector['terms_list']]
                track_list += tmp_terms

        if track_list:
            track_list = list(set(track_list))

        tweetsFileList = get_tweet_file_queue(Config, rawdir)
        files_in_queue = len(tweetsFileList)

        if files_in_queue < 1:
            time.sleep(180)
        else:
            logger.info('Queue length is %d' % files_in_queue)
            rawTweetsFile = tweetsFileList[0]
            logger.info('Preprocess raw file: %s' % rawTweetsFile)

            processed_tweets_file = get_processed_tweets_file_name(Config, rawTweetsFile, rawdir, archdir)

            # TODO - Dynamic copy time
            # lame workaround, but for now we assume it will take less than a minute to
            # copy a file so this next sleep is here to wait for a copy to finish on the
            # off chance that we happy to see it just as it is being copied to the directory
            time.sleep(60)

            f_out = open(processed_tweets_file, 'w')

            tweets_list = []
            tweet_total = 0
            lost_tweets = 0
            line_number = 0

            with open(rawTweetsFile) as f:
                if '-delete-' not in rawTweetsFile and '-streamlimits-' not in rawTweetsFile:
                    for line in f:
                        try:
                            line_number += 1
                            line = line.strip()

                            tweet_out_string = tweetprocessing.process_tweet(line, track_list, expand_url=EXPAND_URLS)
                            f_out.write(tweet_out_string)
                            tweet_total += 1
                            # print tweet_out_string

                        except ValueError as e:
                            lost_tweets += 1
                            print("ValueError. tweet not processed: %d (%s)" % (line_number, rawTweetsFile))
                            logger.warning("tweet not processed: %d (%s)" % (line_number, rawTweetsFile))
                            logging.exception(e)
                            error_tweet.write(line + "\n")
                            print(traceback.format_exc())
                            pass
                        except TypeError as e:
                            lost_tweets += 1
                            print("TypeError. tweet not processed: %d (%s)" % (line_number, rawTweetsFile))
                            logger.warning("tweet not processed: %d (%s)" % (line_number, rawTweetsFile))
                            logging.exception(e)
                            error_tweet.write(line + "\n")
                            print(traceback.format_exc())
                            pass
                        except KeyError as e:
                            lost_tweets += 1
                            print("KeyError. tweet not processed: %d (%s)" % (line_number, rawTweetsFile))
                            logger.warning("tweet not processed: %d (%s)" % (line_number, rawTweetsFile))
                            logging.exception(e)
                            error_tweet.write(line + "\n")
                            print(traceback.format_exc())
                            pass
                elif '-streamlimits-' in rawTweetsFile:
                    server_name = os.uname()[1]
                    try:
                        collector_id = rawTweetsFile.split('-')[6]
                        collector = db.get_collector_detail(project_id=project_id, collector_id=collector_id)
                        col_type = collector['collector']['api']
                    except:
                        col_type = 'UNDEFINED'
                    for line in f:
                        line = line.strip()
                        limit_out_string = tweetprocessing.process_limit(line, col_type, server_name, project_name,
                                                                         project_id, collector_id)
                        f_out.write(limit_out_string)

            f_out.close()
            f.close()

            logger.info('Tweets processed: %d, lost: %d' % (tweet_total, lost_tweets))

            archive_processed_file(Config, rawTweetsFile, logger, rawdir, archdir)
            queue_up_processed_tweets(Config, processed_tweets_file, logger, archdir, insertdir)

        # Incrementally delays reconnect if Mongo is offline
        exception = None
        max_sleep_time = 1800
        try:
            module_config = project_config_db.find_one({'module': 'twitter'})
            runPreProcessor = module_config['processor']['run']
        # If mongo is unavailable, decrement processing loop by 2 sec.
        # increments until connection is re-established.
        except Exception as exception:
            print('Mongo connection for preprocessor refused with exception: %s' % exception)
            logger.error('Mongo connection for preprocessor refused with exception: %s' % exception)
            runLoopSleep += 2
            time.sleep(runLoopSleep)

    error_tweet.close()
    logger.info('Exiting preprocessor Program...')
    print('Exiting preprocessor Program...')

    # Reference for controller if script is active or not.
    project_config_db.update({'module': 'twitter'}, {'$set': {'processor_active': 0}})




