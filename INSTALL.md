Installing STACK
=========

Welcome to STACK! This doc will take you through the installation of STACK and will guide you through the basic setup of a data collection process.

**_This documentation assumes the following:_**

* You know how to use ssh.
* Your server has [MongoDB already installed](http://docs.mongodb.org/manual/installation/).
* You understand how to edit files using vim (“vi”).
* You have rights and know how to install Python libraries.

In addition, this doc is geared towards working on a Linux system (for testing we use Ubuntu). We've tried to link to external documentation where installation diverges if you are using other systems.

Finally, the instructions below detail how to install STACK. To learn more about STACK semantics, or how to interact with the app in more detail, [refer to our wiki](https://github.com/bitslabsyr/stack/wiki).

## Step 1) Download STACK

First, clone the 'wb' branch of this repo to your local machine:

    git clone -b wb https://github.com/bitslabsyr/stack.git

Next, make sure to install the required Python libraries  outlined in the _requirements.txt_ file. We use pip to install and manage dependencies:

    pip install -r requirements.txt

We also use Python's virtualenv to manage our development environments. To setup a virtual environment for STACK, simply run virtualenv's setup command and then activate the environment:

    virtualenv env
    . env/bin/activate

You can learn more about pip [here](https://pypi.python.org/pypi/pip) and virtualenv [here](http://virtualenv.readthedocs.org/en/latest/).

**Note** - We use Python 2.7.6 for STACK.

## Step 2) Configuration & Setup

STACK is built to work with MongoDB. The app stores most configuration information in Mongo, however we also use a configuration (.ini) file to manage some parts of the collection process from the Streaming API. Before getting started with STACK, you'll need to do the following:

* Setup a project account
* Edit the master configuration file
* Create & start a collector

These steps are detailed below.

**Project Account Setup**

TODO - wiki link

STACK uses "project accounts" to maintain ownership over collection processes. A project account can own multiple collection processes that run concurrently. _To learn more about project accounts and STACK configuration, [see the wiki](#)_.

After cloning the STACK repo to your local machine, move into the main directory and activate the _setup.py_ script:

    cd stack
    python setup.py

The setup script initializes the Mongo database with important configuration information, as well as creates your user account. The script will prompt you for the following information:

* _Project Name_: A unique account name for your project. STACK calls all login accounts "projects" and allows for multiple projects at once.
* _Password_: A password for your project account.
* _Description_: A short description for your project account.

If the script returns a successful execution notice, you will be able to start creating and running collection processes for that account. You can rerun the setup.py script to create new accounts.

**Creating a Collector**

Each project account can instantiate multiple **collectors** that will scrape data. A collector is defined as a singular instance that collects data for a specific set of user-provided terms. A project can have multiple collectors running for a given network.

To create a collector, first run the following command from the main STACK diretcory:

    python __main__.py db set_collector_detail

You will then be prompted to provide the following configuration information for the collector:

* _Project Account Name_ (required): The name of your project account.
* _Collector Name_ (required): Non-unique name to identify your collector instance.
* _Language(s)_ (optional): A list of [BCP-47](http://tools.ietf.org/html/bcp47) language codes. If this used, the collector will only grab tweets in this language. [Learn more here](https://dev.twitter.com/streaming/overview/request-parameters#language) about Twitter language parameters.
* _Location(s)_ (optional): A list of location coordinates. If used, we will collect all geocoded tweets within the location bounding box. Bounding boxes must consist of four lat/long pairs. [Learn more here](https://dev.twitter.com/streaming/overview/request-parameters#locations) about location formatting for the Twitter API.
* _Terms_ (optiona): A line item list of terms for the collector to stream.
* _API_ (required): Three options: track, follow, or none. Each collector can stream from one part of Twitter's Streaming API:
    * **Track**: Collects all mentions (hashtags included) for a given list of terms.
    * **Follow**: Collects all tweets, retweets, and replies for a given use handle. Each term must be a valid Twitter screen name.
    * **None**: Only choose this option if you have not inputted a terms list and are collecting for a given set of language(s) and/or location(s). If you do not track a terms list, make sure you are tracking at least one language or location.
* _OAuth Information_: Four keys used to authenticate with the Twitter API. To get consumer & access tokens, first register your app on [https://dev.twitter.com/apps/new](https://dev.twitter.com/apps/new). Navigate to Keys and Access Tokens and click "Create my access token." **NOTE** - Each collector needs to have a unique set of access keys, or else the Streaming API will limit your connection. The four keys include:
    * Consumer Key
    * Consumer Secret
    * Access Token
    * Access Token Secret

_A note on location tracking_: Location tracking with Twitter is an OR filter. We will collect all tweets that match other filters (such as a terms list or a language identifier) OR tweets in the given location. Please plan accordingly.

**Config File**

As of v1.0, most configuration information has been moved away from .ini files and into Mongo. However, we still use the config file to maintain rollover rates for data collection. First, open the config file:

    vim ./stack/twitter/platform.ini

Edit the following key line items:

* _tweets_file_date_frmt_: The rollover rate for the collection file (minutes, hours, or days). By default it is set to hours, our suggest rate for production use.

## Step 3) Starting STACK

There a three processes to start to have STACK running in full: collector, processor, and inserter. As noted above, multiple instances of each process can run at the same time. In turn, an instance of each process need not run for STACK to operate.

* _Collectors_: A specific collector used to scrape data for a given set of filters. Multiple can be created/run for each project account.
* _Processors_: This processes raw tweet files written by a collector. Only one processor can be run for a given project account.
* _Inserters_: A process that takes processed tweets and inserts them into MongoDB. Only one inserter can be run for a given project account.

TODO - wiki

To learn more about STACK processes and architecture, [please consult our wiki](#).

**Starting a Collector**

To start a collector, you'll need to pass both a project_id and collector_id to STACK via the console. First, get your project accounts ID:

    $ python __main__.py db auth [project_name] [password]
    {"status": 1, "message": "Success", "project_id": "your_id_value"}

Then, using the project_id returned above, find a list of your collectors and their ID values:

    $ python __main__.py db get_collector_ids [project_id]
    {"status": 1, "collectors": [{"collector_name": [your_collector_name], "collector_id": [your_collector_id]}]}

Finally, using the project_id and collector_id values returned above, start the given collector for the project account of your choice:

    python __main__.py controller collect start [project_id] [collector_id]

Your collector is now running!

**Starting a Processor**

To start a processor, the syntax is very similar to the collector start command above. Here though, you only need to pass a project account ID:

    python __main__.py controller process start [project_id] twitter

Your processor is now running!

**Starting an Inserter**

To start an inserter, follow the syntax for starting a processor, but instead calling the "insert" command instead:

    python __main__.py controller insert start [project_id] twitter

Your inserter is now running!

