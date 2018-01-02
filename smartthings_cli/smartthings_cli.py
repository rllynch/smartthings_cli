#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" SmartThings CLI

Copyright 2015 Richard L. Lynch <rich@richlynch.com>

Description: Control SmartThings devices from the command line.

Dependencies: twisted, requests, future

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

from future.standard_library import install_aliases
install_aliases()

import argparse
import logging
import requests
import json
import os
import sys
from urllib.parse import urlencode
import socket
from twisted.web import server, resource
from twisted.internet import reactor

class OAuthHandler(resource.Resource):
    """Web server to receive OAuth2 authorization code"""
    isLeaf = True
    def __init__(self):
        self.auth_code = None
        resource.Resource.__init__(self)

    def render_GET(self, request): # pylint: disable=invalid-name
        """Handle GET from auth server"""
        logging.debug('Received GET for %s / %s', request.uri, request.args)
        if b'code' in request.args:
            self.auth_code = request.args[b'code'][0].decode('utf-8')
            logging.debug('Parsed auth code: %s', self.auth_code)
            # Schedule shutdown of reactor
            reactor.callLater(1, reactor.stop) # pylint: disable=no-member
            return 'smartthings_cli.py received auth code'.encode('utf-8')
        return ''.encode('utf-8')

def get_auth_code(redirect_url, bind_port, client_id):
    """Prompt user to allow access, wait for response from auth server"""
    param = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': 'app',
        'redirect_uri': redirect_url
    }
    auth_code_url = 'https://graph.api.smartthings.com/oauth/authorize?' + urlencode(param)

    logging.info('Please go to the following URL in your browser')
    logging.info('%s', auth_code_url)

    # HTTP site to handle subscriptions/polling
    handler = OAuthHandler()
    status_site = server.Site(handler)
    reactor.listenTCP(bind_port, status_site) # pylint: disable=no-member
    reactor.run() # pylint: disable=no-member

    auth_code = handler.auth_code
    logging.info('Received auth code: %s', auth_code)
    return auth_code

def get_access_token(redirect_url, client_id, client_secret, auth_code):
    """Trade the auth code for an access token"""
    param = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_url,
        'scope': 'app',
        'code': auth_code
    }
    access_token_url = 'https://graph.api.smartthings.com/oauth/token?' + urlencode(param)

    logging.debug("Requesting access token from: %s", access_token_url)

    req = requests.get(access_token_url)
    req_json = req.json()

    access_token = req_json['access_token']
    logging.debug('Received access token response: %s', req_json)
    logging.info('Received access token: %s', access_token)
    return access_token

def get_endpoint_url(access_token):
    """Retrieve the URL for the SmartApp"""
    endpoint_discovery_url = 'https://graph.api.smartthings.com/api/smartapps/endpoints'
    headers = {'Authorization': 'Bearer ' + access_token}
    logging.debug('Requesting endpoints from: %s', endpoint_discovery_url)
    req = requests.get(endpoint_discovery_url, headers=headers)
    req_json = req.json()
    logging.debug('Received endpoint discovery response: %s', req_json)
    endpoint_base_url = req_json[0]['base_url']
    endpoint_url = req_json[0]['url']
    logging.info('Received endpoint URL: %s%s', endpoint_base_url, endpoint_url)
    return endpoint_base_url, endpoint_url

def get_status(access_token, endpoint_base_url, endpoint_url, device_type):
    """Query the status and device ID of all devices of one type"""
    url = endpoint_base_url + endpoint_url
    url += '/' + device_type

    headers = {'Authorization': 'Bearer ' + access_token}

    logging.debug('Requesting status from: %s', url)
    req = requests.get(url, headers=headers)
    logging.debug('Response: %s', req.text)
    req_json = req.json()
    logging.debug('Received status response: %s', req_json)

    dev_list = {}
    for json_dev in req_json:
        key = json_dev['label']

        dev_list[key] = {}
        dev_list[key]['device_id'] = json_dev['id']

        if 'state' in json_dev['value']:
            dev_list[key]['state'] = json_dev['value']['state']

    return dev_list


def update_device(access_token, endpoint_base_url, endpoint_url, dev_list, device_type, device_name, cmd): # pylint: disable=too-many-arguments
    """Issue a command to a device"""

    if not device_name in dev_list:
        logging.error('%s "%s" does not exist!', device_type, device_name)
        return

    logging.info('Issuing "%s" command to %s "%s"', cmd, device_type, device_name)

    url = endpoint_base_url + endpoint_url
    url += '/' + device_type
    url += '/' + dev_list[device_name]['device_id']
    url += '/' + cmd

    headers = {'Authorization': 'Bearer ' + access_token}

    logging.debug('Requesting status from: %s', url)
    req = requests.get(url, headers=headers)
    logging.debug('Response (%d): %s', req.status_code, req.text)

def load_config():
    """Load the script's configuration from a JSON file"""
    home_dir = os.path.expanduser("~")
    config_fn = os.path.join(home_dir, '.smartthings_cli.json')

    if os.path.exists(config_fn):
        with open(config_fn) as json_file:
            config = json.load(json_file)
    else:
        config = {}

    return config

def save_config(config):
    """Save script's configuration to a JSON file"""
    home_dir = os.path.expanduser("~")
    config_fn = os.path.join(home_dir, '.smartthings_cli.json')

    with open(config_fn, 'w') as json_file:
        json.dump(config, json_file, indent=4)

def get_this_host_ip():
    '''Returns the IP address of this computer used to connect to the internet
    (i.e. not the loopback interface's IP)'''
    # Adapted from Alexander at http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/1267524#1267524
    ghbn_ips = socket.gethostbyname_ex(socket.gethostname())[2]
    ip_list = [ip for ip in ghbn_ips if not ip.startswith("127.")]
    if len(ip_list) > 0:
        return ip_list[0]
    # Find the IP used to connect to the internet
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(('8.8.8.8', 80))
    gsn_ip = sock.getsockname()[0]
    sock.close()
    return gsn_ip

def main():
    """Main function to handle use from command line"""
    # pylint: disable=too-many-locals

    arg_proc = argparse.ArgumentParser(description='SmartThings CLI', formatter_class=argparse.RawTextHelpFormatter)
    arg_proc.add_argument('--httpport', dest='http_port', help='HTTP port number for initial authentication', default=8080, type=int)
    arg_proc.add_argument('--debug', dest='debug', help='Enable debug messages', default=False, action='store_true')
    arg_proc.add_argument('--clientid', dest='client_id', help='OAuth2 client ID', default=None)
    arg_proc.add_argument('--clientsecret', dest='client_secret', help='OAuth2 client secret', default=None)
    arg_proc.add_argument('--publicip', dest='public_ip', help='Public IP of this computer', default=None)
    arg_proc.add_argument('commands', nargs='*', help='The following commands are supported:\nquery DEVICE_TYPE all\nquery DEVICE_TYPE DEVICE_NAME\nset DEVICE_TYPE DEVICE_NAME COMMAND')
    options = arg_proc.parse_args()

    return_code = 0

    log_level = logging.INFO
    if options.debug:
        log_level = logging.DEBUG

    logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=log_level)
    logging.getLogger("requests").setLevel(logging.WARNING)

    config = load_config()

    client_id = None
    if 'client_id' in config:
        client_id = config['client_id']
    if options.client_id:
        client_id = options.client_id
    if not client_id:
        logging.error('Client ID must be specified on the command line or config file!')
        sys.exit(1)

    client_secret = None
    if 'client_secret' in config:
        client_secret = config['client_secret']
    if options.client_secret:
        client_secret = options.client_secret
    if not client_secret:
        logging.error('Client secret must be specified on the command line or config file!')
        sys.exit(1)

    access_token = None
    if 'access_token' in config:
        access_token = config['access_token']

    endpoint_base_url = None
    if 'endpoint_base_url' in config:
        endpoint_base_url = config['endpoint_base_url']

    endpoint_url = None
    if 'endpoint_url' in config:
        endpoint_url = config['endpoint_url']

    if not access_token:
        public_ip = options.public_ip
        public_port = options.http_port
        bind_port = public_port

        if not public_ip:
            public_ip = get_this_host_ip()
            logging.debug('IP of this computer is: %s', public_ip)

        oauth_redirect_url = 'http://%s:%d/' % (public_ip, public_port)
        auth_code = get_auth_code(oauth_redirect_url, bind_port, client_id)
        access_token = get_access_token(oauth_redirect_url, client_id, client_secret, auth_code)
        config['client_id'] = client_id
        config['client_secret'] = client_secret
        config['access_token'] = access_token

    if not endpoint_url or not endpoint_base_url:
        endpoint_base_url, endpoint_url = get_endpoint_url(access_token)
        config['endpoint_base_url'] = endpoint_base_url
        config['endpoint_url'] = endpoint_url

    dev_lists = {}
    cmd_list = options.commands

    valid_device_types = [
        'switch',
        'motion',
        'temperature',
        'humidity',
        'contact',
        'acceleration',
        'presence',
        'battery',
        'threeAxis'
    ]

    while len(cmd_list):
        cmd = cmd_list.pop(0)

        if cmd == 'set':
            device_type = cmd_list.pop(0)
            device_name = cmd_list.pop(0)
            device_cmd = cmd_list.pop(0)

            if not device_type in valid_device_types:
                logging.error("Invalid device type: %s", device_type)
                continue

            if not device_type in dev_lists:
                dev_lists[device_type] = get_status(access_token, endpoint_base_url, endpoint_url, device_type)
            update_device(access_token, endpoint_base_url, endpoint_url, dev_lists[device_type], device_type, device_name, device_cmd)

        if cmd == 'query':
            device_type = cmd_list.pop(0)
            device_name = cmd_list.pop(0)

            if not device_type in valid_device_types:
                logging.error("Invalid device type: %s", device_type)
                continue

            if not device_type in dev_lists:
                dev_lists[device_type] = get_status(access_token, endpoint_base_url, endpoint_url, device_type)

            if device_name == 'all':
                for device_name in dev_lists[device_type]:
                    device_state = dev_lists[device_type][device_name]['state']
                    logging.info('%s %s: %s', device_type, device_name, device_state)
                    if device_state:
                        return_code = 1
            else:
                if not device_name in dev_lists[device_type]:
                    logging.error('%s "%s" does not exist!', device_type, device_name)
                    continue
                device_state = dev_lists[device_type][device_name]['state']
                logging.info('%s %s: %s', device_type, device_name, device_state)
                if device_state:
                    return_code = 1

    save_config(config)
    sys.exit(return_code)

if __name__ == "__main__":
    main()
