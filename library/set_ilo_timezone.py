 # Copyright 2019 Hewlett Packard Enterprise Development LP
 #
 # Licensed under the Apache License, Version 2.0 (the "License"); you may
 # not use this file except in compliance with the License. You may obtain
 # a copy of the License at
 #
 #      http://www.apache.org/licenses/LICENSE-2.0
 #
 # Unless required by applicable law or agreed to in writing, software
 # distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 # WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 # License for the specific language governing permissions and limitations
 # under the License.

# -*- coding: utf-8 -*-
"""
An example of setting the timezone for HPE iLO systems
"""
DOCUMENTATION = '''
---
module: set_ilo_timezone
short_description: This module obtains the iLO timezone
'''

EXAMPLES = '''
- name: set iLO timezone
  become: yes
  set_ilo_timezone:
    name: "Set iLO timezone"
    enabled: True
    olson_timezone: "America/Chicago"
'''

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory

def set_timezone(_redfishobj, timezone):

    date_time_uri = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        managers_uri = _redfishobj.root.obj['Managers']['@odata.id']
        managers_response = _redfishobj.get(managers_uri)
        managers_members_uri = next(iter(managers_response.obj['Members']))['@odata.id']
        managers_members_response = _redfishobj.get(managers_members_uri)
        date_time_uri = managers_members_response.obj.Oem.Hpe.Links['DateTimeService']['@odata.id']
    else:
        #Use Resource directory to find the relevant URI
        for instance in resource_instances:
            if '#HpeiLODateTime.' in instance['@odata.type']:
                date_time_uri = instance['@odata.id']

    if date_time_uri:
        data = _redfishobj.get(date_time_uri)
        if data.dict.get('TimeZone'):
            _data = {'TimeZone': {"Name": timezone}}
            resp = _redfishobj.patch(date_time_uri, _data)
        else:
            raise Exception("\'TimeZone\' property is not available/modifyable.\n")
        #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended info
        #error message to see what went wrong
        if resp.status == 400:
            try:
                print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, \
                                                                                sort_keys=True))
                print(json.dumps(data.obj.get('TimeZoneList'), indent=4, sort_keys=True))
                sys.stderr.write("Check the TimeZone value...\n")
            except Exception as excp:
                sys.stderr.write("A response error occurred, unable to access iLO Extended " \
                                 "Message Info...")
        elif resp.status != 200:
            sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
        else:
            print("Success!\n")
            print(json.dumps(resp.dict, indent=4, sort_keys=True))
            ntp_data = _redfishobj.get(date_time_uri).dict.get('TimeZone')
            print("Printing updated NTP Servers:\n")
            print(json.dumps(ntp_data, indent=4, sort_keys=True))

if __name__ == "__main__":
    # When running on the server locally use the following commented values
    #SYSTEM_URL = None
    #LOGIN_ACCOUNT = None
    #LOGIN_PASSWORD = None

    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='present', choices=['present', 'absent']),
            name      = dict(required=True),
            enabled   = dict(required=True, type='bool'),
            timezone = dict(required=True, type='str')
        )
    )
    # Set variables based on vars fed from .yml
    TIMEZONE = module.params['timezone']
    # When running remotely connect using the secured (https://) address,
    # account name, and password to send https requests
    # SYSTEM_URL acceptable examples:
    # "https://10.0.0.100"
    # "https://ilo.hostname"
    SYSTEM_URL = "blobstore://."
    LOGIN_ACCOUNT = "None"
    LOGIN_PASSWORD = "None"
    
    #timezone property (review the list of timezones ('TimeZoneList') within the DateTime URI.
    #TIMEZONE = "US/Central"
    # flag to force disable resource directory. Resource directory and associated operations are
    # intended for HPE servers.
    DISABLE_RESOURCE_DIR = True

    try:
        # Create a Redfish client object
        REDFISHOBJ = RedfishClient(base_url=SYSTEM_URL, username=LOGIN_ACCOUNT, \
                                                                            password=LOGIN_PASSWORD)
        # Login with the Redfish client
        REDFISHOBJ.login()
    except ServerDownOrUnreachableError as excp:
        sys.stderr.write("ERROR: server not reachable or does not support RedFish.\n")
        sys.exit()

    set_timezone(REDFISHOBJ, TIMEZONE)
    REDFISHOBJ.logout()
    module.exit_json(changed=True)
