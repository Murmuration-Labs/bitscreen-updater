import os

import sys
import json

from bitscreen_updater.provider_session import ProviderSession
from bitscreen_updater.task_runner import TaskRunner

SECONDS_BETWEEN_UPDATES = 5
DEFAULT_CIDS_FILE = '~/.murmuration/bitscreen'

class FilterUpdater:
    def __init__(self, api_host, provider_id, private_key=None, seed_phrase=None):
        self._api_host = api_host
        self._provider_id = provider_id
        self._cids_to_block = set()
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

    def get_cids_to_block(self):
        return self._cids_to_block

    def set_cids_to_block(self, cids):
        self._cids_to_block = cids

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
            if cids_to_block != self.get_cids_to_block():
                self.set_cids_to_block(cids_to_block)
                self.write_to_file(cids_to_block)
                print('got a new set of CIDs (total of %s).' % len(cids_to_block))

        except Exception as err:
            print('Error fetching cids to block: %s' % err)

    def write_to_file(self, cids):
        filePath = os.getenv('BITSCREEN_CIDS_FILE', DEFAULT_CIDS_FILE)
        with open(os.path.expanduser(filePath), 'w') as cids_file:
            cids_file.write(json.dumps(cids))

if __name__ == "__main__":
    updater = FilterUpdater(sys.argv[1], sys.argv[2], sys.argv[3])
    updater.start_updater()
