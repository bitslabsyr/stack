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






