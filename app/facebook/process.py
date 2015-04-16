import os
import time
import glob

from app.processes import BaseProcessor


class Processor(BaseProcessor):
    """
    Facebook processor, extended from class BaseProcessor
    """
    def __init__(self, project_id, process_name, network):
        BaseProcessor.__init__(self, project_id, process_name)
        self.network = network

        # Establish connections to data directories
        self.raw = self.datadir + '/' + self.network + '/raw'
        self.archive = self.datadir + '/' + self.network + '/archive'
        self.queue = self.datadir + '/' + self.network + '/queue'
        self.error = self.datadir + '/' + self.network + '/error'

        if not os.path.exists(self.raw):
            os.makedirs(self.raw)
        if not os.path.exists(self.archive):
            os.makedirs(self.archive)
        if not os.path.exists(self.queue):
            os.makedirs(self.queue)
        if not os.path.exists(self.error):
            os.makedirs(self.error)

    def process(self):
        """
        Processing logic - extended from BaseProcessor
        """

        # First, grab file list. If none, processor should sleep for three min.
        file_list = self.get_files()
        if len(file_list) < 1:
            time.sleep(180)

    def get_files(self):
        """
        Grabs list of raw files ready to be processed
        """
        file_list = [f for f in os.listdir(self.raw) if os.path.isfile(os.path.join(self.raw, f))]

        # Now, remove any file being written to currently based on timestr
        # TODO - create instance var for timestr
        timestr = time.strftime('%Y%m%d-%H')
        current_list = glob.glob(self.raw + '/' + timestr + '*')
        current_list = [f.split('raw/')[1] for f in current_list]

        file_list = [f for f in file_list if f not in current_list]

        return file_list

    def archive_and_queue(self):
        """
        Archives and queues up processed files for the inserter
        """