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
An example of getting the resource directory for HPE iLO systems
"""

import sys
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError

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

if __name__ == "__main__":
    # When running on the server locally use the following commented values
    #SYSTEM_URL = None
    #LOGIN_ACCOUNT = None
    #LOGIN_PASSWORD = None

    # When running remotely connect using the secured (https://) address,
    # account name, and password to send https requests
    # SYSTEM_URL acceptable examples:
    # "https://10.0.0.100"
    # "https://ilo.hostname"
    SYSTEM_URL = "https://10.0.0.100"
    LOGIN_ACCOUNT = "admin"
    LOGIN_PASSWORD = "password"

    # Create a REDFISH object
    try:
        REDFISH_OBJ = RedfishClient(base_url=SYSTEM_URL, username=LOGIN_ACCOUNT, \
                          password=LOGIN_PASSWORD)
        REDFISH_OBJ.login()
    except ServerDownOrUnreachableError:
        sys.stderr.write("ERROR: server not reachable or doesn't support Redfish.\n")
        sys.exit()

    resources = get_resource_directory(REDFISH_OBJ)

    for resource in resources:
        try:
            sys.stdout.write("\t" + str(resource["@odata.type"]) + \
                             "\n\t\t" + str(resource["@odata.id"]) + "\n")
        except KeyError:
            pass

    REDFISH_OBJ.logout()
