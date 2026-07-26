"""Graphical dialogs used by the GUI application."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from acamp.models import InventoryDraft
from acamp.services import (
    InventoryOperationResult,
    validate_inventory_draft,
)


class AddInventoryItemDialog(QDialog):
    def __init__(
        self,
        submit: Callable[[InventoryDraft], InventoryOperationResult],
        parent=None,
    ):
        super().__init__(parent)
        self._submit = submit
        self.setObjectName("inventoryDialog")
        self.setWindowTitle("Adicionar Item")
        self.setModal(True)
        self.setMinimumWidth(470)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        title = QLabel("Adicionar item ao inventário")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setVerticalSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome do item")
        form.addRow("Nome do item", self.name_input)

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("0.00")
        form.addRow("Valor unitário", self.value_input)

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 1_000_000)
        self.quantity_input.setValue(1)
        form.addRow("Quantidade", self.quantity_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Descrição opcional")
        self.description_input.setMaximumHeight(90)
        form.addRow("Descrição", self.description_input)
        layout.addLayout(form)

        self.validation_label = QLabel()
        self.validation_label.setObjectName("dialogError")
        self.validation_label.setWordWrap(True)
        self.validation_label.hide()
        layout.addWidget(self.validation_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Adicionar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self._validate_and_submit)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_submit(self) -> None:
        validation = validate_inventory_draft(
            item=self.name_input.text(),
            value=self.value_input.text(),
            quantity=self.quantity_input.value(),
            description=self.description_input.toPlainText(),
        )
        if not validation.succeeded or validation.draft is None:
            self.validation_label.setText("\n".join(validation.errors.values()))
            self.validation_label.show()
            return

        result = self._submit(validation.draft)
        if result.succeeded:
            self.accept()
            return

        self.validation_label.setText(
            result.message or "Não foi possível salvar as alterações."
        )
        self.validation_label.show()
