#!/usr/bin/python3
# coding=utf-8

#   Copyright 2025 getcarrier.io
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

""" Method """

import arbiter

from pylon.core.tools import log  # pylint: disable=E0611,E0401
from pylon.core.tools import web  # pylint: disable=E0611,E0401


class Method:  # pylint: disable=E1101,R0903
    """
        Method Resource

        self is pointing to current Module instance

        web.method decorator takes zero or one argument: method name
        Note: web.method decorator must be the last decorator (at top)

    """

    @web.init()
    def _tasks_init(self):
        self.event_node = arbiter.make_event_node(
            config={
                "type": "MockEventNode",
            },
        )
        #
        self.task_node = arbiter.TaskNode(
            self.event_node,
            pool="admin",
            task_limit=None,
            ident_prefix="admin_",
            multiprocessing_context="threading",
            task_retention_period=3600,
            housekeeping_interval=60,
            thread_scan_interval=0.1,
            start_max_wait=3,
            query_wait=3,
            watcher_max_wait=3,
            stop_node_task_wait=3,
            result_max_wait=3,
            result_transport="memory",
        )
        #
        self.task_node.start()

    @web.deinit()
    def _tasks_deinit(self):
        self.task_node.stop()
