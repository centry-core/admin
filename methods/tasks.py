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

from ..tasks import db_tasks
from ..tasks import indexer_tasks
from ..tasks import project_tasks
from ..tasks import mesh_tasks


class Method:  # pylint: disable=E1101,R0903
    """
        Method Resource

        self is pointing to current Module instance

        web.method decorator takes zero or one argument: method name
        Note: web.method decorator must be the last decorator (at top)

    """

    @web.init()
    def _tasks_init(self):
        self.admin_tasks = {}  # name -> func
        #
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
            start_attempts=1,
        )
        #
        self.task_node.start()
        #
        local_admin_tasks = [
            ("create_tables", db_tasks.create_tables),
            ("create_tables_for_failed", db_tasks.create_tables_for_failed),
            ("propose_migrations", db_tasks.propose_migrations),
            ("create_database", db_tasks.create_database),
            #
            ("indexer_migrate", indexer_tasks.indexer_migrate),
            #
            ("list_failed_projects", project_tasks.list_failed_projects),
            ("delete_failed_projects", project_tasks.delete_failed_projects),
            ("fix_personal_projects", project_tasks.fix_personal_projects),
            #
            ("mesh_get_plugin_frozen_requirements", mesh_tasks.mesh_get_plugin_frozen_requirements),
        ]
        #
        for task_name, task_func in local_admin_tasks:
            self.register_admin_task(task_name, task_func)

    @web.method()
    def register_admin_task(self, name, func):
        """ Method """
        if name in self.admin_tasks:
            raise RuntimeError(f"Task already registered: {name}")
        #
        self.admin_tasks[name] = func
        self.task_node.register_task(func, name)

    @web.method()
    def unregister_admin_task(self, name, func):
        """ Method """
        if name not in self.admin_tasks:
            raise RuntimeError(f"Task is not registered: {name}")
        #
        self.task_node.unregister_task(func, name)
        self.admin_tasks.pop(name, None)

    @web.method()
    def present_admin_tasks(self):
        """ Method """
        result = list(self.admin_tasks)
        result.sort()
        return result

    @web.deinit()
    def _tasks_deinit(self):
        for task_name, task_func in list(self.admin_tasks.items()):
            self.unregister_admin_task(task_name, task_func)
        #
        self.task_node.stop()
