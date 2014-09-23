from pymongo import Connection()

class ConfigController(object):

    def __init__(self, config_db, config_collection, module_name, config_type):
        self.config_db = config_db
        self.config_collection = config_collection
        self.module_name = module_name

    def connect(self):
        connection = Connection()
        db = connection.(self.config_db)
        config_collection = db.(self.config_collection)

        return config_collection

    def setup(self, name=None, db_name=None, collection_name=None, file_path=None, date_frmt=None, output_file=None, terms_file=None, log_dir=None, log_config_file=None, consumer_key=None, consumer_secret=None, access_token=None, access_secret=None):
        config_collection = self.connect()
        # TODO - Check if already exists
        config_collection.insert({"module": str(self.module_name)})

        if self.config_type == "config":
            config_collection.update({"module": str(self.module_name)},
                {"$set": {"collection": {
                    "name": str(name),
                    "db_name": str(db_name),
                    "collection_name": str(collection_name)
                }}})

            config_collection.update({"module": str(self.module_name)},
                {"$set": {"files": {
                    "file_path": str(file_path),
                    "date_frmt": str(date_frmt),
                    "output_file": str(output_file),
                    "terms_file": str(terms_file),
                    "log_dir": str(log_dir),
                    "log_config_file": str(log_config_file)
                }}})

            config_collection.update({"module": str(self.module_name)},
                {"$set": {"auth": {
                    "consumer_key": str(consumer_key),
                    "consumer_secret": str(consumer_secret),
                    "access_token": str(access_token),
                    "access_secret": str(access_secret)
                }}})

    def update(self):
        pass

class Collector(ConfigController):
    pass

class Processor(ConfigController):
    pass

class Inserter(ConfigController):
    pass

if __name__ == "__main__":
    pass

