# Using the Enphase API

## Get and use an Access Token

1. Run the python script enphase_token_fetch.py (The token is ony valid for 1 year and a new one needs to be created and updated on the local gateway)

2. On the same wifi network as the local gateway, browse to https://{envoy_ip_address}/home

3. Paste the token into the form

4. Update the tokens in 'instance/enphase_config.json' on the live and dev servers.
