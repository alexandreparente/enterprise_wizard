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
import xml.etree.ElementTree as ET
from qgis.core import QgsSettings

from ..enterprise_wizard_base_manager import BaseManager
from ..enterprise_wizard_util import tr


class GenericConnectionManager(BaseManager):
    """
    Base logic for XML-based connections.
    Subclasses only need to define WHERE to look and WHERE to save.
    """

    @property
    def allowed_extensions(self):
        return ('.xml',)

    # --- Specific Configuration ---
    @property
    def target_xml_tags(self):
        """List of XML tags to search (e.g. ['postgis'])"""
        return []

    @property
    def settings_base_path(self):
        """Path in QgsSettings (e.g. '/PostgreSQL/connections')"""
        return ""

    def _get_settings_path(self, item_data=None):
        """
        Helper to determine the correct settings path.
        Returns the configured base path by default.
        """
        return self.settings_base_path

    # --- Discovery Override ---
    def _discover_folder_items(self, div_label, div_folder_name):
        """
        Overrides BaseManager logic.
        Instead of 1 File = 1 Item, we parse the XML and create 1 Item per Connection found.
        """
        items = []
        path = os.path.join(self.config_root, div_folder_name, self.source_subfolder)

        if not os.path.isdir(path):
            return []

        for f in os.listdir(path):
            if not f.lower().endswith(self.allowed_extensions):
                continue

            full_path = os.path.join(path, f)

            try:
                tree = ET.parse(full_path)
                root = tree.getroot()

                # Find all matching connection tags in the XML
                found_nodes = []
                for tag in self.target_xml_tags:
                    if root.tag == tag:
                        found_nodes.append(root)
                    found_nodes.extend(root.findall(f".//{tag}"))

                # Create an item for EACH connection found
                for node in found_nodes:
                    conn_name = node.get('name')
                    if not conn_name:
                        continue

                    conn_params = node.attrib
                    # Save the tag type (e.g., 'wms' or 'wfs') to decide destination later
                    conn_type = node.tag

                    label = f"[{div_label}] {conn_name}"

                    items.append({
                        'id': f"{div_label}::{f}::{conn_name}",
                        'label': label,
                        'checked': False,
                        'source_path': full_path,
                        'collision_id': conn_name,
                        'is_remote': False,
                        'connection_params': conn_params,
                        'connection_type': conn_type
                    })

            except Exception as e:
                print(f"Error parsing connection file {f}: {e}")
                continue

        return items

    # --- Existence Check Override (QgsSettings) ---
    def _item_exists(self, final_path, item_data):
        """
        Checks if the connection name already exists in QGIS Settings.
        """
        name = item_data.get('collision_id')
        if not name: return False

        target_path = self._get_settings_path(item_data)

        s = QgsSettings()
        s.beginGroup(target_path)
        existing_connections = s.childGroups()  # Returns list of connection names
        s.endGroup()

        return name in existing_connections

    # --- Installation Action ---
    def _install_action(self, source_path, final_path, item_data):
        try:
            params = item_data.get('connection_params')
            if not params:
                raise Exception("Missing connection parameters.")

            name = params.get('name')
            if not name:
                raise Exception("Connection has no name.")

            target_path = self._get_settings_path(item_data)

            settings = QgsSettings()
            self._save_to_settings(settings, name, params, target_path)
            settings.sync()

            return True
        except Exception as e:
            raise Exception(f"Connection Install Error: {e}")

    def _save_to_settings(self, s, name, params, base_path):
        """
        Default save method
        """
        base = f"{base_path}/{name}"
        for key, value in params.items():
            if key != "name": s.setValue(f"{base}/{key}", value)

    @property
    def show_overwrite_option(self):
        return True


# --- Page Configuration ---

class PostgresConnectionManager(GenericConnectionManager):
    @property
    def label(self): return tr("PostgreSQL Connections")

    @property
    def description(self): return tr("PostGIS databases")

    @property
    def source_subfolder(self): return "connections/postgis"

    @property
    def destination_subfolder(self): return None

    @property
    def target_xml_tags(self): return ["postgis", "postgresql"]

    @property
    def settings_base_path(self): return "/PostgreSQL/connections"


class XyzConnectionManager(GenericConnectionManager):
    @property
    def label(self):
        return tr("XYZ Tiles Connections")

    @property
    def description(self):
        return tr("Base maps (Google, OSM, etc)")

    @property
    def source_subfolder(self):
        return "connections/xyz"

    @property
    def destination_subfolder(self):
        return None

    @property
    def target_xml_tags(self):
        return ["xyztiles", "xyztile"]

    @property
    def settings_base_path(self):
        # Writes to the new structure for instant visibility
        return "/connections/xyz/items"

    def _item_exists(self, final_path, item_data):
        """
        OVERRIDE: Checks for existence in BOTH the new structure and the legacy path.
        """
        name = item_data.get('collision_id')
        if not name: return False

        possible_paths = [
            "/connections/xyz/items",  # New
            "/qgis/connections-xyz"  # Legacy
        ]

        s = QgsSettings()
        for path in possible_paths:
            s.beginGroup(path)
            existing = s.childGroups()
            s.endGroup()

            if name in existing:
                return True

        return False

    def _save_to_settings(self, s, name, params, base_path):
        base = f"{base_path}/{name}"
        s.setValue(f"{base}/url", params.get("url", ""))
        s.setValue(f"{base}/zmin", int(params.get("zmin", 0)))
        s.setValue(f"{base}/zmax", int(params.get("zmax", 22)))
        for key in ("authcfg", "username", "password", "referer"):
            if params.get(key): s.setValue(f"{base}/{key}", params.get(key))


class WfsConnectionManager(GenericConnectionManager):
    @property
    def label(self):
        return tr("WFS Connections (Vector)")

    @property
    def description(self):
        return tr("WFS/OGC Vector Services")

    @property
    def source_subfolder(self):
        return "connections/wfs"

    @property
    def destination_subfolder(self):
        return None

    @property
    def target_xml_tags(self):
        return ["wfs"]

    @property
    def settings_base_path(self):
        # New structure for wfs
        return "/connections/ows/items/wfs/connections/items"

    def _item_exists(self, final_path, item_data):
        """
        OVERRIDE: Check New and Legacy paths.
        """
        name = item_data.get('collision_id')
        if not name: return False

        possible_paths = [
            "/connections/ows/items/wfs/connections/items",  # New
            "/qgis/connections-wfs"  # Legacy
        ]

        s = QgsSettings()
        for path in possible_paths:
            s.beginGroup(path)
            existing = s.childGroups()
            s.endGroup()

            if name in existing:
                return True
        return False

    def _save_to_settings(self, s, name, params, base_path):
        base = f"{base_path}/{name}"
        s.setValue(f"{base}/url", params.get("url", ""))
        for key in ["authcfg", "username", "password", "ignoreURI"]:
            if params.get(key): s.setValue(f"{base}/{key}", params.get(key))


class WmsConnectionManager(GenericConnectionManager):
    @property
    def label(self):
        return tr("WMS/WMTS Connections (Raster)")

    @property
    def description(self):
        return tr("WMS, WMTS and OGC Raster Services")

    @property
    def source_subfolder(self):
        return "connections/wms"

    @property
    def destination_subfolder(self):
        return None

    @property
    def target_xml_tags(self):
        return ["wms"]

    @property
    def settings_base_path(self):
        # New structure for WMS
        return "/connections/ows/items/wms/connections/items"

    def _item_exists(self, final_path, item_data):
        """
        OVERRIDE: Check New and Legacy paths.
        """
        name = item_data.get('collision_id')
        if not name: return False

        possible_paths = [
            "/connections/ows/items/wms/connections/items",  # New
            "/qgis/connections-wms"  # Legacy
        ]

        s = QgsSettings()
        for path in possible_paths:
            s.beginGroup(path)
            existing = s.childGroups()
            s.endGroup()

            if name in existing:
                return True
        return False

    def _save_to_settings(self, s, name, params, base_path):
        base = f"{base_path}/{name}"
        s.setValue(f"{base}/url", params.get("url", ""))
        for key in ["authcfg", "username", "password", "ignoreURI", "referer"]:
            if params.get(key): s.setValue(f"{base}/{key}", params.get(key))


class ArcGisConnectionManager(GenericConnectionManager):
    @property
    def label(self):
        return tr("ArcGIS Server Connections")

    @property
    def description(self):
        return tr("ArcGIS Feature Server")

    @property
    def source_subfolder(self):
        return "connections/arcgis"

    @property
    def destination_subfolder(self):
        return None

    @property
    def target_xml_tags(self):
        return ["arcgisfeatureserver", "rest"]

    @property
    def settings_base_path(self):
        # New structure for arcgisfeatureserver
        return "/connections/arcgisfeatureserver/items"

    def _item_exists(self, final_path, item_data):
        name = item_data.get('collision_id')
        if not name: return False

        # Check New and Legacy
        possible_paths = [
            "/connections/arcgisfeatureserver/items",  # New
            "/qgis/connections-arcgisfeatureserver"  # Legacy
        ]
        s = QgsSettings()
        for path in possible_paths:
            s.beginGroup(path)
            if name in s.childGroups(): return True
        return False

    def _save_to_settings(self, s, name, params, base_path):
        base = f"{base_path}/{name}"
        s.setValue(f"{base}/url", params.get("url", ""))
        for key in ["authcfg", "username", "password"]:
            if params.get(key): s.setValue(f"{base}/{key}", params.get(key))
