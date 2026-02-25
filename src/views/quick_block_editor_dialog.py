"""Dialog for creating or editing Quick Blocks."""

from __future__ import annotations

import uuid

from PySide6 import QtWidgets, QtCore

from src.utils.quick_blocks_repository import QuickBlock, QuickGroup
from src.utils.translator import tr


class QuickBlockEditorDialog(QtWidgets.QDialog):
    """Modal dialog used to create or edit Quick Blocks."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        *,
        groups: list[QuickGroup],
        block: QuickBlock | None = None,
    ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(
            tr("quick_block_editor", "Quick Block Editor")
        )
        self._groups = groups
        self._editing_block = block
        self._build_ui()
        self._populate_groups()
        if block:
            self._load_block(block)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QtWidgets.QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self._title_edit = QtWidgets.QLineEdit()
        self._title_edit.setPlaceholderText(tr("block_name", "Block name"))
        form.addRow(tr("name", "Name:"), self._title_edit)

        group_row = QtWidgets.QHBoxLayout()
        self._group_combo = QtWidgets.QComboBox()
        group_row.addWidget(self._group_combo, 1)
        add_group_btn = QtWidgets.QToolButton()
        add_group_btn.setText("+")
        add_group_btn.setToolTip(tr("add_group", "Add group"))
        add_group_btn.clicked.connect(self._prompt_new_group)
        group_row.addWidget(add_group_btn, 0)
        group_wrapper = QtWidgets.QWidget()
        group_wrapper.setLayout(group_row)
        form.addRow(tr("group", "Group:"), group_wrapper)

        self._port_combo = QtWidgets.QComboBox()
        self._port_combo.addItems(["cpu1", "cpu2", "tlm", "combo"])
        form.addRow(tr("port", "Port:"), self._port_combo)

        self._send_combo_chk = QtWidgets.QCheckBox(
            tr("send_to_combo", "Send to combo (CPU1+CPU2)")
        )
        self._send_combo_chk.setChecked(True)
        form.addRow("", self._send_combo_chk)

        self._mode_checkbox = QtWidgets.QCheckBox(
            tr("supports_off", "Supports OFF command")
        )
        self._mode_checkbox.setChecked(True)
        self._mode_checkbox.stateChanged.connect(self._on_mode_toggled)
        form.addRow("", self._mode_checkbox)

        self._hotkey_edit = QtWidgets.QLineEdit()
        self._hotkey_edit.setPlaceholderText(tr("hotkey_hint", "e.g. Ctrl+Alt+1"))
        form.addRow(tr("hotkey", "Hotkey:"), self._hotkey_edit)

        self._command_on = QtWidgets.QPlainTextEdit()
        self._command_on.setPlaceholderText(
            tr("command_on", "Command ON")
        )
        form.addRow(tr("command_on", "Command ON:"), self._command_on)

        self._command_off = QtWidgets.QPlainTextEdit()
        self._command_off.setPlaceholderText(
            tr("command_off", "Command OFF")
        )
        form.addRow(tr("command_off", "Command OFF:"), self._command_off)

        layout.addLayout(form)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_groups(self) -> None:
        self._group_combo.clear()
        for group in self._groups:
            self._group_combo.addItem(group.name, group.id)

    def _prompt_new_group(self) -> None:
        text, ok = QtWidgets.QInputDialog.getText(
            self,
            tr("new_group", "New group"),
            tr("enter_group_name", "Enter group name"),
        )
        cleaned = text.strip()
        if ok and cleaned:
            group_id = uuid.uuid4().hex
            group = QuickGroup(id=group_id, name=cleaned)
            self._groups.append(group)
            self._group_combo.addItem(group.name, group.id)
            self._group_combo.setCurrentIndex(self._group_combo.count() - 1)

    def _on_mode_toggled(self, state: int) -> None:
        has_off = state == QtCore.Qt.Checked
        self._command_off.setEnabled(has_off)

    def _load_block(self, block: QuickBlock) -> None:
        self._title_edit.setText(block.title)
        index = next(
            (i for i in range(self._group_combo.count())
             if self._group_combo.itemData(i) == block.group_id),
            0,
        )
        self._group_combo.setCurrentIndex(index)
        if block.port:
            port_index = self._port_combo.findText(block.port)
            if port_index >= 0:
                self._port_combo.setCurrentIndex(port_index)
        self._send_combo_chk.setChecked(block.send_to_combo)
        self._mode_checkbox.setChecked(block.mode != "single")
        self._command_on.setPlainText(block.command_on)
        self._command_off.setPlainText(block.command_off or "")
        self._command_off.setEnabled(block.mode != "single")
        self._hotkey_edit.setText(block.hotkey or "")

    def _validate(self) -> tuple[bool, str]:
        title = self._title_edit.text().strip()
        if not title:
            return False, tr("validation_title", "Name is required")
        if len(title) > 128:
            return False, tr("validation_title_len", "Name too long")
        cmd_on = self._command_on.toPlainText().strip()
        if not cmd_on:
            return False, tr("validation_on", "Command ON is required")
        if len(cmd_on) > 1024:
            return False, tr("validation_on_len", "Command ON too long")
        if self._mode_checkbox.isChecked():
            cmd_off = self._command_off.toPlainText().strip()
            if not cmd_off:
                return False, tr("validation_off", "Command OFF is required")
            if len(cmd_off) > 1024:
                return False, tr("validation_off_len", "Command OFF too long")
        return True, ""

    def _on_accept(self) -> None:
        valid, message = self._validate()
        if not valid:
            QtWidgets.QMessageBox.warning(self, self.windowTitle(), message)
            return
        self.accept()

    def result_block(self) -> QuickBlock:
        group_id = self._group_combo.currentData()
        block_id = (
            self._editing_block.id if self._editing_block else uuid.uuid4().hex
        )
        has_off = self._mode_checkbox.isChecked()
        return QuickBlock(
            id=block_id,
            title=self._title_edit.text().strip(),
            command_on=self._command_on.toPlainText().strip(),
            command_off=(
                self._command_off.toPlainText().strip() if has_off else None
            ),
            send_to_combo=self._send_combo_chk.isChecked(),
            group_id=group_id,
            order=self._editing_block.order if self._editing_block else 0,
            mode="dual" if has_off else "single",
            icon=self._editing_block.icon if self._editing_block else None,
            port=self._port_combo.currentText(),
            hotkey=self._hotkey_edit.text().strip() or None,
        )


def create_block(
    parent: QtWidgets.QWidget | None,
    *,
    groups: list[QuickGroup],
    block: QuickBlock | None = None,
) -> QuickBlock | None:
    dialog = QuickBlockEditorDialog(parent, groups=groups, block=block)
    if dialog.exec() == QtWidgets.QDialog.Accepted:
        return dialog.result_block()
    return None
