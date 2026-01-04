
def get_local_production() ->dict:
    """ A function to fetch the production info from the Enphase gateway

    Query the Enphase Gateway found at host and return
    the solor production data.

    Report an error if authentication fails

    Args: None

    Returns:  dict such as:
        {
        "wattHoursToday": 4741,
        "wattHoursSevenDays": 20370543,
        "wattHoursLifetime": 20375284,
        "wattsNow": 510
        }

    Raises: None
    """

    from shotglass2.takeabeltof.mailer import alert_admin
    import json
    import requests
    import urllib3

    urllib3.disable_warnings() # disable the security warning

    production = {}

    try:
        with open('instance/enphase_config.json', "r") as f:
            conf = json.loads(f.read())
            host = conf.get("host")
            token = conf.get("token")

        headers = {
            "Accept":"application/json",
            "Authorization":f"Bearer {token}",
        }
        response = requests.get(host, 
                                headers=headers, 
                                verify=False, # don't try to verify certificate
                                timeout=(4.0,4.0) # Shorten the timeout '(connect limit,read limit)'
                                ) 

        if response.status_code == 200:
            # print(response.text)
            production = json.loads(response.text)

        elif response.status_code == 401:
            alert_admin("Enphase Production Error",
                        """Authentication may have failed, Get a new token?
                        Run the enphase_token_fetch.py script to update.
                        """
                        )
        else:
            alert_admin("Bad Enphase response code:",
                        f"""Receive an unexpected response code
                        while attempting to get the Enphase producton data. 
                        Responce Code: {response.status_code}"""
                        )
            
    except requests.ConnectTimeout:
        # just what it says... took too long
        pass

    except urllib3.exceptions.NewConnectionError:
        # Sometimes the gateway is just very slow to respond, so ignore it...
        pass

    except urllib3.exceptions.MaxRetryError:
        # Sometimes the gateway is just very slow to respond, so ignore it...
        pass

    except Exception as e:
        alert_admin("Enphase Production Exception",
                    f"""
                    An Error was encountered while attempting to get the 
                    production data from the Enphase Gateway.

                    Exception: {str(e)}
                    """
                    )

    return production
