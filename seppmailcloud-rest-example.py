#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Example for how to use the REST API for the SEPPmail Cloud Portal.

(c) 2023, SEPPmail AG.

Please note that this example is not intended for production purposes and you need to
adapt/integrate it into a proper framework. At present, there is no dedicated support
for REST API calls to the SEPPmail Cloud Portal.

You MUST create a dedicated api_user and api_secret (using the Userlist > Internal User
in seppmail.cloud portal, roles "Sales" or "ALL" for this example). SEPPmail is 
monitoring the use of REST APIs and may rate limit or disable the access of user 
accounts making too many requests, or making requests which initiate operations which 
are too complex or otherwise interfere with the platform in undesirable ways.

The code below has been developed with Python 3.11. 

This example has two main parts:

1. class SEPPmailCloud has a login and a generic api request function. With the
login, a token is stored internally which is then used for the generic requests
with a "Authorization" header.

2. Call of the api_request function to get "salesorder" data (ie, the invoices)
of the previous month (hardcoded as '2023-1-1'). Alternatively, you may use the
path "salesorders/csv" to get the data in CSV rather than JSON format.

"""

api_url = 'https://login.seppmail.cloud/api/v1/'
api_user = 'REPLACE ME WITH user@domain.com'
api_secret = 'REPLACE ME WITH the complex password for_api_user'


# Ideally, you replace this with your unique string, for debugging purposes
user_agent = 'seppmailcloud-rest-example/1.0'

import json
import requests
import time

class SEPPmailCloud:

    def __init__(self):
        self.token = None

    def api_request(self, url, params=None, retry=3, type='GET') -> str:
        """Perform GET/POST request against SEPPmail Cloud Portal"""

        if self.token == None:
            print('Need to login first')
            return None
        
        headers = {
            'user-agent': user_agent,
            'accept': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

        real_url = api_url + url

        if type == 'GET':
            params = None
            r = requests.get(real_url, headers=headers, verify=True)
        elif type == 'POST':
            r = requests.post(real_url, headers=headers, data=params, verify=True)
        else:
            print('Only GET/POST supported in this example.')
            return None

        data = None

        # Success, return data
        if r.status_code == 200:
            try:
                data = r.content
            except Exception as e:
                print(f'Exception fetching data: {e} {e.__class__.__name__}\nContent of response: {r.content}')

        # No retry for 4xx return code, return None
        elif r.status_code >= 400 and r.status_code < 500:
            print(f'Status code {r.status_code}\nContent of response: {r.content}')
            return None

        # Likely a timeout or some other retry-worthy condition
        # May return None, or get back into one of the status codes
        # above.
        else:
            if retry > 0:
                print(f'Got error {r.text}\nRetrying, attempt {str(retry)}')
                time.sleep(0.1 * (4 - retry))
                data = self.api_request(url, params, retry=retry - 1, type=type)
            else:
                raise Exception(f'Got HTTP status code {r.status_code} from {url}')
        return data

    def login(self) -> bool:
        """Logs in to SEPPmail Cloud Portal stores the token internally for further accesses"""

        self.token = None
        headers = {
            'user-agent': user_agent,
            'accept': 'application/json',
        }
        data = {
            'username': api_user,
            'password': api_secret
        }
        r = requests.post(api_url + 'login/access-token?return_permissions=true', headers=headers, data=data, verify=True)
        if r.status_code == 200:
            try:
                data = r.json()
                if 'access_token' in data:
                    self.token = data['access_token']
                    return True
                else:
                    print('No access_token returned')
                    return False
            except Exception as e:
                print(f'Exception fetching data: {e} {e.__class__.__name__}\nContent of response: {r.content}')
        else:
            print(f'Login failed, status code {r.status_code}\nContent of response: {r.content}')
            
        return False

######################################################################################################3
#
# Create instance and log in. You MUST supply your own credentials in api_user
# and api_secret above.


sc = SEPPmailCloud()
if sc.login():

    # The "version" endpoint may be useful for debugging purpses
    #print(sc.api_request('version', params=None, retry=1, type='GET'))

    # Get the invoice of a partiuclar month, for all tenants
    output = sc.api_request('salesorders?time_start=2023-1-1', params=None, retry=1, type='GET')

    # Format as JSON; in this example, we just dump it to STDOUT
    j = json.loads(output)
    print(j)
else:
    print('Login failed')


# EOF