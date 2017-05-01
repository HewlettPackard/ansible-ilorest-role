iLOrest Ansible Role
======

[![Build Status](https://travis-ci.org/HewlettPackard/ansible-ilorest-role.svg?branch=master)](https://travis-ci.org/HewlettPackard/ansible-ilorest-role)
[![GitHub license](https://img.shields.io/badge/license-Apache%202-blue.svg)](https://raw.githubusercontent.com/HewlettPackard/puppet-ilorest-module/master/LICENSE)

#### Table of Contents

1. [Overview](#overview)
2. [Usage](#usage)
3. [Writing a Module](#module)
4. [Writing a Playbook](#playbook)
5. [Usage](#usage)
5. [History](#history)
5. [License](#license)
5. [Authors](#authors)

## Overview

This Ansible iLO REST role for HPE iLO is intended to provide an simple solution for user to manage server setting

## Usage

Examples should be run in the root folder. Note that the library folder is automatically searched by Ansible for modules when running from playbooks. 

**Example command to run restart_server.yml:**

`ansible-playbook restart_server.yml` 

A verbose version can be run with 

`ansible-playbook restart_server.yml -v`

`ansible_main.yml` is the updated playbook.

## Module

The example modules provided here are based off the example scripts in the [python-ilorest-library](https://github.com/HewlettPackard/python-ilorest-library/). These are run through local login, thus ensuring playbooks will work for every assigned server without issue.

Due to the nature of ansible, and the need for modules to be self-contained, we have to integrate the contents of `_restobject.py` and `_redfishobject.py` into our module first. 

Additionally, we need the boilerplate code from `ansible.module_tils.basic`:

```
from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
```

Do note that in our case, we use the * import. prior to Ansible-2.1.0 importing only what you required did not work, hence the use of a wildcard import.

Next, the module class needs to be instantiated like so:
```
def main():
    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='present', choices=['present', 'absent']),
            name      = dict(required=True),
            enabled   = dict(required=True, type='bool'),
            something = dict(aliases=['whatever'])
        )
    )
```

The arguments provided here can be set to correspond to the arguments passed in the playbook, enabling the setting of values and commands.

## Playbook

Playbooks are a series of tasks that are performed on the remote machine.

Debug core module can be used to return debug messages.

**Debug Examples**

```
# Example that prints the loopback address and gateway for each host
- debug: msg="System {{ inventory_hostname }} has uuid {{ ansible_product_uuid }}"

- debug: msg="System {{ inventory_hostname }} has gateway {{ ansible_default_ipv4.gateway }}"
  when: ansible_default_ipv4.gateway is defined

- shell: /usr/bin/uptime
  register: result

- debug: var=result verbosity=2

- name: Display all variables/facts known for a host
  debug: var=hostvars[inventory_hostname] verbosity=4
  ```

## History

* 05/01/2017: Initial Commit

## License

Copyright 2017 Hewlett Packard Enterprise Development LP

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Authors

* [Jack Garcia](http://github.com/LumbaJack)
* [Matthew Kocurek](http://github.com/Yergidy)
* [Prithvi Subrahmanya](http://github.com/PrithviBS)
