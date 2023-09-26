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
                ipfs_add_list = self.generate_cids_add_list(['//' + s for s in ipfs_cids])
                self.write_to_file(ipfs_add_list, 'ipfs')
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
            with open(os.path.expanduser(ipfsFilePath), "at", encoding="utf-8") as ipfs_cids_file:
                ipfs_cids_file.write('\n'.join(cids) + '\n')

    @staticmethod
    def process_file_cids(input_list):
        processed_dict = {}
        for string in input_list:
            key = string.lstrip('!')  # Remove any leading exclamation marks for the key
            processed_dict[key] = string[0] != '!'  # True if no exclamation mark, False if there is
        return processed_dict

    def generate_cids_add_list(self, db_cids):
        ipfsFilePath = os.getenv('IPFS_CIDS_FILE', DEFAULT_IPFS_FILE)
        with open(os.path.expanduser(ipfsFilePath), 'a+', encoding='utf-8') as file:
            file.seek(0)  # Set the file pointer to the beginning of the file
            if file.readable() and not file.read(1):  # Check if file is readable and empty
                file_cids = []
            else:
                file.seek(0)  # Reset the file pointer to the beginning of the file
                file_cids = [line.strip() for line in file if line.strip()]

        processed_file_cids = self.process_file_cids(file_cids)

        cids_to_add = []

        # Step 1: Process dbCids
        for cid in db_cids:
            if processed_file_cids.get(cid, False) is False:
                cids_to_add.append(cid)
            if cid in processed_file_cids:  # if cid is a key and its associated value is True
                del processed_file_cids[cid]  # Remove the key from the dictionary

        # Step 2: Process remaining keys in processed_file_cids
        for cid, value in processed_file_cids.items():
            if value is True:
                cids_to_add.append('!' + cid)  # Add with an exclamation mark at the beginning

        return cids_to_add
        

if __name__ == "__main__":
    updater = FilterUpdater(sys.argv[1], sys.argv[2], sys.argv[3])
    updater.start_updater()
