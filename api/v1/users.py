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
from flask import request
from pydantic import ValidationError

from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611
from tools import auth, api_tools  # pylint: disable=E0401

from ...models.pd.user_input_field import UserInputFieldPD

class AdminAPI(api_tools.APIModeHandler):
    pass


class ProjectAPI(api_tools.APIModeHandler):
    pass

class API(api_tools.APIBase):  # pylint: disable=R0903
    url_params = [
        '<int:project_id>',
        '<string:mode>/<int:project_id>'
    ]
    mode_handlers = {
        'default': ProjectAPI,
        'administration': AdminAPI,
    }
    
    @auth.decorators.check_api({
        "permissions": ["configuration.users.users.view"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def get(self, project_id: int, **kwargs):
        all_users = auth.list_users()
        project_users = self.module.context.rpc_manager.call.get_users_roles_in_project(
            project_id)
        users_roles = []
        for user_id, roles in project_users.items():
            user = {'id': user_id, 'roles': roles}
            user.update([u for u in all_users if user['id'] == u['id']][0])
            if user['last_login']:
                user['last_login'] = user['last_login'].strftime("%d.%m.%Y %H:%M")
            users_roles.append(user)
        return {
            "total": len(users_roles),
            "rows": users_roles,
        }, 200

    @auth.decorators.check_api({
        "permissions": ["configuration.users.users.create"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def post(self, project_id: int, **kwargs):
        user_emails = request.json["emails"]
        user_roles = request.json["roles"]
        results = []
        for user_email in user_emails:
            try:
                UserInputFieldPD(user_email=user_email)
            except ValidationError as e:
                results.append({'msg': e.errors()[0]["msg"], 'status': 'error'})
                continue
            result = self.module.context.rpc_manager.call.add_user_to_project_or_create(
                user_email, project_id, user_roles)
            results.append(result)
        return results, 200

    @auth.decorators.check_api({
        "permissions": ["configuration.users.users.edit"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def put(self, project_id: int, **kwargs):
        user_id = request.json["id"]
        new_user_roles = request.json["roles"]
        result = self.module.context.rpc_manager.call.update_roles_for_user(
            project_id, user_id, new_user_roles)
        return {'msg': f'roles updated' if result else 'something is wrong'}, 200

    @auth.decorators.check_api({
        "permissions": ["configuration.users.users.delete"],
        "recommended_roles": {
            "administration": {"admin": True, "viewer": False, "editor": False},
            "default": {"admin": True, "viewer": False, "editor": False},
            "developer": {"admin": True, "viewer": False, "editor": False},
        }})
    def delete(self, project_id, **kwargs):
        try:
            delete_ids = list(map(int, request.args["id[]"].split(',')))
        except TypeError:
            return 'IDs must be integers', 400
        for user_id in delete_ids:
            self.module.context.rpc_manager.call.remove_user_from_project(
                project_id, user_id)
        return {'msg': 'users succesfully removed'}, 204
