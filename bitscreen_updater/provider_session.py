from collections import namedtuple

import eth_account
import requests
from web3.auto import w3
from eth_account.messages import encode_defunct
from py_crypto_hd_wallet import HdWalletFactory, HdWalletCoins, HdWalletDataTypes, HdWalletKeyTypes

from bitscreen_updater.exceptions import AuthError, BackendError

Wallet = namedtuple('Wallet', ('address', 'key'))


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers['Authorization'] = "Bearer " + self.token
        return r


class ProviderSession:
    def __init__(self, host, private_key=None, seed_phrase=None):
        assert private_key or seed_phrase, 'one of `private_key` or `seed_phrase` must be provided.'
        self.host = host
        self.access_token = None
        self.provider = {} # id, accessToken, businessName,
        self.wallet = self._get_wallet(seed_phrase, private_key)

    def _get_wallet(self, mnemonic=None, private_key=None):
        if mnemonic:
            hd_wallet_fact = HdWalletFactory(HdWalletCoins.ETHEREUM)
            hd_wallet = hd_wallet_fact.CreateFromMnemonic("_my_wallet_", mnemonic)
            hd_wallet.Generate(addr_num=1)
            hd_wallet_key = hd_wallet.GetData(HdWalletDataTypes.ADDRESSES)[0]
            # address = hd_wallet_key.GetKey(HdWalletKeyTypes.ADDRESS)
            private_key = hd_wallet_key.GetKey(HdWalletKeyTypes.RAW_PRIV)
        else:
            assert private_key, 'one of private_key or mnemonic must be provided.'

        address = eth_account.Account().privateKeyToAccount(private_key).address
        print(f'loaded wallet for address {address.lower()}')
        return Wallet(address, private_key)

    def _get_nonce(self):
        response = requests.get(self.host + '/provider/' + self.wallet.address.lower())
        if response.status_code == 200:
            try:
                return response.json()['nonce']
            except:
                pass

        return None

    def sign_message(self, msg):
        message = encode_defunct(text=msg)
        signedMessage = w3.eth.account.sign_message(
            message, private_key=self.wallet.key
        )

        return signedMessage.signature.hex()

    def authenticate(self, signature):
        response = requests.post(
            self.host + '/provider/auth/' + self.wallet.address.lower(),
            json={'signature': signature}
        )
        if response.status_code in {200, 201}:
            self.provider = response.json()
            assert 'id' in self.provider, 'provider object is missing the `id`.'
            if 'accessToken' in self.provider:
                self.access_token = self.provider['accessToken']
            else:
                raise AuthError(f'auth response is missing the `accessToken`: '
                                f'response is {self.provider}')

        else:
            raise AuthError(f'auth endpoint failed with status {response.status_code}, {response.text}')

    def login(self):
        nonce = self._get_nonce()
        if nonce is None:
            raise AuthError("There's no account associated with this wallet.")

        try:
            signed_nonce = self.sign_message(nonce)
        except Exception as e:
            raise AuthError(f"Login failed: invalid private key or signing failed ({e})")

        try:
            self.authenticate(signed_nonce)
        except AuthError as e:
            print(f'authenticate failed: {e}')
            raise

        assert self.access_token, 'authenticate did not raise an exception but `accessToken` is not set.'
        print(f"Authenticated as " + self.provider.get('businessName', self.wallet.address.lower()))

    def get_cids_to_block(self):
        if not self.access_token:
            self.login()

        response = requests.get(
            self.host + '/cid/blocked',
            params={'download': False},
            auth=BearerAuth(self.access_token))

        if response.status_code == 200:
            try:
                cid_list = response.json()
            except Exception as e:
                raise BackendError(
                    f'Error fetching filters cids from host {self.host} using'
                    f'accessToken {self.access_token} and providerId {self.provider["id"]}.'
                    f'Something wrong with the response object response.content={response.content}.'
                    f'original error was {e}')
            # cids = []
            # exception_cids = []
            # for _filter in response_dict['filters']:
            #     _list = exception_cids if _filter['override'] else cids
            #     _list.extend([cid['cid'] for cid in _filter['cids']])
            #
            # exception_cids = set(exception_cids)
            # cids = {cid for cid in cids if cid not in exception_cids}

            return cid_list

        raise BackendError(
            f'Error fetching filters cids from host {self.host} using'
            f'accessToken {self.access_token} and providerId {self.provider["id"]}: '
            f'status {response.status_code}, message {response.text}'
        )

    def submit_cid_blocked(self, cid, deal_type='retrieval', rejected=True):
        if not self.access_token:
            self.login()

        payload = {
            'wallet': self.wallet.address.lower(),
            'cid': cid,
            'dealType': 1 if deal_type == 'retrieval' else 0,
            'status': 0 if rejected else 1,
        }
        response = requests.post(
            self.host + '/deals',
            json=payload,
            auth=BearerAuth(self.access_token))
        if response.status_code in {200, 201}:
            return True

        return False
