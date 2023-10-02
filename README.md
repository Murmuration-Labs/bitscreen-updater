# list-updater

Python process to keep the list of filters up to date

## Setup

Environment variables

| description                  | env var                        | default                                |
| ---------------------------- | ------------------------------ | -------------------------------------- |
| socket_port                  | BITSCREEN_SOCKET_PORT          | 5555                                   |
| host                         | BITSCREEN_BACKEND_HOST         | http://localhost:3030                  |
| filecoin (lotus) cids file   | FILECOIN_CIDS_FILE             | ~/.murmuration/bitscreen               |
| ipfs (kubo) cids file        | IPFS_CIDS_FILE                 | ~/.config/ipfs/denylist/bitscreen.deny |
| Should lotus block from file | LOTUS_BLOCK_FROM_FILE          | 0                                      |
| key                          | BITSCREEN_PROVIDER_KEY         |
| seed_phrase                  | BITSCREEN_PROVIDER_SEED_PHRASE |

`To load the provider wallet to communicate with the backend either
BITSCREEN_PROVIDER_KEY or BITSCREEN_PROVIDER_SEED_PHRASE must be set.`

`For Lotus: To use the specified file to block unwanted deals you must set the environment variable
LOTUS_BLOCK_FROM_FILE to 1. The default value (0) queries the server directly instead of using the file content.`

## pip install

```bash
pip install bitscreen-updater
```

## Development install

```bash
sudo python setup.py install
```

## Run from source

```bash
# clone this repo
cd bitscreen-updater
export BITSCREEN_PROVIDER_SEED_PHRASE="provider wallet seed phrase"

# Run the Updater
python -m bitscreen_updater run

# Start the daemon
python -m bitscreen_updater start

# Stop the daemon
python -m bitscreen_updater stop

# Restart the daemon
python -m bitscreen_updater restart

# Get the status of the daemon
python -m bitscreen_updater status

```

## Run installed

```bash
bitscreen-updater [run|start|stop|restart|status]
```

## IPFS CONTENT FILTERING GUIDE

This guide applies to anyone who wants to filter the content that can be retrieved from their IPFS nodes. For the initial setup (unrelated to BitScreen) the IPFS node must be initialized through KUBO (`https://docs.ipfs.tech/how-to/command-line-quick-start/`) and the Nopfs plugin must be added (`https://github.com/ipfs-shipyard/nopfs`).

Afterwards, the BitScreen Updater has to be installed: `https://github.com/Murmuration-Labs/bitscreen-updater`

The BitScreen Updater connects to an existing account on BitScreen. One can be created in the BitScreen GUI here: `https://app.bitscreen.co` . The account must be created with a wallet or have a wallet address associated to it. To load the provider wallet to communicate with the backend either `BITSCREEN_PROVIDER_KEY` or `BITSCREEN_PROVIDER_SEED_PHRASE` must be set.

We then run the BitScreen Updater with the command: `bitscreen-updater run` . The Updater will create the `bitscreen.denylist` file used by the Nopfs plugin and will keep it updated by constantly communicating with the server. Restart the IPFS node if it was already running when the BitScreen Updater was first started, as the plugin will not identify the creation of new .denylist files.

In order to block different content ids (CIDs) from being retrieved you must add them in a filter list in BitScreen either through the BitScreen CLI or through the BitScreen GUI. These CIDs will be added to the denylist in a hashed version. As previously mentioned the file is always kept up-to-date for both adding new CIDs or allowing some that were previously blocked.
