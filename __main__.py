#!env/bin/python

import sys
import os
from src.controller import Controller

basedir = os.getcwd()

Twitter = Controller(
    module='twitter',
    run_script='ThreadedCollector',
    process_script='preprocess',
    insert_script='mongoBatchInsert'
)

if __name__ == "__main__":
    pass

# Command Line syntax
#
# USAGE: python [toolkit-name] [network-module] run|collect|process|insert start|stop|update
#
# Examples --
#
# python BITS twitter run start
# python BITS twitter process stop
