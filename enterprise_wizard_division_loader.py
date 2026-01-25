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

import requests

from .enterprise_wizard_util import (
    DIV_TYPE_FOLDER,
    DIV_TYPE_REMOTE_MANIFEST,
    DIV_TYPE_LOCAL_MANIFEST
)


class DivisionLoader:
    """
    Responsible for enriching division configurations.
    Handles network requests (Lazy Loading) and local file parsing.
    """

    def __init__(self, config_root):
        self.config_root = config_root

    def enrich_config(self, config):
        """
        Analyzes the divisions dictionary and injects 'manifest_data' if necessary.
        Raises Exceptions if loading fails, to be caught by the UI.
        Modifies the dictionary in-place.
        """
        div_type = config.get('type', DIV_TYPE_FOLDER)

        # Optimization: If data is already loaded, skip
        if 'manifest_data' in config:
            return

        if div_type == DIV_TYPE_REMOTE_MANIFEST:
            self._load_remote(config)

        elif div_type == DIV_TYPE_LOCAL_MANIFEST:
            self._load_local(config)

    def _load_remote(self, config):
        url = config.get('url')
        if not url:
            raise ValueError(f"Remote division '{config.get('name')}' is missing 'url'.")

        try:
            # 10s timeout prevents freezing QGIS forever
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                config['manifest_data'] = response.json()
            else:
                raise ConnectionError(f"HTTP Error {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Network error: {str(e)}")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from server.")

    def _load_local(self, config):
        path_ref = config.get('path')
        if not path_ref:
            raise ValueError(f"Local manifest '{config.get('name')}' is missing 'path'.")

        full_path = os.path.join(self.config_root, path_ref)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Manifest file not found: {path_ref}")

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                config['manifest_data'] = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in local file: {path_ref}")
        except Exception as e:
            raise RuntimeError(f"Error reading file: {str(e)}")
