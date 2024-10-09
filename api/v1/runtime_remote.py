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

import time
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
        for pylon_id in list(sorted(self.module.remote_runtimes.keys())):
            data = self.module.remote_runtimes[pylon_id]
            #
            if time.time() - data["timestamp"] > 60:  # 4 announces missing (for 15s interval)
                self.module.remote_runtimes.pop(pylon_id, None)
                continue
            #
            runtime_info = data["runtime_info"]
            #
            for plugin in sorted(runtime_info, key=lambda x: x["name"]):
                item = plugin.copy()
                item["pylon_id"] = pylon_id
                item.pop("config", None)
                item.pop("config_data", None)
                #
                result.append(item)
        #
        return {
            "total": len(result),
            "rows": result,
        }

    @auth.decorators.check_api(["runtime.plugins"])
    def post(self):
        """ Process POST """
        data = flask.request.get_json()
        #
        if "data" not in data or not data["data"]:
            return {"ok": True}
        #
        targets = {}
        #
        for item in data["data"]:
            pylon_id = item.get("pylon_id", "")
            #
            if not pylon_id:
                continue
            #
            if pylon_id not in targets:
                targets[pylon_id] = []
            #
            plugin_state = item.get("state", False)
            plugin_name = item.get("name", "")
            #
            if not plugin_state or not plugin_name:
                continue
            #
            if plugin_name not in targets[pylon_id]:
                targets[pylon_id].append(plugin_name)
        #
        events = []
        #
        for pylon_id, plugins in targets.items():
            if not plugins:
                continue
            #
            log.info("Requesting plugin update(s): %s -> %s", pylon_id, plugins)
            #
            event_data = {
                "pylon_id": pylon_id,
                "plugins": plugins,
                "restart": True,
                "pylon_pid": 1,
            }
            #
            if pylon_id == self.module.context.id:
                events.append(event_data)
            else:
                events.insert(0, event_data)
        #
        for event_item in events:
            self.module.context.event_manager.fire_event(
                "bootstrap_runtime_update",
                event_item,
            )
        #
        return {"ok": True}


class API(api_tools.APIBase):  # pylint: disable=R0903
    """ API """

    url_params = [
        "<string:mode>",
    ]

    mode_handlers = {
        'administration': AdminAPI,
    }
