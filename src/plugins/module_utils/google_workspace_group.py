"""
Util class for google_workspace_groups
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from googleapiclient.discovery import build
from google.oauth2 import service_account

#
# class: GoogleWorkspaceGroupHelper
#

class GoogleWorkspaceGroupHelper:
    """
    Class GoogleWorkspaceGroupHelper
    """

    def __init__(self, module):
        self.module = module


    def get_members(self, group, service):

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


    def check_config(self):

        result = {
            "changed": False,
            "failed": False,
            "message": []
        }

        # auth google
        target_scopes = [
            "https://www.googleapis.com/auth/admin.directory.group.readonly",
            "https://www.googleapis.com/auth/apps.groups.settings",
        ]
        credentials = service_account.Credentials.from_service_account_file(
            self.module.params['credential_file'],
            scopes=target_scopes)
        service = build("groupssettings", "v1", credentials=credentials)

        for group in self.module.params['groups']:
            group_definition = next((sub for sub in self.module.params['groups_definition'] if sub['mail'] == group), None)
            types_definition = next((sub for sub in self.module.params['groups_types'] if sub['name'] == group_definition["type"]), None)

            settings_definition = types_definition["settings"][0]
            settings_current = self.get_settings(service, group)
            if settings_definition != settings_current:
                result["failed"] = True

            result["message"].append(settings_definition)
            result["message"].append(settings_current)

        return result


    def get_settings(self, service, group):

        results_group_settings = (
            service.groups()
            .get(groupUniqueId=group)
            .execute()
        )

        current_settings = {}
        current_settings["whoCanJoin"] = results_group_settings['whoCanJoin']
        current_settings["whoCanAdd"] = results_group_settings['whoCanAdd']
        current_settings["whoCanInvite"] = results_group_settings['whoCanInvite']
        current_settings["whoCanViewMembership"] = results_group_settings['whoCanViewMembership']
        current_settings["allowExternalMembers"] = results_group_settings['allowExternalMembers']
        current_settings["whoCanContactOwner"] = results_group_settings['whoCanContactOwner']
        current_settings["whoCanViewGroup"] = results_group_settings['whoCanViewGroup']
        current_settings["whoCanPostMessage"] = results_group_settings['whoCanPostMessage']

        return current_settings
