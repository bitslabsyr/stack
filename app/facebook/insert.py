import os
import time
import json

from app.processes import BaseInserter


class Inserter(BaseInserter):
    """
    Facebook processor, extended from class BaseProcessor
    """
    def __init__(self, project_id, process_name, network):
        BaseInserter.__init__(self, project_id, process_name)
        self.network = network

        # Hook into the "facebook" collection
        self.insert_db = self.insert_db.facebook

        # Batch processing size
        self.BATCH = 1000

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
        Insertion logic - extended from BaseInserter
        """

        # First, grab file list. If none, processor should sleep for three min.
        file_list = self.get_files()
        queue_length = len(file_list)

        if queue_length < 1:
            time.sleep(180)
        else:
            self.log('Files in queue: %d' % queue_length)

            queued_file = file_list[0]
            self.log('Inserting file: %s' % queued_file)

            # For now, we just insert everything into the database - will add more functionality
            post_list = []
            posts = 0
            line_count = 0

            with open(queued_file, 'r') as f:
                for line in f:
                    line_count += 1

                    post = line.strip()
                    post = json.loads(post)
                    post_list.append(post)

                    if len(post_list) == self.BATCH:
                        self.log('Batch size of %d reached at file line %d. Inserting batch now.' %
                                 (self.BATCH, line_count))
                        inserted_ids_list = self.handle_insert(post_list)

                        posts += len(inserted_ids_list)

                        failed_count = len(post_list) - len(inserted_ids_list)
                        self.log('Insertion completed. Failed to insert %d posts.' % failed_count)

            # Once the file has finished, insert any additional tweets
            if len(post_list) > 0:
                self.log('Inserting remaining %d posts.' % len(post_list))
                inserted_ids_list = self.handle_insert(post_list)

                posts += len(inserted_ids_list)

                failed_count = len(post_list) - len(inserted_ids_list)
                self.log('Insertion completed. Failed to insert %d posts.' % failed_count)

            self.log('Insertion for file %s completed!' % queued_file)
            self.log('Inserted %d posts in total.' % posts)

            os.remove(queued_file)

    def get_files(self):
        """
        Grabs list of queued files ready to be inserted
        """
        file_list = [f for f in os.listdir(self.queue) if os.path.isfile(os.path.join(self.queue, f))]
        return file_list

    def handle_insert(self, post_list):
        """
        Actually inserts into Mongo - handles errors
        """
        inserted_ids_list = []

        try:
            inserted_ids_list = self.insert_db.insert(post_list, continue_on_error=True)
        except ValueError as e:
            self.log('Exception on Mongo insert: %e' % e, level='error')

        return inserted_ids_list