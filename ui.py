import logging
logger = logging.getLogger(__name__)

import os
import json
import csv
from PyQt5 import QtWidgets, QtGui, QtCore

from .workers import PushWorker


class PersistantList(list):
    """A list that persists to a JSON file."""
    def __init__(self, filepath, *args, **kwargs):
        """Initialize the PersistantList with a file path."""
        super().__init__(*args, **kwargs)
        self.filepath = filepath
        self.load() if os.path.isfile(self.filepath) else self.dump()

    def dump(self):
        """Save the list to a JSON file."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            json.dump(self, f, indent=4)

    def load(self):
        """Load the list from a JSON file."""
        if os.path.isfile(self.filepath):
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                super().extend(data)

    def __setitem__(self, index, value):
        """Set an item in the list and dump the changes to the file."""
        super().__setitem__(index, value)
        self.dump()

    def append(self, item):
        """Append an item to the list and dump the changes to the file."""
        super().append(item)
        self.dump()

    def remove(self, item):
        """Remove an item from the list and dump the changes to the file."""
        super().remove(item)
        self.dump()

    def clear(self):
        """Clear the list and dump the changes to the file."""
        super().clear()
        self.dump()


class AddConfigurationDialog(QtWidgets.QDialog):
    """Dialog to add a new configuration to the pushboard."""

    def __init__(self, form):
        """Initialize the AddConfigurationDialog."""
        super().__init__(form)
        self.form = form
        self.setWindowTitle("Add Configuration")
        self.setWindowIcon(self.form._get_icon("add"))
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.show()

    def setup_ui(self):
        """Setup the UI for the AddConfigurationDialog."""
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        self.config_group = QtWidgets.QGroupBox("Configuration")
        self.layout.addWidget(self.config_group)
        self.config_layout = QtWidgets.QVBoxLayout(self.config_group)
        self.config_text_edit = QtWidgets.QTextEdit(self.config_group)
        self.config_text_edit.setPlaceholderText("Enter your configuration here...")
        self.config_layout.addWidget(self.config_text_edit)

        self.browse_button = QtWidgets.QPushButton("Browse", self.config_group)
        self.browse_button.setFixedWidth(100)
        self.browse_button.clicked.connect(self.browse_file)
        self.config_layout.addWidget(self.browse_button, alignment=QtCore.Qt.AlignLeft)

        self.target_line_edit = QtWidgets.QLineEdit(self)
        self.target_line_edit.setPlaceholderText("Enter comma separated targets (e.g., host1,host2)")
        self.layout.addWidget(self.target_line_edit)

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setFixedWidth(100)
        self.button_box.button(QtWidgets.QDialogButtonBox.Cancel).setFixedWidth(100)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def accept(self):
        targets = self.target_line_edit.text().strip()
        config = self.config_text_edit.toPlainText().strip()

        if not targets or not config:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please provide both targets and configuration.")
            return

        target_list = [target.strip() for target in targets.split(',')]
        for target in target_list:
            if not target:
                QtWidgets.QMessageBox.warning(self, "Input Error", f"Invalid target: '{target}'")
                return

            self.form.pushboard_table.add_row(target, config, "Pending")
        self.form.status_label.setText("Configuration added successfully.")
        super().accept()

    def browse_file(self):
        """Open a file dialog to select a configuration file."""
        file_dialog = QtWidgets.QFileDialog(self, "Select Configuration File")
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Configuration Files (*.conf *.txt);;All Files (*)")
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                with open(file_path, 'r') as file:
                    config_content = file.read()
                    self.config_text_edit.setPlainText(config_content)


class PushBoardTable(QtWidgets.QTableWidget):
    """Table widget to display and manage push configurations."""

    def __init__(self, form):
        """Initialize the PushBoardTable."""
        super().__init__(form)
        self.form = form
        self.workers = []
        self.data = PersistantList(os.path.join(os.path.expanduser("~"), ".netmig", "pushboard.json"),)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Target", "Configuration", "Lines", "Save", "Status"])
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(1, self.horizontalHeader().Stretch)
        self.verticalHeader().setVisible(False)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(2, 60)
        self.setColumnWidth(3, 40)
        self.setColumnWidth(4, 150)

        self.create_context_menu()
        self.customContextMenuRequested.connect(self.table_menu_event)

        self.load_rows()

    def create_context_menu(self):
        """Create the context menu for the table."""
        self.context_menu = QtWidgets.QMenu(self)

        self.add_action = QtWidgets.QAction(self)
        self.add_action.setIcon(self.form._get_icon("add"))
        self.add_action.setText("Add")
        self.context_menu.addAction(self.add_action)

        self.import_action = QtWidgets.QAction(self)
        self.import_action.setIcon(self.form._get_icon("import-csv"))
        self.import_action.setText('Import CSV')
        self.context_menu.addAction(self.import_action)

        self.clear_action = QtWidgets.QAction(self)
        self.clear_action.setIcon(self.form._get_icon("clear"))
        self.clear_action.setText('Clear')
        self.context_menu.addAction(self.clear_action)

        self.context_menu.addSeparator()

        self.push_selected_action = QtWidgets.QAction(self)
        self.push_selected_action.setIcon(self.form._get_icon("send"))
        self.push_selected_action.setText("Push Selected")
        self.context_menu.addAction(self.push_selected_action)

        self.abort_selected_action = QtWidgets.QAction(self)
        self.abort_selected_action.setIcon(self.form._get_icon("esc"))
        self.abort_selected_action.setText("Abort Selected")
        self.context_menu.addAction(self.abort_selected_action)

        self.delete_action = QtWidgets.QAction(self)
        self.delete_action.setIcon(self.form._get_icon("delete2"))
        self.delete_action.setText("Delete Selected")
        self.context_menu.addAction(self.delete_action)

        self.context_menu.addSeparator()

        self.push_action = QtWidgets.QAction(self)
        self.push_action.setIcon(self.form._get_icon("send"))
        self.push_action.setText("Push All")
        self.context_menu.addAction(self.push_action)

        self.abort_action = QtWidgets.QAction(self)
        self.abort_action.setIcon(self.form._get_icon("esc"))
        self.abort_action.setText("Abort All")
        self.context_menu.addAction(self.abort_action)

    def table_menu_event(self, pos):
        """Handle the context menu event."""
        selected = bool(self.selectedIndexes())
        self.delete_action.setDisabled(not selected)
        self.push_selected_action.setDisabled(not selected)
        self.abort_selected_action.setDisabled(not selected)
        self.context_menu.exec_(self.mapToGlobal(pos))

    def load_rows(self):
        """Load rows from the persistent data."""
        self.setRowCount(0)
        if not self.data:
            return
        for config_data in self.data:
            self._insert_row(config_data)

    def _insert_row(self, config_data):
        """Insert a new row into the table with the given configuration data."""
        row_idx = self.rowCount()
        self.insertRow(row_idx)

        self.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(config_data.get("target")))
        self.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(self._get_config_preview(config_data.get("config"))))
        self.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(len(config_data.get("config").splitlines()))))
        self.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(config_data.get("status")))

        checkbox = QtWidgets.QCheckBox()
        checkbox.setStyleSheet("margin-left:10px; margin-right:10px;")
        checkbox.setChecked(config_data.get("save", True))
        self.setCellWidget(row_idx, 3, checkbox)

        def on_checkbox_changed(state, row=row_idx):
            self.data[row]["save"] = (state == QtCore.Qt.Checked)
            self.data.dump()

        checkbox.stateChanged.connect(on_checkbox_changed)

    def _get_config_preview(self, config_text):
        """Get a preview of the configuration text."""
        preview_config = config_text
        if len(config_text) > 120:
            preview_config = config_text[:60] + "  ..  ..  ..  " + config_text[-60:]
        return preview_config.replace("\n", "\\n").strip()

    def add_row(self, target, config, status, save=True):
        """Add a new row to the table with the given target, configuration, and status."""
        config_data = {
            "target": target,
            "config": config,
            "save": save,
            "status": status,
        }
        self._insert_row(config_data)
        self.data.append(config_data)
        self.workers.append(None)

    def delete_row(self):
        """Delete the selected row from the table."""
        row_index = self.selectedIndexes()[0].row()
        self.removeRow(row_index)
        if self.data:
            self.data.remove(self.data[row_index])
            self.workers.pop(row_index)

    def update_row(self, row_index, config_data):
        """Update the row at the given index with the provided configuration data."""
        self.item(row_index, 0).setText(config_data.get("target"))
        self.item(row_index, 1).setText(self._get_config_preview(config_data.get("config")))
        self.item(row_index, 2).setText(str(len(config_data.get("config").splitlines())))
        self.item(row_index, 4).setText(config_data.get("status"))
        if self.data:
            self.data[row_index] = config_data

    def clear_all(self):
        """Clear all configurations from the table."""
        self.setRowCount(0)
        self.data.clear()
        self.workers.clear()
        self.form.status_label.setText("All configurations cleared.")
        logger.info("All configurations cleared from the pushboard table.")


class Ui_Form:
    """Base class for the main form UI."""

    def setup_ui(self, form):
        """Setup the UI for the main form."""
        self.form = form
        self.layout = QtWidgets.QVBoxLayout(form)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        self.action_layout = QtWidgets.QHBoxLayout()
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        self.action_layout.setSpacing(5)
        self.layout.addLayout(self.action_layout)

        self.add_button = QtWidgets.QPushButton()
        self.add_button.setIcon(self._get_icon("add"))
        self.add_button.setToolTip("Add Configuration")
        self.action_layout.addWidget(self.add_button)
        self.import_button = QtWidgets.QPushButton()
        self.import_button.setIcon(self._get_icon("import-csv"))
        self.import_button.setToolTip("Import CSV")
        self.action_layout.addWidget(self.import_button)
        self.push_button = QtWidgets.QPushButton()
        self.push_button.setIcon(self._get_icon("send"))
        self.push_button.setToolTip("Push All")
        self.action_layout.addWidget(self.push_button)
        self.abort_button = QtWidgets.QPushButton()
        self.abort_button.setIcon(self._get_icon("esc"))
        self.abort_button.setToolTip("Abort All")
        self.action_layout.addWidget(self.abort_button)
        self.clear_button = QtWidgets.QPushButton()
        self.clear_button.setIcon(self._get_icon("clear"))
        self.clear_button.setToolTip("Clear Table")
        self.action_layout.addWidget(self.clear_button)

        self.action_layout.addStretch()

        self.pushboard_table = PushBoardTable(self.form)
        self.layout.addWidget(self.pushboard_table)

        self.status_layout = QtWidgets.QHBoxLayout()
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.setSpacing(5)
        self.layout.addLayout(self.status_layout)
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_layout.addWidget(self.status_label)

    def _get_icon(self, filename):
        """Get the icon for the given filename."""
        icon_path = os.path.join(os.path.dirname(__file__), "assets", f"{filename}.ico")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        return icon


class Form(QtWidgets.QWidget, Ui_Form):
    """Main form for the pushboard application."""

    def __init__(self, parent=None, **kwargs):
        """Initialize the main form."""
        super().__init__(parent)
        self.kwargs = kwargs
        self.session = kwargs.get("session")
        self.setup_ui(self)

        self.add_button.clicked.connect(lambda: AddConfigurationDialog(self))
        self.import_button.clicked.connect(self.import_csv)
        self.clear_button.clicked.connect(self.pushboard_table.clear_all)
        self.push_button.clicked.connect(self.push_all)

        self.pushboard_table.add_action.triggered.connect(lambda: AddConfigurationDialog(self))
        self.pushboard_table.delete_action.triggered.connect(self.pushboard_table.delete_row)
        self.pushboard_table.import_action.triggered.connect(self.import_csv)
        self.pushboard_table.clear_action.triggered.connect(self.pushboard_table.clear_all)
        self.pushboard_table.push_action.triggered.connect(self.push_all)
        self.pushboard_table.push_selected_action.triggered.connect(self.push_selected)
        self.abort_button.clicked.connect(self.abort_all)
        self.pushboard_table.abort_action.triggered.connect(self.abort_all)
        self.pushboard_table.abort_selected_action.triggered.connect(self.abort_selected)

    def import_csv(self):
        """Import configurations from a CSV file."""
        file_dialog = QtWidgets.QFileDialog(self, "Import CSV File")
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("CSV Files (*.csv);;All Files (*)")
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                try:
                    if not os.path.isfile(file_path):
                        raise FileNotFoundError(f"File not found: {file_path}")

                    with open(file_path, 'r', encoding="utf-8-sig") as csv_file:
                        csv_reader = csv.reader(csv_file)
                        for row in csv_reader:
                            if len(row) < 2:
                                logger.warning(f"Skipping invalid row: {row}")
                                continue
                            target, config = row[0].strip(), row[1].strip()
                            if not target or not config:
                                logger.warning(f"Skipping row with empty target or config: {row}")
                                continue
                            self.pushboard_table.add_row(target, config, "Pending")

                except Exception as e:
                    logger.error(f"Error importing CSV: {e}")
                    QtWidgets.QMessageBox.critical(self, "Import Error", f"Failed to import CSV file: {e}")

    def _push(self, index, target, config):
        """Push the configuration to the target using a worker thread."""
        if not target or not config:
            logger.error("Target or configuration is empty.")
            return

        checkbox = self.pushboard_table.cellWidget(index, 3)
        save = checkbox.isChecked() if checkbox is not None else False

        self.status_label.setText(f"Pushing configuration to {target}...")
        worker = PushWorker(target, config, save, self.session)
        worker.start()
        worker.status_signal.connect(lambda status: self._update_status(index, status))
        self.pushboard_table.workers.insert(index, worker)

    def push_all(self):
        """Push all configurations in the pushboard table."""
        for index, config_data in enumerate(self.pushboard_table.data):
            target = config_data.get("target")
            config = config_data.get("config")
            status = config_data.get("status")
            if status != "Pushed":
                self._push(index, target, config)

    def push_selected(self):
        """Push the selected configurations in the pushboard table."""
        selected_rows = self.pushboard_table.selectedIndexes()
        for index in set(row.row() for row in selected_rows):
            config_data = self.pushboard_table.data[index]
            target = config_data.get("target")
            config = config_data.get("config")
            status = config_data.get("status")
            if status != "Pushed":
                self._push(index, target, config)

    def abort_all(self):
        """Abort all running PushWorker threads."""
        for worker in self.pushboard_table.workers:
            if worker and worker.isRunning():
                worker.abort()

    def abort_selected(self):
        """Abort selected PushWorker threads."""
        selected_rows = self.pushboard_table.selectedIndexes()
        for index in set(row.row() for row in selected_rows):
            worker = self.pushboard_table.workers[index]
            if worker and worker.isRunning():
                worker.abort()

    def _update_status(self, index, status):
        """Update the status of the configuration at the given index."""
        config_data = self.pushboard_table.data[index]
        config_data["status"] = status
        self.pushboard_table.update_row(index, config_data)
