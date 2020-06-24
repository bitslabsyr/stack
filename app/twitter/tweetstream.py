#
# swipped from https://github.com/salathegroup/mkondo/tree/master/mkondo
#
import tweepy
import http.client
from socket import timeout
from socket import error as socket_error
from time import sleep
import logging
import logging.config

class CompliantStream(tweepy.Stream):
	"""This class extends Tweepy's Stream class by adding HTTP and TCP/IP
	back-off (according to Twitter's guidelines)."""

	def __init__(self, auth, listener, retry_count, logger, min_http_delay=5,
		max_http_delay=320, min_http_420_delay=60, min_tcp_ip_delay=0.5,
		max_tcp_ip_delay=16, **options):

		self.logger = logger
		self.logger.info('COMPLIENT STREAM: Initializing complient stream...')
		self.min_http_delay = min_http_delay
		self.max_http_delay = max_http_delay
		self.min_tcp_ip_delay = min_tcp_ip_delay
		self.max_tcp_ip_delay = max_tcp_ip_delay
		self.running = False
		self.retry_count = retry_count
		self.auth = auth

		#Twitter sends a keep-alive every twitter_keepalive seconds
		self.twitter_keepalive = 30

		#Add a couple seconds more wait time.
		self.twitter_keepalive += 2.0

		self.sleep_time = 0

		#logging.info('COMPLIANT STREAM: Initializing compliant stream...')

		tweepy.Stream.__init__(self, auth, listener, secure=True, **options)

	def _run(self):
		url = "%s://%s%s" % (self.scheme, self.host, self.url)

		# Connect and process the stream
		error_counter = 0
		conn = None
		exception = None
		while self.running:
			if self.retry_count and error_counter > self.retry_count:
				# quit if error count greater than retry count
				break
			try:
				if self.scheme == "http":
					conn = http.client.HTTPConnection(self.host)
				else:
 					conn = http.client.HTTPSConnection(self.host)
				self.auth.apply_auth(url, 'POST', self.headers, self.parameters)
				conn.connect()
				conn.sock.settimeout(self.twitter_keepalive)
				conn.request('POST', self.url, self.body, headers=self.headers)
				resp = conn.getresponse()
				if resp.status != 200:
					self.logger.exception('COMPLIANT STREAM: API Error %s.' % resp.status)
					if self.listener.on_error(resp.status) is False:
						break
					error_counter += 1
					#HTTP delay is based on error count, since we have exponential back-off
					if resp.status == 420:
						http_delay = self.get_http_420_delay(error_counter)
					else:
						http_delay = self.get_http_delay(error_counter)
					self.sleep_time = http_delay
					sleep(http_delay)
				else:
					error_counter = 0
					http_delay = 0
					tcp_ip_delay = 0
					self._read_loop(resp)
			except (timeout, socket_error):
				if self.listener.on_timeout() == False:
					break
				if self.running is False:
					break
				conn.close()
				error_counter += 1
				self.logger.exception('COMPLIANT STREAM: TCP/IP error caught.')
				tcp_ip_delay = self.get_tcp_ip_delay(error_counter)
				self.sleep_time = tcp_ip_delay
				sleep(tcp_ip_delay)
			except http.client.IncompleteRead:
				self.logger.exception('COMPLIANT STREAM: Incomplete Read.')

				#We assume there are connection issues at the other end, so we'll
				#try again in a little bit.
				error_counter += 1
				#HTTP delay is based on error count, since we have exponential back-off
				http_delay = self.get_http_delay(error_counter)
				self.logger.info('COMPLIANT STREAM: HTTP Delay. Sleeping for: %s' % tcp_ip_delay)
				self.sleep_time = http_delay
				sleep(http_delay)

			except Exception as e:
				self.logger.exception('Unexpected exception: %s' % e)
				self.logger.exception(e)
				print(e.args)
				break
				# any other exception is fatal, so kill loop

		# cleanup
		self.running = False
		if conn:
			conn.close()

		if exception:
			raise

	def get_http_delay(self, error_count):
		''' Exponential back-off, based on the number of times we've failed (error_count) '''
		delay = self.min_http_delay * (2.0 ** error_count)
		print("Error Count: %d -- Delay: %d" % (error_count, delay))
		if delay > self.max_http_delay:
			return self.max_http_delay
		return delay

	def get_http_420_delay(self, error_count):
		''' Exponential back-off, based on the number of times we've failed (error_count) '''
		delay = self.min_http_420_delay * (2.0 ** error_count)
		return delay

	def get_tcp_ip_delay(self, error_count):
		''' Linear back-off, based on the number of times we've failed (error_count) '''
		delay = float(self.min_tcp_ip_delay * error_count)
		if delay > self.max_tcp_ip_delay:
			return self.max_tcp_ip_delay
		return delay
