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


class ComposerTemplatesManager(BaseManager):

    @property
    def label(self):
        return tr("Print Layout Templates")

    @property
    def description(self):
        return tr("Select print layout templates (.qpt) for installation")

    @property
    def destination_subfolder(self):
        """
        Defines the destination and source folder as 'composer_templates'.
        Searches in: divisions/<division>/composer_templates
        Installs in: .../profiles/default/composer_templates
        """
        return "composer_templates"

    @property
    def allowed_extensions(self):
        """
        Filters only files with .qpt extension (QGIS Print Template)
        """
        return ('.qpt',)
