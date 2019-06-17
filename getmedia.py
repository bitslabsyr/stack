"""
    Functions to create local copies of embedded media in tweets
"""

from datetime import datetime
import time
import simplejson
import urllib2
import sys
import os
import string
import re

MEDIA_USAGE = 'USAGE: python getmedia.py {project_name}\nproject_name should include bson identifier\nIf you don\'t want to download media, add "-nd" after the project_name'

try:
    project_name = sys.argv[1]
except:
    print MEDIA_USAGE
    sys.exit()

try:
    if sys.argv[2] == "-nd":
        no_download = True
    else:
        no_download = False
except IndexError:
    no_download = False

basedir = os.getcwd()
project_data_dir = basedir + '/data/' + project_name + '/twitter/'
project_media_dir = project_data_dir + 'media/'
if not os.path.exists(project_media_dir):
    os.makedirs(project_media_dir)

trim_url_pattern = re.compile('[\?|=][^\.]*$')

def build_tweet_file_queue():
    project_files = os.listdir(project_data_dir + 'insert_queue')
    media_files = [project_data_dir + 'insert_queue/' + f for f in project_files if 'media_tweets' in f]
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
            file_type = re.sub(trim_url_pattern, '', file_type)
            try:
                media_obj = urllib2.urlopen(media_urls[index]).read()
                file_name = daily_media_dir + tweet_id + file_suffixes[index] + '.' + file_type
                with open(file_name, 'wb') as media_file:
                    media_file.write(media_obj)
            except urllib2.HTTPError as e:
                print "Error in trying to download and save " + media_urls[index]
                print e
                pass

    elif len(media_urls) == 1:
        file_type = media_urls[0].split('.')[-1]
        try:
            media_obj = urllib2.urlopen(media_urls[0]).read()
            file_name = daily_media_dir + tweet_id + '.' + file_type
            with open(file_name, 'wb') as media_file:
                media_file.write(media_obj)
        except urllib2.HTTPError as e:
            print "Error in trying to download and save " + media_urls[0]
            print e
            pass
    elif len(media_urls) == 0:
        pass

    return len(media_urls)


def process_media_file(media_file_path, daily_media_dir):
    with open(media_file_path, 'r') as infile:
        tweet_counter = 0
        total_media_counter = 0
        for line in infile:
            line = line.strip()
            try:
                tweet = simplejson.loads(line)
                tweet_counter += 1
                media_count = archive_media(tweet, daily_media_dir)
                total_media_counter += media_count
            except AttributeError:
                print "Error in reading a tweet from " + media_file_path + " as json"
                pass
        print "Saved %d media files from %d tweets with media" % (total_media_counter, tweet_counter)


def main_archiving_function():
    archiving = True
    while archiving:
        today = datetime.today().strftime('%Y%m%d')
        daily_media_dir = project_media_dir + today + '/'
        if not os.path.exists(daily_media_dir):
            os.makedirs(daily_media_dir)
        media_files = build_tweet_file_queue()
        if no_download:
            print "Deleting media files without downloading."
            if media_files:
                for file in media_files:
                    os.remove(file)
                print "All media files deleted. Sleeping until the new hour."
            elif not media_files:
                print "No media files found. Sleeping until the new hour."
        elif not no_download:
            if media_files:
                for file in media_files:
                    print "Downloading media from " + file
                    process_media_file(file, daily_media_dir)
                    os.remove(file)
                print "Media downloads complete. Sleeping until the new hour."
            elif not media_files:
                print "No media files found. Sleeping until the new hour."
        sleep_seconds = (60 - datetime.now().minute)*60
        time.sleep(sleep_seconds)


main_archiving_function()
