#!env/bin/python

import sys
import os
from src.controller import Controller

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

    Collector = Controller(
        module=module,
        api='follow',
        collector=twitter_collector,
        processor=twitter_processor,
        inserter=twitter_inserter
    )

    Collector.run(process, command)

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
