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

""" 
Task to list available database backups

This module provides functionality to list available database backups.

To use this task:
1. Go to Admin -> Tasks
2. Select "list_backups" from the dropdown
3. No parameters are required
4. Click "Start task"

The task will:
- List all available backups in the configured backup directory
- Return backup details including timestamps and available schemas
"""

import os
import time
import json
import datetime

from tools import context  # pylint: disable=E0401
from tools import config as c  # pylint: disable=E0401

from .logs import make_logger


# Configure backup location - can be overridden in config
DEFAULT_BACKUP_DIR = "/opt/carrier/backup"


def list_backups(*args, **kwargs):  # pylint: disable=R0914
    """ Task to list available database backups """
    #
    with make_logger() as log:
        log.info("Listing available database backups")
        start_ts = time.time()
        #
        try:
            # Get backup directory from config or use default
            backup_dir = getattr(c, "BACKUP_DIR", DEFAULT_BACKUP_DIR)
            
            # Check if backup directory exists
            if not os.path.isdir(backup_dir):
                log.error("Backup directory does not exist: %s", backup_dir)
                return {
                    "status": "error",
                    "error": f"Backup directory not found: {backup_dir}"
                }
            
            # Find manifest files
            manifests = []
            for filename in os.listdir(backup_dir):
                if filename.startswith("backup_manifest_") and filename.endswith(".json"):
                    manifest_path = os.path.join(backup_dir, filename)
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest_data = json.load(f)
                            timestamp = manifest_data.get("timestamp")
                            if timestamp:
                                # Parse the timestamp to format a readable date
                                try:
                                    dt = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                                    readable_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                                except ValueError:
                                    readable_date = timestamp
                                
                                # Get the schemas in this backup
                                schemas = list(manifest_data.get("backups", {}).keys())
                                
                                # Check that backup files exist
                                valid_backup = True
                                for schema, backup_info in manifest_data.get("backups", {}).items():
                                    if not os.path.exists(backup_info.get("filepath", "")):
                                        log.warning("Backup file missing for %s in manifest %s", schema, filename)
                                        valid_backup = False
                                
                                # Add to list if valid
                                if valid_backup:
                                    manifests.append({
                                        "timestamp": timestamp,
                                        "date": readable_date,
                                        "schemas": schemas,
                                        "manifest_path": manifest_path,
                                        "valid": True
                                    })
                                else:
                                    log.warning("Skipping invalid backup manifest: %s", filename)
                    except Exception as e:  # pylint: disable=W0703
                        log.error("Error reading manifest file %s: %s", filename, str(e))
            
            # Sort manifests by timestamp (newest first)
            manifests.sort(key=lambda x: x["timestamp"], reverse=True)
            
            log.info("Found %d valid backup manifests", len(manifests))
            return {
                "status": "success",
                "backups": manifests
            }
            
        except Exception as exc:  # pylint: disable=W0703
            log.exception("Got exception listing backups: %s", str(exc))
            return {
                "status": "error",
                "error": str(exc)
            }
        finally:
            end_ts = time.time()
            log.info("Exiting (duration = %s)", end_ts - start_ts)
