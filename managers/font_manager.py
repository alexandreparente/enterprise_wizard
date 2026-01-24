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

from qgis.core import QgsApplication

from .base_manager import BaseManager
from ..enterprise_wizard_util import tr


class FontManager(BaseManager):
    """
    Manages Font installation (TTF/OTF) using the native QgsFontManager API.
    """

    @property
    def label(self):
        return tr("Fonts")

    @property
    def description(self):
        return tr("Select fonts for installation")

    @property
    def destination_subfolder(self):
        return "fonts"

    @property
    def allowed_extensions(self):
        return (".ttf", ".otf", ".woff", ".woff2")

    def _install_action(self, source_path, final_path, item_data):
        """
        Loads font into memory via QGIS API instead of just copying.
        BaseManager has already handled the download (if remote)
        and passed the path here.
        """
        filename = item_data['collision_id']
        # Extract extension without dot (e.g. "ttf")
        extension = os.path.splitext(filename)[1].replace(".", "")

        try:
            with open(source_path, 'rb') as f:
                font_data = f.read()

            # API: installFontsFromData(data, fontFamily, extension)
            font_manager = QgsApplication.fontManager()
            result = font_manager.installFontsFromData(font_data, filename, extension)

            # result = (success, error_msg, families_list)
            if not result[0]:
                raise Exception(f"{tr('QGIS Error')}: {result[1]}")

            return True

        except Exception as e:
            # Re-raise to be caught and logged by BaseManager
            raise Exception(f"{tr('Font Load Error')}: {e}")

    @property
    def show_overwrite_option(self):
        return False
