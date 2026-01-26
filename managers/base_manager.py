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

import os
import shutil
import tempfile
import zipfile
from abc import ABC, abstractmethod

import requests
from qgis.core import QgsApplication

from ..enterprise_wizard_util import (
    tr, format_resource_name, parse_remote_json, DOWNLOAD_MARKER,
    DIV_TYPE_FOLDER, DIV_TYPE_REMOTE_MANIFEST, DIV_TYPE_LOCAL_MANIFEST
)


class BaseManager(ABC):
    """
    Base class 'Batteries Included' for resource managers.
    """

    def __init__(self, config_root, divisoes=None):
        self.config_root = config_root
        self.divisoes = divisoes or []

    # --- Mandatory Properties ---
    @property
    @abstractmethod
    def label(self):
        pass

    @property
    @abstractmethod
    def description(self):
        pass

    # --- Configuration Properties ---
    @property
    def destination_subfolder(self):
        return None

    @property
    def source_subfolder(self):
        return self.destination_subfolder

    @property
    def json_section_name(self):
        """
        Defines the JSON key this manager listens to (e.g., 'fonts', 'styles').
        Defaults to the source_subfolder name.
        """
        return self.source_subfolder

    @property
    def allowed_extensions(self):
        return None

    # --- Label Customization ---
    def _generate_label(self, div_label, filename, source_path, is_remote, manifest_label=None):
        """
        Hook to customize how the item label is displayed.
        Subclasses can override this to read metadata from the file.
        """
        if is_remote and manifest_label:
            clean_name = manifest_label
        else:
            clean_name = format_resource_name(filename)

        marker = DOWNLOAD_MARKER if is_remote else ""
        return f"[{div_label}] {clean_name}{marker}"

    # --- Existence Check (New Hook) ---
    def _item_exists(self, final_path, item_data):
        """
        Checks if the item already exists in the destination.
        Default implementation checks for file existence on disk.
        Subclasses (like Connections) should override this to check QgsSettings.
        """
        # Only check file existence if we have a destination folder
        if self.destination_subfolder:
            return os.path.exists(final_path)
        return False

    # --- Installation Action ---
    def _install_action(self, source_path, final_path, item_data):
        """
        Hook to define HOW the file is installed.
        Default: Copy or Move the file to the destination folder.
        Subclasses (like Style/Font) can override this to import via API instead.
        """
        # Default behavior: File Copy
        if item_data.get('is_remote') and not item_data.get('is_zip'):
            # If it was a remote download (temp file)
            shutil.move(source_path, final_path)
        else:
            # Local file or extracted zip
            shutil.copy2(source_path, final_path)
        return True

    # --- Main Methods ---

    def discover_items(self):
        if not self.source_subfolder:
            return []

        all_items = []

        for div_config in self.divisoes:
            if isinstance(div_config, str):
                div_config = {'id': div_config, 'type': DIV_TYPE_FOLDER, 'path': div_config}

            div_id = div_config.get('id', 'unknown')
            div_name = div_config.get('name', div_id)
            div_type = div_config.get('type', DIV_TYPE_FOLDER)

            if div_type == DIV_TYPE_FOLDER:
                path_to_scan = div_config.get('path', div_id)
                items = self._discover_folder_items(div_name, path_to_scan)
                all_items.extend(items)

            elif div_type in (DIV_TYPE_REMOTE_MANIFEST, DIV_TYPE_LOCAL_MANIFEST):
                # Manifest data is expected to be a Dict with sections
                manifest_data = div_config.get('manifest_data', {})
                items = self._discover_manifest_items(div_name, manifest_data)
                all_items.extend(items)

        return sorted(all_items, key=lambda x: x['collision_id'])

    def _discover_folder_items(self, div_label, div_folder_name):
        items = []
        path = os.path.join(self.config_root, div_folder_name, self.source_subfolder)
        valid_exts = self.allowed_extensions

        if not os.path.isdir(path): return []

        for f in os.listdir(path):
            f_lower = f.lower()
            full_path = os.path.join(path, f)

            # 1. Physical Files
            if valid_exts and f_lower.endswith(valid_exts):
                label = self._generate_label(div_label, f, full_path, False)
                items.append({
                    'id': f"{div_label}::{f}",
                    'label': label,
                    'checked': False,
                    'source_path': full_path,
                    'collision_id': f,
                    'is_remote': False
                })

            # 2. JSON Manifests
            elif f_lower.endswith('.json'):
                remote_data = parse_remote_json(full_path)
                if not remote_data: continue

                # Validates against strict schema
                if isinstance(remote_data, list):
                    remote_data = {self.json_section_name: remote_data}

                items.extend(self._discover_manifest_items(div_label, remote_data))

        return items

    def _discover_manifest_items(self, div_label, manifest_dict):
        """
        Processes a manifest dict using the manager's section key.
        """
        items = []
        section_key = self.json_section_name

        if not isinstance(manifest_dict, dict): return []
        if section_key not in manifest_dict: return []

        raw_list = manifest_dict[section_key]

        for r in raw_list:
            url = r.get('download_url')
            label_text = r.get('name', 'Unnamed Resource')
            filename = r.get('filename')

            if not filename:
                filename = r.get('id', r.get('plugin_id'))
                is_zip_context = r.get('is_zip', False)
                if is_zip_context and filename and not filename.endswith('.zip'):
                    filename += ".zip"

            if not url or not filename:
                continue

            if self.allowed_extensions:
                is_zip = r.get('is_zip', filename.lower().endswith('.zip'))
                if not is_zip:
                    if not filename.lower().endswith(self.allowed_extensions):
                        continue

            final_label = self._generate_label(div_label, filename, url, True, label_text)

            items.append({
                'id': f"{div_label}::MANIFEST::{filename}",
                'label': final_label,
                'checked': False,
                'source_path': url,
                'collision_id': filename,
                'is_remote': True,
                'is_zip': r.get('is_zip', False)
            })
        return items

    def install_items(self, items, log_callback, overwrite=False):
        subfolder = self.destination_subfolder
        # Default destination (files).
        dest_dir = os.path.join(QgsApplication.qgisSettingsDirPath(), subfolder) if subfolder else ""
        if dest_dir: os.makedirs(dest_dir, exist_ok=True)

        for item in items:
            filename = item.get('collision_id')
            src = item.get('source_path')
            is_remote = item.get('is_remote', False)
            final_path = os.path.join(dest_dir, filename) if dest_dir else filename

            # 1. Check Existence (Polymorphic)
            if self._item_exists(final_path, item):
                if not overwrite:
                    log_callback(tr("[SKIPPED] Exists: %s") % filename)
                    continue
                else:
                    log_callback(tr("[OVERWRITE] Updating: %s") % filename)

            try:
                # 2. Download / Acquire Resource
                if is_remote:
                    log_callback(tr("[DOWNLOAD] Downloading: %s...") % filename)
                    temp_file = self._download_file(src)
                    source_to_use = temp_file
                else:
                    temp_file = None
                    source_to_use = src

                # 3. Detect ZIP (Flag OR Extension)
                is_zip_file = item.get('is_zip', False) or filename.lower().endswith('.zip')

                if is_zip_file:
                    with zipfile.ZipFile(source_to_use, 'r') as z:
                        if dest_dir: z.extractall(dest_dir)
                    log_callback(tr("[OK] Extracted: %s") % item['label'])
                else:
                    success = self._install_action(source_to_use, final_path, item)
                    if success:
                        log_callback(tr("[OK] Installed: %s") % item['label'])

                # Cleanup
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)

            except Exception as e:
                log_callback(tr("[ERROR] Failed to install %s: %s") % (filename, str(e)))

    def _download_file(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        r = requests.get(url, stream=True, timeout=30, headers=headers)
        r.raise_for_status()
        fd, temp_path = tempfile.mkstemp()
        with os.fdopen(fd, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        try:
            with open(temp_path, 'rb') as f:
                header = f.read(4)
                if header.startswith(b'<') or header.startswith(b'<!'):
                    with open(temp_path, 'r', encoding='utf-8', errors='ignore') as fr:
                        content_preview = fr.read(100)
                    os.remove(temp_path)
                    raise Exception(f"Server returned HTML/Error instead of file: {content_preview}")
        except Exception as e:
            if os.path.exists(temp_path): os.remove(temp_path)
            raise e

        return temp_path

    @property
    def requires_folder_input(self):
        return False

    def set_output_folder(self, folder_path):
        self.output_folder = folder_path

    @property
    def show_overwrite_option(self):
        return True