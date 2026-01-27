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
from qgis.core import QgsCoordinateReferenceSystem, QgsApplication
from pyproj import CRS

from .base_manager import BaseManager
from ..enterprise_wizard_util import tr


class CrsManager(BaseManager):

    @property
    def label(self):
        return tr("Reference Systems (CRS)")

    @property
    def description(self):
        return tr("Select custom projections (WKT) for installation")

    @property
    def source_subfolder(self):
        return "crs"

    @property
    def destination_subfolder(self):
        return None

    @property
    def allowed_extensions(self):
        return ('.wkt', '.json')

    # User Space Collision Detection
    def _item_exists(self, final_path, item_data):
        """
        Checks if the CRS already exists in the QGIS User Database (qgis.db).
        """

        target_name = None

        # 1. Remote or manifest CRS -> use technical name already cleaned
        if item_data.get('is_remote'):
            target_name = item_data.get('name')

        # 2. Local CRS -> extract technical name via pyproj
        else:
            source_path = item_data.get('source_path')
            if source_path and os.path.exists(source_path):
                try:
                    with open(source_path, 'r', encoding='utf-8') as f:
                        target_name = CRS.from_user_input(f.read().strip()).name
                except Exception:
                    return False

        if not target_name:
            return False

        # 3. Check for user CRS in the registry
        registry = QgsApplication.coordinateReferenceSystemRegistry()

        return any(
            details.name == target_name
            for details in registry.userCrsList()
        )

    def _generate_label(self, div_label, filename, source_path, is_remote, manifest_label=None):
        """
        Reads WKT content to extract pretty name if file is local.
        """
        if is_remote:
            return super()._generate_label(div_label, filename, source_path, is_remote, manifest_label)

        display_name = filename
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                tech_name = CRS.from_user_input(f.read().strip()).name
                if tech_name:
                    display_name = tech_name
        except Exception:
            pass

        return f"[{div_label}] {display_name}"


    def _remove_existing_user_crs(self, crs_name):
        """
        Removes an existing user CRS by name.
        """
        registry = QgsApplication.coordinateReferenceSystemRegistry()

        for details in registry.userCrsList():
            if details.name == crs_name:
                # The identifier for removal is details.id
                registry.removeUserCrs(details.id)
                return True

        return False


    def _install_action(self, source_path, final_path, item_data):
        """
        Receives the local path (or downloaded temp path) and installs CRS.
        """
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                proj_data = f.read().strip()

            proj = CRS.from_user_input(proj_data)

            if not proj.name:
                raise Exception(tr("The CRS file lacks an internal name."))

            # Overwrite (remove/install)
            if item_data.get('overwrite'):
                self._remove_existing_user_crs(proj.name)

            crs = QgsCoordinateReferenceSystem()
            crs.createFromWkt(proj.to_wkt())

            if not crs.isValid():
                raise Exception(tr("Invalid CRS definition"))

            res = crs.saveAsUserCrs(proj.name)

            if res == -1:
                raise Exception(tr("QGIS API failed to save CRS"))

            return True

        except Exception as e:
            # Re-raise to be caught by BaseManager logger
            raise Exception(f"CRS Error: {e}")

    @property
    def show_overwrite_option(self):
        return True
