#!/usr/bin/env python

import json
import os
import time

import zmq

from bitscreen_updater.updater import FilterUpdater

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


def main():
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
                blocked = cid in updater.get_cids_to_block()
                deal_type = deal_request.get('dealType', 1)
                msg = json.dumps({
                    'reject': int(blocked),
                    'dealCid': deal_request.get('dealCid', ''),
                    'cid': cid
                })

            socket.send(msg)
            if cid is not None:
                updater.update_cid_blocked(cid, deal_type, int(not blocked))
        except Exception:
            pass

        time.sleep(0.01)


if __name__ == "__main__":
    main()
