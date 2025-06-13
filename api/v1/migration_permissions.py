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
import asyncio
from collections import defaultdict
from typing import List, Dict, Set, Tuple, Any
from functools import lru_cache

from pylon.core.tools import log  # pylint: disable=E0611,E0401,W0611

from tools import auth  # pylint: disable=E0401
from tools import api_tools  # pylint: disable=E0401
from tools import VaultClient  # pylint: disable=E0401,C0415
from tools import config as c  # pylint: disable=E0401,C0415
from tools import this  # pylint: disable=E0401,C0415


DEFAULT_CONCURRENT_TASKS: int = 20


@lru_cache(maxsize=128)
def get_project_ids(mode: str, personal_project_ids: Tuple[int, ...]) -> List[int]:
    """Get project IDs based on mode and personal project IDs."""
    personal_project_ids = tuple(personal_project_ids)  # Convert to tuple for caching
    if mode in ["add_user_project_defaults", "add_user_project_permissions", "delete_user_project_permissions"]:
        return list(personal_project_ids)
    elif mode in ["add_team_project_defaults", "add_team_project_permissions", "delete_team_project_permissions"]:
        secrets = VaultClient().get_all_secrets()
        ai_project_id = secrets.get('ai_project_id')
        if ai_project_id:
            ai_project_id = int(ai_project_id)
        return [
            i['id']
            for i in this.context.rpc_manager.call.project_list()
            if (i['id'] not in personal_project_ids) and (i['id'] != ai_project_id)
        ]
    elif mode in ["add_public_project_defaults", "add_public_project_permissions", "delete_public_project_permissions"]:
        secrets = VaultClient().get_all_secrets()
        ai_project_id = secrets.get('ai_project_id')
        if ai_project_id:
            ai_project_id = int(ai_project_id)
        return [ai_project_id]
    return []


def build_role_map(roles: List[Dict], permissions: List[Dict]) -> Dict[str, List[str]]:
    """Build a role map from roles and permissions."""
    role_map = {}
    for item in roles:
        role_map[item["name"]] = set()
    for item in permissions:
        role_map[item["name"]].add(item["permission"])
    for item in roles:
        role_map[item["name"]] = list(role_map[item["name"]])
        role_map[item["name"]].sort()
    return role_map


def parse_permission_items(permission_items: str) -> List[Tuple[str, List[str]]]:
    """Parse permission items from string format."""
    input_permissions = []
    for item in permission_items.strip().splitlines():
        permission, roles = item.split(":", 1)
        roles = roles.split(",")
        input_permissions.append((permission, roles))
    return input_permissions


async def process_projects(
        project_ids: List[int],
        process_func: callable,
        concurrent_tasks: int = DEFAULT_CONCURRENT_TASKS
) -> Dict[int, Dict]:
    """Process projects with controlled concurrency."""
    result = defaultdict(dict)
    result_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(concurrent_tasks)

    async def process_with_semaphore(project_id: int) -> None:
        async with semaphore:
            try:
                project_result = await process_func(project_id)
                async with result_lock:
                    result[project_id].update(project_result)
            except Exception as e:
                async with result_lock:
                    result[project_id]['status'] = 'error'
                    result[project_id]['message'] = str(e)
                log.exception('Error processing project')

    # Process all projects concurrently with controlled concurrency
    tasks = [process_with_semaphore(pid) for pid in project_ids]
    await asyncio.gather(*tasks)
    
    return dict(result)


class AdminAPI(api_tools.APIModeHandler):  # pylint: disable=R0903
    """ API """

    @auth.decorators.check_api(["migration.permissions"])
    def post(self):  # pylint: disable=R0912,R0914,R0915
        """ Process POST """
        data = flask.request.get_json()
        mode = data.get("mode", "unknown")
        concurrent_tasks: int = int(data.get('concurrent_tasks', DEFAULT_CONCURRENT_TASKS))
        #
        logs = []
        result = dict()
        #
        if mode in [
                "add_user_project_defaults",
                "add_team_project_defaults",
                "add_public_project_defaults",
        ]:
            #
            # Build default role map
            #
            default_project_roles = auth.get_roles(mode="default")
            default_project_permissions = auth.get_permissions(mode="default")
            default_role_map = build_role_map(default_project_roles, default_project_permissions)
            #
            # Get projects
            #
            personal_project_ids = \
                self.module.context.rpc_manager.call.projects_get_personal_project_ids()
            #
            if not personal_project_ids:
                return {"error": "Personal projects not set"}, 400
            #
            project_ids = get_project_ids(mode, tuple(personal_project_ids))

            async def process_project(project_id: int) -> Dict:
                # Build project role map
                project_roles = self.module.get_roles(project_id)
                project_permissions = self.module.get_permissions(project_id)
                project_role_map = build_role_map(project_roles, project_permissions)
                #
                # Diff
                missing_roles = []
                missing_permissions = []
                #
                for role, permissions in default_role_map.items():
                    if role not in project_role_map:
                        missing_roles.append(role)
                    #
                    role_permissions = project_role_map.get(role, [])
                    #
                    for permission in permissions:
                        if permission not in role_permissions:
                            missing_permissions.append({"role": role, "permission": permission})
                #
                project_log = f"Project {project_id}: {missing_roles=} {missing_permissions=}"
                #
                # Apply
                if missing_roles:
                    try:
                        self.module.context.rpc_manager.call.admin_add_role(
                            project_id, missing_roles
                        )
                    except:  # pylint: disable=W0702
                        log.exception("Failed to add missing roles")
                        project_log += "\n> Failed to add missing roles"
                #
                for permission in missing_permissions:
                    try:
                        self.module.context.rpc_manager.call.admin_set_permission_for_role(
                            project_id, permission["role"], permission["permission"]
                        )
                    except:  # pylint: disable=W0702
                        log.exception(
                            "Failed to add missing permission: %s:%s",
                            permission["role"], permission["permission"],
                        )
                        #
                        l_role = permission["role"]
                        l_perm = permission["permission"]
                        #
                        project_log += f"\n> Failed to add missing permission: {l_role}:{l_perm}"

                return {
                    'status': 'success',
                    'log': project_log
                }

            # Process projects with controlled concurrency
            result = asyncio.run(process_projects(
                project_ids=project_ids,
                process_func=process_project,
                concurrent_tasks=concurrent_tasks
            ))

            # Collect logs
            logs.extend([result[pid]['log'] for pid in project_ids if pid in result])

        elif mode in [  # pylint: disable=R1702
                "add_user_project_permissions",
                "add_team_project_permissions",
                "add_public_project_permissions",
                "delete_user_project_permissions",
                "delete_team_project_permissions",
                "delete_public_project_permissions",
        ]:
            #
            # Parse input permissions
            #
            permission_items = data.get("permissions", "").strip()
            input_permissions = parse_permission_items(permission_items)
            #
            # Get projects
            #
            personal_project_ids = \
                self.module.context.rpc_manager.call.projects_get_personal_project_ids()
            #
            if not personal_project_ids:
                return {"error": "Personal projects not set"}, 400
            #
            project_ids = get_project_ids(mode, tuple(personal_project_ids))

            async def process_project(project_id: int) -> Dict:
                # Build project role map
                project_roles = self.module.get_roles(project_id)
                project_permissions = self.module.get_permissions(project_id)
                project_role_map = build_role_map(project_roles, project_permissions)
                #
                # Perform
                if mode in [
                        "add_user_project_permissions",
                        "add_team_project_permissions",
                        "add_public_project_permissions",
                ]:
                    #
                    # Diff
                    missing_roles = []
                    missing_permissions = []
                    #
                    for permission, roles in input_permissions:
                        for role in roles:
                            if role not in project_role_map:
                                missing_roles.append(role)
                            #
                            role_permissions = project_role_map.get(role, [])
                            #
                            if permission not in role_permissions:
                                missing_permissions.append({"role": role, "permission": permission})
                    #
                    project_log = f"Project {project_id}: {missing_roles=} {missing_permissions=}"
                    #
                    # Apply
                    if missing_roles:
                        self.module.context.rpc_manager.call.admin_add_role(
                            project_id, missing_roles
                        )
                    #
                    for permission in missing_permissions:
                        self.module.context.rpc_manager.call.admin_set_permission_for_role(
                            project_id, permission["role"], permission["permission"]
                        )

                elif mode in [
                        "delete_user_project_permissions",
                        "delete_team_project_permissions",
                        "delete_public_project_permissions",
                ]:
                    #
                    # Data
                    removed_permissions = []
                    #
                    # Apply
                    for permission, roles in input_permissions:
                        for role in roles:
                            if role not in project_role_map:
                                continue
                            #
                            role_permissions = project_role_map.get(role, [])
                            #
                            if permission in role_permissions:
                                self.module.context.rpc_manager.call.admin_remove_permission_from_role(  # pylint: disable=C0301
                                    project_id, role, permission
                                )
                                removed_permissions.append(f"{role}:{permission}")
                    #
                    # Log
                    project_log = f"Project {project_id}: {removed_permissions=}"

                return {
                    'status': 'success',
                    'log': project_log
                }

            # Process projects with controlled concurrency
            result = asyncio.run(process_projects(
                project_ids=project_ids,
                process_func=process_project,
                concurrent_tasks=concurrent_tasks
            ))

            # Collect logs
            logs.extend([result[pid]['log'] for pid in project_ids if pid in result])

        else:
            logs.append(f"Current mode: {mode}")
        #
        return {
            "ok": True,
            "logs": "\n".join(logs),
            "result": result
        }


class API(api_tools.APIBase):
    url_params = api_tools.with_modes([
        '',
    ])

    mode_handlers = {
        c.ADMINISTRATION_MODE: AdminAPI,
    }
