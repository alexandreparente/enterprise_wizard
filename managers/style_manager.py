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

from qgis.core import QgsStyle

from .base_manager import BaseManager
from ..enterprise_wizard_util import tr


class StyleManager(BaseManager):
    """
    Manages the import of QGIS style files (.xml).
    """

    @property
    def label(self):
        return tr("Style Libraries")

    @property
    def description(self):
        return tr("Select XML style files for import")

    @property
    def destination_subfolder(self):
        return "styles"

    @property
    def allowed_extensions(self):
        return ('.xml',)

    def _install_action(self, source_path, final_path, item_data):
        """
        Imports XML into QGIS Style Database.
        """
        style = QgsStyle.defaultStyle()
        if not style:
            raise Exception("Could not access QGIS style library.")

        if not style.importXml(source_path):
            raise Exception("QGIS failed to import style XML")

        return True

    @property
    def show_overwrite_option(self):
        return False
