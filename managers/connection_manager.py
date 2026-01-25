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

import xml.etree.ElementTree as ET

from qgis.core import QgsSettings

from .base_manager import BaseManager
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

    # Generate Label
    def _generate_label(self, div_label, filename, source_path, is_remote, manifest_label=None):
        if is_remote and manifest_label:
            return super()._generate_label(div_label, filename, source_path, is_remote, manifest_label)

        conn_name = filename
        try:
            tree = ET.parse(source_path)
            root = tree.getroot()
            # Searches in allowed tags
            for tag in self.target_xml_tags:
                node = root if root.tag == tag else root.find(f".//{tag}")
                if node is not None and node.get('name'):
                    conn_name = node.get('name')
                    break
        except:
            pass

        return f"[{div_label}] {conn_name}"

    # Install ---
    def _install_action(self, source_path, final_path, item_data):
        try:
            tree = ET.parse(source_path)
            root = tree.getroot()

            # Finds elements
            elements = []
            for tag in self.target_xml_tags:
                if root.tag == tag:
                    elements.append(root)
                elements.extend(root.findall(f".//{tag}"))

            if not elements:
                raise Exception(f"No valid tags {self.target_xml_tags} found.")

            settings = QgsSettings()
            for elem in elements:
                name = elem.get('name')
                if not name: continue

                # Saves parameters
                self._save_to_settings(settings, name, elem.attrib)

            settings.sync()
            return True
        except Exception as e:
            raise Exception(f"Connection Error: {e}")

    def _save_to_settings(self, s, name, params):
        """
        Default save method
        """
        base = f"{self.settings_base_path}/{name}"
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

    # Defines which subfolder to scan: divisions/<division>/connections/postgis
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
        return "/qgis/connections-xyz"

    # XYZ has specific fields that need to be converted (int)
    def _save_to_settings(self, s, name, params):
        base = f"{self.settings_base_path}/{name}"
        s.setValue(f"{base}/url", params.get("url", ""))
        s.setValue(f"{base}/zmin", int(params.get("zmin", 0)))
        s.setValue(f"{base}/zmax", int(params.get("zmax", 22)))
        for key in ("authcfg", "username", "password", "referer"):
            if params.get(key): s.setValue(f"{base}/{key}", params.get(key))


class WfsConnectionManager(GenericConnectionManager):
    @property
    def label(self):
        return tr("WFS/OGC Connections")

    @property
    def description(self):
        return tr("WFS and WMS services")

    @property
    def source_subfolder(self):
        return "connections/wfs"

    @property
    def destination_subfolder(self):
        return None

    @property
    def target_xml_tags(self):
        return ["wfs", "wms", "ows"]

    @property
    def settings_base_path(self):
        return "/qgis/connections-wfs"

    def _save_to_settings(self, s, name, params):
        base = f"{self.settings_base_path}/{name}"
        s.setValue(f"{base}/url", params.get("url", ""))
        for key in ["authcfg", "username", "password", "ignoreURI"]:
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
        return "/qgis/connections-arcgisfeatureserver"

    def _save_to_settings(self, s, name, params):
        base = f"{self.settings_base_path}/{name}"
        s.setValue(f"{base}/url", params.get("url", ""))
        for key in ["authcfg", "username", "password"]:
            if params.get(key): s.setValue(f"{base}/{key}", params.get(key))