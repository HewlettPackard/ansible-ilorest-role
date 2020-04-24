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
An example of configuring SNMP for HPE iLO systems
"""
DOCUMENTATION = '''
---
module: configure_snmp
short_description: This module configures snmp settings
'''

EXAMPLES = '''
- name: Add iLO user account
  become: yes
  configure_snmp:
    name: "Configure SNMP"
    enabled: True
    snmp_mode: 'Agentless'
    snmp_alert: False
'''

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError

from get_resource_directory import get_resource_directory

def configure_snmp(_redfishobj, read_communities, snmp_alerts):

    snmp_service_uri = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        managers_uri = _redfishobj.root.obj['Managers']['@odata.id']
        managers_response = _redfishobj.get(managers_uri)
        managers_members_uri = next(iter(managers_response.obj['Members']))['@odata.id']
        managers_members_response = _redfishobj.get(managers_members_uri)
        snmp_service_uri = managers_members_response.obj.Oem.Hpe.Links['Snmp']['@odata.id']
    else:
        for instance in resource_instances:
            #Use Resource directory to find the relevant URI
            if '#HpeiLOSnmpService.' in instance['@odata.type']:
                snmp_service_uri = instance['@odata.id']

    if snmp_service_uri:
        body = {"AlertsEnabled": snmp_alerts, "ReadCommunities": read_communities}
        resp = _redfishobj.patch(snmp_service_uri, body)

        #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended info
        #error message to see what went wrong
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
            print("Success!\n")
            print(json.dumps(resp.dict, indent=4, sort_keys=True))

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
            snmp_mode = dict(required=True, type='str'),
            snmp_alerts = dict(required=True, type='bool')
        )
    )
    # Set variables based on vars fed from .yml
    snmp_mode = module.params['snmp_mode']
    ALERTS_ENABLED = module.params['snmp_alerts']

    # When running remotely connect using the secured (https://) address,
    # account name, and password to send https requests
    # SYSTEM_URL acceptable examples:
    # "https://10.0.0.100"
    # "https://ilo.hostname"
    SYSTEM_URL = "blobstore://."
    LOGIN_ACCOUNT = "None"
    LOGIN_PASSWORD = "None"

    #Properties:
    #read communities array
    READ_COMMUNITIES = ["public", "", ""]
    #alerts_enabled primitive (boolean)
    #ALERTS_ENABLED = True
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

    configure_snmp(REDFISHOBJ, READ_COMMUNITIES, ALERTS_ENABLED, DISABLE_RESOURCE_DIR)
    REDFISHOBJ.logout()
