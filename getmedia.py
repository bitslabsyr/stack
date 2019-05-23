"""
    Functions to create local copies of embedded media in tweets
"""

from datetime import datetime, timedelta
import time
from email.utils import parsedate_tz
import simplejson
import urllib2
import sys
import os
import string

MEDIA_USAGE = 'USAGE: python getmedia.py {project_name}\nproject_name should include bson identifier'

try:
    project_name = sys.argv[1]
except:
    print MEDIA_USAGE
    sys.exit()

basedir = os.getcwd()
project_data_dir = basedir + '/data/' + project_name + '/twitter/'
project_media_dir = project_data_dir + 'media/'
if not os.path.exists(project_media_dir):
    os.makedirs(project_media_dir)

def build_tweet_file_queue():
    project_files = os.listdir(project_data_dir + 'archive')
    media_files = [project_data_dir + 'archive/' + f for f in project_files if 'media_tweets_processed' in f]
    print "Found %d media files" % len(media_files)
    if len(media_files) == 0:
        media_files = False
    return media_files


def archive_media(tweet, daily_media_dir):
    tweet_id = tweet['id_str']
    media_urls = tweet['media_urls']

    if len(media_urls) > 1:
        file_suffixes = list(string.ascii_lowercase[0:len(media_urls)])
        for index in range(0, len(media_urls)):
            file_type = media_urls[index].split('.')[-1]
            media_obj = urllib2.urlopen(media_urls[index]).read()
            file_name = daily_media_dir + tweet_id + file_suffixes[index] + '.' + file_type
            with open(file_name, 'wb') as media_file:
                media_file.write(media_obj)

    elif len(media_urls) == 1:
        file_type = media_urls[0].split('.')[-1]
        media_obj = urllib2.urlopen(media_urls[0]).read()
        file_name = daily_media_dir + tweet_id + '.' + file_type
        with open(file_name, 'wb') as media_file:
            media_file.write(media_obj)

    elif len(media_urls) == 0:
        pass

    return len(media_urls)


def process_media_file(media_file_path, daily_media_dir):
    with open(media_file_path, 'r') as infile:
        tweet_counter = 0
        total_media_counter = 0
        for line in infile:
            tweet_counter += 1
            line = line.strip()
            tweet = simplejson.loads(line)
            media_count = archive_media(tweet, daily_media_dir)
            total_media_counter += media_count

        print "Saved %d media files from %d tweets with media" % (total_media_counter, tweet_counter)

def main_archiving_function():
    today = datetime.today().strftime('%Y%m%d')
    daily_media_dir = project_media_dir + today
    if not os.path.exists(daily_media_dir):
        os.makedirs(daily_media_dir)
    media_files = build_tweet_file_queue()
    for file in media_files:
        process_media_file(file, daily_media_dir)
        os.remove(file)

main_archiving_function()