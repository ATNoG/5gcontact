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
from werkzeug.routing import BaseConverter


logging.basicConfig(filename='log/mlapp.log',level=logging.INFO, filemode='a', format='%(created)f::MLAPP::%(message)s')
werkzeug = logging.getLogger('werkzeug')
werkzeug.setLevel(logging.WARNING)
logger = logging.getLogger('ES')


# Ends the process
def signal_handler(sig, frame):
    os.kill(os.getpid(), signal.SIGTERM)


# Rescue operation function
def rescue_operation(mean, std, url_sensor):
    delay = random.gauss(mean, std)
    logger.info('Rescue (%s) with delay = %s', url_sensor, delay)
    time.sleep(abs(delay))
    logger.info('Send Rescue')
    requests.put(url_sensor, json={'method': 'rescue_operation'})
    return


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


# Define the facts/events
class CO2:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__


class Fireman:
    def __init__(self, position):
        self.position = position

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__


# Define the states of the state machine
class Low(State):
    def on_event(self, event):
        msg, url_sensor, url_control, mean, std = event
        if isinstance(msg, CO2):
            if msg.value == 'low':
                return self
            else:
                requests.put(url_sensor, json={'method': 'request_high_frequency'})
                return Severe_Co2()
        elif isinstance(msg, Fireman):
            if msg.position == 'up':
                return self
            else:
                requests.put(url_sensor, json={'method': 'request_high_frequency'})
                return Severe_Fireman()
        else:
            return self


class Severe_Co2(State):
    def on_event(self, event):
        msg, url_sensor, url_control, mean, std = event
        if isinstance(msg, CO2):
            if msg.value == 'low':
                requests.put(url_sensor, json={'method': 'request_low_frequency'})
                return Low()
            else:
                return self
        elif isinstance(msg, Fireman):
            if msg.position == 'up':
                return self
            else:
                requests.put(url_control, json={'method': 'go_to_edge'})
                # Setup rescue
                rescue_thread = threading.Thread(
                    target=rescue_operation, args=(mean, std, url_sensor))
                rescue_thread.start()
                return Critical()
        else:
            return self


class Severe_Fireman(State):
    def on_event(self, event):
        msg, url_sensor, url_control, mean, std = event
        if isinstance(msg, CO2):
            if msg.value == 'low':
                return self
            else:
                requests.put(url_control, json={'method': 'go_to_edge'})
                # Setup rescue
                rescue_thread = threading.Thread(
                    target=rescue_operation, args=(mean, std, url_sensor))
                rescue_thread.start()
                return Critical()
        elif isinstance(msg, Fireman):
            if msg.position == 'up':
                requests.put(url_sensor, json={'method': 'request_low_frequency'})
                return Low()
            else:
                return self
        else:
            return self


class Critical(State):
    def on_event(self, event):
        msg, url_sensor, url_control, mean, std = event
        url = '{}control'.format(url_sensor)
        if isinstance(msg, CO2):
            if msg.value == 'low':
                requests.put(url=url, json={'method': 'go_to_core'})
                return Severe_Fireman()
            else:
                return self
        elif isinstance(msg, Fireman):
            if msg.position == 'up':
                requests.put(url=url, json={'method': 'go_to_core'})
                return Severe_Co2()
            else:
                return self
        else:
            return self


def switch_state(state: str):
    return {'Low': Low(),
            'Severe_Co2': Severe_Co2(),
            'Severe_Fireman': Severe_Fireman(),
            'Critical': Critical}[state]


# Definition of the BPM object
class BPM(object):
    def __init__(self, fid, max_size, buffer):
        self.fid = fid
        self.max_size = max_size
        self.buffer = buffer
    
    def enqueue (self, value):
        self.buffer.append(value)
        if len(self.buffer) > self.max_size:
            self.buffer.pop(0)
    
    def avg(self):
        rv = 0

        for v in self.buffer:
            rv += v
        
        if len(self.buffer) > 0:
            rv /= len(self.buffer)
        
        return rv
    
    def to_json(self):
        return {'fid': self.fid, 'buffer':self.buffer, 'max_size': self.max_size}


# Definition of the State Machine
class StateMachine(object):
    def __init__(self, fid, url_sensor, url_control, mean, std, state='Low'):
        self.fid = fid
        self.url_sensor = url_sensor
        self.url_control = url_control
        self.mean = mean
        self.std = std
        self.lock = threading.Lock()
        self.state = switch_state(state)

    def set_urls(self, url_sensor=None, url_control=None):
        self.url_sensor = url_sensor
        self.url_control = url_control

    def set_rescue_delay(self, mean, std):
        self.mean = mean
        self.std = std

    def on_event(self, event=None):
        with self.lock:
            self.state = self.state.on_event(
                (event, self.url_sensor, self.url_control, self.mean, self.std))
        logger.info(self.state)
    
    def deploy(self):
        requests.put(url=self.url_sensor, json={'method': 'deploy'})

    def to_json(self):
        return {'fid': self.fid,
                'state': self.state.__str__(),
                'url_sensor': self.url_sensor,
                'url_control': self.url_control,
                'mean': self.mean,
                'std': self.std}


class IntListConverter(BaseConverter):
    regex = r'\d+(?:,\d+)*,?'

    def to_python(self, value):
        return [int(x) for x in value.split(',')]

    def to_url(self, value):
        return ','.join(str(x) for x in value)


def create_app(config=None):
    app = Flask(__name__)

    # app.config.update(dict(DEBUG=True))
    app.config.update(config or {})
    app.url_map.converters['int_list'] = IntListConverter

    @app.route('/', methods=['GET'])
    def info():
        rv = {}
        return jsonify(rv)

    @app.route('/register', methods=['POST'])
    def register():
        if request.is_json:
            content = request.get_json()
            fid = content['id']
            if fid not in app.config['firemans']:
                app.config['firemans'][fid] = (
                    StateMachine(fid, content['url'], app.config['url_control'], app.config['rescue_delay_mean'], app.config['rescue_delay_std']),
                    BPM(fid, app.config['max_size'], [])
                )
                logger.info('Register %s fireman', fid)
            else:
                werkzeug.warning('Fireman %s already exists', fid)
        else:
            werkzeug.warning('Request is not JSON: %s', request)
        return ('', 204)

    @app.route('/save/<int_list:ids>', methods=['GET'])
    def save(ids):
        rv = []
        for fid in ids:
            if fid in app.config['firemans']:
                logger.info("FID %s", fid)
                sm, bpm = app.config['firemans'][fid]
                logger.info({'sm': sm.to_json(), 'bpm': bpm.to_json()})
                rv.append({'id':fid, 'sm': sm.to_json(), 'bpm': bpm.to_json()})
            else:
                werkzeug.warning('Fireman %s does not exists', fid)
        return jsonify({'fireman': rv})

    @app.route('/restore', methods=['POST'])
    def restore():
        if request.is_json:
            content = request.get_json()
            firemans = app.config['firemans']
            json_firemans = content['fireman']
            for f in json_firemans:
                fid = f['id']
                if fid not in firemans:
                    sm = f['sm']
                    bpm = f['bpm']
                    firemans[fid] = (StateMachine(
                        fid, sm['url'], sm['url_control'], sm['rescue_delay_mean'], sm['rescue_delay_std'], sm['state']),
                        BPM(fid, bpm['max_size'], bpm['buffer']))
                else:
                    werkzeug.warning('Fireman %s already exists', fid)
        else:
            werkzeug.warning('Request is not JSON: %s', request)
        return ('', 204)
    
    @app.route('/rank/<int:n>', methods=['GET'])
    def rank(n: int):
        rv = []
        firemans = app.config['firemans']
        for k in firemans:
            sm, bpm = firemans[k]
            rv.append((k, bpm.avg()))
        rv.sort(key=lambda f: f[1])
        n = n if n < len(rv) else len(rv)
        rv = rv[:n]
        rank = []
        for r in rv:
            rank.append({'id':r[0], 'avg_bpm':r[1]})
        return jsonify({'rank': rank})

    @app.route('/sensor/<int:fid>', methods=['PUT'])
    def sensor(fid: int):
        if request.is_json:
            fid = int(fid)
            content = request.get_json()
            if fid not in app.config['firemans']:
                logger.warning('Unknown fireman: %s', fid)
                return ('', 404)
            sm, bpm = app.config['firemans'][fid]
            if content['sensor'] == 'co2':
                sm.on_event(CO2(content['value']))
            elif content['sensor'] == 'body':
                sm.on_event(Fireman(content['position']))
            elif content['sensor'] == 'bpm':
                bpm.enqueue(content['value'])
            else:
                logger.warning('Unknown sensor: %s', content['sensor'])
                return ('', 404)
        else:
            logger.warning('Request is not JSON: %s', request)
            return ('', 406)
        return ('', 204)
    
    @app.route('/deploy/<int_list:ids>', methods=['PUT'])
    def deploy(ids):
        for fid in ids:
            if fid in app.config['firemans']:
                logger.info("FID %s", fid)
                sm, bpm = app.config['firemans'][fid]
                sm.deploy()
            else:
                werkzeug.warning('Fireman %s does not exists', fid)
        return ('', 204)

    return app


if __name__ == "__main__":
    random.seed(time.time())
    parser = argparse.ArgumentParser(description='5G Contact - Expert System')
    parser.add_argument('-H', dest='host', type=str,
                        help='HTTP host', default='localhost')
    parser.add_argument('-p', dest='port', type=int,
                        help='HTTP port', default=8765)
    parser.add_argument('-u', dest='url_control', type=str,
                        help='Control Endpoint', default='http://localhost:7654/')
    parser.add_argument('-m', dest='mean', type=float,
                        help='Rescue Operation mean delay', default=5.0)
    parser.add_argument('-s', dest='std', type=float,
                        help='Rescue Operation std delay', default=2.5)
    parser.add_argument('-ms', dest='ms', type=int,
                        help='BPM buffer max size', default=20)
    args = parser.parse_args()

    app = create_app({
        'url_control': args.url_control,
        'rescue_delay_mean': args.mean,
        'rescue_delay_std': args.std,
        'max_size': args.ms,
        'firemans': {}})

    logger.info("UpAndRunning")
    app.run(host=args.host, port=args.port)
