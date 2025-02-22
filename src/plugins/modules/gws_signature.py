#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: gws_signature

short_description: Set signature

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Set email signature for specific users or group of users.

options:
    credential_file:
        description:
            - Path to the credential file associated with the service account, we assume the json file is in the same location of the playbook.
        type: str
        required: true
        default: 'credential.json'
    signature_folder:
        description:
          - Full path to folder where jinja2 template of signature is located.
          - We use the option 'signature' from the properties of the user to set the filename.
          - The template need to use '.j2' extension
        type: str
        required: true
    current_users:
        description:
            - A list of users that exists in the domain.
        type: list
        elements: dict
        required: true
        default: []
    current_groups:
        description:
            - A list of groups that exists in the domain.
        type: list
        elements: dict
        required: true
        default: []
    users:
        description:
          - A list of users to update their signature.
        type: list
        elements: str
        required: false
    groups:
        description:
          - A list of groups to update their signature.
        type: list
        elements: str
        required: false

author:
    - IT I2B
'''

EXAMPLES = r'''
- name: Set signature for users/groups
    i2btech.ops.gws_signature:
    current_users: "{{ gws_users }}"
    current_groups: "{{ gws_groups }}"
    signature_folder: "{{ playbook_dir }}/templates/signatures"
    users:
        - "user.name@i2btech.com"
    groups:
        - "group.users@i2btech.com"
'''

RETURN = r'''
message:
    description: Message associated with result of the action.
    type: str
    returned: always
    sample: 'Signatures updated'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.i2btech.ops.plugins.module_utils.google_workspace import GoogleWorkspaceHelper

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        credential_file=dict(type="str", default="credential.json"),
        signature_folder=dict(type="str", required=True),
        current_users=dict(type="list", required=True, elements="dict"),
        current_groups=dict(type="list", required=True, elements="dict"),
        users=dict(type="list", elements="str", required=False, default=[]),
        groups=dict(type="list", elements="str", required=False, default=[])
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        failed=False,
        message=""
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)


    gws = GoogleWorkspaceHelper(module)
    result_signature = gws.apply_signature()

    result['message'] = result_signature["message"]
    result['changed'] = result_signature["changed"]
    result['failed'] = result_signature["failed"]


    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if result['failed']:
        module.fail_json(msg='An error occur', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
