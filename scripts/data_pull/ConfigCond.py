from datetime import datetime
## Database ##
DB_AUTH = {
           'DB_IS_AUTH': False, # True if DB is password protected otherwise False
           'DB_USERNAME': 'DB_USERNAME',
           'DB_PASSWORD': 'DB_PASSWORD'
           }
DB = {
      'DB_NAME': 'DB_NAME',
      'COL_NAME': 'tweets'
      }

# Output
# Headers: Field names must be exactly like in Mongo documents 
#          For nested objects: names are separated by .
OUTPUT = {
          'OUT_FILENAME': './out/out.csv',
          'HEADER': ["id", "text", "created_ts", "hashtags", "mentions",
                     "in_reply_to_status_id", "in_reply_to_screen_name", 
                     "retweeted_status.id", "retweeted_status.user.id", "retweeted_status.user.screen_name", 
                     "retweeted_status.user.followers_count", "retweeted_status.user.friends_count",
                     "user.id", "user.screen_name", 
                     "user.followers_count", "user.friends_count", 
                     "user.statuses_count", "user.created_ts",
                     "user.time_zone", "user.location"]
          }

# Conditions
# tweet_id = None | filename | [id_1, id_2]
# user_id = None | filename | [user_id_1, user_id_2]
# screen_name = None | filename | [name_1, name_2]
# created_at_from = None | datetime(YYYY, M, D, H)
# created_at_to = None | datetime(YYYY, M, D, H)
# retweet_included = None | True | False
CONDITIONS = {
              'tweet_id': './tweetIDs.txt',#['757604886141820928', '757605167818608641', '757606596839079936', '757606903753084928'],
              'reply_to_id': ,#'./reply_to_IDs.txt',
              'user_id': [],
              'screen_name': [],
              'created_at_from': None,#datetime(2016, 1, 1, 0), 
              'created_at_to': None,#datetime(2018, 2, 1, 0),
              'retweet_included': True
              }




