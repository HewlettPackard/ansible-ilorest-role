#!/usr/bin/python

# Copyright 2016 Hewlett Packard Enterprise Development, LP.
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
 
 
DOCUMENTATION = '''
---
module: ex11_modify_ilo_user_account
short_description: This module modifies ilo user accounts along with their permissions
'''

EXAMPLES = '''
- name: Modify iLO user account
  become: yes
  ex11_modify_ilo_user_account:
    name: "Add ilo user account"
    enabled: True
    login_name_to_modify: 'oldname'
    new_loginname: 'name'
    new_username: 'user'
    new_password: 'password'
'''

import sys
from redfish.rest.v1 import ServerDownOrUnreachableError

#import sys
import logging
import json
from redfish import AuthMethod, ilorest_logger, redfish_client

#Config logger used by HPE Restful library
LOGGERFILE = "RedfishApiExamples.log"
LOGGERFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOGGER = ilorest_logger(LOGGERFILE, LOGGERFORMAT, logging.INFO)
LOGGER.info("HPE Redfish API examples")

class RedfishObject(object):
    def __init__(self, host, login_account, login_password):
        try:
            self.redfish_client = redfish_client(base_url=host, \
                      username=login_account, password=login_password, \
                      default_prefix="/redfish/v1")
        except:
            raise
        self.redfish_client.login(auth=AuthMethod.SESSION)
        self.SYSTEMS_RESOURCES = self.ex1_get_resource_directory()
        self.MESSAGE_REGISTRIES = self.ex2_get_base_registry()

    def __del__(self):
        try:
            self.redfish_client.logout()
        except AttributeError, excp:
            pass

    def search_for_type(self, type):
        instances = []

        for item in self.SYSTEMS_RESOURCES["resources"]:
            foundsettings = False

            if "@odata.type" in item and type.lower() in \
                                                    item["@odata.type"].lower():
                for entry in self.SYSTEMS_RESOURCES["resources"]:
                    if (item["@odata.id"] + "/settings/").lower() == \
                                                (entry["@odata.id"]).lower():
                        foundsettings = True

                if not foundsettings:
                    instances.append(item)

        if not instances:
            sys.stderr.write("\t'%s' resource or feature is not " \
                                            "supported on this system\n" % type)
        return instances

    def error_handler(self, response):
        if not self.MESSAGE_REGISTRIES:
            sys.stderr.write("ERROR: No message registries found.")

        try:
            message = json.loads(response.text)
            newmessage = message["error"]["@Message.ExtendedInfo"][0]\
                                                        ["MessageId"].split(".")
        except:
            sys.stdout.write("\tNo extended error information returned by " \
                                                                    "iLO.\n")
            return

        for err_mesg in self.MESSAGE_REGISTRIES:
            if err_mesg != newmessage[0]:
                continue
            else:
                for err_entry in self.MESSAGE_REGISTRIES[err_mesg]:
                    if err_entry == newmessage[3]:
                        sys.stdout.write("\tiLO return code %s: %s\n" % (\
                                 message["error"]["@Message.ExtendedInfo"][0]\
                                 ["MessageId"], self.MESSAGE_REGISTRIES\
                                 [err_mesg][err_entry]["Description"]))

    def redfish_get(self, suburi):
        """REDFISH GET"""
        return self.redfish_client.get(path=suburi)

    def redfish_patch(self, suburi, request_body, optionalpassword=None):
        """REDFISH PATCH"""
        sys.stdout.write("PATCH " + str(request_body) + " to " + suburi + "\n")
        response = self.redfish_client.patch(path=suburi, body=request_body, \
                                            optionalpassword=optionalpassword)
        sys.stdout.write("PATCH response = " + str(response.status) + "\n")

        return response

    def redfish_put(self, suburi, request_body, optionalpassword=None):
        """REDFISH PUT"""
        sys.stdout.write("PUT " + str(request_body) + " to " + suburi + "\n")
        response = self.redfish_client.put(path=suburi, body=request_body, \
                                            optionalpassword=optionalpassword)
        sys.stdout.write("PUT response = " + str(response.status) + "\n")

        return response


    def redfish_post(self, suburi, request_body):
        """REDFISH POST"""
        sys.stdout.write("POST " + str(request_body) + " to " + suburi + "\n")
        response = self.redfish_client.post(path=suburi, body=request_body)
        sys.stdout.write("POST response = " + str(response.status) + "\n")

        return response


    def redfish_delete(self, suburi):
        """REDFISH DELETE"""
        sys.stdout.write("DELETE " + suburi + "\n")
        response = self.redfish_client.delete(path=suburi)
        sys.stdout.write("DELETE response = " + str(response.status) + "\n")

        return response


    def ex1_get_resource_directory(self):
        response = self.redfish_get("/redfish/v1/resourcedirectory/")
        resources = {}
    
        if response.status == 200:
            resources["resources"] = response.dict["Instances"]
            return resources
        else:
            sys.stderr.write("\tResource directory missing at " \
                                        "/redfish/v1/resourcedirectory" + "\n")
    
    def ex2_get_base_registry(self):
        response = self.redfish_get("/redfish/v1/Registries/")
        messages = {}
        location = None
        
        for entry in response.dict["Members"]:
            if not [x for x in ["/Base/", "/iLO/"] if x in entry["@odata.id"]]:
                continue
            else:
                registry = self.redfish_get(entry["@odata.id"])
            
            for location in registry.dict["Location"]:  
                if "extref" in location["Uri"]:
                    location = location["Uri"]["extref"]
                else:
                    location = location["Uri"]
                reg_resp = self.redfish_get(location)
    
                if reg_resp.status == 200:
                    messages[reg_resp.dict["RegistryPrefix"]] = \
                                                    reg_resp.dict["Messages"]
                else:
                    sys.stdout.write("\t" + reg_resp.dict["RegistryPrefix"] + \
                                            " not found at " + location + "\n")
    
        return messages

#Main function
def modify_ilo_user_account(redfishobj, ilo_login_name_to_modify, \
                new_ilo_loginname, new_ilo_username, new_ilo_password, \
                irc=None, cfg=None, virtual_media=None, usercfg=None, vpr=None):
    instances = redfishobj.search_for_type("AccountService.")

    for instance in instances:
        rsp = redfishobj.redfish_get(instance["@odata.id"])
        accounts = redfishobj.redfish_get(rsp.dict["Accounts"]["@odata.id"])

        for entry in accounts.dict["Members"]:
            account = redfishobj.redfish_get(entry["@odata.id"])

            if account.dict["UserName"] == ilo_login_name_to_modify:
                body = {}
                body_oemhp = {}
                body_oemhp_privs = {}
    
                # if new loginname or password specified
                if new_ilo_password:
                    body["Password"] = new_ilo_password
                if new_ilo_loginname:
                    body["UserName"] = new_ilo_loginname
    
                # if different username specified
                if new_ilo_username:
                    body_oemhp["LoginName"] = new_ilo_username
    
                # if different privileges were requested (None = no change)
                if irc != None:
                    body_oemhp_privs["RemoteConsolePriv"] = irc
                if virtual_media != None:
                    body_oemhp_privs["VirtualMediaPriv"] = virtual_media
                if cfg != None:
                    body_oemhp_privs["iLOConfigPriv"] = cfg
                if usercfg != None:
                    body_oemhp_privs["UserConfigPriv"] = usercfg
                if vpr != None:
                    body_oemhp_privs["VirtualPowerAndResetPriv"] = vpr
    
                # component assembly
                if len(body_oemhp_privs):
                    body_oemhp["Privileges"] = body_oemhp_privs
                if len(body_oemhp):
                    if redfishobj.typepath.defs.isgen9:
                        body["Oem"] = {"Hp": body_oemhp}
                    else:
                        body["Oem"] = {"Hpe": body_oemhp}

                newrsp = redfishobj.redfish_patch(entry["@odata.id"], body)
                redfishobj.error_handler(newrsp)
                return
            
    sys.stderr.write("Account not found\n")

#Instantiating module class        
from ansible.module_utils.basic import *
    
def main():
    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='present', choices=['present', 'absent']),
            name      = dict(required=True),
            enabled   = dict(required=True, type='bool'),
            login_name_to_modify = dict(required=True, type='str'),
            new_loginname = dict(required=True, type='str'),
            new_username = dict(required=True, type='str'),
            new_password = dict(required=True, type='str'),
            irc = dict(required=False, type='bool', default=None),
            cfg = dict(required=False, type='bool', default=None),
            virtual_media = dict(required=False, type='bool', default=None),
            usercfg = dict(required=False, type='bool', default=None),
            vpr = dict(required=False, type='bool', default=None)
        )
    )
    # Set variables based on vars fed from .yml
    login_name_to_modify = module.params['login_name_to_modify']
    new_loginname = module.params['new_loginname']
    new_username = module.params['new_username']
    new_password = module.params['new_password']
    irc = module.params['irc']
    cfg = module.params['cfg']
    virtual_media = module.params['virtual_media']
    usercfg = module.params['usercfg']
    vpr = module.params['vpr']
    
    # When running on the server locally use the following commented values
    # While this example can be run remotely, it is used locally to locate the
    # iLO IP address
    iLO_https_url = "blobstore://."
    iLO_account = "None"
    iLO_password = "None"

    try:
        REDFISH_OBJ = RedfishObject(iLO_https_url, iLO_account, iLO_password)
    except ServerDownOrUnreachableError, excp:
        sys.stderr.write("ERROR: server not reachable or doesn't support " \
                                                                "RedFish.\n")
        sys.exit()
    except Exception, excp:
        raise excp
    modify_ilo_user_account(REDFISH_OBJ, login_name_to_modify, new_loginname, new_username, \
                         new_password, irc, cfg, virtual_media, usercfg, vpr)
    module.exit_json(changed=True)

if __name__ == "__main__":
    main()
