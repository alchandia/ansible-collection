"""
Util class for google_workspace_groups
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient import errors

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
            if group_definition is None:
                result["failed"] = True
                result["message"] = "Group definition don't exist "
                return result

            types_definition = next((sub for sub in self.module.params['groups_types'] if sub['name'] == group_definition["type"]), None)
            if types_definition is None:
                result["failed"] = True
                result["message"] = "Group type definition don't exist "
                return result

            settings_definition = types_definition["settings"][0]
            settings_current = self.get_settings(service, group)
            if settings_definition != settings_current:
                result["failed"] = True
                settings = {
                    "current": settings_current,
                    "definition": settings_definition
                }
                result["message"].append(settings)
            else:
                result["message"] = "Definition and current settings match"

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


    def create_update(self):

        result = {}
        # auth google
        target_scopes = [
            "https://www.googleapis.com/auth/admin.directory.group",
            "https://www.googleapis.com/auth/admin.directory.group.member"
        ]
        credentials = service_account.Credentials.from_service_account_file(
            self.module.params['credential_file'],
            scopes=target_scopes,
            subject=self.module.params['used_by'])
        service = build("admin", "directory_v1", credentials=credentials)

        for group in self.module.params['groups']:
            # get detail of group from list
            group_definition = next((sub for sub in self.module.params['groups_definition'] if sub['mail'] == group), None)
            if group_definition is None:
                result = {
                    "changed": False,
                    "failed": True,
                    "message": "Group definition don't exist"
                }
            else:
                IF_EXIST_RES=self.check_if_exists(service, group)
                if IF_EXIST_RES == "TRUE":
                    result = self.update(service, group_definition)
                elif IF_EXIST_RES == "FALSE":
                    result = self.create(service, group_definition)
                else:
                    result = {
                        "changed": False,
                        "failed": True,
                        "message": IF_EXIST_RES
                    }

        return result
 
    # Create group
    def create(self, service, group_definition):
        result = {
            "changed": False,
            "failed": False,
            "message": []
        }
        try:
            body_info = {}
            body_info = {
                "email": group_definition["mail"],
                "name": group_definition["name"],
                "description": group_definition["description"]
            }
            service.groups().insert(body=body_info).execute()
            result["changed"] = True
            result["message"] = "Group created"
        except Exception as error:
            result['failed'] = True
            result["message"] = error

        return result


    def update(self, service, group):
        result = {
            "changed": False,
            "failed": False,
            "message": []
        }

        definition_members = group["members"] if "members" in group else []
        current_members = []
        try:
            results = (
                service.members()
                .list(groupKey=group["mail"])
                .execute()
            )
            if "members" in results:
                for member in results["members"]:
                    current_members.append(member["email"])

            # estos se borran
            for deleted in set(current_members).difference(definition_members):
                res = self.member_insert_delete("delete", service, group["mail"], deleted)
                if res != "OK":
                    result["failed"] = True
                    result["message"].append(deleted + ": " + res)

            # estos se agregan
            for added in set(definition_members).difference(current_members):
                res = self.member_insert_delete("insert", service, group["mail"], added)
                if res != "OK":
                    result["failed"] = True
                    result["message"].append(added + ": " + res)

        except Exception as error:
            result["failed"] = True
            result["message"].append(str(error))

        return result


    def check_if_exists(self, service, group):
        result = "NONE"
        try:
            results = (
                service.groups()
                .get(groupKey=group)
                .execute()
            )
            result = "TRUE"
        except errors.HttpError as error:
            if str(error.status_code) == "404":
                result = "FALSE"
            else:
                result = str(error.error_details)
        except Exception as error:
            result = str(error)

        return result

    def member_insert_delete(self, action, service, group, member):
        result = "ERROR"
        try:
            if action == "insert":
                # TODO: insert method don't fail if the user don't exists
                body_member = {
                    "email": member
                }
                service.members().insert(
                    groupKey=group,
                    body=body_member
                ).execute()
                result = "OK"
            if action == "delete":
                service.members().delete(
                        groupKey=group,
                        memberKey=member
                    ).execute()
                result = "OK"

        except Exception as error:
            result = str(error)

        return result
