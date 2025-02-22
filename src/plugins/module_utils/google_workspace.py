"""
Util class for google_workspace
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

#
# class: GoogleWorkspaceHelper
#

class GoogleWorkspaceHelper:
    """
    Class GoogleWorkspaceHelper
    """

    def __init__(self, module):
        self.module = module


    def get_group_members(self, group, service):

        results = (
            service.members()
            .list(groupKey=group)
            .execute()
        )
        members = results.get("members", [])
        user_list = []
        if not members:
            user_list = [None]
        else:
            for member in members:
                user_list.append(member['email'])

        return user_list


    def signout_users(self):

        result_signout = {
            "changed": False,
            "failed": False,
            "message": []
        }

        users_from_groups = []
        target_scopes = ["https://www.googleapis.com/auth/admin.directory.group.readonly"]
        credentials = service_account.Credentials.from_service_account_file(
            self.module.params['credential_file'],
            scopes=target_scopes)
        service_members = build("admin", "directory_v1", credentials=credentials)

        if self.module.params['groups'] is not None:
            for group in self.module.params['groups']:
                users_from_groups = users_from_groups + self.get_group_members(group, service_members)

        target_scopes_security = ["https://www.googleapis.com/auth/admin.directory.user.security"]
        credentials_security = service_account.Credentials.from_service_account_file(
            self.module.params['credential_file'],
            scopes=target_scopes_security,
            subject=self.module.params['used_by'])
        service_signout = build("admin", "directory_v1", credentials=credentials_security)

        if (len(self.module.params['users']) == 0) and len(users_from_groups) == 0:
            result_signout['failed'] = True
            result_signout['message'].append("Need users or groups")
        else:
            for user in self.module.params['users'] + users_from_groups:
                try:
                    results = (
                        service_signout.users()
                        .signOut(userKey=user)
                        .execute()
                    )
                    result_signout['changed'] = True
                except Exception as error:
                    result_signout['failed'] = True
                    current_user = {
                        "user": user,
                        "message": error
                    }
                    result_signout['message'].append(current_user)

        if not result_signout['failed']:
            result_signout['message'].append("All sessions closed")

        return result_signout


    def render_signature(self, user_info, template_folder):
        # create signature from template
        env = Environment(loader=FileSystemLoader(template_folder))
        rendered_string = env.get_template(user_info['signature'] + ".j2").render(
            full_name=user_info['full_name'],
            title=user_info['title'],
            phone=user_info['phone'] if "phone" in user_info else None,
        )
        return rendered_string


    def apply_signature(self):

        result_signature = {
            "changed": False,
            "failed": False,
            "message": []
        }

        # get users from current groups
        users_from_groups = []
        for group in self.module.params['current_groups']:
            if group['mail'] in self.module.params['groups']:
                users_from_groups = users_from_groups + group['members']

        if (len(self.module.params['users']) == 0) and len(users_from_groups) == 0:
            result_signature['failed'] = True
            result_signature['message'].append("Need users or groups")
        else:
            # iterate over list of all users that need to be updated
            for user in self.module.params['users'] + users_from_groups:
                try:
                    # iterate over list of all current users if use that need to be updated
                    # exist, apply change
                    for current_user in self.module.params['current_users']:
                        if current_user['mail'] == user:

                            # auth google
                            target_scopes = ["https://www.googleapis.com/auth/gmail.settings.basic"]
                            credentials = service_account.Credentials.from_service_account_file(
                                self.module.params['credential_file'],
                                scopes=target_scopes,
                                subject=current_user['mail'])
                            service_user = build("gmail", "v1", credentials=credentials)

                            send_as_configuration = {
                                "signature": self.render_signature(current_user, self.module.params['signature_folder']),
                            }
                            # pylint: disable=E1101
                            result = (
                                service_user.users()
                                .settings()
                                .sendAs()
                                .patch(
                                    userId=current_user['mail'],
                                    sendAsEmail=current_user['mail'],
                                    body=send_as_configuration,
                                )
                                .execute()
                            )
                            result_signature['changed'] = True

                except Exception as error:
                    result_signature['failed'] = True
                    current_user = {
                        "user": user,
                        "message": error
                    }
                    result_signature['message'].append(current_user)

        if not result_signature['failed']:
            result_signature['message'].append("Signatures updated")

        return result_signature
