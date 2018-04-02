"""
	Functions to process tweet meta data
	expand URLs, add counts of urls/hashtags/mentions, and list of hashtags/mentions.

"""

import sys
from datetime import datetime, timedelta
import time
from email.utils import parsedate_tz
import simplejson
import re
import hashlib
import string
from collections import defaultdict
import traceback


# Parse Twitter created_at datestring and turn it into
def to_datetime(datestring):
    time_tuple = parsedate_tz(datestring.strip())
    dt = datetime(*time_tuple[:6])
    return dt

def ck_coded_url(urlstring):
	cur.execute("""select code, hashtag from tweets_sample_test where url = %s and hashtag in ('ows','occupyoakland','occupyseattle') and date(created_at) between '2011-10-19' and '2012-04-30' and spike is null""", urlstring.encode("utf-8"))
	result = cur.fetchone()
	if result:
		return result
	else:
		return None


def process_tweet(line, track_list, expand_url=False):

    tweet = simplejson.loads(line)

    if track_list:
        track_set = set(track_list)
    else:
        track_set = None
	# List of punct to remove from string for track keyword matching
    punct = re.escape('!"$%&\'()*+,-./:;<=>?@[\\]^`{|}~')


    if (tweet.has_key("entities") and "created_at" in tweet and "created_at" in tweet['user']):
        hashtag_num = 0
        tweet['hashtags'] = []
        tweet['mentions'] = []
        tweet['codes'] = []

        if "hashtags" in tweet['entities']:
			hashtag_num = len(tweet['entities']['hashtags'])
			for index in range(len(tweet['entities']['hashtags'])):
				tweet['hashtags'].append(tweet['entities']['hashtags'][index]['text'].lower())


        urls_num = 0
        coded_url_num = 0
        urls = []
        if "urls" in tweet['entities']:
			urls_num = len(tweet['entities']['urls'])
			if expand_url:
				for urls in tweet['entities']['urls']:
					url_code = None
					if 'long-url' in urls and urls['long-url'] is not None:
						url_code = ck_coded_url(urls['long-url'])
					elif "expanded_url" in urls and urls['expanded_url'] is not None:
						url_code = ck_coded_url(urls['expanded_url'])
					elif "url" in urls:
						url_code = ck_coded_url(urls['url'])
					if url_code:
						urls['code'] = url_code[0]
						urls['hashtag'] = url_code[1]
						tweet['codes'].append(url_code[0])
			coded_url_num = len(tweet['codes'])

        mentions_num = 0
        if "user_mentions" in tweet['entities']:
			mentions_num = len(tweet['entities']['user_mentions'])
			for index in range(len(tweet['entities']['user_mentions'])):
				if "screen_name" in tweet['entities']['user_mentions'][index]:
					tweet['mentions'].append(tweet['entities']['user_mentions'][index]['screen_name'].lower())

        tweet['counts'] = {
							'urls': urls_num,
							'hashtags': hashtag_num,
							'user_mentions': mentions_num,
							'coded_urls': coded_url_num
							};

        tweet['hashtags'].sort()
        tweet['mentions'].sort()

        tweet['text_hash'] = hashlib.md5(tweet['text'].encode("utf-8")).hexdigest()
	
	tweet["track_kw"] = {"org_tweet" : {}, "rt_tweet" : {}, "qt_tweet" : {}}
	
	# Check to see if we have a retweet
        if tweet.has_key("retweeted_status") and tweet['retweeted_status']['truncated']== True:

	    rt_hashtags = []
            rt_mentions = []
	    rt_urls = []

            for index in range(len(tweet['retweeted_status']['extended_tweet']['entities']['hashtags'])):
            	rt_hashtags.append(tweet['retweeted_status']['extended_tweet']['entities']['hashtags'][index]['text'].lower())
            for index in range(len(tweet['retweeted_status']['extended_tweet']['entities']['user_mentions'])):
            	rt_mentions.append(tweet['retweeted_status']['extended_tweet']['entities']['user_mentions'][index]['screen_name'].lower())
	    for index in range(len(tweet['retweeted_status']['extended_tweet']['entities']['urls'])):
                rt_urls.append(tweet['retweeted_status']['extended_tweet']['entities']['urls'][index]['expanded_url'].lower())

            if track_set:
                rt_hashtags = set([x.lower() for x in rt_hashtags])
                rt_mentions = set([x.lower() for x in rt_mentions])
                track_set = set([x.lower() for x in track_set])
		tweet["track_kw"]["rt_tweet"]["hashtags"]  = list(set(rt_hashtags).intersection(track_set)) 
		tweet["track_kw"]["rt_tweet"]["mentions"] = list(set(rt_mentions).intersection(track_set))
		rt_text = re.sub('[%s]' % punct, ' ', tweet['retweeted_status']['extended_tweet']['full_text'])
		rt_text = rt_text.lower().split()
		tweet["track_kw"]["rt_tweet"]["text"] = list(set(rt_text).intersection(track_set))
		tmpURLs = []
		for url in rt_urls:
			for x in track_set:
				if x in url:
					tmpURLs.append(url)
		tweet["track_kw"]["rt_tweet"]["urls"] = list(tmpURLs)

	#Check if is retweet and it is not truncated
	elif tweet.has_key("retweeted_status") and tweet['retweeted_status']['truncated']== False:
            rt_hashtags = []
            rt_mentions = []
            rt_urls = []

            for index in range(len(tweet['retweeted_status']['entities']['hashtags'])):
                rt_hashtags.append(tweet['retweeted_status']['entities']['hashtags'][index]['text'].lower())
            for index in range(len(tweet['retweeted_status']['entities']['user_mentions'])):
                rt_mentions.append(tweet['retweeted_status']['entities']['user_mentions'][index]['screen_name'].lower())
            for index in range(len(tweet['retweeted_status']['entities']['urls'])):
                rt_urls.append(tweet['retweeted_status']['entities']['urls'][index]['expanded_url'].lower())

            if track_set:
                rt_hashtags = set([x.lower() for x in rt_hashtags])
                rt_mentions = set([x.lower() for x in rt_mentions])
                track_set = set([x.lower() for x in track_set])
                tweet["track_kw"]["rt_tweet"]["hashtags"]  = list(set(rt_hashtags).intersection(track_set))  #list(rt_hashtags.intersection(track_set))
                tweet["track_kw"]["rt_tweet"]["mentions"] = list(set(rt_mentions).intersection(track_set))  #list(rt_mentions.intersection(track_set))
                rt_text = re.sub('[%s]' % punct, ' ', tweet['retweeted_status']['text'])
                rt_text = rt_text.lower().split()
                tweet["track_kw"]["rt_tweet"]["text"] = list(set(rt_text).intersection(track_set))
                tmpURLs = []
                for url in rt_urls:
                        for x in track_set:
                                if x in url:
                                        tmpURLs.append(url)
                tweet["track_kw"]["rt_tweet"]["urls"] = list(tmpURLs)


	#check if we have a quoted tweet and if it is truncated
	if tweet.has_key("quoted_status") and tweet['quoted_status']['truncated']== True :

            qt_hashtags = []
            qt_mentions = []
	    qt_urls = []

 	    for index in range(len(tweet['quoted_status']['extended_tweet']['entities']['hashtags'])):
                qt_hashtags.append(tweet['quoted_status']['extended_tweet']['entities']['hashtags'][index]['text'].lower())
            for index in range(len(tweet['quoted_status']['extended_tweet']['entities']['user_mentions'])):
                qt_mentions.append(tweet['quoted_status']['extended_tweet']['entities']['user_mentions'][index]['screen_name'].lower())
	    for index in range(len(tweet['quoted_status']['extended_tweet']['entities']['urls'])):
                qt_urls.append(tweet['quoted_status']['extended_tweet']['entities']['urls'][index]['expanded_url'].lower())

            
            if track_set:
                qt_hashtags = set([x.lower() for x in qt_hashtags])
                qt_mentions = set([x.lower() for x in qt_mentions])
                track_set = set([x.lower() for x in track_set])
                tweet["track_kw"]["qt_tweet"]["hashtags"]  = list(set(qt_hashtags).intersection(track_set))
                tweet["track_kw"]["qt_tweet"]["mentions"] = list(set(qt_mentions).intersection(track_set))
                qt_text = re.sub('[%s]' % punct, ' ', tweet['quoted_status']['extended_tweet']['full_text'])
                qt_text = qt_text.lower().split()
                tweet["track_kw"]["qt_tweet"]["text"] = list(set(qt_text).intersection(track_set))
		tmpURLs = []
                for url in qt_urls:
                        for x in track_set:
                                if x in url:
                                        tmpURLs.append(url)
                tweet["track_kw"]["qt_tweet"]["urls"] = list(tmpURLs)

	#Check if we have a quoted tweet and it is not truncated
	elif  tweet.has_key("quoted_status") and tweet['quoted_status']['truncated']== False :

            qt_hashtags = []
            qt_mentions = []
            qt_urls = []

            for index in range(len(tweet['quoted_status']['entities']['hashtags'])):
                qt_hashtags.append(tweet['quoted_status']['entities']['hashtags'][index]['text'].lower())
            for index in range(len(tweet['quoted_status']['entities']['user_mentions'])):
                qt_mentions.append(tweet['quoted_status']['entities']['user_mentions'][index]['screen_name'].lower())
            for index in range(len(tweet['quoted_status']['entities']['urls'])):
                qt_urls.append(tweet['quoted_status']['entities']['urls'][index]['expanded_url'].lower())


            if track_set:
                qt_hashtags = set([x.lower() for x in qt_hashtags])
                qt_mentions = set([x.lower() for x in qt_mentions])
                track_set = set([x.lower() for x in track_set])
                tweet["track_kw"]["qt_tweet"]["hashtags"]  = list(set(qt_hashtags).intersection(track_set))
                tweet["track_kw"]["qt_tweet"]["mentions"] = list(set(qt_mentions).intersection(track_set))
                qt_text = re.sub('[%s]' % punct, ' ', tweet['quoted_status']['text'])
                qt_text = qt_text.lower().split()
                tweet["track_kw"]["qt_tweet"]["text"] = list(set(qt_text).intersection(track_set))

                tmpURLs = []
                for url in qt_urls:
                        for x in track_set:
                                if x in url:
                                        tmpURLs.append(url)
                tweet["track_kw"]["qt_tweet"]["urls"] = list(tmpURLs)

	#Check Original tweets
        if track_set and tweet['truncated'] == False :

                        myURLs = []
			for index in range(len(tweet['entities']['urls'])):
				myURLs.append(tweet['entities']['urls'][index]['expanded_url'].lower())
			
			hashTags_set = set([x.lower() for x in tweet['hashtags']])
                        mentions_set = set([x.lower() for x in tweet['mentions']])
                        track_set = set([x.lower() for x in track_set])
                        tweet["track_kw"]["org_tweet"]["hashtags"] = list(set(hashTags_set).intersection(track_set))
			tweet["track_kw"]["org_tweet"]["mentions"] = list(set(mentions_set).intersection(track_set))

                        tweet_text = re.sub('[%s]' % punct, ' ', tweet['text'])
                        tweet_text = tweet_text.lower().split()
			tweet["track_kw"]["org_tweet"]["text"] = list(set(tweet_text).intersection(track_set))
			tmpURLs = []
			for url in myURLs:
                        	for x in track_set:
                                	if x in url:
                                        	tmpURLs.append(url)
                	tweet["track_kw"]["org_tweet"]["urls"] = list(tmpURLs)

	elif track_set and tweet['truncated'] == True :
                        ext_hashtags = []
			ext_mentions = []
			ext_urls = []

			for index in range(len(tweet['extended_tweet']['entities']['hashtags'])):
    				ext_hashtags.append(tweet['extended_tweet']['entities']['hashtags'][index]['text'].lower())
			for index in range(len(tweet['extended_tweet']['entities']['user_mentions'])):
    				ext_mentions.append(tweet['extended_tweet']['entities']['user_mentions'][index]['screen_name'].lower())
			for index in range(len(tweet['extended_tweet']['entities']['urls'])):
				ext_urls.append(tweet['extended_tweet']['entities']['urls'][index]['expanded_url'].lower())

                        hashTags_set = set([x.lower() for x in ext_hashtags])
                        mentions_set = set([x.lower() for x in ext_mentions])
                        track_set = set([x.lower() for x in track_set])
                        tweet["track_kw"]["org_tweet"]["hashtags"] = list(set(hashTags_set).intersection(track_set))
                        tweet["track_kw"]["org_tweet"]["mentions"] = list(set(mentions_set).intersection(track_set))
                        #tweet['track_kw']['hashtags'] = list(set(hashTags_set).intersection(track_set))
                        #tweet['track_kw']['mentions'] = list(set(mentions_set).intersection(track_set))
                        #---------------------------------End new code by Dani-------------------------------------------------
                        tweet_text = re.sub('[%s]' % punct, ' ', tweet['extended_tweet']['full_text'])
                        tweet_text = tweet_text.lower().split()
                        tweet["track_kw"]["org_tweet"]["text"] = list(set(tweet_text).intersection(track_set))
                        tmpURLs = []
                        for url in ext_urls:
                                for x in track_set:
                                        if x in url:
                                                tmpURLs.append(url)
                        tweet["track_kw"]["org_tweet"]["urls"] = list(tmpURLs)


        # Convert dates 2012-09-22 00:10:46
        # Note that we convert these to a datetime object and then convert back to string
        # and update the tweet with the new string. We do this becuase we want to find
        # and log any process issues here, not when we do an insert.
        #
        #tweet['created_ts'] = to_datetime(tweet['created_at'])
        #tweet['user']['created_ts'] = to_datetime(tweet['user']['created_at'])
        t = to_datetime(tweet['created_at'])
        tweet['created_ts'] = t.strftime('%Y-%m-%d %H:%M:%S')

        t = to_datetime(tweet['user']['created_at'])
        tweet['user']['created_ts'] = t.strftime('%Y-%m-%d %H:%M:%S')

        #print tweet['created_ts']

    tweet_out_string = simplejson.dumps(tweet).encode('utf-8') + '\n'

    return tweet_out_string


