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

import flask  # pylint: disable=E0401,W0611
import flask_restful  # pylint: disable=E0401
from flask import g, request

from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611
from sqlalchemy import schema

from tools import auth, db, api_tools  # pylint: disable=E0401


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

    def get(self, project_id: int, **kwargs):
        all_users = auth.list_users()
        project_users = self.module.context.rpc_manager.call.get_users_roles_in_project(
            project_id)
        users_roles = []
        for user_id, roles in project_users.items():
            user = {'id': user_id, 'roles': roles}
            user.update([u for u in all_users if user['id'] == u['id']][0])
            users_roles.append(user)
        return {
            "total": len(users_roles),
            "rows": users_roles,
        }

    def post(self, project_id: int, **kwargs):
        user_name = request.json["name"]
        user_email = request.json["email"]
        user_roles = request.json["roles"]
        return self.module.context.rpc_manager.call.add_user_to_project_or_create(
            user_email, user_email, project_id, user_roles)
  
