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
An example of uploading firmware to the iLO Repository for flashing
"""

import os
import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
#Instantiating module class        
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory

def upload_firmware(_redfishobj, firmware_loc, update_repo=True, update_target=False):
    resource_instances = get_resource_directory(_redfishobj)

    if DISABLE_RESOURCE_DIR or not resource_instances:
        #resource directory is not available so we will navigate through paths manually
        update_service_uri = _redfishobj.root.obj['UpdateService']['@odata.id']
    else:
        #obtain all account instances from resource directory
        for instance in resource_instances:
            if '#UpdateService.' in instance['@odata.type']:
                update_service_uri = instance['@odata.id']

    update_service_response = _redfishobj.get(update_service_uri)

    path = update_service_response.obj.HttpPushUri

    body = []
    json_data = {'UpdateRepository': update_repo, 'UpdateTarget': update_target, 'ETag': 'atag', 'Section': 0}
    session_key = _redfishobj.session_key

    filename = os.path.basename(firmware_loc)
    with open(firmware_loc, 'rb') as fle:
        output = fle.read()

    session_tuple = ('sessionKey', session_key)
    parameters_tuple = ('parameters', json.dumps(json_data))
    file_tuple = ('file', (filename, output, 'application/octet-stream'))

    #Build the payload from each multipart-form data tuple
    body.append(session_tuple)
    body.append(parameters_tuple)
    body.append(file_tuple)

    #Create our header dictionary
    header = {'Cookie': 'sessionKey=' + session_key}

    #We pass the whole list payload to post
    resp = _redfishobj.post(path, body, headers=header)

    if resp.status == 400:
        sys.stderr.write("Failed to upload firmware...")
    elif not resp.status in [200, 201]:
        sys.stderr.write("An http response of '%s' was returned.\n" % resp.status)
    else:
        print("Upload complete!\n")

if __name__ == "__main__":
    # When running on the server locally use the following commented values
    #SYSTEM_URL = None
    #LOGIN_ACCOUNT = None
    #LOGIN_PASSWORD = None

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True, type='str'),
            dia_ilo_ip=dict(required=True, type='str'),
            dia_ilo_pass=dict(required=True, type='str'),
            dia_ilo_user=dict(required=True, type='str'),
            flag=dict(required=True, type='bool'),
            state=dict(default='present', choices=['present']),
            url=dict(required=True, type='str')))
    action = module.params['action']
    SYSTEM_URL = "https://" + module.params['dia_ilo_ip']
    LOGIN_ACCOUNT = module.params['dia_ilo_user']
    LOGIN_PASSWORD = module.params['dia_ilo_pass']
    UPDATE_TARGET = module.params['flag']
    FIRMWARE_PATH = module.params['url']
    
    

    # When running remotely connect using the secured (https://) address,
    # account name, and password to send https requests
    # SYSTEM_URL acceptable examples:
    # "https://10.0.0.0"
    # "https://ilo.hostname"
    #SYSTEM_URL = "https://10.0.0.0"
    #LOGIN_ACCOUNT = "admin"
    #LOGIN_PASSWORD = "password"

    # The path to the firmware file to upload
    #FIRMWARE_PATH = "/path/to/firmware.bin"
    # Upload the firmware file to the iLO Repository
    UPDATE_REPO = True
    # Update the system with the firmware file
    #UPDATE_TARGET = False

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

    upload_firmware(REDFISHOBJ, FIRMWARE_PATH, UPDATE_REPO, UPDATE_TARGET)
    REDFISHOBJ.logout()
    module.exit_json(changed=True)
