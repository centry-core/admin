#!/usr/bin/python3
# coding=utf-8

#   Copyright 2024 getcarrier.io
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

from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611

from tools import auth  # pylint: disable=E0401
from tools import api_tools  # pylint: disable=E0401


class AdminAPI(api_tools.APIModeHandler):  # pylint: disable=R0903
    """ API """

    @auth.decorators.check_api(["runtime.plugins"])
    def get(self):
        """ Process GET """
        result = []
        #
        node = flask.request.args.get("node", None)
        scope = flask.request.args.get("scope", None)
        #
        module_manager = self.module.context.module_manager
        #
        if node is not None and scope is not None:
            plugin_name, task_node_name = node.split(".", 1)
            #
            if plugin_name in module_manager.modules:
                plugin = module_manager.modules[plugin_name].module
                task_node = getattr(plugin, task_node_name, None)
                #
                if task_node is not None:
                    if scope == "pool":
                        with task_node.lock:
                            for pool, state in task_node.global_pool_state.items():
                                result.append({
                                    "pool": pool,
                                    "state": str(state),
                                })
                    #
                    if scope == "task":
                        with task_node.lock:
                            for task_id, state in task_node.global_task_state.items():
                                result_state = state.copy()
                                result_state.pop("result", None)
                                #
                                result.append({
                                    "task_id": task_id,
                                    "state": str(result_state),
                                })
        #
        return {
            "total": len(result),
            "rows": result,
        }


class API(api_tools.APIBase):  # pylint: disable=R0903
    """ API """

    url_params = [
        "<string:mode>",
    ]

    mode_handlers = {
        'administration': AdminAPI,
    }
