#!env/bin/python

import sys
import os
from src import controller

Twitter = Controller(
    module='Twitter',
    run_script='ThreadedCollector',
    process_script='preprocess',
    insert_script='mongoBatchInsert'
)

if __name__ == "__main__":
    # controller.test()
    controller.run()
