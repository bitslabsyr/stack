import threading
import time
import requests
import json
from datetime import datetime

from bson.objectid import ObjectId

from facebook import Facebook, FacebookError
from app.processes import BaseCollector
from app.models import DB


class CollectionListener(object):
    """
    Class to handle the connection to the Facebook API
    """
    def __init__(self, Collector):
        self.c = Collector
        self.fb = self.c.fb
        self.id_list = self.c.terms_list
        self.collection_type = self.c.collection_type
        self.params = self.c.params

        self.e = self.c.e
        self.running = False

        self.project_db = self.c.project_db
        self.collector_id = self.c.collector_id

        self.post_count = 0
        self.rate_limit_count = 0
        self.error_count = 0

        # For logging
        self.thread = 'LISTENER:'

    def run(self):
        """
        Starts the Facebook collection - sends to proper method based on type
        """
        # TODO - load in photos, need to actual store: collecting images off by default

        if self.collection_type == 'realtime':
            self.run_loop()
        elif self.collection_type == 'historical':
            self.run_search()

    def run_loop(self):
        """
        Infinite loop for real-time collections
        """
        self.running = True
        while self.running:

            # First, check to see if the thread has been set to shut down. If so, break
            thread_status = self.e.isSet()
            if thread_status:
                self.c.log('Collection thread set to shut down. Shutting down.', thread=self.thread)
                self.running = False
                break

            # Loop thru each term and queries the API
            for id in self.id_list:
                d = datetime.now()
                since = d.strftime('%Y-%m-%d')

                # TESTING
                since = '2015-04-14'

                # Loop thru until the paging has finished
                paging_url = 'none'
                while paging_url is not None:
                    try:
                        if paging_url is not 'none':
                            resp = requests.get(paging_url)
                            resp = json.loads(resp.content)
                        else:
                            resp = self.fb.get_object_feed(id, since=since)

                        # If there is not data and no more pages, the historical search has completed, so shut down
                        # TODO - can't shut down after first term!!
                        if not resp['data']:
                            self.c.log('All tweets for term %s collected for now. Sleeping for 10 minutes' % str(id),
                                       thread=self.thread)
                            paging_url = None
                            pass
                        # If there's data, process it
                        elif resp['data']:
                            self.on_data(resp['data'])
                            # Set the paging url for the next loop thru
                            if 'paging' not in resp.keys():
                                self.c.log('All tweets for term %s collected for now. Sleeping for 10 minutes' % str(id),
                                       thread=self.thread)
                                paging_url = None
                            else:
                                paging_url = resp['paging']['next']

                    # On error, logs and records in DB
                    except FacebookError as e:
                        self.c.log('Query for term ID %s failed.' % str(id), thread=self.thread, level='error')

                        now = time.strftime('%Y-%m-%d %H:%M:%S')
                        self.project_db.update({'_id': ObjectId(self.collector_id)},
                            {'$push': {'error_codes': {'code': e[0]['code'], 'message': e[0]['message'], 'date': now}}})

            # Collection loop has finished - now sleep for 10 minutes
            time.sleep(600)

    def run_search(self):
        """
        One-time Graph API search for historical collections
        """
        self.running = True
        while self.running:

            # First, check to see if the thread has been set to shut down. If so, break
            thread_status = self.e.isSet()
            if thread_status:
                self.c.log('Collection thread set to shut down. Shutting down.', thread=self.thread)
                self.running = False
                break

            # Loop thru each term and queries the API
            for id in self.id_list:
                since = self.params['since']
                until = self.params['until']

                # Check to see if there's a last value less than until. If so, replace b/c got cut off
                # mid collection last time
                last = self.params['last']
                if last:
                    if until is None or last < until:
                        until = last

                # Loop thru until the paging has finished
                paging_url = 'none'
                while paging_url is not None:
                    try:
                        if paging_url is not 'none':
                            resp = requests.get(paging_url)
                            resp = json.loads(resp.content)
                        else:
                            resp = self.fb.get_object_feed(id, since=since, until=until)

                        # If there is not data and no more pages, the historical search has completed, so shut down
                        # TODO - can't shut down after first term!!
                        if 'paging' not in resp.keys() or not resp['data']:
                            self.c.log('Historical query collection completed for term: %s.' % str(id), thread=self.thread)
                            paging_url = None
                            pass
                        # If there's data, process it
                        elif resp['data']:
                            self.on_data(resp['data'])
                            # Set the paging url for the next loop thru
                            paging_url = resp['paging']['next']

                    # On error, logs and records in DB
                    except FacebookError as e:
                        self.c.log('Query for term ID %s failed.' % str(id), thread=self.thread, level='error')

                        now = time.strftime('%Y-%m-%d %H:%M:%S')
                        self.project_db.update({'_id': ObjectId(self.collector_id)},
                            {'$push': {'error_codes': {'code': e[0]['code'], 'message': e[0]['message'], 'date': now}}})

            self.c.log('Historical query collection completed for all terms. Shutting down.', thread=self.thread)
            db = DB()
            db.set_collector_status(self.c.project_id, self.collector_id, collector_status=0)
            self.running = False

    def on_data(self, data):
        """
        Parses raw data and calls Collector's write() method to send to a file
        """
        try:
            # Loop thru each post
            for item in data:
                # First, check to see if the thread has been set to shut down. If so, break
                thread_status = self.e.isSet()
                if thread_status:
                    self.c.log('Collection thread set to shut down. Shutting down.', thread=self.thread)
                    self.running = False
                    break

                # First, if there are likes & a paging key, page thru
                if 'likes' in item.keys() and 'next' in item['likes']['paging'].keys():
                    paging_url = item['likes']['paging']['next']

                    # Now loop thru until no more comments to page thru
                    while paging_url is not None:
                        resp = requests.get(paging_url)
                        resp = json.loads(resp.content)

                        # Add likes to the data item
                        for like in resp['data']:
                            item['likes']['data'].append(like)

                        if 'next' in resp['paging'].keys():
                            paging_url = resp['paging']['next']
                        else:
                            # If no more 'next' key the page has finished
                            paging_url = None

                # Same thing for comments
                if 'comments' in item.keys() and 'next' in item['comments']['paging'].keys():
                    paging_url = item['comments']['paging']['next']

                    # Now loop thru until no more comments to page thru
                    while paging_url is not None:
                        resp = requests.get(paging_url)
                        resp = json.loads(resp.content)

                        # Add likes to the data item
                        for comment in resp['data']:
                            item['comments']['data'].append(comment)

                        if 'next' in resp['paging'].keys():
                            paging_url = resp['paging']['next']
                        else:
                            # If no more 'next' key the page has finished
                            paging_url = None

                # Logs this item as the last item in case cut off
                created_at = item['created_time'].split('T')[0]
                self.project_db.update({'_id': ObjectId(self.collector_id)}, {'$set': {'params.last': created_at}})

                # Finally, write the line to our outfile
                self.c.write(item)

        # Catch known data handling errors that could be raised
        except (ValueError, TypeError, KeyError) as e:
            self.c.log('Fatal exception raised upon data handling: %s' % e, thread=self.thread, level='error')
        # Need to catch all exceptions b/c we don't want data handling to kill the collector
        except Exception as e:
            self.c.log('Unknown data handling exception caught: %s' % e, thread=self.thread, level='error')


class Collector(BaseCollector):
    """
    Extension of the STACK Collector for Facebook
    """
    def __init__(self, project_id, collector_id, process_name):
        BaseCollector.__init__(self, project_id, collector_id, process_name)
        self.thread_count = 0
        self.thread_name = ''
        self.l = None
        self.l_thread = None

        self.e = threading.Event()

        # First, authenticate with the Facebook Graph API w/ creds from Mongo
        self.fb = Facebook(client_id=self.auth['client_id'], client_secret=self.auth['client_secret'])

    def start_thread(self):
        """
        Starts the CollectionThread()
        """
        self.thread_count += 1
        self.thread_name = self.collector_name + '-thread%d' % self.thread_count

        self.log("Terms list length: %d" % len(self.terms_list))
        self.log("Querying the Facebook Graph API for term IDs...")

        success_terms = []
        failed_terms = []
        for item in self.terms_list:
            term = item['term']

            # If the term already has an ID, pass
            if item['id'] is not None:
                pass
            else:
                try:
                    term_id = self.fb.get_object_id(term)
                # Term failed - not valid
                except FacebookError as e:
                    self.log('Page %s does not exist or is not accessible.' % term, level='warn')
                    item['collect'] = 0
                    item['id'] = None
                    failed_terms.append(term)
                # On success
                else:
                    item['id'] = term_id
                    success_terms.append(term)

        self.log('Collected %d new IDs for Facebook collection.' % len(success_terms))
        self.log('IDs for the following %d terms could not be found:' % len(failed_terms))
        self.log(failed_terms)

        self.log('Updating in Mongo...')

        self.project_db.update({'_id': ObjectId(self.collector_id)},
            {'$set': {'terms_list': self.terms_list}})

        # Now set terms list to be the final list of IDs
        ids = [item['id'] for item in self.terms_list if item['id'] and item['collect']]
        self.terms_list = ids

        self.log('Now initializing Facebook listener...')

        # Sets up thread
        self.l = CollectionListener(self)
        self.l_thread = threading.Thread(name=self.thread_name, target=self.l.run)
        self.l_thread.start()

        self.collecting_data = True
        self.log('Started Facebook listener thread: %s' % self.thread_name)

    def stop_thread(self):
        """
        Stops the CollectionThread()
        """
        if self.update_flag:
            self.log('Received UPDATE signal. Attempting to restart collection thread.')
            self.db.set_collector_status(self.project_id, self.collector_id, update_status=1)
        if not self.collect_flag or not self.run_flag:
            self.log('Received STOP/EXIT signal. Attempting to stop collection thread.')
            self.db.set_colllector_status(self.project_id, self.collector_id, collector_status=0)
            self.collect_flag = 0

        self.e.set()
        wait_count = 0
        while self.l_thread.isAlive():
            wait_count += 1
            self.log('%d) Waiting on Facebook listener thread shutdown.' % wait_count)
            time.sleep(wait_count)

        self.collecting_data = False

        # TODO - Facebook count, limit, error logging