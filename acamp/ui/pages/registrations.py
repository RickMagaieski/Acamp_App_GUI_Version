"""Participant list with coordinated Google/local deletion requests."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
)

from acamp.repositories import ParticipantLoadResult, ParticipantLoadStatus
from acamp.ui.models import (
    ParticipantTableModel,
    filter_participants,
    paginate_participants,
    sort_participants,
)

from ..widgets import Card, PageScaffold, PrimaryButton


class RegistrationsPage(PageScaffold):
    deletion_requested = Signal(object)

    PAGE_SIZE = 10

    def __init__(self, load_result: ParticipantLoadResult):
        super().__init__(
            "INSCRIÇÕES",
            "Gerencie os participantes inscritos no acampamento.",
            "♙",
        )
        self._load_result = load_result
        self._participants = load_result.participants
        self._page_index = 0
        self._sort_column = 0
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._active_participant_operation: str | None = None
        self._cache_reconciliation_required = False

        search_row = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setObjectName("placeholderSearch")
        self.search_field.setPlaceholderText("Pesquisar por nome...")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.setAccessibleName("Pesquisar participantes por nome")
        self.search_field.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self.search_field, 1)

        self.search_button = PrimaryButton("⌕  Pesquisa")
        self.search_button.setToolTip("A busca é atualizada enquanto você digita.")
        self.search_button.clicked.connect(self.search_field.setFocus)
        search_row.addWidget(self.search_button)
        self.content.addLayout(search_row)

        self.operation_label = QLabel()
        self.operation_label.setObjectName("participantOperationStatus")
        self.operation_label.setWordWrap(True)
        self.operation_label.hide()
        self.content.addWidget(self.operation_label)

        self.cache_warning_label = QLabel()
        self.cache_warning_label.setObjectName("participantCacheWarning")
        self.cache_warning_label.setWordWrap(True)
        self.cache_warning_label.hide()
        self.content.addWidget(self.cache_warning_label)

        table_card = Card()
        table_card.setMinimumHeight(480)
        table_card.body.setContentsMargins(0, 0, 0, 0)

        self.table_model = ParticipantTableModel(parent=self)
        self.table_view = QTableView()
        self.table_view.setObjectName("participantTable")
        self.table_view.setModel(self.table_model)
        self.table_view.setAlternatingRowColors(False)
        self.table_view.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_view.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.table_view.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table_view.setShowGrid(False)
        self.table_view.clicked.connect(self._on_table_clicked)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.verticalHeader().setDefaultSectionSize(48)
        self.table_view.horizontalHeader().setMinimumHeight(46)
        self.table_view.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for column in range(1, self.table_model.columnCount()):
            self.table_view.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )

        self.state_label = QLabel()
        self.state_label.setObjectName("participantState")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setWordWrap(True)
        self.state_label.setMinimumHeight(360)

        table_card.body.addWidget(self.table_view)
        table_card.body.addWidget(self.state_label)
        self.content.addWidget(table_card)

        footer = QHBoxLayout()
        self.total_label = QLabel()
        self.total_label.setObjectName("participantTotal")
        footer.addWidget(self.total_label)
        footer.addStretch(1)

        self.previous_button = QPushButton("‹")
        self.previous_button.setObjectName("paginationButton")
        self.previous_button.setAccessibleName("Página anterior")
        self.previous_button.clicked.connect(self._previous_page)
        footer.addWidget(self.previous_button)

        self.page_label = QLabel()
        self.page_label.setObjectName("pageInformation")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.addWidget(self.page_label)

        self.next_button = QPushButton("›")
        self.next_button.setObjectName("paginationButton")
        self.next_button.setAccessibleName("Próxima página")
        self.next_button.clicked.connect(self._next_page)
        footer.addWidget(self.next_button)
        self.content.addLayout(footer)
        self.content.addStretch(1)

        self.table_view.horizontalHeader().sortIndicatorChanged.connect(
            self._on_sort_changed
        )
        self.table_view.setSortingEnabled(True)
        self.table_view.sortByColumn(
            self._sort_column,
            self._sort_order,
        )

        can_search = load_result.succeeded and bool(self._participants)
        self.search_field.setEnabled(can_search)
        self.search_button.setEnabled(can_search)
        self._refresh_view()

    def _on_search_changed(self, _text: str) -> None:
        self._page_index = 0
        self._refresh_view()

    def _previous_page(self) -> None:
        self._page_index -= 1
        self._refresh_view()

    def _next_page(self) -> None:
        self._page_index += 1
        self._refresh_view()

    def _on_sort_changed(
        self,
        column: int,
        order: Qt.SortOrder,
    ) -> None:
        self._sort_column = column
        self._sort_order = order
        self._page_index = 0
        self._refresh_view()

    def _on_table_clicked(self, index) -> None:
        if (
            self._active_participant_operation is not None
            or not index.isValid()
            or index.column() != ParticipantTableModel.ACTION_COLUMN
        ):
            return

        participant = self.table_model.participant_at(index.row())
        if participant is None:
            return
        if not participant.has_usable_id:
            self.show_deletion_error(
                "Esta inscrição não possui um identificador válido e não "
                "pode ser removida do Google Sheets."
            )
            return
        if self._confirm_deletion(participant.name):
            self.deletion_requested.emit(participant)

    def _confirm_deletion(self, participant_name: str) -> bool:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setWindowTitle("Remover inscrição")
        dialog.setTextFormat(Qt.TextFormat.PlainText)
        dialog.setText(
            "Tem certeza de que deseja remover a inscrição de "
            f"{participant_name}?\n\n"
            "A inscrição será removida do Google Sheets e dos dados locais."
        )
        cancel_button = dialog.addButton(
            "Cancelar",
            QMessageBox.ButtonRole.RejectRole,
        )
        remove_button = dialog.addButton(
            "Remover",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        remove_button.setObjectName("destructiveButton")
        dialog.setDefaultButton(cancel_button)
        dialog.exec()
        return dialog.clickedButton() is remove_button

    def _load_state_message(self) -> str | None:
        messages = {
            ParticipantLoadStatus.LOADING:
                "Carregando participantes...",
            ParticipantLoadStatus.FILE_MISSING:
                "Arquivo de participantes não encontrado.",
            ParticipantLoadStatus.FILE_EMPTY:
                "O arquivo de participantes está vazio.",
            ParticipantLoadStatus.INVALID_JSON:
                "Não foi possível carregar os participantes.",
            ParticipantLoadStatus.ROOT_NOT_LIST:
                "Não foi possível carregar os participantes.",
            ParticipantLoadStatus.READ_ERROR:
                "Não foi possível carregar os participantes.",
            ParticipantLoadStatus.VALID_EMPTY:
                "Não há participantes cadastrados.",
        }
        return messages.get(self._load_result.status)

    def set_load_result(self, load_result: ParticipantLoadResult) -> None:
        """Apply one application-level load result without reading the file."""
        self._load_result = load_result
        self._participants = load_result.participants
        can_search = load_result.succeeded and bool(self._participants)
        self.search_field.setEnabled(can_search)
        self.search_button.setEnabled(can_search)
        self._refresh_view()

    def set_participant_operation(self, operation: str | None) -> None:
        self._active_participant_operation = operation
        self.table_view.setEnabled(
            operation is None
            and not self._cache_reconciliation_required
        )
        if operation == "deletion":
            self.operation_label.setText("Removendo inscrição...")
            self.operation_label.show()
        elif operation == "synchronization":
            self.operation_label.setText(
                "Sincronização em andamento. Aguarde para remover "
                "inscrições."
            )
            self.operation_label.show()
        else:
            self.operation_label.hide()

    def show_deletion_success(self, participant_name: str) -> None:
        QMessageBox.information(
            self,
            "Inscrição removida",
            f"A inscrição de {participant_name} foi removida com sucesso.",
        )

    def show_deletion_error(self, message: str) -> None:
        QMessageBox.warning(
            self,
            "Não foi possível remover a inscrição",
            message,
        )

    def mark_cache_reconciliation_required(self, message: str) -> None:
        self._cache_reconciliation_required = True
        self.table_view.setEnabled(False)
        self.cache_warning_label.setText(message)
        self.cache_warning_label.show()
        QMessageBox.warning(
            self,
            "Sincronização necessária",
            message,
        )

    def clear_cache_reconciliation_warning(self) -> None:
        self._cache_reconciliation_required = False
        self.table_view.setEnabled(
            self._active_participant_operation is None
        )
        self.cache_warning_label.clear()
        self.cache_warning_label.hide()

    def _refresh_view(self) -> None:
        total = len(self._participants)
        noun = "inscrito" if total == 1 else "inscritos"
        self.total_label.setText(f"♙  Total: {total} {noun}")

        load_message = self._load_state_message()
        if load_message is not None:
            self._show_state(load_message)
            return

        filtered = filter_participants(
            self._participants,
            self.search_field.text(),
        )
        filtered = sort_participants(
            filtered,
            self._sort_column,
            self._sort_order,
        )
        page = paginate_participants(filtered, self._page_index, self.PAGE_SIZE)
        self._page_index = page.page_index

        if not page.items:
            self._show_state("Nenhum participante encontrado para esta busca.")
            return

        self.table_model.set_participants(page.items)
        self.table_view.show()
        self.state_label.hide()
        self.page_label.setText(
            f"Página {page.page_index + 1} de {page.total_pages}"
        )
        self.previous_button.setEnabled(page.page_index > 0)
        self.next_button.setEnabled(page.page_index + 1 < page.total_pages)

    def _show_state(self, message: str) -> None:
        self.table_model.set_participants(())
        self.table_view.hide()
        self.state_label.setText(message)
        self.state_label.show()
        self.page_label.setText("Página 0 de 0")
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
