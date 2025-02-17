#!/usr/bin/python3
# coding=utf-8

#   Copyright 2022 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

""" API """
from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611

from tools import auth, api_tools  # pylint: disable=E0401


class AdminAPI(api_tools.APIModeHandler):  # pylint: disable=R0903,C0115
    @auth.decorators.check_api({
        "permissions": ["projects.projects.projects.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self):
        """ Process """
        result = []
        #
        all_projects = self.module.context.rpc_manager.call.project_list()
        #
        for project in all_projects:
            project_users = self.module.get_users_roles_in_project(
                project["id"],
                filter_system_user=True,
            )
            #
            is_personal_project = project["name"].startswith("project_user_")
            project_admin_ids = []
            #
            if is_personal_project:
                project_admin_ids.extend(
                    user_id for user_id, user_roles in project_users.items()
                    if "editor" in user_roles
                )
            #
            project_admin_ids.extend(
                user_id for user_id, user_roles in project_users.items()
                if "admin" in user_roles
            )
            #
            user_infos = auth.list_users(user_ids=set(project_admin_ids))
            #
            admin_names = []
            for user in user_infos:
                if user["name"] is not None:
                    admin_names.append(user["name"])
                else:
                    admin_names.append(str(user["email"]))
            #
            result_item = project.copy()
            result_item["project_name"] = result_item["name"]
            result_item["admin_name"] = ", ".join(admin_names)
            #
            result.append(result_item)
        #
        return {
            "total": len(result),
            "rows": result,
        }


class API(api_tools.APIBase):  # pylint: disable=R0903
    url_params = [
        "<string:mode>",
    ]

    mode_handlers = {
        'administration': AdminAPI,
    }
