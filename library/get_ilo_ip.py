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
An example of getting the Manager IP
"""

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
#Instantiating module class        
from ansible.module_utils.basic import *

#from get_resource_directory import get_resource_directory

def get_resource_directory(redfishobj):

    try:
        resource_uri = redfishobj.root.obj.Oem.Hpe.Links.ResourceDirectory['@odata.id']
    except KeyError:
        sys.stderr.write("Resource directory is only available on HPE servers.\n")
        return None

    response = redfishobj.get(resource_uri)
    resources = []

    if response.status == 200:
        sys.stdout.write("\tFound resource directory at /redfish/v1/resourcedirectory" + "\n\n")
        resources = response.dict["Instances"]
    else:
        sys.stderr.write("\tResource directory missing at /redfish/v1/resourcedirectory" + "\n")

    return resources


def get_ilo_ip(_redfishobj, DISABLE_RESOURCE_DIR):
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
        for instance in resource_instances:
            #Use Resource directory to find the relevant URI
            if '#EthernetInterfaceCollection.' in instance['@odata.type'] and 'Managers' in \
                                                                        instance['@odata.id']:
                ethernet_uri = instance['@odata.id']
                ethernet_interfaces = _redfishobj.get(ethernet_uri).obj['Members']
                for _ethernet_interface in ethernet_interfaces:
                    ethernet_data[_ethernet_interface['@odata.id']] = _redfishobj.\
                                                        get(_ethernet_interface['@odata.id']).dict
                break

    if ethernet_data:
        for ethernet_interface in ethernet_data:
            sys.stdout.write("\n\nShowing iLO IPv4 Address Info on: %s\n\n" % ethernet_interface)
            #print(json.dumps(ethernet_data[ethernet_interface]['IPv4Addresses'],\
            #                                                            indent=4, sort_keys=True))
    return ethernet_data

if __name__ == "__main__":
    # When running on the server locally use the following commented values
    #SYSTEM_URL = None
    #LOGIN_ACCOUNT = None
    #LOGIN_PASSWORD = None

    module = AnsibleModule(
        argument_spec = dict(
            name      = dict(required=True),
            enabled   = dict(required=True, type='bool'),
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

    ilo_ip = get_ilo_ip(REDFISHOBJ, DISABLE_RESOURCE_DIR)
    REDFISHOBJ.logout()
    module.exit_json(changed=True, msg=ilo_ip)
