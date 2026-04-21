"""
    Use this script to get a fresh access token for the local Enphase Gateway.
    Then be sure you're on the same wifi network as the gateway (Wallace) and
    enter 'https://192.168.10.107/home' (or whatever the ip of the gateway is...)
    and paste the new token into the form.
    
    Finally, update the token at 'instance/enphase_config.json' on both the live server and
    the dev site.
    
    It appears, but I'm not sure that the token remains the same until it expires after one year, so
    running this script before it has expired (or is about to expire?) will return the same token.
    
    The current token was fetched on 12/24/25 or there abouts.
    
"""

import json
import requests

with open('instance/enphase_config.json','r') as f:
    creds = json.loads(f.read())
user=creds["user"]
password=creds['password']
envoy_serial=creds['envoy_serial']
data = {'user[email]': user, 'user[password]': password}
print(data)
# response = requests.post('http://enlighten.enphaseenergy.com/login/login.json?', data=data)
# response_data = json.loads(response.text)
# data = {'session_id': response_data['session_id'], 'serial_num': envoy_serial, 'username': user}
# response = requests.post('http://entrez.enphaseenergy.com/tokens', json=data)
# token_raw = response.text
# print(token_raw)
