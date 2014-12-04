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

    track_set = set(track_list)
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

		# Check to see if we have a retweet
        if tweet.has_key("retweeted_status") and tweet['truncated']== True:
			# Track rule matches
			tweet['track_kw'] = {}

			rt_hashtags = []
			rt_mentions = []

			for index in range(len(tweet['retweeted_status']['entities']['hashtags'])):
				rt_hashtags.append(tweet['retweeted_status']['entities']['hashtags'][index]['text'].lower())
			for index in range(len(tweet['retweeted_status']['entities']['user_mentions'])):
				rt_mentions.append(tweet['retweeted_status']['entities']['user_mentions'][index]['screen_name'].lower())
			untion_hashtags = set(tweet['hashtags']).union(set(rt_hashtags))
			untion_mentions = set(tweet['mentions']).union(set(rt_hashtags))
			tweet['track_kw']['hashtags'] = list(untion_hashtags.intersection(track_set))
			tweet['track_kw']['mentions'] = list(untion_mentions.intersection(track_set))
			tweet_text = re.sub('[%s]' % punct, ' ', tweet['text'])
			rt_text = re.sub('[%s]' % punct, ' ', tweet['retweeted_status']['text'])
			tweet_text = tweet_text.lower().split()
			rt_text = rt_text.lower().split()
			union_text = set(rt_text).union(set(tweet_text))
			tweet['track_kw']['text'] = list(union_text.intersection(track_set))

        else:
			# Track rule matches
			tweet['track_kw'] = {}
			tweet['track_kw']['hashtags'] = list(set(tweet['hashtags']).intersection(track_set))
			tweet['track_kw']['mentions'] = list(set(tweet['mentions']).intersection(track_set))
			tweet_text = re.sub('[%s]' % punct, ' ', tweet['text'])
			tweet_text = tweet_text.lower().split()
			tweet['track_kw']['text'] = list(set(tweet_text).intersection(track_set))

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


