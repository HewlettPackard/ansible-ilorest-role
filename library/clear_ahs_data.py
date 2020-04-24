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
An example of clearing AHS data for HPE iLO systems
"""

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory

def clear_ahs_data(_redfishobj):

    active_health_system_clear_log_uri = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        managers_uri = _redfishobj.root.obj['Managers']['@odata.id']
        managers_response = _redfishobj.get(managers_uri)
        managers_members_uri = next(iter(managers_response.obj['Members']))['@odata.id']
        managers_members_response = _redfishobj.get(managers_members_uri)
        active_health_system_uri = managers_members_response.obj.Oem.Hpe.Links\
                                    ['ActiveHealthSystem']['@odata.id']
        active_health_system_response = _redfishobj.get(active_health_system_uri)
        active_health_system_clear_log_uri = active_health_system_response.obj['Actions']\
                                            ['#HpeiLOActiveHealthSystem.ClearLog']['target']
    else:
        for instance in resource_instances:
            if '#HpeiLOActiveHealthSystem.' in instance['@odata.type']:
                active_health_system_uri = instance['@odata.id']
                active_health_system_response = _redfishobj.get(active_health_system_uri)
                active_health_system_clear_log_uri = active_health_system_response['Actions']\
                                                    ['#HpeiLOActiveHealthSystem.ClearLog']['target']
            break

    if active_health_system_clear_log_uri:
        body = {"Action": "HpeiLOActiveHealthSystem.ClearLog"}
        resp = _redfishobj.redfish_client.post(active_health_system_clear_log_uri, body)

        #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended info
        #error message to see what went wrong
        if resp.status == 400:
            try:
                print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4,\
                                                                                sort_keys=True))
            except Exception:
                sys.stderr.write("A response error occurred, unable to access iLO Extended " \
                                 "Message Info...")
        elif resp.status != 200:
            sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
        else:
            print("Success!\n")
            print(json.dumps(resp.dict, indent=4, sort_keys=True))

if __name__ == "__main__":
    module = AnsibleModule(
        argument_spec = dict(            
            name      = dict(required=True),
            enabled   = dict(required=True, type='bool')
        )
    )

    # When running remotely connect using the secured (https://) address,
    # account name, and password to send https requests
    # SYSTEM_URL acceptable examples:
    # "https://10.0.0.100"
    # "https://ilo.hostname"
    SYSTEM_URL = "blobstore://."
    LOGIN_ACCOUNT = "None"
    LOGIN_PASSWORD = "None"

    # flag to force disable resource directory. Resource directory and associated operations are
    # intended for HPE servers.
    DISABLE_RESOURCE_DIR = False

    try:
        # Create a Redfish client object
        REDFISHOBJ = RedfishClient(base_url=SYSTEM_URL, username=LOGIN_ACCOUNT, \
                                                                            password=LOGIN_PASSWORD)
        # Login with the Redfish client
        REDFISHOBJ.login()
    except ServerDownOrUnreachableError as excp:
        sys.stderr.write("ERROR: server not reachable or does not support RedFish.\n")
        sys.exit()

    clear_ahs_data(REDFISHOBJ)
    REDFISHOBJ.logout()
    module.exit_json(changed=True)
    
