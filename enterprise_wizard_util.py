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

from qgis.PyQt.QtCore import QCoreApplication

# --- Constants for Division Types ---
DIV_TYPE_FOLDER = "folder"
DIV_TYPE_REMOTE_MANIFEST = "remote_manifest"
DIV_TYPE_LOCAL_MANIFEST = "local_manifest"

# --- Visual Markers ---
DOWNLOAD_MARKER = " \u2B07"


def tr(string):
    """Translates a string using the default QGIS context"""
    return QCoreApplication.translate('@default', string)


def format_resource_name(filename):
    """
    Humanizes a filename for UI display:
    Example: 'my_template_v1.qpt' -> 'my template v1'
    """
    name = os.path.splitext(filename)[0]
    return name.replace("_", " ")


def parse_remote_json(json_path):
    """
    Loads a JSON file with STRICT rules.

    Allowed Formats:
    1. Dictionary (Standard): { "fonts": [...], "styles": [...] }
    2. Plugin List (Exception): [ {"plugin_id":...}, ... ] -> Converted to { "plugins": [...] }

    Any other format (e.g. flat list of fonts) is considered INVALID (Error).
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Case 1: Standard Dictionary
        if isinstance(data, dict):
            return data

        # Case 2: List (Strict Check)
        if isinstance(data, list):
            # Only allowed if it is a Plugin Exporter list (must have 'plugin_id')
            is_plugin_list = False
            for item in data:
                if isinstance(item, dict) and 'plugin_id' in item:
                    is_plugin_list = True
                    break

            if is_plugin_list:
                return {"plugins": data}

            # If it is a list but NOT plugins -> ERROR (Strict Mode)
            print(f"Ignored JSON {json_path}: Flat lists are only allowed for Plugins.")
            return None

        return None

    except Exception as e:
        print(f"Error parsing JSON {json_path}: {e}")
        return None