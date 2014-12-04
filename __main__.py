#!env/bin/python

import sys
import os
from stack.controller import Controller
from stack.db import DB

basedir = os.getcwd()

twitter_collector = 'ThreadedCollector'
twitter_processor = 'preprocess'
twitter_inserter = 'mongoBatchInsert'

if __name__ == "__main__":

    try:
        module = sys.argv[1]
        process = sys.argv[2]
        command = sys.argv[3]
    except:
        print 'Please try again!'
        print '-----------------\n'
        print 'USAGE: python . [network-module] run|collect|process|insert start|stop|update'
        sys.exit()

    collector = Controller(
        project_id='548078f2eb8f80044a9d3b4f',
        collector_id=''
    )

    collector.run(process, command)

#######################
# Command Line syntax
#######################
#
# RUNNING THE TOOLKIT
# -------------------
#
# USAGE: python [toolkit-name] [network-module] run|collect|process|insert start|stop|update
#
# Examples:
#
#   python BITS twitter run start
#   python BITS twitter process stop
#
# INTERACTING w/ MONGODB
# ----------------------
#
# TODO
