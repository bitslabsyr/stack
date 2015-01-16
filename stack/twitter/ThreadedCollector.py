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

import sys

from tweepy.streaming import StreamListener, Stream
from tweepy.error import TweepError
from tweepy import OAuthHandler
from tweepy.api import API
from pymongo import MongoClient

from . import module_dir
from stack.db import DB

import httplib
from socket import timeout
import ssl
import threading
import os.path
import json
import ConfigParser
import datetime
import logging
import logging.config
import time
from time import sleep
import traceback
from bson.objectid import ObjectId

# Config file includes paths, parameters, and oauth information for this module
# Complete the directions in "example_platform.ini" for configuration before proceeding

PLATFORM_CONFIG_FILE = module_dir + '/platform.ini'

# Connect to Mongo
db = DB()

# Program thread
e = threading.Event()

class fileOutListener(StreamListener):
    """ This listener handles tweets as they come in by converting them
    to JSON and sending them to a file. Each line in the file is a tweet.
    """
    def __init__(self, tweetsOutFilePath, tweetsOutFileDateFrmt, tweetsOutFile, logger, collection_type, project_id, collector_id):
        self.logger = logger
        self.logger.info('COLLECTION LISTENER: Initializing Stream Listener...')
        self.buffer = ''
        self.tweet_count = 0
        self.delete_count = 0

        self.limit_count = 0 # Count of tweets lost due to stream limits
        self.rate_limit_count = 0 # Count of times our conn is rate limited
        self.error_code = 0 # Last error code received before forced shutdown

        self.tweetsOutFilePath = tweetsOutFilePath
        self.tweetsOutFileDateFrmt = tweetsOutFileDateFrmt
        self.tweetsOutFile = tweetsOutFile
        self.collection_type = collection_type
        self.project_id = project_id
        self.collector_id = collector_id

        resp = db.get_collector_detail(self.project_id, self.collector_id)
        self.collector = resp['collector']

        project = db.get_project_detail(project_id)
        self.project_config_db = project['project_config_db']

        timestr = time.strftime(self.tweetsOutFileDateFrmt)
        self.tweetsOutFileName = self.tweetsOutFilePath + timestr + '-' + self.collector['collector_name'] + '-' + self.project_id + '-' + self.collector_id + '-' + self.tweetsOutFile
        self.logger.info('COLLECTION LISTENER: initial data collection file: %s' % self.tweetsOutFileName)

        self.db_name = self.collector_id + '_' + self.collector['collector_name']
        self.delete_db = self.db_name + '_delete'
        self.delete_db = db.connection[self.delete_db]
        self.delete_tweets = self.delete_db['tweets']

    def on_data(self, data):
        self.buffer += data

        exception = None
        try:
            if data.endswith('\r\n') and self.buffer.strip():
                # complete message received so convert to JSON and proceed
                message = json.loads(self.buffer)
                self.buffer = ''
                msg = ''
                # Rate limiting logging
                if message.get('limit'):
                    self.on_limit(message)

                # Disconnect message handling
                elif message.get('disconnect'):
                    self.on_disconnect(message)

                # Warning handling
                elif message.get('warning'):
                    self.logger.info('COLLECTION LISTENER: Got warning: %s' % message['warning'].get('message'))
                    print 'Got warning: %s' % message['warning'].get('message')

                # Delete Collection
                elif message.get('delete'):
                    self.on_delete(message)

                # Else good to go, read data
                else:
                    self.tweet_count += 1

                    # this is a timestamp using the format in the config
                    timestr = time.strftime(self.tweetsOutFileDateFrmt)
                    # this creates the filename. If the file exists, it just adds to it, otherwise it creates it
                    JSONfileName = self.tweetsOutFilePath + timestr + '-' + self.collector['collector_name'] + '-' + self.project_id + '-' + self.collector_id + '-' + self.tweetsOutFile
                    if not os.path.isfile(JSONfileName):
                        self.logger.info('Creating new file: %s' % JSONfileName)
                    myFile = open(JSONfileName,'a')
                    myFile.write(json.dumps(message).encode('utf-8'))
                    myFile.write('\n')
                    myFile.close()
                    return True

        except (ValueError, TypeError, KeyError) as e:
            print 'COLLECTION LISTENER: Exception raised upon data handling\n%s\n' % e
            print 'Check logs for problematic data.'
            self.logger.error('ERROR: Fatal exception raised upon data handling\n%s\n' % e)
            self.logger.error('Logging problematic data.')
            self.logger.error(message)
            self.buffer = ''
            msg = ''

        except Exception as exception:
            print 'COLLECTION LISTENER: Unkown data handling exception caught.\n%s' % exception
            print 'Check logs for problematic data.'
            self.logger.error('COLLECTION LISTENER: Unkown data handling exception caught.\n%s' % exception)
            self.logger.error('Logging problematic data.')
            self.logger.error(message)
            self.buffer = ''
            msg = ''

    def on_delete(self, message):
        """
        Handles delete tweets
        """
        self.delete_count += 1

        timestr = time.strftime(self.tweetsOutFileDateFrmt)
        JSONfileName = self.tweetsOutFilePath + timestr + '-' + self.collector['collector_name'] + '-delete-' + self.project_id + '-' + self.collector_id + '-' + self.tweetsOutFile
        if not os.path.isfile(JSONfileName):
            self.logger.info('Creating new file: %s' % JSONfileName)
        myFile = open(JSONfileName,'a')
        myFile.write(json.dumps(message).encode('utf-8'))
        myFile.write('\n')
        myFile.close()
        return True

    def on_limit(self, message):
        """
        Handles limit notices
        """
        self.logger.warning('COLLECTION LISTENER: Stream rate limiting caused us to miss %s tweets' % (message['limit'].get('track')))
        print 'Stream rate limiting caused us to miss %s tweets' % (message['limit'].get('track'))

        rate_limit_info = { 'date': now, 'lost_count': int(message['limit'].get('track')) }
        self.project_config_db.update({
            '_id': ObjectId(self.collector_id)},
            {"$push": {"stream_limit_loss.counts": rate_limit_info}})

        # Total tally
        self.limit_count += int(message['limit'].get('track'))
        return True

    def on_disconnect(self, message):
        """Called when twitter sends a disconnect notice

        Disconnect codes are listed here:
        https://dev.twitter.com/docs/streaming-apis/messages#Disconnect_messages_disconnect
        """
        print 'COLLECTION LISTENER: Got disconnect: %s' % message['disconnect'].get('reason')
        self.logger.info('COLLECTION LISTENER: Got disconnect: %s' % message['disconnect'].get('reason'))
        return False

    # Twitter's http error codes are listed here:
    # https://dev.twitter.com/streaming/overview/connecting
    # Starts retry loop for:
    #   A) 420 - rate limited
    #   B) 503 - service unavailable
    # Otherwise, stops stream & logs error info
    def on_error(self, status):
        self.error_code = status
        now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

        # Retries if rate limited (420) or unavailable (520)
        if status in [420, 503]:
            if status == 420:
                self.logger.error('COLLECTION LISTENER: Twitter rate limited our connection with error code: %d. Retrying.' % status)
                print 'COLLECTION LISTENER: Twitter rate limited our connection at %s with error code: %d. Retrying.' % (now, status)
                self.rate_limit_count += 1
            else:
                self.logger.error('COLLECTION LISTENER: Twitter service is currently unavailable with error code: %d. Retrying.' % status)
                print 'COLLECTION LISTENER: Twitter service is currently unavailable at %s with error code: %d. Retrying.' % (now,status)
            return True # Initiates retry backoff loop
        else:
            self.logger.error('COLLECTION LISTENER: Twitter refused or aborted our connetion with the following error code: %d. Shutting down.' % status)
            print 'COLLECTION LISTENER: Twitter refused or aborted our connetion with the following error code: %d. Shutting down at %s' % (status, now)
            return False # Breaks stream

# Extends Tweepy's Stream class to include our logging
class ToolkitStream(Stream):

    host = 'stream.twitter.com'

    def __init__(self, auth, listener, logger, **options):
        self.auth = auth
        self.listener = listener
        self.running = False
        self.timeout = options.get("timeout", 300.0)
        self.retry_count = options.get("retry_count")
        self.retry_time_start = options.get("retry_time", 5.0)
        self.retry_420_start = options.get("retry_420", 60.0)
        self.retry_time_cap = options.get("retry_time_cap", 320.0)
        self.snooze_time_step = options.get("snooze_time", 0.25)
        self.snooze_time_cap = options.get("snooze_time_cap", 16)
        self.buffer_size = options.get("buffer_size",  1500)
        if options.get("secure", True):
            self.scheme = "https"
        else:
            self.scheme = "http"

        self.api = API()
        self.headers = options.get("headers") or {}
        self.parameters = None
        self.body = None
        self.retry_time = self.retry_time_start
        self.snooze_time = self.snooze_time_step

        self.logger = logger
        self.logger.info('TOOLKIT STREAM: Stream initialized.')
        print 'TOOLKIT STREAM: Stream initialized.'

    def _run(self):
        # Authenticate
        url = "%s://%s%s" % (self.scheme, self.host, self.url)

        # Connect and process the stream
        error_counter = 0
        conn = None
        exception = None
        while self.running:
            if self.retry_count is not None and error_counter > self.retry_count:
                self.logger.info('TOOLKIT STREAM: Stream stopped after %d retries.' % self.retry_count)
                break
            try:
                if self.scheme == "http":
                    conn = httplib.HTTPConnection(self.host, timeout=self.timeout)
                else:
                    conn = httplib.HTTPSConnection(self.host, timeout=self.timeout)
                self.auth.apply_auth(url, 'POST', self.headers, self.parameters)
                conn.connect()
                conn.request('POST', self.url, self.body, headers=self.headers)
                resp = conn.getresponse()
                if resp.status != 200:
                    if self.listener.on_error(resp.status) is False:
                        break
                    error_counter += 1
                    print 'Retry count %d of %d.' % (error_counter, self.retry_count)
                    self.logger.info('Retry count %d of %d.' % (error_counter, self.retry_count))
                    if resp.status == 420:
                        self.retry_time = max(self.retry_420_start, self.retry_time)
                    print 'Retry time: %d seconds.' % self.retry_time
                    self.logger.info('Retry time: %d seconds.' % self.retry_time)
                    sleep(self.retry_time)
                    self.retry_time = min(self.retry_time * 2, self.retry_time_cap)
                else:
                    error_counter = 0
                    self.retry_time = self.retry_time_start
                    self.snooze_time = self.snooze_time_step
                    self.listener.on_connect()
                    self._read_loop(resp)
            except (timeout, ssl.SSLError) as exc:
                # If it's not time out treat it like any other exception
                if isinstance(exc, ssl.SSLError) and not (exc.args and 'timed out' in str(exc.args[0])):
                    exception = exc
                    break

                if self.listener.on_timeout() == False:
                    break
                if self.running is False:
                    break
                conn.close()
                sleep(self.snooze_time)
                self.snooze_time = min(self.snooze_time + self.snooze_time_step,
                                       self.snooze_time_cap)
            except Exception as exception:
                print 'TOOKLKIT STREAM: Unkown stream exception caught.\n%s' % exception
                print 'Retrying in %d seconds.' % self.retry_time_cap
                self.logger.error('TOOKLKIT STREAM: Unkown stream exception caught.\n%s' % exception)
                self.logger.error('Retrying in %d seconds.' % self.retry_time_cap)

                sleep(self.retry_time_cap)

        e.set()

        resp = db.get_collector_detail(listener.project_id, listener.collector_id)
        if resp['collector']['collector']['collect']:
            print 'TOOKLKIT STREAM: Terminating collection due to unknown issue. Please consult the disconnect info below.'
            self.logger.error('TOOKLKIT STREAM: Terminating collection due to unknown issue. Please consult the disconnect info below.')
            db.set_collector_status(listener.project_id, listener.collector_id, collector_status=0)

        self.running = False
        if conn:
            conn.close()

    def disconnect(self):
        print 'TOOLKIT STREAM: Streaming API disconnect initiated.'
        self.logger.info('TOOLKIT STREAM: Streaming API disconnect initiated.')
        if self.running is False:
            return
        self.running = False

def go(collection_type, project_id, collector_id):
    if collection_type not in ['track', 'follow', 'none']:
        print "ThreadedCollector accepts inputs 'track', 'follow', or 'none'."
        print 'Exiting with invalid params...'
        sys.exit()
    else:
        # Grab collector & project details from DB
        project = db.get_project_detail(project_id)
        resp = db.get_collector_detail(project_id, collector_id)

        if project['status'] and resp['status']:
            collector = resp['collector']
            configdb = project['project_config_db']
            project_config_db = db.connection[configdb]
            project_config_db = project_config_db.config
            collector_name = collector['collector_name']
            project_name = project['project_name']
        else:
            'Invalid project account & collector. Try again!'

    module_config = project_config_db.find_one({'module': 'twitter'})

    # Reference for controller if script is active or not.
    project_config_db.update({'_id': ObjectId(collector_id)}, {'$set': {'active': 1}})

    Config = ConfigParser.ConfigParser()
    Config.read(PLATFORM_CONFIG_FILE)

    # Grabs logging director info & creates if doesn't exist
    logDir = module_dir + Config.get('files', 'log_dir', 0)
    if not os.path.exists(logDir):
        os.makedirs(logDir)

    # Creates logger w/ level INFO
    logger = logging.getLogger(collector_name)
    logger.setLevel(logging.INFO)
    # Creates rotating file handler w/ level INFO
    # NAMING CONVENTION - [collector_id]-log-[twitter_api_name].out
    fh = logging.handlers.TimedRotatingFileHandler(module_dir + '/logs/' + project_name + '-' + collector_name + '-' + collection_type + '-collector-log-' + collector_id + '.out', 'D', 1, 30, None, False, False)
    fh.setLevel(logging.INFO)
    # Creates formatter and applies to rotating handler
    format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    datefmt = '%m-%d %H:%M'
    formatter = logging.Formatter(format, datefmt)
    fh.setFormatter(formatter)
    # Finishes by adding the rotating, formatted handler
    logger.addHandler(fh)

    # Sets current date as starting point
    tmpDate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info('Starting collection system at %s' % tmpDate)
    logger.info('Collector name: %s' % collector_name)

    # Grabs tweets out file info from config
    # TODO - move this info to Mongo
    tweetsOutFilePath = module_dir + module_config['raw_tweets_dir']
    if not os.path.exists(tweetsOutFilePath):
        os.makedirs(tweetsOutFilePath)
    tweetsOutFileDateFrmt = Config.get('files', 'tweets_file_date_frmt', 0)
    tweetsOutFile = Config.get('files', 'tweets_file', 0)

    # NOTE - proper naming for api_auth dictionary from front_end
    # TODO (mook) - api_auth should be a straight document, not array of documents
    oauth_info = collector['api_auth']

    consumerKey = oauth_info['consumer_key']
    consumerSecret = oauth_info['consumer_secret']
    accessToken = oauth_info['access_token']
    accessTokenSecret = oauth_info['access_token_secret']

    # Authenticates via app info
    auth = OAuthHandler(consumerKey, consumerSecret)
    auth.set_access_token(accessToken, accessTokenSecret)

    # Sets Mongo collection; sets rate_limitng & error counts to 0
    if 'stream_limit_loss' not in collector:
        project_config_db.update({'_id': ObjectId(collector_id)}, {'$set' : { 'stream_limit_loss': { 'counts': [], 'total': 0 }}})

    if 'rate_limit_count' not in collector:
        project_config_db.update({'_id': ObjectId(collector_id)}, {'$set': {'rate_limit_count': 0}})

    if 'error_code' not in collector:
        project_config_db.update({"_id" : ObjectId(collector_id)}, {'$set' : {'error_code': 0}})

    runCollector = collector['collector']['run']

    if runCollector:
        print 'Starting process w/ start signal %d' % runCollector
        logger.info('Starting process w/ start signal %d' % runCollector)
    collectingData = False

    i = 0
    myThreadCounter = 0
    runLoopSleep = 0

    while runCollector:
        i += 1

        # Finds Mongo collection & grabs signal info
        # If Mongo is offline throws an acception and continues
        exception = None
        try:
            resp = db.get_collector_detail(project_id, collector_id)
            collector = resp['collector']
            flags = collector['collector']
            runCollector = flags['run']
            collectSignal = flags['collect']
            updateSignal = flags['update']
        except Exception, exception:
            logger.info('Mongo connection refused with exception: %s' % exception)

        """
        Collection process is running, and:
        A) An update has been triggered -OR-
        B) The collection signal is not set -OR-
        C) Run signal is not set
        """
        if collectingData and (updateSignal or not collectSignal or not runCollector):
            # Update has been triggered
            if updateSignal:
                logger.info('MAIN: received UPDATE signal. Attempting to stop collection thread')
                resp = db.set_collector_status(project_id, collector_id, collector_status=1)
            # Collection thread triggered to stop
            if not collectSignal:
                logger.info('MAIN: received STOP signal. Attempting to stop collection thread')
            # Entire process trigerred to stop
            if not runCollector:
                logger.info('MAIN: received EXIT signal. Attempting to stop collection thread')
                resp = db.set_collector_status(project_id, collector_id, collector_status=0)
                collectSignal = 0

            # Send stream disconnect signal, kills thread
            stream.disconnect()
            wait_count = 0
            while e.isSet() is False:
                wait_count += 1
                print '%d) Waiting on collection thread shutdown' % wait_count
                sleep(wait_count)

            collectingData = False

            logger.info('COLLECTION THREAD: stream stopped after %d tweets' % l.tweet_count)
            logger.info('COLLECTION THREAD: collected %d error tweets' % l.delete_count)
            print 'COLLECTION THREAD: collected %d error tweets' % l.delete_count
            logger.info('COLLECTION THREAD: lost %d tweets to stream rate limit' % l.limit_count)
            print 'COLLECTION THREAD: lost %d tweets to stream rate limit' % l.limit_count
            print 'COLLECTION THREAD: stream stopped after %d tweets' % l.tweet_count

            if not l.error_code == 0:
                resp = db.set_collector_status(project_id, collector_id, collector_status=0)
                project_config_db.update({"_id" : ObjectId(collector_id)}, {'$set' : {'error_code': l.error_code}})

            if not l.limit_count == 0:
                project_config_db.update({'_id': ObjectId(collector_id)}, {'$set' : { 'stream_limit_loss.total': l.limit_count}})

            if not l.rate_limit_count == 0:
                project_config_db.update({'_id': ObjectId(collector_id)}, {'$set': {'rate_limit_count': 0}})

        # Collection has been signaled & main program thread is running
        # TODO - Check Mongo for handle:ID pairs
        # Only call for new pairs
        if collectSignal and (threading.activeCount() == 1):
            # Names collection thread & adds to counter
            myThreadCounter += 1
            myThreadName = 'collector-' + collection_type + '%s' % myThreadCounter

            termsList = collector['terms_list']
            if termsList:
                print 'Terms list length: ' + str(len(termsList))

                # Grab IDs for follow stream
                if collection_type == 'follow':
                    """
                    TODO - Update Mongo terms w/ set for collect status 0 or 1
                    # Updates current stored handles to collect 0 if no longer listed in terms file
                    stored_terms = doc['termsList']
                    for user in stored_terms:
                        if user['handle'] not in termsList:
                            user_id = user['id']
                            mongo_config.update({'module': 'collector-follow'},
                                {'$pull': {'termsList': {'handle': user['handle']}}})
                            mongo_config.update({'module': 'collecting-follow'},
                                {'$set': {'termsList': {'handle': user['handle'], 'id': user_id, 'collect': 0 }}})

                    # Loops thru current stored handles and adds list if both:
                    #   A) Value isn't set to None (not valid OR no longer in use)
                    all_stored_handles = [user['handle'] for user in stored_terms]
                    stored_handles = [user['handle'] for user in stored_terms if user['id'] and user['collect']]

                    print 'MAIN: %d user ids for collection found in Mongo!' % len(stored_handles)
                    """

                    # Loop thru & query (except handles that have been stored)
                    print 'MAIN: Querying Twitter API for handle:id pairs...'
                    logger.info('MAIN: Querying Twitter API for handle:id pairs...')
                    # Initiates REST API connection
                    twitter_api = API(auth_handler=auth)
                    failed_handles = []
                    success_handles = []
                    # Loops thru user-given terms list
                    for item in termsList:
                        term = item['term']
                        # If term already has a valid ID, pass
                        if item['id'] is not None:
                            pass
                        # Queries the Twitter API for the ID value of the handle
                        else:
                            try:
                                user = twitter_api.get_user(screen_name=term)
                            except TweepError as tweepy_exception:
                                error_message = tweepy_exception.args[0][0]['message']
                                code = tweepy_exception.args[0][0]['code']
                                # Rate limited for 15 minutes w/ code 88
                                if code == 88:
                                    print 'MAIN: User ID grab rate limited. Sleeping for 15 minutes.'
                                    logger.exception('MAIN: User ID grab rate limited. Sleeping for 15 minutes.')
                                    time.sleep(900)
                                # Handle doesn't exist, added to Mongo as None
                                elif code == 34:
                                    print 'MAIN: User w/ handle %s does not exist.' % handle
                                    logger.exception('MAIN: User w/ handle %s does not exist.' % term)
                                    item['collect'] = 0
                                    item['id'] = None
                                    failed_handles.append(term)
                            # Success - handle:ID pair stored in Mongo
                            else:
                                user_id = user._json['id_str']
                                item['id'] = user_id
                                success_handles.append(term)

                    print 'MAIN: Collected %d new ids for follow stream.' % len(success_handles)
                    logger.info('MAIN: Collected %d new ids for follow stream.' % len(success_handles))
                    print 'MAIN: %d handles failed to be found.' % len(failed_handles)
                    logger.info('MAIN: %d handles failed to be found.' % len(failed_handles))
                    logger.info(failed_handles)
                    print failed_handles
                    print 'MAIN: Grabbing full list of follow stream IDs from Mongo.'
                    logger.info('MAIN: Grabbing full list of follow stream IDs from Mongo.')

                    # Updates term list with follow values
                    project_config_db.update({'_id': ObjectId(collector_id)},
                        {'$set': {'terms_list': termsList}})

                    # Loops thru current stored handles and adds to list if:
                    #   A) Value isn't set to None (not valid OR no longer in use)
                    ids = [item['id'] for item in termsList if item['id'] and item['collect']]
                    termsList = ids
                else:
                    terms = [item['term'] for item in termsList if item['collect']]
                    termsList = terms

                print termsList

                logger.info('Terms list: %s' % str(termsList).strip('[]'))

            print 'COLLECTION THREAD: Initializing Tweepy listener instance...'
            logger.info('COLLECTION THREAD: Initializing Tweepy listener instance...')
            l = fileOutListener(tweetsOutFilePath, tweetsOutFileDateFrmt, tweetsOutFile, logger, collection_type, project_id, collector_id)

            print 'TOOLKIT STREAM: Initializing Tweepy stream listener...'
            logger.info('TOOLKIT STREAM: Initializing Tweepy stream listener...')

            # Initiates async stream via Tweepy, which handles the threading
            # TODO - location & language

            languages = collector['languages']
            location = collector['location']

            if languages:
                print '%s language codes found!' % len(languages)
            if location:
                print 'Location points found!'
                for i in range(len(location)):
                    location[i] = float(location[i])

            stream = ToolkitStream(auth, l, logger, retry_count=100)
            if collection_type == 'track':
                stream.filter(track=termsList, languages=languages, locations=location, async=True)
            elif collection_type == 'follow':
                stream.filter(follow=termsList, languages=languages, locations=location, async=True)
            elif collection_type == 'none':
                stream.filter(locations=location, languages=languages, async=True)
            else:
                sys.exit('ERROR: Unrecognized stream filter.')

            collectingData = True
            print 'MAIN: Collection thread started (%s)' % myThreadName
            logger.info('MAIN: Collection thread started (%s)' % myThreadName)


        #if threading.activeCount() == 1:
        #    print "MAIN: %d iteration with no collection thread running" % i
        #else:
        #    print "MAIN: %d iteration with collection thread running (%d)" % (i, threading.activeCount())

        # Incrementally delays loop if Mongo is offline, otherwise 2 seconds
        if exception:
            print "Exception caught, sleeping for: %d" % runLoopSleep
            runLoopSleep += 2
            time.sleep(runLoopSleep)
        else:
            time.sleep( 2 )

    logger.info('Exiting Collection Program...')
    print 'Exiting Collection Program...'

    # Reference for controller if script is active or not.
    project_config_db.update({'_id': ObjectId(collector_id)}, {'$set': {'active': 0}})
