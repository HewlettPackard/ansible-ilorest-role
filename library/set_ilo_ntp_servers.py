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
An example of setting NTP servers for HPE iLO systems
"""

import sys
import json
import time
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory
from reset_ilo import reset_ilo
from enable_ntp_servers import enable_ntp

def set_ilo_ntp_servers(_redfishobj, ntp_server_list):

    date_time_uri = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        managers_uri = _redfishobj.root.obj['Managers']['@odata.id']
        managers_response = _redfishobj.get(managers_uri)
        managers_members_uri = next(iter(managers_response.obj['Members']))['@odata.id']
        managers_members_response = _redfishobj.get(managers_members_uri)
        date_time_uri = managers_members_response.obj.Oem.Hpe.Links['DateTimeService']['@odata.id']
    else:
        #Use Resource directory to find the relevant URI
        for instance in resource_instances:
            if '#HpeiLODateTime.' in instance['@odata.type']:
                date_time_uri = instance['@odata.id']

    if date_time_uri:
        data = _redfishobj.get(date_time_uri)
        if data.dict.get('StaticNTPServers'):
            resp = _redfishobj.patch(date_time_uri, {'StaticNTPServers': ntp_server_list})
        else:
            raise Exception("\'StaticNTPServers\' property is not available/modifyable.\n")
        #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended info
        #error message to see what went wrong
        if resp.status == 400:
            try:
                print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, \
                                                                                sort_keys=True))
            except Exception as excp:
                sys.stderr.write("A response error occurred, unable to access iLO Extended " \
                                 "Message Info...")
        elif resp.status != 200:
            sys.stderr.write("An http response of \'%s\' was returned.\n" % resp.status)
        else:
            print("Success!\n")
            print(json.dumps(resp.dict, indent=4, sort_keys=True))
            ntp_data = _redfishobj.get(date_time_uri).dict.get('StaticNTPServers')
            print("Printing updated NTP Servers:\n")
            print(json.dumps(ntp_data, indent=4, sort_keys=True))

def give_client():
    try:
        # Create a Redfish client object
        rf_obj = RedfishClient(base_url=SYSTEM_URL, username=LOGIN_ACCOUNT, \
                                                                            password=LOGIN_PASSWORD)
        # Login with the Redfish client
        rf_obj.login()
    except ServerDownOrUnreachableError as excp:
        sys.stderr.write("ERROR: server not reachable or does not support RedFish.\n")
        sys.exit()

    return rf_obj

if __name__ == "__main__":
    module = AnsibleModule(
        argument_spec = dict(            
            name      = dict(required=True),
            enabled   = dict(required=True, type='bool'),
            ntp_server_list = dict(required=True, type='list')
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

    # Static NTP Servers
    NTP_SERVER_LIST = module.params['ntp_server_list']
    # flag to force disable resource directory. Resource directory and associated operations are
    # intended for HPE servers
    DISABLE_RESOURCE_DIR = True

    REDFISHOBJ = give_client()
    #must enable ntp servers for the primary iLO network management interface
    enable_ntp(REDFISHOBJ, True)
    sys.stdout.write("NTP Servers property has been set on the relevant ethernet management "\
                                                                                "interfaces...\n")
    #must reset iLO for ntp servers changes to be applied.
    sys.stdout.write("iLO must be reset to apply the NTP Server properties and reveal the "\
                     " static NTP servers in the DateTime URI.\n")
    reset_ilo(REDFISHOBJ)
    sys.stdout.write("iLO has been reset...sleeping 60 seconds before trying login.\n")
    #logout to release the channel
    REDFISHOBJ.logout()
    #delete the redfish object. By a new token must be issued when iLO is reset
    #(all channels are cleared), and this library does not cache credentials (for security reasons)
    #A new redfish object must be created and asigned the appropriate credentials.
    del REDFISHOBJ
    time.sleep(60)
    REDFISHOBJ = give_client()
    set_ilo_ntp_servers(REDFISHOBJ, NTP_SERVER_LIST)
    REDFISHOBJ.logout()
    module.exit_json(changed=True)
  
