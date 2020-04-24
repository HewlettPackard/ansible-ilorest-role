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
An example of generating a certificate signing request for HPE iLO systems
"""
import sys
import json
import time
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError
from ansible.module_utils.basic import *

from get_resource_directory import get_resource_directory

def generate_csr(_redfishobj, csr_file, csr_properties):

    csr_uri = None
    generate_csr_uri = None

    resource_instances = get_resource_directory(_redfishobj)
    if DISABLE_RESOURCE_DIR or not resource_instances:
        #if we do not have a resource directory or want to force it's non use to find the
        #relevant URI
        managers_uri = _redfishobj.root.obj['Managers']['@odata.id']
        managers_response = _redfishobj.get(managers_uri)
        managers_members_uri = next(iter(managers_response.obj['Members']))['@odata.id']
        managers_members_response = _redfishobj.get(managers_members_uri)
        security_service_uri = managers_members_response.obj.Oem.Hpe.Links\
                                                                ['SecurityService']['@odata.id']
        security_service_response = _redfishobj.get(security_service_uri)
        csr_uri = security_service_response.obj.Links['HttpsCert']['@odata.id']
        https_cert_response = _redfishobj.get(csr_uri)
        generate_csr_uri = https_cert_response.obj['Actions']['#HpeHttpsCert.GenerateCSR']\
                                                                                    ['target']
    else:
        #Use Resource directory to find the relevant URI
        for instance in resource_instances:
            if '#HpeHttpsCert.' in instance['@odata.type']:
                csr_uri = instance['@odata.id']
                generate_csr_uri = _redfishobj.get(csr_uri).obj['Actions']\
                                                        ['#HpeHttpsCert.GenerateCSR']['target']
                break

    if generate_csr_uri:
        body = dict()
        body["Action"] = "HpeHttpsCert.GenerateCSR"
        body["City"] = csr_properties["City"]
        body["CommonName"] = csr_properties["CommonName"]
        body["Country"] = csr_properties["Country"]
        body["OrgName"] = csr_properties["OrgName"]
        body["OrgUnit"] = csr_properties["OrgUnit"]
        body["State"] = csr_properties["State"]
        resp = _redfishobj.post(generate_csr_uri, body)
        if resp.status in [200, 201]:
            sys.stdout.write("Generating CSR, this may take a few minutes\n")
            sys.stdout.write("Sleeping for 5 minutes...\n")
            time.sleep(600)
            csr_resp = _redfishobj.get(csr_uri).dict['CertificateSigningRequest']
            with open(csr_file, 'wb') as csroutput:
                csroutput.write(csr_resp)
            sys.stdout.write("CSR Data saved to file: '%s'\n" % csr_file)
        else:
            #If iLO responds with soemthing outside of 200 or 201 then lets check the iLO extended
            #info error message to see what went wrong
            if resp.status not in [200, 201]:
                try:
                    print(json.dumps(resp.obj['error']['@Message.ExtendedInfo'], indent=4, \
                                                                                    sort_keys=True))
                except Exception as excp:
                    sys.stderr.write("A response error occurred, unable to access iLO "\
                                     "Extended Message Info...\n")

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

    #CSR Dictionary, each value should be updated to reflect the desired CSR
    CSR_DICT = {"City" : "City", "CommonName": "Common Name", "Country": "US", \
                "OrgName": "Organization", "OrgUnit": "Unit", "State": "State"}

    #After CSR is generated, a file will be created and the CSR will be downloaded
    CSR_FILE = "csr.txt"
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

    generate_csr(REDFISHOBJ, CSR_FILE, CSR_DICT)
    REDFISHOBJ.logout()
    module.exit_json(changed=True)
