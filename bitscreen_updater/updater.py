import os

import sys
import json
import traceback

from bitscreen_updater.provider_session import ProviderSession
from bitscreen_updater.task_runner import TaskRunner

SECONDS_BETWEEN_UPDATES = 5
DEFAULT_FILECOIN_FILE = '~/.murmuration/bitscreen'
DEFAULT_IPFS_FILE = "~/.config/ipfs/denylists/bitscreen.deny"

class FilterUpdater:
    def __init__(self, api_host, provider_id, private_key=None, seed_phrase=None):
        self._api_host = api_host
        self._provider_id = provider_id
        self._filecoin_cids_to_block = set()
        self._ipfs_cids_to_block = set()
        self._seconds_between_updates = FilterUpdater.get_seconds_between_updates()
        self.provider = ProviderSession(api_host, private_key, seed_phrase)
        self.task_runner = None

    @staticmethod
    def get_seconds_between_updates():
        try:
            seconds = int(os.getenv('BITSCREEN_UPDATER_SECONDS_PAUSE', SECONDS_BETWEEN_UPDATES))
            return max(seconds, 1)
        except (TypeError, ValueError):
            return SECONDS_BETWEEN_UPDATES

    def get_filecoin_cids_to_block(self):
        return self._filecoin_cids_to_block

    def get_ipfs_cids_to_block(self):
        return self._ipfs_cids_to_block

    def set_filecoin_cids_to_block(self, cids):
        self._filecoin_cids_to_block = cids

    def set_ipfs_cids_to_block(self, cids):
        self._ipfs_cids_to_block = cids

    def start_updater(self):
        if self.task_runner:
            self.task_runner.stop()

        self.task_runner = TaskRunner(self._seconds_between_updates, self.do_one_update)
        self.task_runner.start()

    def fetch_provider_cids(self):
        return self.provider.get_cids_to_block()

    def update_cid_blocked(self, cid, deal_type, status):
        try:
            self.provider.submit_cid_blocked(cid, deal_type, status)
        except Exception as err:
            print(f'Error updating cid blocked: {cid}, {err}')

    def do_one_update(self):
        try:
            cids_to_block = self.fetch_provider_cids()
            filecoin_cids = cids_to_block.get("filecoinCids")
            ipfs_cids = cids_to_block.get("ipfsCids")

            if filecoin_cids != self.get_filecoin_cids_to_block():
                self.set_filecoin_cids_to_block(filecoin_cids)
                self.write_to_file(filecoin_cids, 'filecoin')
                print('got a new set of CIDs for Filecoin (total of %s).' % len(filecoin_cids))

            if ipfs_cids != self.get_ipfs_cids_to_block():
                self.set_ipfs_cids_to_block(ipfs_cids)
                self.write_to_file(ipfs_cids, 'ipfs')
                print('got a new set of CIDs for IPFS (total of %s).' % len(ipfs_cids))

        except Exception as err:
            print('Error fetching cids to block: %s' % err)
            traceback.print_exc()

    def write_to_file(self, cids, network):
        filecoinFilePath = os.getenv('FILECOIN_CIDS_FILE', DEFAULT_FILECOIN_FILE)
        ipfsFilePath = os.getenv('IPFS_CIDS_FILE', DEFAULT_IPFS_FILE)

        if (network == 'filecoin'):
            with open(os.path.expanduser(filecoinFilePath), 'w') as filecoin_cids_file:
                filecoin_cids_file.write(json.dumps(cids))

        if (network == 'ipfs'):
            with open(os.path.expanduser(ipfsFilePath), "wt", encoding="utf-8") as ipfs_cids_file:
                ipfs_cids_file.write('\n'.join(list(map(lambda x: '//' + x, cids))) + '\n')

if __name__ == "__main__":
    updater = FilterUpdater(sys.argv[1], sys.argv[2], sys.argv[3])
    updater.start_updater()
