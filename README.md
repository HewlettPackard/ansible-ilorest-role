iLOrest Ansible Role
======
## Overview

This Ansible iLO REST role for HPE iLO is intended to provide an simple solution for user to manage server setting.  In addition to using ilorest_library, some of the playbooks also uses redfish_command, redfish_config and redfish_info from ansible package.

## Install

To install ansible on linux,
pip install ansible

## Usage

Examples should be run in the root folder. Note that the library folder is automatically searched by Ansible for modules when running from playbooks. 

**Example command to run restart_server.yml:**

`ansible-playbook restart_server.yml` 

A verbose version can be run with 

`ansible-playbook restart_server.yml -v`


## Module

The example modules provided here are based off the example scripts in the [python-ilorest-library](https://github.com/HewlettPackard/python-ilorest-library/). These are run through local login, thus ensuring playbooks will work for every assigned server without issue.

we need the boilerplate code from `ansible.module_tils.basic`:

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
