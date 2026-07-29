"""Graphical dialogs used by the GUI application."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from acamp.models import InventoryDraft, TeamDraft, TeamMemberDraft
from acamp.pricing import ParticipantPayment
from acamp.services import (
    InventoryOperationResult,
    TeamOperationResult,
    validate_inventory_draft,
    validate_score_amount,
    validate_team_draft,
    validate_team_member_name,
)
from acamp.ui.models import PaymentTableModel


def confirm_destructive(
    parent: QWidget | None,
    *,
    title: str,
    message: str,
    confirm_text: str,
) -> bool:
    """Show one consistently styled, plain-text destructive confirmation."""

    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Icon.Warning)
    dialog.setWindowTitle(title)
    dialog.setTextFormat(Qt.TextFormat.PlainText)
    dialog.setText(message)
    cancel_button = dialog.addButton(
        "Cancelar",
        QMessageBox.ButtonRole.RejectRole,
    )
    confirm_button = dialog.addButton(
        confirm_text,
        QMessageBox.ButtonRole.DestructiveRole,
    )
    confirm_button.setObjectName("destructiveButton")
    dialog.setDefaultButton(cancel_button)
    dialog.setEscapeButton(cancel_button)
    dialog.exec()
    return dialog.clickedButton() is confirm_button


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


class PaymentDetailsDialog(QDialog):
    """Read-only participant payment details."""

    def __init__(
        self,
        payments: tuple[ParticipantPayment, ...],
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("paymentDialog")
        self.setWindowTitle("Detalhes dos pagamentos")
        self.setModal(True)
        self.resize(980, 600)
        self.setMinimumSize(760, 440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel("Pagamentos dos participantes")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        if payments:
            table = QTableView()
            table.setObjectName("paymentTable")
            table.setModel(PaymentTableModel(payments, table))
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
            table.setShowGrid(False)
            table.verticalHeader().setVisible(False)
            table.verticalHeader().setDefaultSectionSize(44)
            table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
            table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.Stretch
            )
            layout.addWidget(table)
        else:
            empty = QLabel("Não há pagamentos para exibir.")
            empty.setObjectName("financeEmptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty, 1)

        close_button = QPushButton("Fechar")
        close_button.setObjectName("primaryButton")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)


class AddTeamDialog(QDialog):
    """Creates a team only; participant and score actions are separate."""

    def __init__(
        self,
        submit: Callable[[TeamDraft], TeamOperationResult],
        parent=None,
    ):
        super().__init__(parent)
        self._submit = submit
        self.setObjectName("teamDialog")
        self.setWindowTitle("Novo Time")
        self.setModal(True)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        title = QLabel("Criar novo time")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(12)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome do time")
        form.addRow("Nome do time", self.name_input)
        self.leader_input = QLineEdit()
        self.leader_input.setPlaceholderText("Nome do capitão")
        form.addRow("Capitão", self.leader_input)
        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("Cor do time")
        form.addRow("Cor", self.color_input)
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
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Criar Time")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self._validate_and_submit)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_submit(self) -> None:
        validation = validate_team_draft(
            self.name_input.text(),
            self.leader_input.text(),
            self.color_input.text(),
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


class AddTeamMemberDialog(QDialog):
    def __init__(
        self,
        team_name: str,
        submit: Callable[[TeamMemberDraft], TeamOperationResult],
        parent=None,
    ):
        super().__init__(parent)
        self._submit = submit
        self.setObjectName("teamDialog")
        self.setWindowTitle("Adicionar Participante")
        self.setModal(True)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        title = QLabel("Adicionar participante")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        context = QLabel(f"Time selecionado: {team_name}")
        context.setObjectName("cardSubtitle")
        layout.addWidget(context)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome do participante")
        layout.addWidget(self.name_input)

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
        validation = validate_team_member_name(self.name_input.text())
        if not validation.succeeded or validation.draft is None:
            self.validation_label.setText(validation.error)
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


class ScoreChangeDialog(QDialog):
    def __init__(
        self,
        team_name: str,
        *,
        adding: bool,
        submit: Callable[[int], TeamOperationResult],
        parent=None,
    ):
        super().__init__(parent)
        self._direction = 1 if adding else -1
        self._submit = submit
        action = "Adicionar" if adding else "Remover"
        self.setObjectName("teamDialog")
        self.setWindowTitle(f"{action} Pontos")
        self.setModal(True)
        self.setMinimumWidth(430)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        title = QLabel(f"{action} pontos")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        context = QLabel(f"Time selecionado: {team_name}")
        context.setObjectName("cardSubtitle")
        layout.addWidget(context)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Pontuação inteira maior que zero")
        layout.addWidget(self.amount_input)

        self.validation_label = QLabel()
        self.validation_label.setObjectName("dialogError")
        self.validation_label.setWordWrap(True)
        self.validation_label.hide()
        layout.addWidget(self.validation_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(action)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self._validate_and_submit)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_submit(self) -> None:
        validation = validate_score_amount(self.amount_input.text())
        if not validation.succeeded or validation.amount is None:
            self.validation_label.setText(validation.error)
            self.validation_label.show()
            return
        result = self._submit(validation.amount * self._direction)
        if result.succeeded:
            self.accept()
            return
        self.validation_label.setText(
            result.message or "Não foi possível salvar as alterações."
        )
        self.validation_label.show()
