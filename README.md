STACK - Social Media Tracker, Aggregator, & Collector Toolkit
=========

STACK is a toolkit designed to collect, process, and store data streamed from online social networks. The toolkit is an ongoing project via the [Syracuse University iSchool](http://ischool.syr.edu), and currently supports the [Twitter Streaming API](https://dev.twitter.com/streaming/overview).

You can cite this repository:

Hemsley, J., Ceskavich, B., Tanupabrungsun, S. (2014). STACK (Version 1.0). Syracuse University, School of Information Studies.

Retrieved from https://github.com/jhemsley/Syr-SM-Collection-Toolkit

DOI: 10.5281/zenodo.12388

**_This documentation assumes the following:_**

* You know how to use ssh.
* Your server has Python, MongoDB, and PHP already installed.
* You understand how to edit files using vim (“vi”).
* You have rights and know how to install Python libraries.

## Wiki

The instructions below detail how to install STACK and work with the toolkit largely from the web front-end. To learn more about STACK semantics, or how to interact with the app directly from the command line, [refer to our wiki](#).

## XAMPP

We use XAMPP to serve a PHP-based front-end and communicate with our Python backend. Before installing STACK proper, we need to get XAMPP setup. The following instructions are specifically geared towars Linux distros that use wget.

First, install the XAMPP server:

    wget http://sourceforge.net/projects/xampp/files/XAMPP%20Linux/1.8.3/xampp-linux-x64-1.8.3-2-installer.run
    chmod 755 xampp-linux-*-installer.run
    sudo ./xampp-linux-*-installer.run

And finally, start XAMPP:

    sudo /opt/lampp/lampp start

That's it!

## Installation

We want to clone STACK within XAMPP, and by default the XAMPP stack uses the directory: /opt/lampp/htdocs/

So, clone this repo to your local machine:

    cd /opt/lampp/htdocs/
    sudo git clone https://github.com/bceskavich/SoMeToolkit.git STACK

Then, grant permissions to this repo:

    cd /opt/lampp/htdocs/STACK/
    sudo chmod -R 775 php/SoMeToolkit

_virtualenv_

We sometimes use Python's virtualenv to manage our development environments. To setup a virtual environment for STACK, simply run virtualenv's setup command and then activate the environment:

    virtualenv env
    . env/bin/activate

Then follow the installation steps below with the activated environment.

**NOTE** - Use of virtualenv is not necessary for STACK. You can learn more about pip [here](https://pypi.python.org/pypi/pip) and virtualenv [here](http://virtualenv.readthedocs.org/en/latest/).

_Requirements Installation_

Next, make sure to install the required dependences outlined in the _requirements.txt_ file. We use pip to install and manage our python dependencies:

    pip install -r requirements.txt

_OpenSSL_

Finally, we need to install and setup OpenSSL in order to maintain security compliance with the APIs STACK works with. The following instructions will work for most Unix and Unix-like systems.

You can read more about compiling and installing OpenSSL [on GitHub](https://github.com/openssl/openssl).

First, in your home directory clone the OpenSSL source, available on GitHub:

    git clone https://github.com/openssl/openssl.git

Next, move into the newly created openssl directory. Then, configure, compile, test, and install OpenSSL on your machine. **NOTE** - the following four steps will take some time.

    cd openssl
    ./config shared
    make
    make test
    make install

Now, we need to move some files to the LAMPP directory. Again, in the openssl directory do the following:

    mv libssl.so* /opt/lampp/lib/
    mv libcrypto.so* /opt/lampp/lib/

Finally, restart LAMPP:

    sudo /opt/lampp/lampp stop
    sudo /opt/lampp/lampp start

**Note** - We use Python 2.7.6 for STACK.

## Configuration & Setup

STACK is built to work with MongoDB. The app stores most configuration information in Mongo, however we also use a configuration (.ini) file to manage some parts of the collection process from the Streaming API. Before getting started with STACK, you'll need to do the following:

* Setup a project account
* Edit the master configuration file
* Create & start a collector

These steps are detailed below.

**Project Account Setup**

There are two ways to setup up a project account for STACK: via the command line or via the STACK front-end.

_Command Line_

From the main STACK package directory (STACK/php/SoMeToolkit/), activate the _setup.py_ script with the following command:

    python setup.py

The setup script initializes the Mongo database with important configuration information, as well as creates the first user account. The script will prompt you for the following information:

* _Project Name_: A unique account name for your project. STACK calls all login accounts "projects" and allows for multiple projects at once.
* _Password_: A password for your project account.
* _Description_: A short description for your project account.

If the script returns a successful execution notice, you will now be able to login to STACK via the web front-end using your project account name and password combination.

_Front End_

After completing all the installation steps detailed below, the main web page will include a link titled "Create New Project." Clicking the link, you'll be asked to fill in the same information as in the command line script noted above. Upon completion, you'll be able to login with your project account.

**Config File**

As of v1.0, most configuration information has been moved away from .ini files and into Mongo. However, we still use the config file to maintain rollover rates for data collection. First, open the config file:

    vim ./stack/twitter/platform.ini

Edit the following key line items:

* _tweets_file_date_frmt_: The rollover rate for the collection file (minutes, hours, or days). By default it is set to hours, our suggest rate for production use.

**Creating a Collector**

Each project account can instantiate multiple **collectors** that will scrape data from the Streaming API. A collector is defined as a singular instance that collects data for a specific set of user-provided terms. A project can have multiple collectors running for a given network.

From the STACK interface, you create a new collector by providing the following information in the appropriate fields:

* _Collector Name_: Non-unique name to identify your collector instance.
* _API_: Two options: track or follow. Each collector can stream from one part of the Streaming API:
    * **Track**: Collects all mentions (hashtags included) for a given list of terms.
    * **Follow**: Collects all tweets, retweets, and replies for a given use handle. Each term must be a valid Twitter screen name.
* _OAuth Information_: Four keys used to authenticate with the Twitter API. To get consumer & access tokens, first register your app on [https://dev.twitter.com/apps/new](https://dev.twitter.com/apps/new). Navigate to Keys and Access Tokens and click "Create my access token." **NOTE** - Each collector news to have a unique set of access keys, or else the Streaming API will limit your connection. The four keys include:
    * Consumer Key
    * Consumer Secret
    * Access Token
    * Access Token Secret
* _Terms_: A line item list of terms for the collector to stream. Each term must be one word.

Once the following information has been inputted, click **Create** followed by **Start**. Your collector is now running!

To learn more about how to interact with STACK from the command line, [refer to our wiki](#).

## Data Processing

STACK processes and stores data in a Mongo at a network level. This means that the app processes data collected for multiple collectors on the same network. While you can instantiate multiple Twitter collectors, processing will be done once.

Once you have created at least one collector, you can start processing and storing data by clicking on the respective buttons for the given network: **Start Pre-Processing** and **Start Insertion**.

To learn more about how to interact with STACK from the command line, [refer to our wiki](#).

## Ongoing Work + Next Action Items

This list will be updated soon with more detailed action items. Please note again that we are actively working on this toolkit!

1. Full move away from .ini file use
2. Extensible module format for future social network implementations
3. Exentesible back-end API

## Credits

Lovingly maintained at Syracuse University by:

* [Jeff Hemsley](https://github.com/jhemsley)
* [Billy Ceskavich](https://github.com/bceskavich/)
* [Sikana Tanupabrungsun](https://github.com/Sikana)

Distributed under the MIT License:

The MIT License (MIT)

Copyright (c) 2009-2013 University of Washington

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
