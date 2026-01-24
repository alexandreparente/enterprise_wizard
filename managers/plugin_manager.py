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

import pyplugin_installer
import qgis.utils

from .base_manager import BaseManager
from ..enterprise_wizard_util import tr


class PluginManager(BaseManager):
    """
    Manages installation of official QGIS Plugins via pyplugin_installer.
    """

    def __init__(self, config_root, divisoes, iface=None):
        # Calls parent init to configure config_root and divisions
        super().__init__(config_root, divisoes)
        self.iface = iface
        self.pyplugin = pyplugin_installer.instance()

    @property
    def label(self):
        return tr("Recommended Plugins")

    @property
    def description(self):
        return tr("Select official plugins for installation")

    # --- Discovery Logic Override

    def discover_items(self):
        found_ids = set()
        items = []

        for div_config in self.divisoes:
            # Normalize
            if isinstance(div_config, str):
                div_config = {'id': div_config, 'type': 'folder', 'path': div_config}

            div_id = div_config.get('name', div_config.get('id'))
            div_type = div_config.get('type', 'folder')

            plugins_list = []

            # Strategy 1: Local File
            if div_type == 'folder':
                path = div_config.get('path', div_config.get('id'))
                json_path = os.path.join(self.config_root, path, "lista_de_plugins.json")
                if os.path.isfile(json_path):
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            plugins_list = json.load(f)
                    except:
                        pass

            # Strategy 2: Manifest Key
            elif div_type in ('remote_manifest', 'local_manifest'):
                manifest = div_config.get('manifest_data', {})
                plugins_list = manifest.get('plugins', [])

            # Process List
            if isinstance(plugins_list, list):
                for plugin in plugins_list:
                    # Accepts ["plugin_id"] or [{"id":"...", "name":"..."}]
                    if isinstance(plugin, dict):
                        pid = plugin.get("id")
                        name = plugin.get("name", pid)
                    else:
                        pid = plugin
                        name = pid

                    if not pid or pid == "-": continue

                    if pid not in found_ids:
                        found_ids.add(pid)
                        items.append({
                            'id': pid,
                            'label': f"[{div_id}] {name} ({pid})",
                            'checked': False,
                            'collision_id': pid,
                            'is_remote': False  # Installing plugins is always "remote" via QGIS repo
                        })

        return sorted(items, key=lambda x: x['label'])

    # --- Installation Logic Override
    def install_items(self, items, log_callback, overwrite=False):
        # Tries to update repositories to ensure download works
        try:
            self.pyplugin.reloadAndExportData()
        except Exception as e:
            log_callback(f"[{tr('WARNING')}] {tr('Could not update repositories')}: {e}")

        # List of plugins already existing on the machine
        installed_plugins = qgis.utils.available_plugins

        for item in items:
            pid = item['id']
            is_installed = pid in installed_plugins

            # Check if already installed
            if is_installed:
                if not overwrite:
                    log_callback(f"[{tr('SKIPPED')}] Installed: {pid}")
                    continue
                else:
                    log_callback(f"[{tr('UPDATE')}] Updating: {pid}")

            try:
                # Official QGIS installation command
                self.pyplugin.installPlugin(pid)
                log_callback(f"[{tr('OK')}] Installed: {pid}")
            except Exception as e:
                log_callback(f"[{tr('ERROR')}] Failed {pid}: {e}")

    @property
    def show_overwrite_option(self):
        """Plugins geralmente gerenciam sua própria atualização, então ocultamos a opção."""
        return False
