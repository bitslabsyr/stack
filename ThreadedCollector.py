#-------------------------------------------------------------------------------
# Name:        Tweet collector.
# Purpose:     Collects tweets based on search terms specified in a terms file
#              Sends tweets as JSON to a file.
#
# Author:      jhemsley
#
# Created:     2013/07/10
# Copyright:   (c) Social Media Lab 2013
# Licence:     <your licence>
#
# Code for this is based on both of these
#   https://github.com/tweepy/tweepy/blob/master/examples/streaming.py
#   https://github.com/arngarden/TwitterStream
#   http://log.widnyana.web.id/2012/05/simple-python-twitter-client-using-tweepy.txt
#
# HOW IT WORKS:
# This process reads a document in the mongo config collection. As of this writting
# the document looks like this:
#   {'module': 'collector', 'run': 1, 'collect': 0, 'update': 0}
# When run=1 this system enters a loop and checks mongo for changes to the signal
# flags: run, collect & update. In the conditions noted below, a worker thread is
# started that collects data from Twitter's streaming API while the main thread
# continues to watch mongo for signals.
#   When RUN is set to 0, stop thread and exit process, otherwise continue
#   When collect is 1, start worker thread. if collect is 0, stop worker thread.
#   When UPDATE is 1, stop thread, change update flag in mongo to 0. note that
#      if the collect flag is 1, then the process will start a worker
#
# Also of note, this system reads platform.ini for config items. One of these sets
# how frequently output JSON files are rolled over. The file name is built using
# three items in the platform.ini:
#  raw_tweets_file_path is the directory location where the output files will go
#  tweets_file_date_frmt is a date format string and is used to build the tweets
#         out file name as well as indicate when the file should rool over. The
#         fastest possible roll over (not reccomended) is seconds and is specified
#         with %Y%m%d-%H%M%S. For testing use minutes (%Y%m%d-%H%M) r hours
#         (%Y%m%d-%H), but for collection use hours or days (%Y%m%d)
#  tweets_file is a suffix for the file name.
#  the final constructed file name will be something like:
#         ./tweets/20130822-1030tweets_out.json
#
#-------------------------------------------------------------------------------

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweetstream import CompliantStream
from pymongo import Connection
import threading
import os.path
import json
import ConfigParser
import datetime
import logging
import logging.config
import time
import traceback

# Config file includes paths, parameters, and oauth information for this module
# Complete the directions in "example_platform.ini" for configuration before proceeding
# TODO - Continue using .ini file, or move to MySQL store?
PLATFORM_CONFIG_FILE = 'platform.ini'

# Connect to Mongo
# SYNC - Connection() is deprecated. Also, collection = "config" here?
connection = Connection()
db = connection.config
mongo_config = db.config

# Program thread
e = threading.Event()

class fileOutListener(StreamListener):
    """ This listener handles tweets as they come in by converting them
    to JSON and sending them to a file. Each line in the file is a tweet.
    """
    def __init__(self, tweetsOutFilePath, tweetsOutFileDateFrmt, tweetsOutFile, logger):
        self.logger = logger
        self.logger.info('COLLECTION LISTENER: Initializing Stream Listener...')
        self.buffer = ''
        self.tweet_count = 0
        self.rate_limit_count = 0
        self.error_code = 0

        self.tweetsOutFilePath = tweetsOutFilePath
        self.tweetsOutFileDateFrmt = tweetsOutFileDateFrmt
        self.tweetsOutFile = tweetsOutFile

        timestr = time.strftime(self.tweetsOutFileDateFrmt)

        self.tweetsOutFileName = self.tweetsOutFilePath + timestr + self.tweetsOutFile
        self.logger.info('COLLECTION LISTENER: initial data collection file: %s' % self.tweetsOutFileName)

        #self.e = e


    def on_data(self, data):
        self.buffer += data

        event_is_set = e.isSet()
        if event_is_set:
            print '\n\nGOT EVENT SIGNAL'
            self.logger.info('COLLECTION LISTENER: Attempting to disconnect...')
            e.clear()
            return False
            # return false ends the streaming process

        if data.endswith('\r\n') and self.buffer.strip():
            # complete message received so convert to JSON and proceed
            message = json.loads(self.buffer)
            self.buffer = ''
            msg = ''
            # TODO - Rate limiting from logs => Mongo?
            if message.get('limit'):
                self.logger.warning('COLLECTION LISTENER: Rate limiting caused us to miss %s tweets' % (message['limit'].get('track')))
                self.rate_limit_count += int(message['limit'].get('track'))
                print 'Rate limiting caused us to miss %s tweets' % (message['limit'].get('track'))
            elif message.get('disconnect'):
                self.logger.info('COLLECTION LISTENER: Got disconnect: %s' % message['disconnect'].get('reason'))
                raise Exception('Got disconnect: %s' % message['disconnect'].get('reason'))
            elif message.get('warning'):
                self.logger.info('COLLECTION LISTENER: Got warning: %s' % message['warning'].get('message'))
                print 'Got warning: %s' % message['warning'].get('message')
            else:
                self.tweet_count += 1

                # just echo the tweet text to the console
                # print '%d %s' % (self.tweet_count, message.get('text').encode('utf-8'))

                # this is a timestamp using the format in the config
                timestr = time.strftime(self.tweetsOutFileDateFrmt)
                # this creates the filename. If the file exists, it just adds to it, otherwise it creates it
                JSONfileName = self.tweetsOutFilePath + timestr + self.tweetsOutFile
                if not os.path.isfile(JSONfileName):
                    self.logger.info('Creating new file: %s' % JSONfileName)
                myFile = open(JSONfileName,'a')
                myFile.write(json.dumps(message).encode('utf-8'))
                myFile.write('\n')
                myFile.close()
                return True

    # TODO - Work w/ Error Codes
    def on_error(self, status):
        # Twitter's http error codes are listed here:
        # https://dev.twitter.com/docs/streaming-apis/connecting#Reconnecting
        # some of these we ought to do something about, and others not.
        # For the short term we will log the status and do something to stop
        # our own collection service.
        self.logger.error('COLLECTION LISTENER: Twitter refused or aborted our connetion with the following error code: %d' % status)
        print 'COLLECTION LISTENER: Twitter refused or aborted our connetion with the following error code: %d' % status
        self.error_code = status
        # return false stops the stream loop, and thus the thread
        return False



def worker(tweetsOutFilePath, tweetsOutFileDateFrmt, tweetsOutFile, logger, auth, termsList):
    l = fileOutListener(tweetsOutFilePath, tweetsOutFileDateFrmt, tweetsOutFile, logger)
    stream = CompliantStream(auth, l, 10, logger)
    # TODO - Filter method part of tweepy.Stream?
    stream.filter(track=termsList)
    logger.info('COLLECTION THREAD: stream stopped after %d tweets' % l.tweet_count)
    logger.info('COLLECTION THREAD: lost %d tweets to rate limit' % l.rate_limit_count)
    print 'COLLECTION THREAD: stream stopped after %d tweets' % l.tweet_count

    if not l.error_code == 0:
        mongo_config.update({"module" : "collector"}, {'$set' : {'collect': 0}})
        mongo_config.update({"module" : "collector"}, {'$set' : {'error_code': l.error_code}})

    if not l.rate_limit_count == 0:
        mongo_config.update({"module" : "collector"}, {'$set' : {'rate_limit': l.rate_limit_count}})


def main():
    Config = ConfigParser.ConfigParser()
    Config.read(PLATFORM_CONFIG_FILE)

    # Grabs logging info (directory, filename) from config file
    logDir = Config.get('files', 'log_dir', 0)
    logConfigFile = Config.get('files', 'log_config_file', 0)
    logging.config.fileConfig(logConfigFile)
    logging.addLevelName('root', 'collector')
    logger = logging.getLogger('collector')

    # Sets current date as starting point
    tmpDate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info('Starting collection system at %s' % tmpDate)

    # Grabs collection name from config
    collectionName = Config.get('collection', 'name', 0)
    logger.info('Collection name: %s' % collectionName)

    # Grabs terms list file from config
    termsListFile = Config.get('files', 'terms_file', 0)

    # Grabs tweets out file info from config
    tweetsOutFilePath = Config.get('files', 'raw_tweets_file_path', 0)
    if not os.path.exists(tweetsOutFilePath):
        os.makedirs(tweetsOutFilePath)
    tweetsOutFileDateFrmt = Config.get('files', 'tweets_file_date_frmt', 0)
    tweetsOutFile = Config.get('files', 'tweets_file', 0)

    consumerKey = Config.get('oauth', 'consumer_key', 0)
    consumerSecret = Config.get('oauth', 'consumer_secret', 0)
    accessToken = Config.get('oauth', 'access_token', 0)
    accessTokenSecret = Config.get('oauth', 'access_token_secret', 0)

    # Authenticates via app info
    auth = OAuthHandler(consumerKey, consumerSecret)
    auth.set_access_token(accessToken, accessTokenSecret)

    # Sets Mongo collection; sets rate_limitng & error counts to 0
    mongoConfigs = mongo_config.find_one({"module" : "collector"})
    mongo_config.update({"module" : "collector"}, {'$set' : {'rate_limit': 0}})
    mongo_config.update({"module" : "collector"}, {'$set' : {'error_code': 0}})

    # Should be 1 by default
    runCollector = mongoConfigs['run']

    if runCollector:
        print 'Starting process'
        logger.info('Collection start signal %d' % runCollector)
    collectingData = False

    i = 0
    myThreadCounter = 0

    while runCollector:
        i += 1

        # Finds Mongo collection & grabs signal info
        mongoConfigs = mongo_config.find_one({"module" : "collector"})
        runCollector = mongoConfigs['run']
        collectSignal = mongoConfigs['collect']
        updateSignal = mongoConfigs['update']

        """
        Collection process is running, and:
        A) An update has been triggered -OR-
        B) The collection signal is not set -OR-
        C) Run signal is not set
        """
        # TODO - Test all command statements
        if collectingData and (updateSignal or not collectSignal or not runCollector):
            # Update has been triggered
            if updateSignal:
                logger.info('MAIN: received UPDATE signal. Attempting to stop collection thread')
                mongo_config.update({"module" : "collector"}, {'$set' : {'update': 0}})
            # Collection thread triggered to stop
            if not collectSignal:
                logger.info('MAIN: received STOP signal. Attempting to stop collection thread')
            # Entire process trigerred to stop
            if not runCollector:
                logger.info('MAIN: received EXIT signal. Attempting to stop collection thread')
                mongo_config.update({"module" : "collector"}, {'$set' : {'collect': 0}})
                mongo_config.update({"module" : "collector"}, {'$set' : {'update': 0}})
                collectSignal = 0

            # TODO - termination bug
            e.set()
            tmpWait = 0
            while tmpWait < 20 and t.isAlive():
                logger.info('%d - Waiting for %s to end ...' % (tmpWait, t.name))
                print '%d - Waiting for %s to end ...' % (tmpWait, t.name)
                tmpWait += 1
                # TODO - Time library
                time.sleep( tmpWait )
            if t.isAlive():
                logger.warning ('MAIN: unable to stop collection thread %s and event flag status is %s' % (t.name, e.isSet()))
                print 'MAIN: unable to stop collection thread %s and event flag status is %s' % (t.name, e.isSet())
            else:
                collectingData = False
                e.clear()

        # Collection has been signaled & main program thread is running
        if collectSignal and (threading.activeCount() == 1):
            # Names collection thread & adds to counter
            myThreadCounter += 1
            myThreadName = 'collector%s' % myThreadCounter

            # Reads & logs terms list
            with open(termsListFile) as f:
                termsList = f.read().splitlines()
            print(termsList)
            logger.info('Terms list: %s' % str(termsList).strip('[]'))

            # Starts collection thread, runs the worker() method
            t = threading.Thread(name=myThreadName, target=worker, args=(tweetsOutFilePath, tweetsOutFileDateFrmt, tweetsOutFile, logger, auth, termsList))
            t.start()
            collectingData = True
            print 'MAIN: Collection thread started (%s)' % myThreadName
            logger.info('MAIN: Collection thread started (%s)' % myThreadName)


        #if threading.activeCount() == 1:
        #    print "MAIN: %d iteration with no collection thread running" % i
        #else:
        #    print "MAIN: %d iteration with collection thread running (%d)" % (i, threading.activeCount())
        time.sleep( 2 )

    logger.info('Exiting Collection Program...')
    print 'Exiting Collection Program...'

    #logging.shutdown()





