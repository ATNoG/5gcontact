import logging
import requests
import time

from requests.exceptions import Timeout, ConnectionError

logger = logging.getLogger(__name__)


class CallbackHelper:

    def __init__(self, url, retries, interval):
        self.headers = {'Content-Type': 'application/json'}
        self.url = url
        self.retries = retries
        self.interval = interval

    def call_callback(self, message):
        r = None
        retry = self.retries
        while retry > 0:
            try:
                r = requests.post(self.url, headers=self.headers, data=message, timeout=(3, 10))
            except Timeout:
                logger.info('Timeout while connecting to callback URL: {}'.format(self.url))
            except ConnectionError:
                logger.info('Connection error while connecting to callback URL: {}'.format(self.url))
            if r and r.status_code == requests.codes.ok:
                return True
            time.sleep(self.interval)
            retry = retry - 1
        return False


if __name__ == '__main__':
    print(CallbackHelper('http://127.0.0.1:8080/callback', 3, 5).call_callback('{"status": "done"}'))
