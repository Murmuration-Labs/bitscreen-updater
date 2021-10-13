# list-updater
Python process to keep the list of filters up to date

## Setup
Environment variables

description       | env var                        | default 
------------- | ------------------------------ | ------- 
socket_port   | BITSCREEN_SOCKET_PORT          | 5555
host          | BITSCREEN_BACKEND_HOST         | http://localhost:3030
cids file     | BITSCREEN_CIDS_FILE            | ~/.murmuration/bitscreen
key           | BITSCREEN_PROVIDER_KEY         | 
seed_phrase   | BITSCREEN_PROVIDER_SEED_PHRASE | 

`To load the provider wallet to communicate with the backend either 
BITSCREEN_PROVIDER_KEY or BITSCREEN_PROVIDER_SEED_PHRASE must be set.`

## Run
```bash
# clone this repo
cd bitscreen-updater
export BITSCREEN_PROVIDER_SEED_PHRASE="provider wallet seed phrase"
python ./bitscreen_updater/main.py



```