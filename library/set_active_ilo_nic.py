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
An example of setting the active Manager NIC
"""

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory

def set_active_ilo_nic(_redfishobj):

    ethernet_data = {}

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        managers_uri = _redfishobj.root.obj['Managers']['@odata.id']
        managers_response = _redfishobj.get(managers_uri)
        managers_members_uri = next(iter(managers_response.obj['Members']))['@odata.id']
        managers_members_response = _redfishobj.get(managers_members_uri)
        manager_ethernet_interfaces = managers_members_response.obj['EthernetInterfaces']\
                                                                                    ['@odata.id']
        manager_ethernet_interfaces_response = _redfishobj.get(manager_ethernet_interfaces)
        manager_ethernet_interfaces_members = manager_ethernet_interfaces_response.\
                                                            obj['Members']
        for _member in manager_ethernet_interfaces_members:
            _tmp = _redfishobj.get(_member['@odata.id']).obj
            ethernet_data[_member['@odata.id']] = _tmp
    else:
        #Use Resource directory to find the relevant URI
        for instance in resource_instances:
            if '#EthernetInterfaceCollection.' in instance['@odata.type'] and 'Managers' in \
                                                                        instance['@odata.id']:
                ethernet_uri = instance['@odata.id']
                ethernet_interfaces = _redfishobj.get(ethernet_uri).obj['Members']
                for _ethernet_interface in ethernet_interfaces:
                    ethernet_data[_ethernet_interface['@odata.id']] = _redfishobj.\
                                                        get(_ethernet_interface['@odata.id']).dict
                break

    if ethernet_data:
        print("\n\nShowing all available ethernet management interfaces before changes:\n\n")
        for interface in ethernet_data:
            sys.stdout.write("Ethernet Management Inteface \'%s\'\n" % ethernet_data\
                                                                            [interface].get('Id'))
            sys.stdout.write("\t\'Interface Enabled\': %s\n" % ethernet_data[interface].\
                                                                        get('InterfaceEnabled'))

    for ethernet in ethernet_data:
        sys.stdout.write("Ethernet Interface: %s\n" % ethernet)
        ans = input("Would you like to enable/disable this interface? (enable/disable)\n")
        if "en" in ans:
            body = {"InterfaceEnabled": True}
        else:
            body = {"InterfaceEnabled": False}
        resp = _redfishobj.patch(ethernet, body)
        if resp.status == 400:
            try:
                print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, \
                                                                                sort_keys=True))
            except Exception as excp:
                sys.stderr.write("A response error occurred, unable to access iLO Extended "\
                                 "Message Info...")
        elif resp.status != 200:
            sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
        else:
            print("Success! You will need to reset iLO for this change to take effect.\n")
            print(json.dumps(resp.dict, indent=4, sort_keys=True))
        break


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
            shared_nic = dict(required=True, type='bool')
        )
    )
    # Set variables based on vars fed from .yml
    shared_nic = module.params['shared_nic']
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
    #SYSTEM_URL = "https://10.0.0.100"
    #LOGIN_ACCOUNT = "admin"
    #LOGIN_PASSWORD = "password"

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

    set_active_ilo_nic(REDFISHOBJ)
    REDFISHOBJ.logout()
    module.exit_json(changed=True)
