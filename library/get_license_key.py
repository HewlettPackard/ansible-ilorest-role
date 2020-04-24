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
An example of getting an iLO license key for HPE iLO systems
"""

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory

def get_license_key(_redfishobj):
    license_uri = None
    license_data = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        managers_uri = _redfishobj.root.obj['Managers']['@odata.id']
        managers_response = _redfishobj.get(managers_uri)
        managers_members_uri = next(iter(managers_response.obj['Members']))['@odata.id']
        managers_members_response = _redfishobj.get(managers_members_uri)
        hp_hpe = next(iter(managers_members_response.obj.Oem))
        license_collection_uri = managers_members_response.obj.Oem[hp_hpe].Links['LicenseService']\
                                                                                    ['@odata.id']
        license_collection_response = _redfishobj.get(license_collection_uri)
        license_collection_members_uri = next(iter(license_collection_response.obj\
                                                                        ['Members']))['@odata.id']
        license_data = _redfishobj.get(license_collection_members_uri).dict
        license_uri = _redfishobj.get(license_collection_members_uri).dict['@odata.id']
    else:
        for instance in resource_instances:
            #Use Resource directory to find the relevant URI
            if '#HpeiLOLicense.' in instance['@odata.type']:
                license_uri = instance['@odata.id']
                license_data = _redfishobj.get(license_uri).dict
                break

    if license_data:
        try:
            sys.stdout.write("\n\'License Info\': \'%s\'\n" % \
            json.dumps(license_data['ConfirmationRequest']['EON'], indent=4, sort_keys=True))
        except KeyError:
            sys.stdout.write("\n\'License Info\': \'%s\'\n" % \
            json.dumps(license_data['LicenseKey'], indent=4, sort_keys=True))

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

    get_license_key(REDFISHOBJ)
    REDFISHOBJ.logout()
    module.exit_json(changed=True)
