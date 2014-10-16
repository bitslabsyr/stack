Syracuse Social Media Collection (SSMC) Toolkit (Development Repo)
=========

The SSMC is a toolkit designed to collect, process, and store data streamed from online social networks. The toolkit is an ongoing project via the Syracuse University iSchool, and currently supports the Twitter Streaming API.

**_This documentation assumes the following:_**

* You know how to use ssh.
* Your server has MongoDB already installed.
* You understand how to edit files using vim (“vi”).
* You have rights and know how to install Python libraries.

## Installation

First, clone this repo to your local machine:

```
git clone https://github.com/jhemsley/Syr-SM-Collection-Toolkit.git
```

Next, make sure to install the required dependences outlined in the _requirements.txt_ file. We use pip to install and manage dependencies:

```
pip install -r requirements.txt
```

We also use Python's virtualenv to manage our development environments. To setup a virtual environment for the SSMC toolkit, simply run virtualenv's setup command and then activate the environment:

    virtualenv env
    . env/bin/activate

You can learn more about pip [here](https://pypi.python.org/pypi/pip) and virtualenv [here](http://virtualenv.readthedocs.org/en/latest/).

**Note** - We use Python 2.7.6 for the SSMC Toolkit.

## Configuration

The toolkit relies upon a configuration (.ini) file, a collection terms file, and MongoDB to run. Be sure to set up each properly before running the program.

**Config File**

Save the example_platform.ini file as a new file (we suggest 'platform.ini') and update the fields as highlighted in the comments. Key line-items to address:

* _tweets_file_date_frmt_: The rollover rate for the collection file (minutes, hours, or days)
* _collection info_: The name of your collection and storage DB in Mongo.
* _OAuth_: The access information used to interact w/ the Twitter API. To get consumer & access tokens, first register your app on https://dev.twitter.com/apps/new. Navigate to _Keys and Access Tokens_ and click "Create my access token."

**MongoDB**

In addition to the storage DB specified above that will be used to store all final, processed data, the toolkit uses a series of flag modules to control the scripts. We suggest using a config collection within a config database in Mongo. To set up the controls this way, follow these steps:

_Navigate to the proper DB_:

    mongo
    use config

_Set up the four flag modules_:

    db.config.insert({'module': 'collector-track', 'run': 0, 'collect': 0, 'update': 0})
    db.config.insert({'module': 'collector-follow', 'run': 0, 'collect': 0, 'update': 0})
    db.config.insert({'module': 'processor', 'run': 0})
    db.config.insert({'module': 'inserter', 'run': 0})

See the "Running the Toolkit" section below for more information on Mongo flags.

**Collection Terms**

Edit the 'collection.terms' file and enter one keyterm per line. Some caveats as of now:

* You need to manually specify the terms file in ThreadedCollector.py, prepocess.py, and mongoBatchInsert.py if you change the title of the file.
* Currently, the toolkit is designed to work with only one terms file.

## Running the Toolkit

Three main scripts constitute this toolkit:

* **ThreadedCollector.py** - Runs the main streaming collection thread. Controlled by the collector-track and collector-follow flag modules.
* **preprocess.py** - Takes raw tweet collection files and performs a series of predefined cleanup processes on them before inserting into Mongo. Controlled by the processor flag module.
* **mongoBatchInsert.py** - Inserts processed tweet files into Mongo based on a dynamic queuing system. Controlled by the inserter flag module.

**Flag Commands**

* _run_ - Runs the script when set to 1. Stops the script when set to 0.
* _collect_ - Runs the collection thread (separate from the main program thread) for the collection script, when set to 1.
* _update_ - When set to 1, the collection script will check for an update to the terms file without a need to restart the script.

**Collector Modules**

The two collection modules allow for two different types of filters for the Twitter Streaming API: track and follow. You can run both at the same time, hence the separate control modules. [Learn more about the Streaming API here](https://dev.twitter.com/streaming/overview).

**Starting Up**

We currently use screen to manage multiple python scripts running at the same time, which is currently a necessary part of this toolkit. To get the toolkit running, after configuring via the above steps, go through the following:

_Collector_

    db.config.update({'module': 'collector-track'}, {$set: {'run': 1, 'collect': 1}})
    [ctrl-c]
    screen -S Collector
    python ThreadedCollector.py track
    [ctrl-a] [ctrl-d]

**_NOTE_** - In the example above we are running the collector for a track filter. To use the follow filter, run the above for the collector-follow module and use replace "track" with "follow" in the final execution command.

_Processor_

    db.config.update({'module': 'processor'}, {$set: {'run': 1}})
    [ctrl-c]
    screen -S Processor
    python preprocess.py
    [ctrl-a] [ctrl-d]

_Inserter_

    db.config.update({'module': 'inserter'}, {$set: {'run': 1}})
    [ctrl-c]
    screen -S Inserter
    python mongoBatchInsert.py
    [ctrl-a] [ctrl-d]

You can use the Mongo $set command in the console to update/run/stop the scripts at any point going forward.

Now, sit back and watch the collection magic happen!

## Ongoing Work + Next Action Items

This list will be updated soon with more detailed action items. Please note again that we are actively working on this toolkit!

1. Multiple terms file support
2. Facebook integration
3. Script consolidation

---

The MIT License (MIT)

Copyright (c) 2009-2013 University of Washington

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
