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

    def render_signature(self, user_info, template):
        # set user info
        addres = None
        location = None

        if user_info['signature'] == "chile":
            addres="La Concepci&oacute;n 141, Depto 501, Piso 5 <br> Santiago, Chile"
            location="https://www.google.com/maps/place/La+Concepci%C3%B3n+141,+Providencia,+Regi%C3%B3n+Metropolitana,+Chile/@-33.4245146,-70.6159423,17z/data=!3m1!4b1!4m2!3m1!1s0x9662cf615b7d4d29:0x6daf452c3d82cad0"
        elif user_info['signature'] == "colombia":
            addres="Cl 114 #42-27 Torre 15 Apt 303 <br> Barranquilla, Colombia"
            location="https://www.google.com/maps/place/Conjunto+T%C3%B3rtola/@10.9917772,-74.8437899,18.96z/data=!4m6!3m5!1s0x8ef42d4709d4f457:0x6205dd66db4079dd!8m2!3d10.9915468!4d-74.8438118!16s%2Fg%2F11hzv4rf3t?entry=ttu&g_ep=EgoyMDI1MDEyOS4xIKXMDSoASAFQAw%3D%3D"           
        elif user_info['signature'] == "peru":
            addres="Av. Republica De Panama Nro. 3535 Int. 403 Otr. <br> San Isidro, Per&uacute;"
            location="https://www.google.com/maps/place/Oficina+403,+Av.+Rep%C3%BAblica+de+Panam%C3%A1+3535,+San+Isidro+15036,+Peru/@-12.0989983,-77.0219499,17z/data=!3m1!4b1!4m6!3m5!1s0x9105c871ab579633:0x60fb1f5ac3a41595!8m2!3d-12.0989983!4d-77.019375!16s%2Fg%2F11s19r3zvr?entry=ttu&g_ep=EgoyMDI1MDEyOS4xIKXMDSoASAFQAw%3D%3D"

        # create signature from template
        path_template = Path(template)
        env = Environment(loader=FileSystemLoader(str(path_template.parent)))
        rendered_string = env.get_template(str(path_template.name)).render(
            full_name=user_info['full_name'],
            title=user_info['title'],
            addres=addres,
            phone=user_info['phone'] if "phone" in user_info else None,
            location=location
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
                                "signature": self.render_signature(current_user, self.module.params['signature_file']),
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
