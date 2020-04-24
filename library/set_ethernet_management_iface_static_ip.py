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
An example of setting the Manager ethernet interface static IP
"""

import sys
import json
from redfish import RedfishClient
from redfish.rest.v1 import ServerDownOrUnreachableError

from get_resource_directory import get_resource_directory

def set_ilo_static_ipv4(_redfishobj, ipv4_dict, dns_dict):

    ethernet_data = {}
    body = dict()

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

            sys.stdout.write("\'DHCPv4\':\n")
            if ethernet_data[interface].get('DHCPv4'):
                print(json.dumps(ethernet_data[interface].get('DHCPv4'), indent=4, sort_keys=True))
            else:
                print(json.dumps(ethernet_data[interface]['Oem']['Hpe'].get('DHCPv4'), indent=4, \
                                                                                sort_keys=True))
            sys.stdout.write("\'IPv4\':\n")
            if ethernet_data[interface].get('IPv4StaticAddresses'):
                print(json.dumps(ethernet_data[interface].get('IPv4Addresses'), indent=4, \
                                                                                sort_keys=True))
            sys.stdout.write("\'StaticNameServers\':\n")
            if ethernet_data[interface].get('StaticNameServers'):
                print(json.dumps(ethernet_data[interface].get('StaticNameServers'), indent=4, \
                                                                                sort_keys=True))

    for ethernet in ethernet_data:
        sys.stdout.write("Ethernet Interface: %s\n" % ethernet)
        ans = input("Would you like to modify this interface? (y/n)\n")
        if "n" in ans:
            continue
        if 'DHCPv4' in ethernet_data[ethernet]:
            if ethernet_data[ethernet]['DHCPv4'].get('UseDNSServers'):
                resp = _redfishobj.patch(ethernet, {"DHCPv4": {"UseDNSServers": False}})
                ilo_response(_redfishobj, resp)
            if ethernet_data[ethernet]['DHCPv4'].get('UseGateway'):
                resp = _redfishobj.pathc(ethernet, {"DHCPv4": {"UseGateway": False}})
                ilo_response(_redfishobj, resp)
        if 'IPv4StaticAddresses' in ethernet_data[ethernet]:
            body.update({"IPv4Addresses": [ipv4_dict]})
        if 'StaticNameServers' in ethernet_data[ethernet]:
            body.update({"StaticNameServers" : [dns_dict.get('PrimaryDNS'), \
                                                                    dns_dict.get('SecondaryDNS')]})
        else:
            body.update({"Oem": {"Hpe": {"IPv4": {"DNSServers": [dns_dict.get('PrimaryDNS'), \
                                                                 dns_dict.get('SecondaryDNS')]}}}})
        resp = _redfishobj.patch(ethernet, body)
        ilo_response(_redfishobj, resp)
        break

def ilo_response(_redfishobj, resp):
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
        print("Success! Suggest to reset iLO for settings to take effect.\n")
        print(json.dumps(resp.dict, indent=4, sort_keys=True))

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

    #IPv4 settings for Address, Gateway and SubnetMask as well as DNS.
    IPV4_DICT = {'Address':'16.83.61.123', \
                 'Gateway':'16.83.60.1', \
                 'SubnetMask':'255.255.252.0' \
                 }
    DNS_DICT = {'PrimaryDNS':'16.110.135.52', \
                'SecondaryDNS':'16.110.135.51' \
                }

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

    set_ilo_static_ipv4(REDFISHOBJ, IPV4_DICT, DNS_DICT)
    REDFISHOBJ.logout()
