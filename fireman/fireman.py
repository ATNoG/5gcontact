# coding: utf-8


import os
import time
import signal
import random
import logging
import argparse
import requests
import threading
from flask import Flask, request, jsonify


logging.basicConfig(level=logging.INFO)
werkzeug = logging.getLogger('werkzeug')
werkzeug.setLevel(logging.WARNING)
logger = logging.getLogger('VF')


# Ends the process
def signal_handler(sig, frame):
    os.kill(os.getpid(), signal.SIGTERM)


# State Object used on the State Machine
class State(object):
    def __init__(self):
        pass

    def on_event(self, event):
        pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__


# Definition of states
class Waiting(State):
    def on_event(self, event=None):
        if event is None:
            return self
        return Normal()


class Normal(State):
    def __init__(self, min_it=10, p=0.9):
        self.p = p
        self.min_it = min_it
        self.it = 0

    def on_event(self, event=None):
        if self.it >= self.min_it:
            if random.random() >= self.p:
                return Co2()
            return self
        else:
            self.it += 1
            return self


class Co2(State):
    def __init__(self, min_it=10, p=0.9):
        self.p = p
        self.min_it = min_it
        self.it = 0

    def on_event(self, event=None):
        if event is None:
            if self.it >= self.min_it:
                if random.random() >= self.p:
                    return Fall()
                return self
            else:
                self.it += 1
                return self
        else:
            return Normal()


class Fall(State):
    def on_event(self, event=None):
        if event is None:
            return self
        return Normal()


# Definition of the State Machine
class StateMachine(object):
    def __init__(self, fid, url, bpm_avg, bpm_std):
        self.state = Waiting()
        self.url = url
        self.fid = fid
        self.bpm_avg = bpm_avg
        self.bpm_std = bpm_std
        self.lock = threading.Lock()

    def on_event(self, event=None):
        with self.lock:
            self.state = self.state.on_event(event)
        logger.info(self.state)
        try:
            url = '{}sensor/{}'.format(self.url, self.fid)
            if isinstance(self.state, Waiting):
                data = {'id': self.fid, 'sensor': 'co2', 'value': 'low'}
                requests.put(url=url, json=data)
                
                data = {'id': self.fid, 'sensor': 'body', 'position': 'up'}
                requests.put(url=url, json=data)
            elif isinstance(self.state, Normal):
                data = {'id': self.fid, 'sensor': 'co2', 'value': 'low'}
                requests.put(url=url, json=data)
                
                data = {'id': self.fid, 'sensor': 'body', 'position': 'up'}
                requests.put(url=url, json=data)
            elif isinstance(self.state, Co2):
                data = {'id': self.fid, 'sensor': 'co2', 'value': 'high'}
                requests.put(url=url, json=data)

                data = {'id': self.fid, 'sensor': 'body', 'position': 'up'}
                requests.put(url=url, json=data)
            else:
                data = {'id': self.fid, 'sensor': 'co2', 'value': 'high'}
                requests.put(url=url, json=data)

                data = {'id': self.fid, 'sensor': 'body', 'position': 'fall'}
                requests.put(url=url, json=data)
            bpm = int(abs(random.gauss(self.bpm_avg, self.bpm_std)))
            data = {'id': self.fid, 'sensor': 'bpm', 'value': bpm}
            logger.info('BPM: %s', data)
            requests.put(url=url, json=data)
        except Exception as es:
            logger.error(es)


class StateMachineLoop(object):
    def __init__(self, sm, rl, rh):
        self.sm = sm
        self.rl = rl
        self.rh = rh
        self.rate = rl
        self.done = False

    def done(self):
        self.done = True

    def low_frequency(self):
        self.rate = self.rl

    def high_frequency(self):
        self.rate = self.rh

    def loop(self):
        while not self.done:
            self.sm.on_event()
            time.sleep(self.rate)


def create_app(config=None):
    app = Flask(__name__)

    app.config.update(config or {})

    @app.route('/', methods=['GET'])
    def info():
        rv = {}
        return jsonify(rv)

    @app.route('/control', methods=['PUT'])
    def endpoint():
        if request.is_json:
            content = request.get_json()
            sm = app.config['sm']
            sml = app.config['sml']
            if content['method'] == 'request_high_frequency':
                sml.high_frequency()
            elif content['method'] == 'request_low_frequency':
                sml.low_frequency()
            elif content['method'] == 'rescue_operation':
                sm.on_event(content['method'])
            elif content['method'] == 'deploy':
                sm.on_event(content['method'])
            else:
                werkzeug.warning('Unknown method: %s', content['method'])
                return ('', 404)
        else:
            werkzeug.warning('Request is not JSON: %s', request)
        return ('', 204)

    return app


if __name__ == "__main__":
    random.seed(time.time())
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser(
        description='5G Contact - Virtual Fireman')
    parser.add_argument('-H', dest='host', type=str,
                        help='HTTP host', default='localhost')
    parser.add_argument('-p', dest='port', type=int,
                        help='HTTP port', default=7654)
    parser.add_argument('-u', dest='url', type=str,
                        help='Endpoint', default='http://localhost:8765/')
    parser.add_argument('-rl', dest='rl', type=float,
                        help='Rate (low frequency)', default=1.0)
    parser.add_argument('-rh', dest='rh', type=float,
                        help='Rate (high frequency)', default=.1)
    parser.add_argument('-id', dest='fid', type=int,
                        help='Identification of the fireman', default=1)
    parser.add_argument('-bm', dest='bpm_avg', type=int,
                        help='Average (Mean) BPM', default=80)
    parser.add_argument('-bs', dest='bpm_std', type=int,
                        help='Standard Deviation BPM', default=15)
    args = parser.parse_args()

    # regiter sensor
    url = '{}register'.format(args.url)
    done = False
    while not done:
        logger.info('URL %s', url)
        response = requests.post(url=url, json={'id': args.fid, 'url': 'http://{}:{}/control'.format(
            args.host, args.port)}, headers={'Content-type': 'application/json'})
        logger.info('Responde code %s', response.status_code)
        if response.status_code == 204:
            done = True
        else:
            time.sleep(1)

    sm = StateMachine(args.fid, args.url, args.bpm_avg, args.bpm_std)
    sml = StateMachineLoop(sm, args.rl, args.rh)
    app = create_app({'sm': sm, 'sml': sml})
    state_machine_thread = threading.Thread(target=sml.loop)
    state_machine_thread.start()
    app.run(host=args.host, port=args.port)
    state_machine_thread.join()
