"""
Request the basic production data from local the Enphase Gateway.
"""

import json
import requests
import urllib3

urllib3.disable_warnings() # disable the security warning

with open('instance/enphase_config.json', "r") as f:
    conf = json.loads(f.read())
    host = conf.get("host")
    token = conf.get("token")

headers = {
    "Accept":"application/json",
    "Authorization":f"Bearer {token}",
}
response = requests.get(host, headers=headers, verify=False ) # don't try to verify certificate

if response.status_code == 200:
    # print(response.text)
    response_data = json.loads(response.text)
    print("Production:",round(response_data['wattHoursToday']/1000,1),"kWh")
elif response.status_code == 401:
    print("Authentication may have failed, Get a new token?")
    print("run the enphase_token_fetch.py script")
else:
    print("Bad response code:",response.status_code)
