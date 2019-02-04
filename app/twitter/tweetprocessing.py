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

def process_limit(line, col_type, server_name, project_name, project_id, collector_id):
    
    line = simplejson.loads(line)
    limit = {'collection_type': col_type,
              'server_name': server_name,
              'project_name': project_name,
              'project_id': project_id,
              'collector_id': collector_id,
              'lost_count': line['limit']['track'],
              'time': line['limit']['time'],
              'timestamp_ms': line['limit']['timestamp_ms'],
              'notified': False}
    
    limit_out_string = simplejson.dumps(limit) + '\n'
    return limit_out_string

def process_tweet(line, track_list, expand_url=False):

    #regular expression to delete emojis
    emoji_pattern = re.compile(u'([\U00002600-\U000027BF])|([\U0001f300-\U0001f64F])|([\U0001f680-\U0001f6FF])')
    # List of punct to remove from string for track keyword matching
    punct = re.escape('!"$%&\'()*+,-./:;<=>?@[\\]^`{|}~')
    
    
    tweet = simplejson.loads(line)
    
    # Initialize stack_vars
    tweet['stack_vars'] = { 'text_hash': None,
                            'created_ts': None,
                            'hashtags': [],
                            'mentions': [],
                            'codes': [],
                            'track_kw': {},
                            'entities_counts': {},
                            'user': {},    
                            'full_tweet': {}}
    
    # Initialize track_kw
    tweet['stack_vars']["track_kw"] = {    "org_tweet" : {}, 
                                        "rt_tweet" : {}, 
                                        "qt_tweet" : {}}
    

    if track_list:
        track_set = set(track_list)
    else:
        track_set = None
    
    
    if tweet['truncated'] == True:
        tweet['stack_vars']['full_tweet'] = tweet['extended_tweet']
        
        hashtag_num = 0
        tweet['stack_vars']['hashtags'] = []
        tweet['stack_vars']['mentions'] = []
        tweet['stack_vars']['codes'] = []

        if "hashtags" in tweet['extended_tweet']['entities']:
            hashtag_num = len(tweet['extended_tweet']['entities']['hashtags'])
            for index in range(len(tweet['extended_tweet']['entities']['hashtags'])):
                tweet['stack_vars']['hashtags'].append(tweet['extended_tweet']['entities']['hashtags'][index]['text'].lower())

        urls_num = 0
        coded_url_num = 0
        urls = []
        
        if "urls" in tweet['extended_tweet']['entities']:
            urls_num = len(tweet['extended_tweet']['entities']['urls'])
            
            if expand_url:
                for urls in tweet['extended_tweet']['entities']['urls']:
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
                        tweet['stack_vars']['codes'].append(url_code[0])
                        
            coded_url_num = len(tweet['stack_vars']['codes'])

        mentions_num = 0
        if "user_mentions" in tweet['extended_tweet']['entities']:
            mentions_num = len(tweet['extended_tweet']['entities']['user_mentions'])
            for index in range(len(tweet['extended_tweet']['entities']['user_mentions'])):
                if "screen_name" in tweet['extended_tweet']['entities']['user_mentions'][index]:
                    tweet['stack_vars']['mentions'].append(tweet['extended_tweet']['entities']['user_mentions'][index]['screen_name'].lower())

        tweet['stack_vars']['entities_counts'] = {  'urls': urls_num,
                                                    'hashtags': hashtag_num,
                                                    'user_mentions': mentions_num,
                                                    'coded_urls': coded_url_num }

        tweet['stack_vars']['hashtags'].sort()
        tweet['stack_vars']['mentions'].sort()

        tweet['stack_vars']['text_hash'] = hashlib.md5(tweet['extended_tweet']['full_text'].encode("utf-8")).hexdigest()
    
    
    else:
        tweet['stack_vars']['full_tweet'] = {'display_text_range': [],
                                                'entities': None,
                                                'full_text': None}
        
        tweet['stack_vars']['full_tweet']['display_text_range'] = [0, len(tweet['text'])]
        tweet['stack_vars']['full_tweet']['entities'] = tweet['entities']
        tweet['stack_vars']['full_tweet']['full_text'] = tweet['text']
        
        if 'entities' in tweet:
            hashtag_num = 0
            tweet['stack_vars']['hashtags'] = []
            tweet['stack_vars']['mentions'] = []
            tweet['stack_vars']['codes'] = []
    
            if "hashtags" in tweet['entities']:
                hashtag_num = len(tweet['entities']['hashtags'])
                for index in range(len(tweet['entities']['hashtags'])):
                    tweet['stack_vars']['hashtags'].append(tweet['entities']['hashtags'][index]['text'].lower())
    
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
                            tweet['stack_vars']['codes'].append(url_code[0])
                coded_url_num = len(tweet['stack_vars']['codes'])
    
            mentions_num = 0
            if "user_mentions" in tweet['entities']:
                mentions_num = len(tweet['entities']['user_mentions'])
                for index in range(len(tweet['entities']['user_mentions'])):
                    if "screen_name" in tweet['entities']['user_mentions'][index]:
                        tweet['stack_vars']['mentions'].append(tweet['entities']['user_mentions'][index]['screen_name'].lower())
    
            tweet['stack_vars']['entities_counts'] = {    'urls': urls_num,
                                                        'hashtags': hashtag_num,
                                                        'user_mentions': mentions_num,
                                                        'coded_urls': coded_url_num };
    
            tweet['stack_vars']['hashtags'].sort()
            tweet['stack_vars']['mentions'].sort()
    
            tweet['stack_vars']['text_hash'] = hashlib.md5(tweet['text'].encode("utf-8")).hexdigest()
    
    
    if track_set:
        if tweet['truncated'] == False:
            myURLs = []
            for index in range(len(tweet['entities']['urls'])):
                myURLs.append(tweet['entities']['urls'][index]['expanded_url'].lower())
                
            hashTags_set = set([x.lower() for x in tweet['stack_vars']['hashtags']])
            mentions_set = set([x.lower() for x in tweet['stack_vars']['mentions']])
            
            track_set = set([x.lower() for x in track_set])
            tweet['stack_vars']["track_kw"]["org_tweet"]["hashtags"] = list(set(hashTags_set).intersection(track_set))
            tweet['stack_vars']["track_kw"]["org_tweet"]["mentions"] = list(set(mentions_set).intersection(track_set))
            
            tweet_text = re.sub('[%s]' % punct, ' ', tweet['text'])
            tweet_text = emoji_pattern.sub(r'', tweet_text)
            tweet_text = tweet_text.lower().split()
            
            tweet['stack_vars']["track_kw"]["org_tweet"]["text"] = list(set(tweet_text).intersection(track_set))
            
            tmpURLs = []
            for url in myURLs:
                for x in track_set:
                    if x in url:
                        tmpURLs.append(url)
            tweet['stack_vars']["track_kw"]["org_tweet"]["urls"] = list(tmpURLs)
        else:
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
            tweet['stack_vars']["track_kw"]["org_tweet"]["hashtags"] = list(set(hashTags_set).intersection(track_set))
            tweet['stack_vars']["track_kw"]["org_tweet"]["mentions"] = list(set(mentions_set).intersection(track_set))
            #tweet['track_kw']['hashtags'] = list(set(hashTags_set).intersection(track_set))
            #tweet['track_kw']['mentions'] = list(set(mentions_set).intersection(track_set))
            #---------------------------------End new code by Dani-------------------------------------------------
            
            tweet_text = re.sub('[%s]' % punct, ' ', tweet['extended_tweet']['full_text'])
            tweet_text = emoji_pattern.sub(r'', tweet_text)
            tweet_text = tweet_text.lower().split()
            tweet['stack_vars']["track_kw"]["org_tweet"]["text"] = list(set(tweet_text).intersection(track_set))
    
            tmpURLs = []
            for url in ext_urls:
                for x in track_set:
                    if x in url:
                        tmpURLs.append(url)
                        
            tweet['stack_vars']["track_kw"]["org_tweet"]["urls"] = list(tmpURLs)
        
    
    
        
        
    
    # Convert dates 2012-09-22 00:10:46
    # Note that we convert these to a datetime object and then convert back to string
    # and update the tweet with the new string. We do this becuase we want to find
    # and log any process issues here, not when we do an insert.
    #
    #tweet['created_ts'] = to_datetime(tweet['created_at'])
    #tweet['user']['created_ts'] = to_datetime(tweet['user']['created_at'])
    t = to_datetime(tweet['created_at'])
    tweet['stack_vars']['created_ts'] = t.strftime('%Y-%m-%d %H:%M:%S')
    
    t = to_datetime(tweet['user']['created_at'])
    tweet['stack_vars']['user']['created_ts'] = t.strftime('%Y-%m-%d %H:%M:%S')
    
    # Check to see if we have a retweet
    if 'retweeted_status' in tweet:
        if tweet['retweeted_status']['truncated'] == True:
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
                
                tweet['stack_vars']["track_kw"]["rt_tweet"]["hashtags"]  = list(set(rt_hashtags).intersection(track_set)) 
                tweet['stack_vars']["track_kw"]["rt_tweet"]["mentions"] = list(set(rt_mentions).intersection(track_set))
                
                rt_text = re.sub('[%s]' % punct, ' ', tweet['retweeted_status']['extended_tweet']['full_text'])
                rt_text = emoji_pattern.sub(r'', rt_text)
                rt_text = rt_text.lower().split()
                
                tweet['stack_vars']["track_kw"]["rt_tweet"]["text"] = list(set(rt_text).intersection(track_set))
                
                tmpURLs = []
                for url in rt_urls:
                    for x in track_set:
                        if x in url:
                            tmpURLs.append(url)
                
                tweet['stack_vars']["track_kw"]["rt_tweet"]["urls"] = list(tmpURLs)
                
        #Check if is retweet and it is not truncated
        elif tweet['retweeted_status']['truncated'] == False:
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
                
                tweet['stack_vars']["track_kw"]["rt_tweet"]["hashtags"]  = list(set(rt_hashtags).intersection(track_set))  #list(rt_hashtags.intersection(track_set))
                tweet['stack_vars']["track_kw"]["rt_tweet"]["mentions"] = list(set(rt_mentions).intersection(track_set))  #list(rt_mentions.intersection(track_set))
                
                rt_text = re.sub('[%s]' % punct, ' ', tweet['retweeted_status']['text'])
                rt_text = emoji_pattern.sub(r'', rt_text)
                rt_text = rt_text.lower().split()
                
                tweet['stack_vars']["track_kw"]["rt_tweet"]["text"] = list(set(rt_text).intersection(track_set))
                tmpURLs = []
                
                for url in rt_urls:
                    for x in track_set:
                        if x in url:
                            tmpURLs.append(url)
                
                tweet['stack_vars']["track_kw"]["rt_tweet"]["urls"] = list(tmpURLs)
            
            

    #check if we have a quoted tweet and if it is truncated
    if 'quoted_status' in tweet:
        if tweet['quoted_status']['truncated']== True :
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
                
                tweet['stack_vars']["track_kw"]["qt_tweet"]["hashtags"]  = list(set(qt_hashtags).intersection(track_set))
                tweet['stack_vars']["track_kw"]["qt_tweet"]["mentions"] = list(set(qt_mentions).intersection(track_set))
                    
                qt_text = re.sub('[%s]' % punct, ' ', tweet['quoted_status']['extended_tweet']['full_text'])
                qt_text = emoji_pattern.sub(r'', qt_text)
                qt_text = qt_text.lower().split()
                
                tweet['stack_vars']["track_kw"]["qt_tweet"]["text"] = list(set(qt_text).intersection(track_set))
                
                tmpURLs = []
                for url in qt_urls:
                    for x in track_set:
                        if x in url:
                            tmpURLs.append(url)
                
                tweet['stack_vars']["track_kw"]["qt_tweet"]["urls"] = list(tmpURLs)

        #Check if we have a quoted tweet and it is not truncated
        elif tweet['quoted_status']['truncated'] == False :
    
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
                
                tweet['stack_vars']["track_kw"]["qt_tweet"]["hashtags"]  = list(set(qt_hashtags).intersection(track_set))
                tweet['stack_vars']["track_kw"]["qt_tweet"]["mentions"] = list(set(qt_mentions).intersection(track_set))
                
                qt_text = re.sub('[%s]' % punct, ' ', tweet['quoted_status']['text'])
                qt_text = emoji_pattern.sub(r'', qt_text)
                qt_text = qt_text.lower().split()
                
                tweet['stack_vars']["track_kw"]["qt_tweet"]["text"] = list(set(qt_text).intersection(track_set))
                
                tmpURLs = []
                for url in qt_urls:
                    for x in track_set:
                        if x in url:
                            tmpURLs.append(url)
                tweet['stack_vars']["track_kw"]["qt_tweet"]["urls"] = list(tmpURLs)

    

    tweet_out_string = simplejson.dumps(tweet).encode('utf-8') + '\n'

    return tweet_out_string