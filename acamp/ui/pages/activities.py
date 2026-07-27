"""Basic local team management for Phase 2D1."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableView,
)

from acamp.models import Team, TeamDraft
from acamp.repositories import TeamLoadStatus
from acamp.services import TeamOperationResult, TeamService
from acamp.ui.dialogs import AddTeamDialog
from acamp.ui.models import TeamTableModel, filter_teams

from ..widgets import Card, PageScaffold, PrimaryButton


class ActivitiesPage(PageScaffold):
    teams_changed = Signal()

    def __init__(self, service: TeamService):
        super().__init__(
            "ATIVIDADES (TIMES)",
            "Gerencie os times, participantes e pontos do acampamento.",
            "♜",
        )
        self._service = service
        self._selected_source_index: int | None = None

        upper = QHBoxLayout()
        upper.setSpacing(16)

        create_team = Card(
            "CRIAR TIME",
            "Crie um time vazio. Participantes serão gerenciados separadamente.",
        )
        self.create_button = PrimaryButton("＋  Novo Time")
        self.create_button.clicked.connect(self._open_create_dialog)
        create_team.body.addWidget(self.create_button)
        upper.addWidget(create_team, 2)

        participants = Card(
            "GERENCIAR PARTICIPANTES DO TIME SELECIONADO",
            "Disponível na Fase 2D2.",
        )
        participant_actions = QHBoxLayout()
        self.add_participant_button = PrimaryButton("＋  Adicionar Participante")
        self.remove_participant_button = PrimaryButton("Remover Participante")
        for button in (
            self.add_participant_button,
            self.remove_participant_button,
        ):
            button.setEnabled(False)
            button.setToolTip("Disponível na Fase 2D2.")
            participant_actions.addWidget(button)
        participants.body.addLayout(participant_actions)
        upper.addWidget(participants, 3)
        self.content.addLayout(upper)

        controls = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setObjectName("placeholderSearch")
        self.search_field.setPlaceholderText("Procurar time...")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.textChanged.connect(self._search_changed)
        controls.addWidget(self.search_field, 1)
        controls.addStretch(1)
        self.points_button = PrimaryButton("＋  Adicionar Pontos")
        self.points_button.setEnabled(False)
        self.points_button.setToolTip("Disponível na Fase 2D2.")
        controls.addWidget(self.points_button)
        self.delete_selected_button = PrimaryButton("Remover Time")
        self.delete_selected_button.setEnabled(False)
        self.delete_selected_button.clicked.connect(self._delete_selected_team)
        controls.addWidget(self.delete_selected_button)
        self.content.addLayout(controls)

        self.error_banner = QLabel()
        self.error_banner.setObjectName("teamError")
        self.error_banner.setWordWrap(True)
        self.error_banner.hide()
        self.content.addWidget(self.error_banner)

        self.selected_label = QLabel("Nenhum time selecionado.")
        self.selected_label.setObjectName("teamSelection")
        self.content.addWidget(self.selected_label)

        table_card = Card()
        table_card.setMinimumHeight(400)
        table_card.body.setContentsMargins(0, 0, 0, 0)

        self.table_model = TeamTableModel(parent=self)
        self.table_view = QTableView()
        self.table_view.setObjectName("teamTable")
        self.table_view.setModel(self.table_model)
        self.table_view.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table_view.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_view.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table_view.setShowGrid(False)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.verticalHeader().setDefaultSectionSize(50)
        self.table_view.horizontalHeader().setMinimumHeight(46)
        for column in range(self.table_model.columnCount()):
            mode = (
                QHeaderView.ResizeMode.Stretch
                if column in (0, 1)
                else QHeaderView.ResizeMode.ResizeToContents
            )
            self.table_view.horizontalHeader().setSectionResizeMode(column, mode)
        self.table_view.clicked.connect(self._table_clicked)

        self.state_label = QLabel()
        self.state_label.setObjectName("teamState")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setWordWrap(True)
        self.state_label.setMinimumHeight(300)
        table_card.body.addWidget(self.table_view)
        table_card.body.addWidget(self.state_label)
        self.content.addWidget(table_card)

        self.total_label = QLabel()
        self.total_label.setObjectName("teamTotal")
        self.content.addWidget(self.total_label)
        self.content.addStretch(1)
        self.refresh_from_service()

    def refresh_from_service(self) -> None:
        self.error_banner.hide()
        self.create_button.setEnabled(self._service.editable)
        self.search_field.setEnabled(bool(self._service.teams))
        self._refresh_table()

    def _state_message(self) -> str | None:
        return {
            TeamLoadStatus.LOADING: "Carregando times...",
            TeamLoadStatus.FILE_MISSING: "Arquivo de times não encontrado.",
            TeamLoadStatus.FILE_EMPTY: "O arquivo de times está vazio.",
            TeamLoadStatus.INVALID_JSON: "Não foi possível carregar os times.",
            TeamLoadStatus.ROOT_NOT_LIST: "Não foi possível carregar os times.",
            TeamLoadStatus.READ_ERROR: "Não foi possível carregar os times.",
            TeamLoadStatus.VALID_EMPTY: "Não há times cadastrados.",
        }.get(self._service.load_result.status)

    def _search_changed(self, _text: str) -> None:
        self._clear_selection()
        self._refresh_table()

    def _refresh_table(self) -> None:
        total = len(self._service.teams)
        noun = "time" if total == 1 else "times"
        self.total_label.setText(f"Total de times: {total} {noun}")
        state_message = self._state_message()
        if state_message is not None:
            self._show_state(state_message)
            return
        filtered = filter_teams(self._service.teams, self.search_field.text())
        if not filtered:
            self._show_state("Nenhum time encontrado para esta busca.")
            return
        self.table_model.set_teams(filtered)
        self.table_view.show()
        self.state_label.hide()
        self._restore_selection(filtered)

    def _show_state(self, message: str) -> None:
        self.table_model.set_teams(())
        self.table_view.hide()
        self.state_label.setText(message)
        self.state_label.show()
        self._clear_selection()

    def _table_clicked(self, index: QModelIndex) -> None:
        team = self.table_model.team_at(index.row())
        if team is None:
            return
        self._select_team(team)
        if index.column() == TeamTableModel.ACTION_COLUMN:
            self._confirm_delete(team)

    def _select_team(self, team: Team) -> None:
        self._selected_source_index = team.source_index
        self.selected_label.setText(f"Time selecionado: {team.name}")
        self.delete_selected_button.setEnabled(self._service.editable)

    def _clear_selection(self) -> None:
        self._selected_source_index = None
        self.table_view.clearSelection()
        self.selected_label.setText("Nenhum time selecionado.")
        self.delete_selected_button.setEnabled(False)

    def _restore_selection(self, teams: tuple[Team, ...]) -> None:
        if self._selected_source_index is None:
            return
        for row, team in enumerate(teams):
            if team.source_index == self._selected_source_index:
                self.table_view.selectRow(row)
                self._select_team(team)
                return
        self._clear_selection()

    def _open_create_dialog(self) -> None:
        AddTeamDialog(self._create_team, self).exec()

    def _create_team(self, draft: TeamDraft) -> TeamOperationResult:
        result = self._service.create_team(draft)
        if result.succeeded:
            self.refresh_from_service()
            self.teams_changed.emit()
        else:
            self._show_save_error(result.message)
        return result

    def _delete_selected_team(self) -> None:
        if self._selected_source_index is None:
            return
        team = next(
            (
                candidate
                for candidate in self._service.teams
                if candidate.source_index == self._selected_source_index
            ),
            None,
        )
        if team is not None:
            self._confirm_delete(team)

    def _confirm_delete(self, team: Team) -> None:
        answer = QMessageBox.question(
            self,
            "Excluir time",
            f'Deseja realmente excluir o time "{team.name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        result = self._service.delete_team(team.source_index)
        if result.succeeded:
            self._clear_selection()
            self.refresh_from_service()
            self.teams_changed.emit()
        else:
            self._show_save_error(result.message)

    def _show_save_error(self, message: str) -> None:
        self.error_banner.setText(
            message or "Não foi possível salvar as alterações."
        )
        self.error_banner.show()
