#!/usr/bin/env python

import json
import os
import time
import sys

import zmq
from Crypto.Hash import keccak

from .updater import FilterUpdater
from .daemon import Daemon

'''
Config:
* Provider wallet (private key or seed phrase)
*
Flow:
* log in using provider wallet, obtain session token
1. Start list/API-updater
  * get list from API
  * save list to file
  * add list to queue if different than old
  * Check CIDs-blocked Counter and send update to API
2. Start the filter-listener to respond to any filter requests
  * Keep pointer to latest CIDs list
  * Listen to requests on open pipe
  * Respond to filter requests by checking against the CIDs list
  * Update counter of CIDs blocked
3. Start main loop
  * Check the list-updater, restart on error/crash
  * Check the filter-listener, restart on error/crash
  * Check and update log-in session token

'''

class UpdaterDaemon(Daemon):
    def run(self):
        socket_port = os.getenv('BITSCREEN_SOCKET_PORT', '5555')
        host = os.getenv('BITSCREEN_BACKEND_HOST', 'http://localhost:3030')
        key = os.getenv('BITSCREEN_PROVIDER_KEY', None)
        seed_phrase = os.getenv('BITSCREEN_PROVIDER_SEED_PHRASE', None)
        updater = FilterUpdater(host, None, key, seed_phrase)
        updater.start_updater()

        context = zmq.Context()
        socket = context.socket(zmq.REP)
        print(f'listening to tcp socket at port {socket_port}')
        socket.bind(f"tcp://*:{socket_port}")

        while True:
            try:
                #  Wait for next deal filter request
                message = socket.recv()
                deal_request = json.loads(message)
                print(f"Received deal request: {deal_request}")

                # check if content cid from this deal is in the block list
                cid = deal_request.get('cid', None)
                blocked = 1
                deal_type = None
                if cid is None:
                    msg = json.dumps({
                        'error': f'missing `cid` in the message deal request.',
                        'reject': 0,
                        'dealCid': deal_request.get('dealCid', '')
                    })
                else:
                    #  Send reply back with dealCid, cid, and result
                    k = keccak.new(digest_bits=256)
                    k.update(cid.encode())
                    hashedCid = k.hexdigest()

                    blocked = hashedCid in updater.get_cids_to_block()
                    deal_type = deal_request.get('dealType', 1)
                    msg = json.dumps({
                        'reject': int(blocked),
                        'dealCid': deal_request.get('dealCid', ''),
                        'cid': cid
                    })

                socket.send_string(msg)
                if cid is not None:
                    updater.update_cid_blocked(cid, deal_type, int(not blocked))
            except Exception as ex:
                socket.send_string(json.dumps({
                    'error': "Invalid message",
                    'reject': 0
                }))
                pass

            time.sleep(0.01)

def main():
    daemon = UpdaterDaemon('/tmp/daemon-updater.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'status' == sys.argv[1]:
            daemon.status()
        else:
                print("Unknown command")
                sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart|status" % sys.argv[0])
        sys.exit(2)

if __name__ == "__main__":
    main()
