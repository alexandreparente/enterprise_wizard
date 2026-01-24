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

from .base_manager import BaseManager
from ..enterprise_wizard_util import tr


class ModelsManager(BaseManager):
    """
    Manages the installation of QGIS Graphical Models (.model3).
    """

    @property
    def label(self):
        return tr("Processing Models")

    @property
    def description(self):
        return tr("Select models (.model3) to add to the Processing Toolbox")

    @property
    def destination_subfolder(self):
        """
        Defines the relative path in the user profile:
        .../profiles/default/processing/models
        """
        return "processing/models"

    @property
    def allowed_extensions(self):
        """
        Filters QGIS 3 model files.
        """
        return ('.model3', '.model')
