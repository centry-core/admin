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

import flask  # pylint: disable=E0401,W0611
import flask_restful  # pylint: disable=E0401
from flask import g, request

from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611

from tools import auth, api_tools  # pylint: disable=E0401


def group_roles_by_permissions(auth_permissions, roles):
    auth_permissions = sorted(auth_permissions, key=lambda x: x['name'])
    roles_to_permissions = {role["name"]: set() for role in roles}
    for key, group_items in groupby(auth_permissions, key=lambda x: x['name']):
        for item in group_items:
            roles_to_permissions[key].add(item['permission'])
    return roles_to_permissions


class AdminAPI(api_tools.APIModeHandler):
    @auth.decorators.check_api({
        "permissions": ["configuration.roles.permissions.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self, target_mode):  # pylint: disable=R0201
        """ Process """
        roles = auth.get_roles(target_mode)
        auth_permissions = auth.get_permissions(target_mode)
        log.info(f"{roles=} {auth_permissions=}")
        all_permissions = auth.local_permissions
        # log.info(f"{permissions=} {local_permissions=} {all_permissions=}")
        roles_to_permissions = group_roles_by_permissions(auth_permissions, roles)
        log.info(
            f"{roles=} \n {auth_permissions=} \n {all_permissions=} \n {roles_to_permissions=}")
        all_permissions = sorted(all_permissions)
        return {
            "total": len(all_permissions),
            "rows": [{
                "name": permission,
                **{role["name"]: permission in roles_to_permissions[role["name"]] for
                   role in roles}
            } for permission in all_permissions]
        }

    @auth.decorators.check_api({
        "permissions": ["configuration.roles.permissions.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def put(self, target_mode):  # pylint: disable=R0201
        """ Process """
        new_data = request.get_json()
        old_data = self.get(target_mode)["rows"]
        old_permissions = set(
            (r, p['name']) for p in old_data for r, v in p.items() if v)
        new_permissions = set(
            (r, p['name']) for p in new_data for r, v in p.items() if v)
        permissions_to_delete = old_permissions - new_permissions
        permissions_to_add = new_permissions - old_permissions
        for permission in permissions_to_add:
            auth.set_permission_for_role(*permission, mode=target_mode)
        for permission in permissions_to_delete:
            auth.remove_permission_from_role(*permission, mode=target_mode)
        return {"ok": True}


class ProjectAPI(api_tools.APIModeHandler):
    @auth.decorators.check_api({
        "permissions": ["configuration.roles.permissions.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self, project_id):  # pylint: disable=R0201
        """ Process """
        roles = self.module.get_roles(project_id)
        auth_permissions = self.module.get_permissions(project_id)
        all_permissions = auth.local_permissions
        roles_to_permissions = group_roles_by_permissions(auth_permissions, roles)
        all_permissions = sorted(all_permissions)
        return {
            "total": len(all_permissions),
            "rows": [{
                "name": permission,
                **{role["name"]: permission in roles_to_permissions[role["name"]] for
                   role in roles}
            } for permission in all_permissions]
        }

    @auth.decorators.check_api({
        "permissions": ["configuration.roles.permissions.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def put(self, project_id):  # pylint: disable=R0201
        """ Process """
        new_data = request.get_json()
        old_data = self.get(project_id)["rows"]
        old_permissions = set(
            (r, p['name']) for p in old_data for r, v in p.items() if v)
        new_permissions = set(
            (r, p['name']) for p in new_data for r, v in p.items() if v)
        permissions_to_delete = old_permissions - new_permissions
        permissions_to_add = new_permissions - old_permissions
        log.info(f"{permissions_to_delete=} {permissions_to_add=}")

        for permission in permissions_to_add:
            self.module.set_permission_for_role(
                project_id,
                *permission,
            )
        for permission in permissions_to_delete:
            self.module.remove_permission_from_role(
                project_id,
                *permission,
            )
        return {"ok": True}


class API(api_tools.APIBase):  # pylint: disable=R0903
    url_params = [
        "<string:target_mode>",
        "<string:mode>/<string:target_mode>",
        "<string:mode>/<int:project_id>",
    ]

    mode_handlers = {
        'default': ProjectAPI,
        'administration': AdminAPI,
    }
