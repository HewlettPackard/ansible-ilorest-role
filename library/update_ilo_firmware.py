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
An example of updating firmware via HTTP URL
"""

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
#Instantiating module class        
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory

def update_ilo_firmware(_redfishobj, fw_url, tpm_flag):

    body = dict()
    update_service_uri = None

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
                break

    if update_service_uri and fw_url:
        update_uri = _redfishobj.get(update_service_uri).obj['Actions']\
                                                        ['#UpdateService.SimpleUpdate']['target']
        body["ImageURI"] = fw_url
        if tpm_flag:
            body["TPMOverrideFlag"] = tpm_flag
        resp = _redfishobj.post(update_uri, body)
        if resp.status == 400:
            try:
                print(json.dumps(resp.obj['error']\
                                 ['@Message.ExtendedInfo'], indent=4, sort_keys=True))
            except Exception as excp:
                sys.stderr.write("A response error occurred, unable to access iLO Extended "\
                                 "Message Info...")
        elif resp.status != 200:
            sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
        else:
            print("Success!\n")
            print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, sort_keys=True))

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
            firmware_url = dict(required=True, type='str'),
            tpm_flag = dict(required=True, type='bool')
        )
    )
    # Set variables based on vars fed from .yml
    FIRMWARE_URL = module.params['firmware_url']
    TPM_FLAG = module.params['tpm_flag']
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
    
    # firmware file path and filename
    #FIRMWARE_URL = "http://<url_to_binary_file>"
    # If a TPM module (Trusted Platform Module/ Cryptographic Co-processor) is installed/present
    # onboard then be sure to include this.
    #TPM_FLAG = True
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

    update_ilo_firmware(REDFISHOBJ, FIRMWARE_URL, TPM_FLAG)
    REDFISHOBJ.logout()
    module.exit_json(changed=True)
