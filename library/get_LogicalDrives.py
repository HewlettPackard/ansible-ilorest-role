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
An example of gathering the Logical Drives on an HPE iLO system
"""

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory

def get_SmartArray_LogicalDrives(_redfishobj):

    smartstorage_response = []
    smartarraycontrollers = dict()

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        systems_uri = _redfishobj.root.obj['Systems']['@odata.id']
        systems_response = _redfishobj.get(systems_uri)
        systems_members_uri = next(iter(systems_response.obj['Members']))['@odata.id']
        systems_members_response = _redfishobj.get(systems_members_uri)
        smart_storage_uri = systems_members_response.obj.Oem.Hpe.Links\
                                                                ['SmartStorage']['@odata.id']
        smart_storage_arraycontrollers_uri = _redfishobj.get(smart_storage_uri).obj.Links\
                                                                ['ArrayControllers']['@odata.id']
        smartstorage_response = _redfishobj.get(smart_storage_arraycontrollers_uri).obj['Members']
    else:
        for instance in resource_instances:
            #Use Resource directory to find the relevant URI
            if '#HpeSmartStorageArrayController.' in instance['@odata.type']:
                smartstorage_uri = instance['@odata.id']
                smartstorage_response = _redfishobj.get(smartstorage_uri).obj['Members']
                break

    for controller in smartstorage_response:
        smartarraycontrollers[controller['@odata.id']] = _redfishobj.get(controller['@odata.id']).\
                                                                                                obj
        sys.stdout.write("Logical Drive URIs for Smart Storage Array Controller \'%s\' : \n" \
                                        % smartarraycontrollers[controller['@odata.id']].get('Id'))
        logicaldrives_uri = smartarraycontrollers[controller['@odata.id']].Links\
                                                                    ['LogicalDrives']['@odata.id']
        logicaldrives_resp = _redfishobj.get(logicaldrives_uri)
        smartarraycontrollers[controller['@odata.id']]['LogicalDrives'] = logicaldrives_resp.dict\
                                                                                        ['Members']
        if not logicaldrives_resp.dict['Members']:
            sys.stderr.write("\tLogical drives are not available for this controller.\n")
        for drives in logicaldrives_resp.dict['Members']:
            sys.stdout.write("\t An associated logical drive: %s\n" % drives)
            drive_data = _redfishobj.get(drives).dict
            print(json.dumps(drive_data, indent=4, sort_keys=True))

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

    get_SmartArray_LogicalDrives(REDFISHOBJ)
    REDFISHOBJ.logout()
    module.exit_json(changed=True)
