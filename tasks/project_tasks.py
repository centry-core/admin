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

import time

from tools import context, log  # pylint: disable=E0401

from .logs import make_logger


def list_failed_projects(*args, **kwargs):
    """ Task """
    #
    with make_logger() as log:
        log.info("Starting")
        start_ts = time.time()
        #
        try:
            log.info("Getting project list")
            project_list = context.rpc_manager.timeout(120).project_list(
                filter_={"create_success": False},
            )
            #
            for project in project_list:
                log.info("Failed project: %s", project)
        except:  # pylint: disable=W0702
            log.exception("Got exception, stopping")
        #
        end_ts = time.time()
        log.info("Exiting (duration = %s)", end_ts - start_ts)


def delete_failed_projects(*args, **kwargs):
    """ Task """
    #
    with make_logger() as log:
        log.info("Starting")
        start_ts = time.time()
        #
        try:
            log.info("Getting project list")
            project_list = context.rpc_manager.timeout(120).project_list(
                filter_={"create_success": False},
            )
            #
            from plugins.projects.api.v1.project import delete_project
            from tools import this
            #
            for project in project_list:
                log.info("Deleting failed project: %s", project)
                #
                delete_project(
                    project_id=project["id"],
                    module=this.for_module("projects").module,
                )
        except:  # pylint: disable=W0702
            log.exception("Got exception, stopping")
        #
        end_ts = time.time()
        log.info("Exiting (duration = %s)", end_ts - start_ts)


def fix_personal_projects(*args, **kwargs):
    """ Task """
    #
    with make_logger() as log:
        log.info("Starting")
        start_ts = time.time()
        #
        try:
            log.info("Fixing personal projects")
            context.rpc_manager.timeout(3600).projects_fix_create_personal_projects()
        except:  # pylint: disable=W0702
            log.exception("Got exception, stopping task (on timeout RPC will continue)")
        #
        end_ts = time.time()
        log.info("Exiting (duration = %s)", end_ts - start_ts)


def sync_pgvector_credentials(*args, **kwargs):
    """ Task """
    #
    with make_logger() as log:
        log.info("Starting")
        start_ts = time.time()
        #
        try:
            log.info("Syncing pgvector credentials for projects")
            #
            param = kwargs.get("param", "")
            #
            force_recreate = "force_recreate" in param
            save_connstr_to_secrets = "save_connstr_to_secrets" in param
            #
            res = context.rpc_manager.timeout(5*60*60).applications_create_pgvector_credentials(
                save_connstr_to_secrets=save_connstr_to_secrets,
                force_recreate=force_recreate,
            )
            #
            log.info("Result: %s", res)
        except:  # pylint: disable=W0702
            log.exception("Got exception, stopping task (on timeout RPC will continue)")
        #
        end_ts = time.time()
        log.info("Exiting (duration = %s)", end_ts - start_ts)


def recreate_project_tokens(*args, **kwargs):
    """ Task """
    log.info("Getting project list")
    project_list = context.rpc_manager.timeout(120).project_list(
        filter_={"create_success": True},
    )
    #
    from plugins.projects.utils import get_project_user
    from tools import VaultClient, auth
    #
    for project in project_list:
        log.info("Recreating project token: %s", project)
        #
        project_id = int(project["id"])
        #
        user = get_project_user(project_id)
        user_id = user["id"]
        #
        log.info("- Project user: %s", user)
        #
        token_id = auth.add_token(user_id, "api")
        token = auth.encode_token(token_id)
        #
        log.info("- Setting token: %s", token_id)
        #
        vault_client = VaultClient(project_id)
        project_secrets = vault_client.get_secrets()
        project_secrets["auth_token"] = token
        vault_client.set_secrets(project_secrets)
        #
        log.info(" - Done")
