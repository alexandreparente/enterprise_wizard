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

from qgis.PyQt.QtCore import QTranslator, QCoreApplication, QSettings, QLocale
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu

from .enterprise_wizard_dialog import InstallerWizard
from .enterprise_wizard_util import tr  # Import translation function
from .managers.composer_templates_manager import ComposerTemplatesManager
# 2. Connections and Data
from .managers.connection_manager import (
    PostgresConnectionManager,
    WfsConnectionManager,
    WmsConnectionManager,
    XyzConnectionManager,
    ArcGisConnectionManager
)
from .managers.crs_manager import CrsManager
from .managers.expressions_manager import ExpressionsManager
from .managers.font_manager import FontManager
from .managers.kart_manager import KartManager
from .managers.models_manager import ModelsManager
from .managers.palette_manager import PaletteManager
# 3. Environment
from .managers.plugin_manager import PluginManager
from .managers.proj_manager import ProjManager
# 1. Visual Resources
from .managers.project_manager import ProjectManager
from .managers.style_manager import StyleManager
from .managers.svg_manager import SvgManager


class EnterpriseWizardPlugin:
    def __init__(self, iface):
        self.iface = iface
        # Path to configuration folder
        self.plugin_dir = os.path.dirname(__file__)
        self.config_root = os.path.join(self.plugin_dir, "divisions")

        # Localization Configuration (i18n)
        settings = QSettings()
        locale = settings.value("locale/userLocale", QLocale.system().name())
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'enterprise_wizard_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        # Main Menu Creation
        self.menu = QMenu(tr("Setup Wizard"), self.iface.mainWindow())
        self.iface.pluginMenu().addMenu(self.menu)

        # ACTION 1: Cartography and Styles
        self.action_cartography = QAction(QIcon(), tr("Cartography and Styles"), self.iface.mainWindow())
        self.action_cartography.triggered.connect(self.run_cartography)
        self.menu.addAction(self.action_cartography)

        # ACTION 2: Connectivity and Data
        self.action_datasources = QAction(QIcon(), tr("Connectivity and Data"), self.iface.mainWindow())
        self.action_datasources.triggered.connect(self.run_datasources)
        self.menu.addAction(self.action_datasources)

        # ACTION 3: Environment and Extensions
        self.action_environment = QAction(QIcon(), tr("Environment and Extensions"), self.iface.mainWindow())
        self.action_environment.triggered.connect(self.run_environment)
        self.menu.addAction(self.action_environment)

    def unload(self):
        self.iface.pluginMenu().removeAction(self.menu.menuAction())

    # --- EXECUTION CALLBACKS ---

    def run_cartography(self):
        """Flow 1: Visual and Aesthetic Resources"""
        managers = [
            StyleManager(self.config_root, []),
            SvgManager(self.config_root, []),
            FontManager(self.config_root, []),
            PaletteManager(self.config_root, []),
            ComposerTemplatesManager(self.config_root, [])
        ]
        self._open_dialog(managers, tr("Cartographic Resources"))

    def run_datasources(self):
        """Flow 2: All data sources"""
        managers = [
            PostgresConnectionManager(self.config_root, []),
            WfsConnectionManager(self.config_root, []),
            WmsConnectionManager(self.config_root, []),
            XyzConnectionManager(self.config_root, []),
            ArcGisConnectionManager(self.config_root, []),
            KartManager(self.config_root, [])
        ]
        self._open_dialog(managers, tr("Data Sources and Connections"))

    def run_environment(self):
        """Flow 3: System Configurations"""
        managers = [
            PluginManager(self.config_root, [], self.iface),
            CrsManager(self.config_root, []),
            ProjManager(self.config_root, []),
            ExpressionsManager(self.config_root, []),
            ModelsManager(self.config_root, []),
            ProjectManager(self.config_root, [])
        ]
        self._open_dialog(managers, tr("Environment and Extensions"))

    def _open_dialog(self, managers, title):
        """
        Helper method to open the Wizard.
        """
        wiz = InstallerWizard(self.config_root, managers, self.iface.mainWindow())
        wiz.setWindowTitle(title)
        wiz.exec_()