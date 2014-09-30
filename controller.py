from pymongo import MongoClient

class ConfigController(object):

    def __init__(self, db_name, collection_name):
        self.db_name = db_name
        self.collection_name = collection_name

    # Connects to DB & Collection as specified by instance
    def _connect(self):
        connection = MongoClient()
        db = connection[self.db_name]
        db_collection = db[self.collection_name]

        return db_collection

    # Initial setup for each network module
    # --1) Module db_info contains final archival information
    # --2) Module file_info contains collection/log file paths & naming format
    # NOTE - The db here should be "config" and the collection should
    #   correspond to the network of interest.
    # TODO - Cleanup w/ *kwargs -- which are things that can remain the same??
    # TODO - Currently ported from the .ini format, should clean-up
    # TODO - Extensible OAuth for all networks
    def _setup(self, name, storage_db, storage_collection, file_path, archive_dir, insert_queue, date_frmt, output_file, terms_file, log_file, log_dir, log_config_file, consumer_key, consumer_secret, access_token, access_secret):
        setup_collection = self._connect()

        # Storage info module
        try:
            setup_collection.find({"module": "db_info"})[0]
        except IndexError:
            setup_collection.insert({"module": "db_info"})

        setup_collection.update({"module": "db_info"},
            { "$set": { "name": str(name),
                "storage_db": str(storage_db),
                "storage_collection": str(storage_collection)
            }})

        # Text & logfile info
        try:
            setup_collection.find({"module": "file_info"})[0]
        except IndexError:
            setup_collection.insert({"module": "file_info"})

        setup_collection.update({"module": "file_info"},
            { "$set": { "file_path": str(file_path),
                "archive_dir": str(archive_dir),
                "insert_queue": str(insert_queue),
                "date_frmt": str(date_frmt),
                "output_file": str(output_file),
                "terms_file": str(terms_file),
                "log_file": str(log_file),
                "log_dir": str(log_dir),
                "log_config_file": str(log_config_file)
            }})

        # OAuth Info
        try:
            setup_collection.find({"module": "oauth"})[0]
        except IndexError:
            setup_collection.insert({"module": "oauth"})

        setup_collection.update({"module": "oauth"},
            { "$set": { "consumer_key": str(consumer_key),
                "consumer_secret": str(consumer_secret),
                "access_token": str(access_secret),
                "access_secret": str(access_secret)
            }})

    def get(self, module_name, key):
        collection = self._connect()
        value = collection.find({"module": module_name},{key:1})[0][key]
        return value


class Collector(object):
    # TODO - Grab Info
    # TODO - Run Function
    # TODO - Update Function
    # TODO - Stop Function
    def __init__(self):
        pass

    def run():
        # Lines 229+ in ThreadCollector
        pass

class Processor(ConfigController):
    pass

class Inserter(ConfigController):
    pass

