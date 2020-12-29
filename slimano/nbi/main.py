#!/usr/bin/env python

from flask import Flask, Response, Request
from flask import request
from nameko.standalone.rpc import ClusterRpcProxy
from templates import json_validator
from templates import exceptions as template_exceptions

import time
import json
import argparse
import logging
import configparser

logger = logging.getLogger(__name__)
config = configparser.ConfigParser()

app = Flask(__name__)


@app.route('/nst', methods=['POST'])
def nst_create():
    """
    :return:
    """
    nstc_b_time = round(time.time() * 1000)

    payload = json.loads(request.data)

    # TODO: Validate template
    try:
        jv.validate_nst(payload)
    except template_exceptions.ValidationError as e:
        app.logger.error(e.message)
        raise

    # Call engine
    with ClusterRpcProxy(nameko_config) as cluster_rpc:
        res = cluster_rpc.engine.create_nst(payload)

    app.logger.debug('$$nbi|Flask|nst_create||{}$$'.format(str(round(time.time() * 1000) - nstc_b_time)))
    return Response(json.dumps(res),
                    status=200,
                    mimetype='application/json')


@app.route('/nst', methods=['PUT'])
def nst_update():
    # Validate template
    payload = json.loads(request.data)

    # TODO: Validate template
    try:
        jv.validate_nst(payload)
    except template_exceptions.ValidationError as e:
        app.logger.error(e.message)
        raise

    # Call engine
    with ClusterRpcProxy(nameko_config) as cluster_rpc:
        res = cluster_rpc.engine.update_nst(payload)

    return Response(json.dumps(res),
                    status=200,
                    mimetype='application/json')


@app.route('/nsi', methods=['POST'])
def nsi_instantiate():
    """
    :return:
    """
    nsic_b_time = round(time.time() * 1000)

    # Validate template
    payload = json.loads(request.data)

    # TODO: Validate template
    try:
        jv.validate_nsi(payload)
    except template_exceptions.ValidationError as e:
        app.logger.error(e.message)
        raise

    # Call engine
    with ClusterRpcProxy(nameko_config) as cluster_rpc:
        res = cluster_rpc.engine.create_nsi(payload)

    app.logger.debug('$$nbi|Flask|nsi_instantiate||{}$$'.format(str(round(time.time() * 1000) - nsic_b_time)))
    return Response(json.dumps(res),
                    status=200,
                    mimetype='application/json')


@app.route('/nsi/<nsi_id>', methods=['PUT'])
def nsi_update(nsi_id):
    """
    :param nsi_id:
    :return:
    """
    pass


@app.route('/nsi/<nsi_id>', methods=['GET'])
def nsi_list(nsi_id):
    # call engine
    with ClusterRpcProxy(nameko_config) as cluster_rpc:
        res = cluster_rpc.engine.get_nsi(nsi_id)

    return Response(json.dumps(res),
                    status=200,
                    mimetype='application/json')


@app.route('/nsi/<nsi_id>', methods=['DELETE'])
def nsi_delete(nsi_id):
    start_time = round(time.time() * 1000)
    # call engine
    with ClusterRpcProxy(nameko_config) as cluster_rpc:
        res = cluster_rpc.engine.delete_nsi(nsi_id)
        status = 200 if res.get('status') == 'error' else 404

    app.logger.debug(
        '$$nbi|Flask|nsi_delete||{}$$'.format(str(round(time.time() * 1000) - start_time)))

    return Response(json.dumps(res),
                    status=status,
                    mimetype='application/json')


@app.route('/nsi/<nsi_id>', methods=['GET'])
def nsi_show(nsi_id):
    pass


@app.route('/vnf/deploy', methods=['POST'])
def vnf_deploy():
    pass


@app.route('/vnf/move', methods=['POST'])
def vnf_move():
    pass


@app.route('/nfvo', methods=['POST'])
def nfvo_create():
    """
    :return:
    """

    # Validate template
    payload = json.loads(request.data)

    # TODO: Validate template
    try:
        jv.validate_nfvo(payload)
    except template_exceptions.ValidationError as e:
        app.logger.error(e.message)
        raise

    with ClusterRpcProxy(nameko_config) as cluster_rpc:
        res = cluster_rpc.engine.create_nfvo(payload)

    return Response(json.dumps(res),
                    status=200,
                    mimetype='application/json')


if __name__ == '__main__':
    # argument parsing
    parser = argparse.ArgumentParser(description='sliMANO NBI application')
    parser.add_argument('config_file', metavar='<config_file>', type=str,
                        help='Configuration file')
    args = parser.parse_args()

    # load configuration file
    config.read_file(open(args.config_file))

    # # setup logging
    # logging.basicConfig(stream=sys.stdout,
    #                     # filename=config.get('DEFAULT', 'log_file'),
    #                     level=logging.DEBUG)
    # logger.addHandler(default_handler)

    nameko_config = {
        'AMQP_URI': config.get('AMQP', 'uri'),
        'rpc_exchange': config.get('AMQP', 'rpc_exchange')
    }

    jv = json_validator.JsonValidator()

    app.run(config.get('API', 'host'), config.get('API', 'port'), debug=config.get('DEFAULT', 'debug'))
