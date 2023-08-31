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
LOTUS_BLOCK_FROM_FILE to 1.`

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
