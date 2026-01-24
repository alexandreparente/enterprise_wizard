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

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QTextCursor
from qgis.PyQt.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel,
    QTextBrowser, QMessageBox, QLineEdit,
    QFileDialog, QPushButton, QApplication, QCheckBox
)

from .enterprise_wizard_division_loader import DivisionLoader
from .enterprise_wizard_util import (
    tr, format_resource_name,
    DIV_TYPE_FOLDER, DIV_TYPE_REMOTE_MANIFEST, DOWNLOAD_MARKER
)


class InstallerWizard(QWizard):
    """
    Installation Wizard.
    Flow: Divisions -> Managers (Dynamic) -> Summary -> Installation.
    """

    def __init__(self, config_root, managers, parent=None):
        super().__init__(parent)
        self.config_root = config_root
        self.managers = managers
        self.active_managers_map = {}

        self.setWindowTitle(tr("Enterprise Setup Wizard"))
        self.setWizardStyle(QWizard.ModernStyle)
        self.resize(700, 500)

        self.setButtonText(QWizard.BackButton, tr("Back"))
        self.setButtonText(QWizard.NextButton, tr("Next"))
        self.setButtonText(QWizard.CancelButton, tr("Cancel"))
        self.setButtonText(QWizard.FinishButton, tr("Close"))
        self.setOption(QWizard.NoCancelButton, False)

        self.PAGE_INTRO = 0
        self.PAGE_RESUMO = 1000
        self.PAGE_INSTALL = 1001

        self.currentIdChanged.connect(self._handle_page_change)

        self.intro_page = PageDivisoes(self)
        self.setPage(self.PAGE_INTRO, self.intro_page)

        self.manager_pages = []
        for i, mgr in enumerate(self.managers):
            page_id = i + 1
            page = PageManager(mgr, self)
            self.setPage(page_id, page)
            self.manager_pages.append(page)

        self.setPage(self.PAGE_RESUMO, PageResumo(self))
        self.setPage(self.PAGE_INSTALL, PageInstalacao(self))

    def _handle_page_change(self, page_id):
        if page_id == self.PAGE_RESUMO:
            self.setButtonText(QWizard.NextButton, tr("Install"))
        elif page_id == self.PAGE_INSTALL:
            pass
        else:
            self.setButtonText(QWizard.NextButton, tr("Next"))

    def discover_active_managers(self, div_configs):
        if not div_configs:
            return []

        active_ids = []
        for i, mgr in enumerate(self.managers):
            mgr.divisoes = div_configs
            items = mgr.discover_items()

            page_id = i + 1
            page = self.page(page_id)

            if items:
                page.set_items(items)
                active_ids.append(page_id)
                self.active_managers_map[page_id] = mgr
            else:
                page.set_items([])

        return active_ids


class PageDivisoes(QWizardPage):
    def __init__(self, wizard):
        super().__init__()
        self.setTitle(tr("Divisions"))
        self.setSubTitle(tr("Select the division of origin for the resources"))
        self.wizard_parent = wizard
        self.cached_chain = []

        layout = QVBoxLayout(self)
        self.list_div = QListWidget()
        layout.addWidget(self.list_div)

        self._populate_list()

    def _populate_list(self):
        """
        Populates the division list using ADDITIVE logic (AND).
        - Load definitions from divisions.json (if exists).
        - Scan local physical folders and add those not present in JSON.
        """
        root = self.wizard_parent.config_root
        divisions_file = os.path.join(root, 'divisions.json')

        available_divisions = []
        loaded_ids = set()  # Used to ensure JSON config has priority

        # Load divisions.json (Explicit/Remote Definitions)
        if os.path.exists(divisions_file):
            try:
                with open(divisions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Normalize: accepts both direct list and dict with 'divisions' key
                    items = []
                    if isinstance(data, list):
                        items = data
                    elif isinstance(data, dict):
                        items = data.get('divisions', [])

                    for entry in items:
                        available_divisions.append(entry)
                        # Register ID to avoid adding duplicated physical folder later
                        entry_id = entry.get('id')
                        if entry_id:
                            loaded_ids.add(entry_id)
            except Exception as e:
                # Silent log to avoid freezing the plugin if JSON is broken
                print(f"Error reading divisions.json: {e}")

        # Scan Physical Folders (Automatic Discovery)
        # Always executes. The administrator controls this by distributing folders or not.
        if os.path.exists(root):
            pastas = sorted(d for d in os.listdir(root)
                            if os.path.isdir(os.path.join(root, d)))

            for d in pastas:
                # The 'AND' Logic:
                # If the folder exists AND it hasn't been defined in the JSON above...
                if d not in loaded_ids:
                    # ...Add as a default local division
                    available_divisions.append({
                        "id": d,
                        "name": format_resource_name(d),  # Ex: "my_folder" -> "My Folder"
                        "type": DIV_TYPE_FOLDER,  # Imported constant
                        "path": d,
                        "default_checked": True
                    })

        # Render in Interface
        self.list_div.clear()
        for div in available_divisions:
            # Fallback for ID if name is missing
            name = div.get('name', div.get('id', 'Unknown'))
            div_type = div.get('type', DIV_TYPE_FOLDER)

            # Re-added logic: Append marker for remote divisions
            if div_type == DIV_TYPE_REMOTE_MANIFEST:
                name += DOWNLOAD_MARKER

            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)

            # Set initial state (checked by default)
            is_checked = div.get('default_checked', True)
            item.setCheckState(Qt.Checked if is_checked else Qt.Unchecked)

            # Store the full configuration object in the item (for later use in Loader)
            item.setData(Qt.UserRole, div)
            self.list_div.addItem(item)

    def get_selected_divisoes_config(self):
        configs = []
        for i in range(self.list_div.count()):
            item = self.list_div.item(i)
            if item.checkState() == Qt.Checked:
                configs.append(item.data(Qt.UserRole).copy())
        return configs

    def validatePage(self):
        """
        Lazy Loading Implementation using DivisionLoader.
        """
        selected_configs = self.get_selected_divisoes_config()

        if not selected_configs:
            QMessageBox.critical(self, tr("Error"), tr("Select at least one division."))
            return False

        # Initialize the Loader
        loader = DivisionLoader(self.wizard_parent.config_root)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            # Lazy Loading Loop via Loader
            for config in selected_configs:
                try:
                    # Logic is now encapsulated in the Loader
                    loader.enrich_config(config)
                except Exception as e:
                    # UI handles the error reporting, keeping Loader clean
                    QApplication.restoreOverrideCursor()
                    QMessageBox.warning(self, tr("Loading Error"),
                                        tr(f"Could not load division '{config.get('name')}':\n{str(e)}"))
                    return False

            self.cached_chain = self.wizard_parent.discover_active_managers(selected_configs)

        finally:
            QApplication.restoreOverrideCursor()

        if not self.cached_chain:
            QMessageBox.warning(
                self, tr("Nothing to install"),
                tr("No installable resources were found for the selected divisions.")
            )
            return False

        return True

    def nextId(self):
        if self.cached_chain:
            return self.cached_chain[0]
        return self.wizard_parent.PAGE_RESUMO


class PageManager(QWizardPage):
    def __init__(self, manager, wizard):
        super().__init__()
        self.manager = manager
        self.wizard_parent = wizard
        self.items = []

        self.setTitle(manager.label)
        self.setSubTitle(manager.description)

        layout = QVBoxLayout(self)

        if getattr(manager, "requires_folder_input", False):
            hl = QHBoxLayout()
            self.path_edit = QLineEdit()
            self.path_edit.setText(os.path.join(os.path.expanduser("~"), "QGIS_Data"))
            btn = QPushButton(tr("Browse..."))
            btn.clicked.connect(self._browse)
            hl.addWidget(QLabel(tr("Destination")))
            hl.addWidget(self.path_edit)
            hl.addWidget(btn)
            layout.addLayout(hl)
            layout.addSpacing(10)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.cb_overwrite = QCheckBox(tr("Overwrite existing files"))
        self.cb_overwrite.setChecked(False)
        self.cb_overwrite.setVisible(getattr(manager, 'show_overwrite_option', True))
        layout.addWidget(self.cb_overwrite)

        btns = QHBoxLayout()
        b_all = QPushButton(tr("Select All"))
        b_none = QPushButton(tr("Deselect All"))
        b_all.clicked.connect(lambda: self._toggle(True))
        b_none.clicked.connect(lambda: self._toggle(False))
        btns.addWidget(b_all)
        btns.addWidget(b_none)
        btns.addStretch()
        layout.addLayout(btns)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, tr("Select Folder"))
        if d: self.path_edit.setText(d)

    def _toggle(self, state):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked if state else Qt.Unchecked)

    def set_items(self, items):
        self.items = items
        self.list_widget.clear()
        for item_data in items:
            li = QListWidgetItem(item_data['label'])
            li.setFlags(li.flags() | Qt.ItemIsUserCheckable)
            li.setCheckState(Qt.Checked if item_data.get('checked', False) else Qt.Unchecked)
            li.setData(Qt.UserRole, item_data)
            self.list_widget.addItem(li)

    def get_selected_items(self):
        sel = []
        for i in range(self.list_widget.count()):
            li = self.list_widget.item(i)
            if li.checkState() == Qt.Checked:
                sel.append(li.data(Qt.UserRole))
        return sel

    def get_output_folder(self):
        if hasattr(self, 'path_edit'): return self.path_edit.text()
        return None

    def allow_overwrite(self):
        """
        Determines if overwrite is allowed.
        BUG FIX: Do NOT use self.cb_overwrite.isVisible() here.
        When this method is called during installation (from PageInstalacao),
        this page (PageManager) is hidden in the wizard stack, so isVisible() returns False.
        We must check the Manager's configuration property directly.
        """
        if not getattr(self.manager, 'show_overwrite_option', True):
            return False
        return self.cb_overwrite.isChecked()

    def validatePage(self):
        selected = self.get_selected_items()
        collisions = {}
        for item in selected:
            cid = item.get('collision_id')
            if cid in collisions:
                QMessageBox.warning(self, tr("Conflict"),
                                    tr("Multiple items for the same destination: ") + cid)
                return False
            collisions[cid] = True
        return True

    def nextId(self):
        chain = self.wizard_parent.intro_page.cached_chain
        current_id = self.wizard().currentId()
        try:
            idx = chain.index(current_id)
            if idx + 1 < len(chain):
                return chain[idx + 1]
        except ValueError:
            pass
        return self.wizard_parent.PAGE_RESUMO


class PageResumo(QWizardPage):
    def __init__(self, wizard):
        super().__init__()
        self.setTitle(tr("Installation Summary"))
        self.setSubTitle(tr("Confirm selected items"))
        self.wizard_parent = wizard
        self._has_items = False

        layout = QVBoxLayout(self)
        self.browser = QTextBrowser()
        layout.addWidget(self.browser)

    def initializePage(self):
        html = "<h3>" + tr("Selected Items") + "</h3><ul>"
        has_items = False
        chain = self.wizard_parent.intro_page.cached_chain

        for page_id in chain:
            page = self.wizard_parent.page(page_id)
            selected = page.get_selected_items()
            if selected:
                has_items = True
                html += f"<li><b>{page.manager.label}</b><ul>"
                for s in selected:
                    html += f"<li>{s.get('label')}</li>"
                html += "</ul></li>"
        html += "</ul>"

        if not has_items:
            html += "<p>" + tr("No items selected.") + "</p>"
            self.wizard().button(QWizard.NextButton).setEnabled(False)
        else:
            self.wizard().button(QWizard.NextButton).setEnabled(True)

        self.browser.setHtml(html)
        self._has_items = has_items
        self.completeChanged.emit()

    def isComplete(self):
        return self._has_items

    def nextId(self):
        return self.wizard_parent.PAGE_INSTALL


class PageInstalacao(QWizardPage):
    def __init__(self, wizard):
        super().__init__()
        self.setTitle(tr("Installation Complete"))
        self.setSubTitle(tr("Operation result"))
        self.wizard_parent = wizard
        self._ja_executado = False

        layout = QVBoxLayout(self)
        self.log = QTextBrowser()
        layout.addWidget(self.log)

    def initializePage(self):
        self.wizard().setButtonLayout([QWizard.Stretch, QWizard.FinishButton])
        if self._ja_executado: return
        self._ja_executado = True
        QApplication.processEvents()
        self.run_installation()

    def run_installation(self):
        btn_finish = self.wizard().button(QWizard.FinishButton)
        if btn_finish: btn_finish.setEnabled(False)

        self.append_log("<b>" + tr("Starting installation...") + "</b><br>")
        chain = self.wizard_parent.intro_page.cached_chain

        for page_id in chain:
            page = self.wizard_parent.page(page_id)
            mgr = page.manager
            items = page.get_selected_items()
            folder = page.get_output_folder()
            overwrite = page.allow_overwrite()

            if items:
                self.append_log(tr("Processing:") + f" {mgr.label}")
                if folder and hasattr(mgr, 'set_output_folder'):
                    mgr.set_output_folder(folder)
                try:
                    mgr.install_items(items, self.append_log, overwrite=overwrite)
                except Exception as e:
                    self.append_log(f"<font color='red'>{tr('Error:')} {e}</font>")
                self.append_log("<hr>")

        self.append_log("<b>" + tr("Process finished.") + "</b>")
        if btn_finish: btn_finish.setEnabled(True)

    def append_log(self, text):
        self.log.moveCursor(QTextCursor.End)
        self.log.insertHtml(str(text) + "<br>")
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())
        QApplication.processEvents()

    def nextId(self):
        return -1