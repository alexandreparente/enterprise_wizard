# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Enterprise Setup Wizard
                                 A QGIS plugin
 Installs standard enterprise resources, models, and connections for QGIS.
                              -------------------
        begin                : 2026-01-22
        copyright            : (C) 2026 by Alexandre Parente Lima
        email                : alexandre.parente@gmail.com
 ***************************************************************************/

/***************************************************************************
 * *
 * This program is free software; you can redistribute it and/or modify  *
 * it under the terms of the GNU General Public License as published by  *
 * the Free Software Foundation; either version 2 of the License, or     *
 * (at your option) any later version.                                   *
 * *
 ***************************************************************************/
"""

__author__ = 'Alexandre Parente Lima'
__date__ = '2026-01-22'
__copyright__ = '(C) 2026 by Alexandre Parente Lima'

import json
import os
import shutil
import stat
import subprocess
import sys

from .base_manager import BaseManager
from ..enterprise_wizard_util import (
    tr,
    DIV_TYPE_FOLDER, DIV_TYPE_REMOTE_MANIFEST, DIV_TYPE_LOCAL_MANIFEST
)

class KartManager(BaseManager):
    """
    Unified Manager: Installs Bases (Kart) and Projects (Git).
    """

    @property
    def label(self):
        return tr("Kart Bases and Projects")

    @property
    def description(self):
        return tr("Select resources to clone (Git/Kart).")

    @property
    def requires_folder_input(self):
        return True

    def discover_items(self):
        items = []

        for div_config in self.divisoes:
            if isinstance(div_config, str):
                div_config = {'id': div_config, 'type': DIV_TYPE_FOLDER, 'path': div_config}

            div_id = div_config.get('name', div_config.get('id'))
            div_type = div_config.get('type', DIV_TYPE_FOLDER)

            repo_list = []

            # --- STRATEGY 1: Local Folder ---
            if div_type == DIV_TYPE_FOLDER:
                path_ref = div_config.get('path', div_config.get('id'))
                json_path = os.path.join(self.config_root, path_ref, "kart", "repositorios_kart.json")
                if os.path.isfile(json_path):
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            repo_list = json.load(f)
                    except:
                        pass

            # --- STRATEGY 2: Manifest ---
            elif div_type in (DIV_TYPE_REMOTE_MANIFEST, DIV_TYPE_LOCAL_MANIFEST):
                manifest = div_config.get('manifest_data', {})
                repo_list = manifest.get('repositories', [])

            if isinstance(repo_list, list):
                for entry in repo_list:
                    name = entry.get('name', 'Unnamed')
                    folder_name = entry.get('folder_name', 'default_workspace')

                    if "kart" in entry:
                        unique_id = f"{div_id}::{folder_name}::kart"
                        items.append({
                            'id': unique_id,
                            'label': f"[{div_id}] {tr('Data')}: {name}",
                            'checked': False,
                            'action_type': 'kart',
                            'repo_info': entry['kart'],
                            'workspace_name': folder_name,
                            'collision_id': f"{div_id}_{folder_name}_1_kart"
                        })

                    if "git" in entry:
                        unique_id = f"{div_id}::{folder_name}::git"
                        items.append({
                            'id': unique_id,
                            'label': f"[{div_id}] {tr('Project')}: {name}",
                            'checked': False,
                            'action_type': 'git',
                            'repo_info': entry['git'],
                            'workspace_name': folder_name,
                            'collision_id': f"{div_id}_{folder_name}_2_git"
                        })

        return sorted(items, key=lambda x: x['collision_id'])

    def install_items(self, items, log_callback, overwrite=False):
        root_folder = self.output_folder or os.path.join(os.path.expanduser("~"), "Kart")
        os.makedirs(root_folder, exist_ok=True)

        for item in items:
            action_type = item['action_type']
            repo_info = item['repo_info']
            workspace_name = item['workspace_name']

            workspace_path = os.path.join(root_folder, workspace_name)
            os.makedirs(workspace_path, exist_ok=True)

            url = repo_info.get('url')
            target_subfolder = repo_info.get('target_dir', 'data')

            if action_type == 'kart':
                self._clone_repo("Kart", url, target_subfolder, workspace_path, log_callback, overwrite)
            elif action_type == 'git':
                self._clone_repo("Git", url, target_subfolder, workspace_path, log_callback, overwrite)

    def _clone_repo(self, tool_name, repo_url, target_dir_name, parent_path, log_callback, overwrite=False):
        tool_exe = shutil.which(tool_name.lower())

        if not tool_exe and tool_name.lower() == 'kart':
            pass  # Logic to handle kart path if needed

        if not tool_exe:
            log_callback(f"[{tr('ERROR')}] '{tool_name}' {tr('not found.')}")
            return

        final_path = os.path.join(parent_path, target_dir_name)

        if os.path.exists(final_path) and os.listdir(final_path):
            if not overwrite:
                log_callback(f"[{tr('SKIPPED')}] Exists: {target_dir_name}")
                return
            else:
                log_callback(f"[{tr('OVERWRITE')}] Updating: {target_dir_name}")
                try:
                    def remove_readonly(func, path, _):
                        os.chmod(path, stat.S_IWRITE)
                        func(path)

                    shutil.rmtree(final_path, onerror=remove_readonly)
                except Exception as e:
                    log_callback(f"[{tr('ERROR')}] Failed cleanup: {e}")
                    return

        try:
            cmd = [tool_exe, "clone", repo_url, final_path]
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo
            )

            if proc.returncode == 0:
                log_callback(f"[{tr('OK')}] {tool_name} cloned: {target_dir_name}")
            else:
                clean_err = proc.stderr.strip() or proc.stdout.strip()
                log_callback(f"[{tr('ERROR')}] {tool_name} failed: {clean_err}")

        except Exception as e:
            log_callback(f"[{tr('EXCEPTION')}] {e}")

    @property
    def show_overwrite_option(self):
        return False
