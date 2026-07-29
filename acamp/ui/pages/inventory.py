"""Functional local inventory page."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableView,
)

from acamp.models import InventoryDraft
from acamp.repositories import InventoryLoadStatus
from acamp.services import InventoryOperationResult, InventoryService
from acamp.ui.dialogs import AddInventoryItemDialog, confirm_destructive
from acamp.ui.models import InventoryTableModel, filter_inventory_items

from ..widgets import Card, PageScaffold, PrimaryButton


class InventoryPage(PageScaffold):
    inventory_changed = Signal()

    def __init__(self, service: InventoryService):
        super().__init__(
            "INVENTÁRIO",
            "Gerencie os itens do acampamento e mantenha o controle do inventário.",
            "◇",
        )
        self._service = service

        actions = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setObjectName("placeholderSearch")
        self.search_field.setPlaceholderText("Procurar item...")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.setAccessibleName("Pesquisar itens por nome")
        self.search_field.textChanged.connect(self._refresh_table)
        actions.addWidget(self.search_field, 1)
        actions.addStretch(1)

        self.add_button = PrimaryButton("＋  Adicionar Item")
        self.add_button.clicked.connect(self._open_add_dialog)
        actions.addWidget(self.add_button)
        self.content.addLayout(actions)

        self.error_banner = QLabel()
        self.error_banner.setObjectName("inventoryError")
        self.error_banner.setWordWrap(True)
        self.error_banner.hide()
        self.content.addWidget(self.error_banner)

        table_card = Card()
        table_card.setMinimumHeight(430)
        table_card.body.setContentsMargins(0, 0, 0, 0)

        self.table_model = InventoryTableModel(parent=self)
        self.table_view = QTableView()
        self.table_view.setObjectName("inventoryTable")
        self.table_view.setModel(self.table_model)
        self.table_view.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table_view.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.table_view.setShowGrid(False)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.verticalHeader().setDefaultSectionSize(50)
        self.table_view.horizontalHeader().setMinimumHeight(46)
        self.table_view.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table_view.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        for column in (1, 2, 3, 5):
            self.table_view.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table_view.clicked.connect(self._table_clicked)

        self.state_label = QLabel()
        self.state_label.setObjectName("inventoryState")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setWordWrap(True)
        self.state_label.setMinimumHeight(330)

        table_card.body.addWidget(self.table_view)
        table_card.body.addWidget(self.state_label)
        self.content.addWidget(table_card)

        self.total_label = QLabel()
        self.total_label.setObjectName("inventoryTotal")
        self.content.addWidget(self.total_label)
        self.content.addStretch(1)
        self.refresh_from_service()

    def refresh_from_service(self) -> None:
        self.error_banner.hide()
        self.add_button.setEnabled(self._service.editable)
        self.search_field.setEnabled(bool(self._service.items))
        self._refresh_table()

    def _state_message(self) -> str | None:
        messages = {
            InventoryLoadStatus.LOADING: "Carregando inventário...",
            InventoryLoadStatus.FILE_MISSING:
                "Arquivo de inventário não encontrado.",
            InventoryLoadStatus.FILE_EMPTY: "O arquivo de inventário está vazio.",
            InventoryLoadStatus.INVALID_JSON:
                "Não foi possível carregar o inventário.",
            InventoryLoadStatus.ROOT_NOT_LIST:
                "Não foi possível carregar o inventário.",
            InventoryLoadStatus.READ_ERROR:
                "Não foi possível carregar o inventário.",
            InventoryLoadStatus.VALID_EMPTY: "O inventário está vazio.",
        }
        return messages.get(self._service.load_result.status)

    def _refresh_table(self) -> None:
        total = len(self._service.items)
        noun = "item" if total == 1 else "itens"
        self.total_label.setText(f"Total de itens: {total} {noun}")

        state_message = self._state_message()
        if state_message is not None:
            self._show_state(state_message)
            return

        filtered = filter_inventory_items(
            self._service.items,
            self.search_field.text(),
        )
        if not filtered:
            self._show_state("Nenhum item encontrado para esta busca.")
            return

        self.table_model.set_items(filtered)
        self.table_view.show()
        self.state_label.hide()

    def _show_state(self, message: str) -> None:
        self.table_model.set_items(())
        self.table_view.hide()
        self.state_label.setText(message)
        self.state_label.show()

    def _open_add_dialog(self) -> None:
        dialog = AddInventoryItemDialog(self._add_item, self)
        dialog.exec()

    def _add_item(self, draft: InventoryDraft) -> InventoryOperationResult:
        result = self._service.add_item(draft)
        if result.succeeded:
            self.refresh_from_service()
            self.inventory_changed.emit()
        else:
            self._show_save_error(result.message)
        return result

    def _table_clicked(self, index: QModelIndex) -> None:
        if index.column() != InventoryTableModel.ACTION_COLUMN:
            return
        item = self.table_model.item_at(index.row())
        if item is None:
            return

        confirmed = confirm_destructive(
            self,
            title="Excluir item",
            message=f'Deseja realmente excluir "{item.item}"?',
            confirm_text="Excluir",
        )
        if not confirmed:
            return

        result = self._service.delete_item(item.source_index)
        if result.succeeded:
            self.refresh_from_service()
            self.inventory_changed.emit()
        else:
            self._show_save_error(result.message)

    def _show_save_error(self, message: str) -> None:
        self.error_banner.setText(
            message or "Não foi possível salvar as alterações."
        )
        self.error_banner.show()
