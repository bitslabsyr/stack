SoMe Toolkit (development repo)
=========

The MIT License (MIT)

Copyright (c) 2009-2013 University of Washington

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

-=-=-=-

This documentation assumes the following:

You know how to use ssh. Your server has mongo already installed. You understand how to edit files using vim (“vi”) You have rights and know how to install Python libraries. You will need to install the following libraries: pymongo json simplejson tweepy ConfigParser

In addition to these, the platform uses these other libraries common to Python installations:

collections datetime email.utils glob hashlib httplib logging logging.config os.path re shutil socket string sys threading time traceback

1. Clone the github repo to the box that has Mongo installed on it
2. ssh user@mongo.xxxxxxx.xxx (if you haven't already)
3. Edit "collection.terms" and enter one keyterm per line.  Save the file.
4. Using a web browser, visit: https://dev.twitter.com/apps/new and fill out an app request form.  Completing the form will provide a web page with a number of OAuth settings.
5. Click the button at the bottom labeled “Create my access token”
6. The website will refresh.  It takes a minute for the access token to appear - keep refreshing your browser until it appears.
7. Leave this website open, and return to your SSH shell
8. Edit "platform.ini".  Scroll to the line starting with "consumer_key".  Edit the keys to match those provided by Twitter in step X. Save the file when you're done.

CHANGES EXPECTED STARTING HERE: 
9. mongo (this assumes you have mongo installed)
10. use config
11. db.config.insert({'module': 'collector', 'run': 1, 'collect': 0, 'update': 0, 'error_code': 0, 'rate_limit':0})
12. db.config.update({'module': 'collector'}, {$set: {'collect': 1}})

THIS WILL CHANGE: NOTE: USE VIRTUALENV RATHER THAN NATIVE PYTHON
13. screen -S ThreadedCollector
14. python ThreadedCollector.py
15. [ctrl-a] [ctrl-d]
16. screen -S preprocess
17 python preprocess.py
18. [ctrl-a] [ctrl-d]
19. screen -S mongoBatchInsert
20. python mongoBatchInsert.py
21. [ctrl-a] [ctrl-d]

Step 11 sets up the collector. Step 12 sets the flag that tells the collector components to run. Steps 13-21 launches the processes informed by steps 11-12. The collector will be running. 

You can run the following commands in db.config using mongo:

This stops the processes: db.config.update({'module': 'collector'}, {$set: {'run': 0}})

This starts it: db.config.update({'module': 'collector'}, {$set: {'run': 1}})

To keep it running, but stop collecting: db.config.update({'module': 'collector'}, {$set: {'collect': 0}})

To start collecting (assumes it is already running): db.config.update({'module': 'collector'}, {$set: {'collect': 1}})
