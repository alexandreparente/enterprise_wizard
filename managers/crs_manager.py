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

import re

from qgis.core import QgsCoordinateReferenceSystem

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
    def destination_subfolder(self):
        return "crs"

    @property
    def allowed_extensions(self):
        return ('.wkt',)

    def _generate_label(self, div_label, filename, source_path, is_remote, manifest_label=None):
        """
        Reads WKT content to extract pretty name if file is local.
        """
        if is_remote:
            return super()._generate_label(div_label, filename, source_path, is_remote, manifest_label)

        crs_name = filename
        try:
            name_pattern = re.compile(r'^\w+\["([^"]+)"')
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                match = name_pattern.search(content)
                if match: crs_name = match.group(1)
        except:
            pass

        return f"[{div_label}] {crs_name}"

    # --- Custom Install Action ---
    def _install_action(self, source_path, final_path, item_data):
        """
        Receives the local path (or downloaded temp path) and installs CRS.
        """
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                wkt = f.read().strip()

            crs = QgsCoordinateReferenceSystem()
            crs.createFromWkt(wkt)

            if not crs.isValid():
                raise Exception("Invalid WKT definition")

            final_name = item_data['collision_id']
            res = crs.saveAsUserCrs(final_name)

            if res == -1: raise Exception("QGIS API failed to save CRS")
            return True

        except Exception as e:
            # Re-raise to be caught by BaseManager logger
            raise Exception(f"CRS Error: {e}")

    @property
    def show_overwrite_option(self):
        return True
