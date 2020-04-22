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
An example of changing the boot order for HPE iLO systems
"""
DOCUMENTATION = '''
---
module: ex06_bios_revert_default
short_description: This module reverts the bios to default settings
'''

EXAMPLES = '''
- name: Change Boot Order
  become: yes
  change_boot_order:
    name: "Change Boot Order"
    enabled: True
    bios_password: None
'''
import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory

def change_boot_order(_redfishobj, bios_password):

    bios_boot_uri = None
    bios_boot_response = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        systems_uri = _redfishobj.root.obj['Systems']['@odata.id']
        systems_response = _redfishobj.get(systems_uri)
        systems_members_uri = next(iter(systems_response.obj['Members']))['@odata.id']
        systems_members_response = _redfishobj.get(systems_members_uri)
        bios_uri = systems_members_response.obj['Bios']['@odata.id']
        bios_response = _redfishobj.get(bios_uri)
        bios_boot_uri = bios_response.obj.Oem.Hpe.Links.Boot['@odata.id']
    else:
        #Use Resource directory to find the relevant URI
        for instance in resource_instances:
            if '#HpeServerBootSettings.' in instance['@odata.type']:
                bios_boot_uri = instance['@odata.id']
                break

    if bios_boot_uri:
        bios_boot_response = _redfishobj.get(bios_boot_uri)
        #Bios boot settings URI is needed
        bios_boot_settings_uri = bios_boot_response.obj['@Redfish.Settings']['SettingsObject']\
                                                                                    ['@odata.id']
        #update bios password
        if bios_password:
            _redfishobj.bios_password = bios_password
        sys.stdout.write("Rotating the first boot device to the end of the boot order.\n")
        sys.stdout.write('Current Order:\n')
        boot_order = bios_boot_response.obj['DefaultBootOrder']
        for indx, boot_device in enumerate(boot_order):
            sys.stdout.write('Pos ' + str(indx) + ' : ' + boot_device + '\n')
        device = boot_order.pop(0)
        sys.stdout.write("Rotating device: \'%s\' to the end of the boot order.\n" % device)
        boot_order.append(device)

        body = {'DefaultBootOrder': boot_order}
        resp = _redfishobj.patch(bios_boot_settings_uri, body)

        #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended info
        #error message to see what went wrong
        if resp.status == 400:
            try:
                print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, \
                                                                                sort_keys=True))
            except Exception as excp:
                sys.stderr.write("A response error occurred, unable to access iLO Extended Message"\
                                 " Info...")
        elif resp.status != 200:
            sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
        else:
            print("Success! Your system may need to be restarted.\n")
            print(json.dumps(resp.dict, indent=4, sort_keys=True))
    else:
        sys.stderr.write("Unable to find Boot Order URI.\n")

if __name__ == "__main__":
    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='present', choices=['present', 'absent']),
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
    LOGIN_ACCOUNT = None
    LOGIN_PASSWORD = None

    BIOS_PASSWORD = module.params['bios_password']
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

    change_boot_order(REDFISHOBJ, BIOS_PASSWORD)
    REDFISHOBJ.logout()
  
