import os
import time
import glob
import shutil

from app.processes import BaseProcessor


class Processor(BaseProcessor):
    """
    Facebook processor, extended from class BaseProcessor
    """
    def __init__(self, project_id, process_name, network):
        BaseProcessor.__init__(self, project_id, process_name, network)

    def process(self):
        """
        Processing logic - extended from BaseProcessor
        """
        # First, grab file list. If none, processor should sleep for three min.
        file_list = self.get_files()
        queue_length = len(file_list)

        if queue_length < 1:
            time.sleep(180)
        else:
            self.log('Raw files in queue: %d' % queue_length)

            raw_file = file_list[0]
            self.log('Processing raw file: %s' % raw_file)

            # For now we literally just queue the files - will add processing later
            self.archive_and_queue(raw_file)

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

    def archive_and_queue(self, raw_file):
        """
        Archives and queues up processed files for the inserter
        """
        split_raw = raw_file.split('.')
        processed_file = split_raw[0] + '_processed.json'

        raw_file_path = self.raw + '/' + raw_file

        # Archive raw file and "processed" raw file
        # Queues up "processed" raw file
        # Removes the original raw file
        shutil.copyfile(raw_file_path, self.archive + '/' + processed_file)
        shutil.copyfile(raw_file_path, self.queue + '/' + processed_file)
        shutil.move(raw_file_path, self.archive + '/' + raw_file)