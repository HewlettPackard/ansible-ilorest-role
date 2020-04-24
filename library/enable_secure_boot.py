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
An example of enabling secure boot
"""

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
#Instantiating module class        
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory

def enable_secure_boot(_redfishobj, secure_boot_enable):

    secure_boot_uri = None
    secure_boot_data = None
    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        systems_uri = _redfishobj.root.obj['Systems']['@odata.id']
        systems_response = _redfishobj.get(systems_uri)
        systems_members_uri = next(iter(systems_response.obj['Members']))['@odata.id']
        systems_members_response = _redfishobj.get(systems_members_uri)
        secure_boot_uri = systems_members_response.obj['SecureBoot']['@odata.id']
        secure_boot_data = _redfishobj.get(secure_boot_uri)
    else:
        #Use Resource directory to find the relevant URI
        for instance in resource_instances:
            if '#SecureBoot.' in instance['@odata.type']:
                secure_boot_uri = instance['@odata.id']
                secure_boot_data = _redfishobj.get(secure_boot_uri)

    if secure_boot_data:
        print("\n\nShowing Secure Boot properties before changes:\n\n")
        print(json.dumps(secure_boot_data.dict, indent=4, sort_keys=True))

    if secure_boot_uri:
        body = {'SecureBootEnable': secure_boot_enable}
        resp = _redfishobj.patch(secure_boot_uri, body)
        #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended info
        #error message to see what went wrong
        if resp.status == 400:
            try:
                print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, \
                                                                                sort_keys=True))
            except Exception:
                sys.stderr.write("A response error occurred, unable to access iLO Extended " \
                                 "Message Info...")
        elif resp.status != 200:
            sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
        else:
            print("\nSuccess!\n")
            print(json.dumps(resp.dict, indent=4, sort_keys=True))
            print("\n\nShowing Secure Boot properties after changes:\n\n")
            secure_boot_data = _redfishobj.get(secure_boot_uri)
            print(json.dumps(secure_boot_data.dict, indent=4, sort_keys=True))

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
            boot_enabled = dict(required=True, type='bool'),
            bios_password = dict(required=False, type='str')
        )
    )
    # Set variables based on vars fed from .yml
    boot_enabled = module.params['boot_enabled']
    bios_password = module.params['bios_password']
    # When running on the server locally use the following commented values
    # While this example can be run remotely, it is used locally to locate the
    # iLO IP address
    SYSTEM_URL = "blobstore://."
    LOGIN_ACCOUNT = "None"
    LOGIN_PASSWORD = "None"

    # When running remotely connect using the secured (https://) address,
    # account name, and password to send https requests
    # SYSTEM_URL acceptable examples:
    # "https://10.0.0.100"
    # "https://ilo.hostname"
    
    #Properties:
    #secure boot enable property
    SECURE_BOOT_ENABLE = True
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

    enable_secure_boot(REDFISHOBJ, SECURE_BOOT_ENABLE)
    REDFISHOBJ.logout()
    module.exit_json(changed=True)
  
