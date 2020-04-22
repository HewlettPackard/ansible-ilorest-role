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
An example of viewing the firmware inventory on HPE iLO systems
"""

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory

def get_inventory_uri(_redfishobj, select):

    update_service_uri = None
    inventory_uri = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        update_service_uri = _redfishobj.root.obj['UpdateService']['@odata.id']
    else:
        #Use Resource directory to find the relevant URI
        for instance in resource_instances:
            if '#UpdateService.' in instance['@odata.type']:
                update_service_uri = instance['@odata.id']

    if update_service_uri:
        update_service_resp = _redfishobj.get(update_service_uri)
        if "software" in select.lower():
            inventory_uri = update_service_resp.obj['SoftwareInventory']['@odata.id']
        elif "firmware" in select.lower():
            inventory_uri = update_service_resp.obj['FirmwareInventory']['@odata.id']
        else:
            raise Exception("Invalid selection provided: Please select 'software' or 'firmware' " \
                            "to obtain the relevant invetory data.")
        sys.stdout.write("Printing data in invetory: %s\n" % inventory_uri)
        get_inventory(_redfishobj, inventory_uri)

def get_inventory(_redfishobj, inventory_uri):

    _members = _redfishobj.get(inventory_uri).obj['Members']
    if not _members:
        sys.stderr.write("\tInventory empty.\n")
    else:
        for inventory_item in _members:
            _resp = _redfishobj.get(inventory_item['@odata.id'])
            sys.stdout.write("Printing contents of inventory item, \'%s\':\'%s\'\n" % \
                                            (_resp.dict.get('Name'), _resp.dict.get('Description')))
            print(json.dumps(_resp.dict, indent=4, sort_keys=True))

if __name__ == "__main__":
    module = AnsibleModule(
        argument_spec = dict(            
            name      = dict(required=True),
            enabled   = dict(required=True, type='bool'),
            select_type = dict(required=True, type='str')
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
    SELECT = module.params['select_type']

    # flag to force disable resource directory. Resource directory and associated operations are
    # intended for HPE servers.
    #SELECT = "firmware" #provide either 'software' or 'firmware' for inventory selection
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

    get_inventory_uri(REDFISHOBJ, SELECT)
    REDFISHOBJ.logout()
