# iLOrest Ansible Usage

## Overview

This Ansible iLO REST role for HPE iLO is intended to provide an simple solution for user to manage server setting.  In addition to using ilorest_library, some of the playbooks also uses redfish_command, redfish_config and redfish_info from ansible package.

## Directory Structure

    ansibleredfish_playbooks - These playbooks use opensource redfish libraries.
    iloresttool_playbooks - These playbooks use ilorest tool which needed to be installed on local/remote.
    ilorestlibraries_playbooks - These playbooks use ilorest library which need to be installed on local/remote
    library - used by ilorestlibraries_playbooks.
    playbooks/hpe - old playbooks - may be duplicates.
    hosts - inventory of hosts, it can have ilo IPs and System IPs depending on the usage.

## Install

RHEL (recomended):
    sudo yum install ansible

Fedora:
    sudo dnf install ansible

Centos:
    sudo yum install epel-release
    sudo yum install ansible

## Usage

There are 3 ways that we can use ansible on HPE servers.

1. Using llorest interface tool   (easiest as we are leveraging the power of this stable tool)
For this to work, ilorest interface tool need to installed using the following ansible script
from [here](https://github.com/HewlettPackard/ansible-ilorest-role/blob/master/iloresttool_playbooks/web_install_rpm.yml)
2. Documentation for tool: [Documentation](https://hewlettpackard.github.io/python-redfish-utility/)
3. Using iLORest libraries  (this is little complicated as we need python and ilorest libraries)
4. Using opensource redfish libraries given by ansible ( works, but some of the ilo functionality not implemented)

Examples should be run in the root folder. Note that the library folder is automatically searched by Ansible for modules when running from playbooks.

**Example command to run restart_server.yml:**

`ansible-playbook restart_server.yml`

A verbose version can be run with

`ansible-playbook restart_server.yml -v`

## Module

The example modules provided here are based off the example scripts in the [python-ilorest-library](https://github.com/HewlettPackard/python-ilorest-library/). These are run through local login, thus ensuring playbooks will work for every assigned server without issue.

we need the boilerplate code from `ansible.module_utils.basic`:

    from ansible.module_utils.basic import AnsibleModule
    if __name__ == '__main__':
        main()

Do note that in our case, we use the * import. prior to Ansible-2.1.0 importing only what you required did not work, hence the use of a wildcard import.

Next, the module class needs to be instantiated like so:

    def main():
        module = AnsibleModule(
            argument_spec = dict(
                state     = dict(default='present', choices=['present', 'absent']),
                name      = dict(required=True),
                enabled   = dict(required=True, type='bool'),
                something = dict(aliases=['whatever'])
            )
        )

The arguments provided here can be set to correspond to the arguments passed in the playbook, enabling the setting of values and commands.

## Playbook

Playbooks are a series of tasks that are performed on the remote machine.

Debug core module can be used to return debug messages.

## Debug Examples

    # Example that prints the loopback address and gateway for each host
    - debug: msg="System {{ inventory_hostname }} has uuid {{ ansible_product_uuid }}"

    - debug: msg="System {{ inventory_hostname }} has gateway {{ ansible_default_ipv4.gateway }}"
    when: ansible_default_ipv4.gateway is defined

    - shell: /usr/bin/uptime
    register: result

    - debug: var=result verbosity=2

    - name: Display all variables/facts known for a host
    debug: var=hostvars[inventory_hostname] verbosity=4
