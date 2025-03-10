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

""" Task """

import logging

from centry_logging.handlers.eventnode import EventNodeLogHandler  # pylint: disable=E0611,E0401
from centry_logging.formatters.secret import SecretFormatter  # pylint: disable=E0611,E0401
from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611

from tools import context  # pylint: disable=E0401


class make_logger:  # pylint: disable=C0103
    """ Task """

    def __init__(self):
        try:
            import tasknode_task  # pylint: disable=E0401,C0415
            #
            self.task_id = tasknode_task.id
            self.task_name = tasknode_task.name
            #
            self.event_node_config = context.module_manager.descriptors[
                "logging_hub"
            ].module.event_node_config
            #
            self.handler = None
            self.logger = None
            #
            self.fallback = False
        except:  # pylint: disable=W0702
            self.fallback = True

    def __enter__(self):
        if self.fallback:
            return log
        #
        self.handler = EventNodeLogHandler({
            "event_node": self.event_node_config,
            "labels": {
                "tasknode_task": f"id:{self.task_id}",
                "stream_id": "",  # until datasources are updated
            }
        })
        self.handler.setFormatter(SecretFormatter())
        #
        self.logger = logging.Logger(f"{self.task_name}:{self.task_id}")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)
        #
        return self.logger

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.fallback:
            return
        #
        if self.handler is not None:
            self.logger.removeHandler(self.handler)
            #
            self.handler.close()
        #
        if self.logger is not None:
            del self.logger
