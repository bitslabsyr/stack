import requests
import json


class Facebook(object):
    """
    Custom Facebook "SDK" - serves as a wrapper for common STACK functions when connecting w/ the Graph API
    """

    def __init__(self, level='app', **kwargs):
        """
        :param type: 'app' (app level requests) | 'user' (user level requests)
        """
        self.level = level

        # TODO - Handle authentication for user level as well
        self.client_id = kwargs['client_id']
        self.client_secret = kwargs['client_secret']

        self.base_url = 'https://graph.facebook.com/v2.3'

        # Load in access token via app-level call
        self.access_token = self._get_access_token()

    def get_object_feed(self, id, limit=250, since=None, until=None):
        """
        Public method to grab feed from an object

        :param id: page_id (required)
        :param since: YYYY-MM-DD formatted date as a lower-boundary limit (optional)
        :param until: YYYY-MM-DD formatted date as an upper-bound (optional)

        :returns resp
        """
        url = self.base_url + '/' + id + '/feed'

        params = {'limit': limit, 'access_token': self.access_token}
        if since is not None:
            params['since'] = since
        if until is not None:
            params['until'] = until

        resp = requests.get(url, params=params)
        resp = json.loads(resp.content)

        if 'error' in resp.keys():
            raise FacebookError(resp)

        return resp

    def get_object_id(self, object):
        """
        Public method to get an ID value for an object name
        """
        url = self.base_url + '/' + object
        params = {'access_token': self.access_token}

        resp = requests.get(url, params=params)
        resp = json.loads(resp.content)

        if 'error' in resp.keys():
            raise FacebookError(resp)

        id = resp['id']
        return id

    def _get_access_token(self):
        """
        Utility method to grab app-level access tokens for app-level requests
        """
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }

        resp = requests.get(self.base_url + '/oauth/access_token', params=params)
        resp = json.loads(resp.content)

        if 'error' in resp.keys():
            raise FacebookError(resp)
        else:
            access_token = resp['access_token']

        return access_token


class FacebookError(Exception):
    def __init__(self, resp):
        self.result = resp
        self.type = self.result['error']['code']
        self.message = self.result['error']['message']

        self.err = {'message': self.message, 'code': self.type}

        Exception.__init__(self, self.err)


if __name__ == '__main__':
    try:
        fb = Facebook(client_id='812448762135498', client_secret='a7461701f336afe91a9d4bbe0373cd9f')
        print json.dumps(fb.get_object_feed('ins', limit=1), indent=1)
    except FacebookError as e:
        print e[0]['code']
