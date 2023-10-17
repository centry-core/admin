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

import uuid
import json

import flask  # pylint: disable=E0401,W0611
import flask_restful  # pylint: disable=E0401

from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611

from tools import auth  # pylint: disable=E0401
from tools import theme  # pylint: disable=E0401
from tools import api_tools  # pylint: disable=E0401


class AdminAPI(api_tools.APIModeHandler):  # pylint: disable=R0903
    @auth.decorators.check_api(["runtime.plugins"])
    def get(self, plugin):  # pylint: disable=R0201
        """ Process GET """
        module_manager = self.module.context.module_manager
        #
        if "market" not in module_manager.modules:
            return {
                "ok": False,
                "error": "Market plugin is not installed",
            }
        #
        market = module_manager.modules["market"].module
        repo_resolver = market.repo_resolver
        #
        plugin_info = repo_resolver.resolve(plugin)
        #
        if plugin_info is None:
            return {
                "ok": False,
                "error": "Plugin is not known by repo resolver(s)",
            }
        #
        metadata_provider = repo_resolver.get_metadata_provider(plugin)
        #
        metadata_url = plugin_info["objects"]["metadata"]
        metadata = metadata_provider.get_metadata({"source": metadata_url})
        #
        return {
            "ok": True,
            "repo_version": metadata.get("version", "0.0.0"),
        }

    @auth.decorators.check_api(["runtime.plugins"])
    def put(self, plugin):  # pylint: disable=R0201
        """ Process PUT """
        module_manager = self.module.context.module_manager
        #
        if "market" not in module_manager.modules:
            return {
                "ok": False,
                "error": "Market plugin is not installed",
            }
        #
        market = module_manager.modules["market"].module
        repo_resolver = market.repo_resolver
        #
        plugin_info = repo_resolver.resolve(plugin)
        #
        if plugin_info is None:
            return {
                "ok": False,
                "error": "Plugin is not known by repo resolver(s)",
            }
        #
        # metadata_provider = repo_resolver.get_metadata_provider(plugin)
        #
        # metadata_url = plugin_info["objects"]["metadata"]
        # metadata = metadata_provider.get_metadata({"source": metadata_url})
        #
        source_target = plugin_info["source"].copy()
        source_type = source_target.pop("type")
        #
        if source_type != "git":
            return {
                "ok": False,
                "error": "Plugin source type is not supported",
            }
        #
        source_provider = repo_resolver.get_source_provider(plugin)
        source = source_provider.get_source(source_target)
        #
        plugins_provider = module_manager.providers["plugins"]
        plugins_provider.add_plugin(plugin, source)
        #
        return {
            "ok": True,
            "message": "Plugin updated, restart pylon to enable new version",
        }

    # @auth.decorators.check_api(["runtime.plugins"])
    # def post(self, plugin):  # pylint: disable=R0201
    #     """ Process POST """
    #     data = flask.request.get_json()  # TODO: validation with pydantic
    #     #
    #     try:
    #         user_id = int(data["user_id"])
    #     except:  # pylint: disable=W0702
    #         user_email = data["user_id"]
    #         user = auth.get_user(email=user_email)
    #         user_id = user["id"]
    #     #
    #     mode = data["mode"]
    #     role = data["role"]
    #     #
    #     self.module.context.rpc_manager.call.auth_assign_user_to_role(
    #         user_id, role, mode
    #     )
    #     #
    #     return {"ok": True}

    # @auth.decorators.check_api(["runtime.plugins"])
    # def delete(self, plugin):  # pylint: disable=R0201
    #     """ Process DELETE """
    #     data = flask.request.args  # TODO: validation with pydantic
    #     #
    #     items = data["id"].split(":")
    #     #
    #     user_id = int(items[0])
    #     mode = items[1]
    #     role = items[2]
    #     #
    #     # TODO: RPC in auth_core
    #     #
    #     return {"ok": True}


class API(api_tools.APIBase):  # pylint: disable=R0903
    url_params = [
        "<string:mode>/<string:plugin>",
    ]

    mode_handlers = {
        'administration': AdminAPI,
    }
