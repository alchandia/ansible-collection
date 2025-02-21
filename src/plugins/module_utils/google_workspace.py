"""
Util class for google_workspace
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from googleapiclient.discovery import build
from google.oauth2 import service_account

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
