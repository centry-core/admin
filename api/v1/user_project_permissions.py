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
from itertools import groupby
from flask import request

from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611
from tools import auth, api_tools  # pylint: disable=E0401


def group_roles_by_permissions(auth_permissions, roles):
    auth_permissions = sorted(auth_permissions, key=lambda x: x['name'])
    roles_to_permissions = {role["name"]: set() for role in roles}
    for key, group_items in groupby(auth_permissions, key=lambda x: x['name']):
        for item in group_items:
            roles_to_permissions[key].add(item['permission'])
    return roles_to_permissions


def get_permissions_map(module, project_id: int) -> tuple[list, list]:
    roles = module.get_roles(project_id)
    auth_permissions = module.get_permissions(project_id)
    all_permissions = auth.local_permissions
    roles_to_permissions = group_roles_by_permissions(auth_permissions, roles)
    all_permissions = sorted(all_permissions)
    permissions_map = [{
        "name": permission,
        **{role["name"]: permission in roles_to_permissions[role["name"]] for
        role in roles}
        } for permission in all_permissions
        ]
    return all_permissions, permissions_map


class AdminAPI(api_tools.APIModeHandler):
    @auth.decorators.check_api({
        "permissions": ["configuration.roles.user_project_permissions.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self):  # pylint: disable=R0201
        """ Process """
        project_ids = self.module.context.rpc_manager.call.projects_get_personal_project_ids()
        if not project_ids:
            return {'error': "Personal projects not set"}, 400

        project_id = project_ids[0]
        all_permissions, permissions_map = get_permissions_map(self.module, project_id)

        return {
            "total": len(all_permissions),
            "rows": permissions_map
        }

    @auth.decorators.check_api({
        "permissions": ["configuration.roles.user_project_permissions.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def put(self):  # pylint: disable=R0201
        """ Process """
        project_ids = self.module.context.rpc_manager.call.projects_get_personal_project_ids()
        if not project_ids:
            return {'error': "Personal projects not set"}, 400

        new_data = request.get_json()
        # _, old_data = get_permissions_map(self.module, project_ids[0])
        # old_permissions = set(
        #     (r, p['name']) for p in old_data for r, v in p.items() if v)
        new_permissions = set(
            (r, p['name']) for p in new_data for r, v in p.items() if v)
        # permissions_to_delete = old_permissions - new_permissions
        # permissions_to_add = new_permissions - old_permissions

        for project_id in project_ids:
            self.module.remove_all_permissions(project_id)

            for permission in new_permissions:
                self.module.set_permission_for_role(
                    project_id,
                    *permission,
                )
            # for permission in permissions_to_delete:
            #     self.module.remove_permission_from_role(
            #         project_id,
            #         *permission,
            #     )
        return {"ok": True}


class API(api_tools.APIBase):  # pylint: disable=R0903
    url_params = [
        "",
        "<string:mode>",
    ]

    mode_handlers = {
        'administration': AdminAPI,
    }
