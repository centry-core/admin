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
from tools import auth, api_tools, db
from collections import defaultdict
from ...models.users import RolePermission


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
            "default": {"admin": False, "viewer": False, "editor": False},
            "developer": {"admin": False, "viewer": False, "editor": False},
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
            "default": {"admin": False, "viewer": False, "editor": False},
            "developer": {"admin": False, "viewer": False, "editor": False},
        }})
    def put(self):  # pylint: disable=R0201
        """ Process """
        project_ids = self.module.context.rpc_manager.call.projects_get_personal_project_ids()
        if not project_ids:
            return {'error': "Personal projects not set"}, 400

        role_map = defaultdict(list)
        for p in request.json:
            role_name = p.pop('name')
            for pr in filter(lambda x: x[1] and isinstance(x[1], bool), p.items()):
                role_map[pr[0]].append(role_name)
        # log.info(f'role_map, {role_map}')
        for project_id in project_ids:
            # log.info(f'doing project {project_id}')
            with db.with_project_schema_session(project_id) as tenant_session:
                tenant_session.query(RolePermission).delete()
                tenant_session.commit()
            for role_name, permissions in role_map.items():
                # log.info(f'\tsetting for role: {role_name}, permissions: {permissions}')
                self.module.set_permissions_for_role(
                    project_id=project_id,
                    role_name=role_name,
                    permissions=permissions
                )
        return {"ok": True, 'role_map': dict(role_map)}, 200


class API(api_tools.APIBase):  # pylint: disable=R0903
    url_params = [
        "",
        "<string:mode>",
    ]

    mode_handlers = {
        'administration': AdminAPI,
    }
