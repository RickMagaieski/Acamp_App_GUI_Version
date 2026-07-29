"""Team management, members, scoring, and ranking."""

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

from acamp.models import Team, TeamDraft, TeamMemberDraft
from acamp.reporting import rank_teams
from acamp.repositories import TeamLoadStatus
from acamp.services import TeamOperationResult, TeamService
from acamp.ui.dialogs import (
    AddTeamDialog,
    AddTeamMemberDialog,
    ScoreChangeDialog,
    confirm_destructive,
)
from acamp.ui.models import (
    TeamMemberTableModel,
    TeamRankingTableModel,
    TeamTableModel,
    filter_teams,
)

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
        self._selected_member_source_index: int | None = None

        upper = QHBoxLayout()
        upper.setSpacing(16)

        create_team = Card(
            "CRIAR TIME",
            "Crie um time vazio. Participantes são gerenciados separadamente.",
        )
        self.create_button = PrimaryButton("＋  Novo Time")
        self.create_button.clicked.connect(self._open_create_dialog)
        create_team.body.addWidget(self.create_button)
        upper.addWidget(create_team, 2)

        selected_card = Card("TIME SELECIONADO")
        self.selected_name_label = QLabel("Selecione uma equipe.")
        self.selected_name_label.setObjectName("selectedTeamName")
        self.selected_meta_label = QLabel("Líder: —   •   Cor: —")
        self.selected_meta_label.setObjectName("cardSubtitle")
        self.selected_score_label = QLabel("Pontuação: —")
        self.selected_score_label.setObjectName("selectedTeamScore")
        selected_card.body.addWidget(self.selected_name_label)
        selected_card.body.addWidget(self.selected_meta_label)
        selected_card.body.addWidget(self.selected_score_label)

        participant_actions = QHBoxLayout()
        self.add_participant_button = PrimaryButton("＋  Adicionar Participante")
        self.add_participant_button.clicked.connect(
            self._open_add_member_dialog
        )
        participant_actions.addWidget(self.add_participant_button)
        self.remove_participant_button = PrimaryButton("Remover Participante")
        self.remove_participant_button.clicked.connect(
            self._remove_selected_member
        )
        participant_actions.addWidget(self.remove_participant_button)
        selected_card.body.addLayout(participant_actions)
        upper.addWidget(selected_card, 3)
        self.content.addLayout(upper)

        controls = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setObjectName("placeholderSearch")
        self.search_field.setPlaceholderText("Procurar time...")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.textChanged.connect(self._search_changed)
        controls.addWidget(self.search_field, 1)
        controls.addStretch(1)
        self.add_points_button = PrimaryButton("＋  Adicionar Pontos")
        self.add_points_button.clicked.connect(
            lambda: self._open_score_dialog(adding=True)
        )
        controls.addWidget(self.add_points_button)
        self.points_button = self.add_points_button
        self.remove_points_button = PrimaryButton("−  Remover Pontos")
        self.remove_points_button.clicked.connect(
            lambda: self._open_score_dialog(adding=False)
        )
        controls.addWidget(self.remove_points_button)
        self.delete_selected_button = PrimaryButton("Remover Time")
        self.delete_selected_button.clicked.connect(self._delete_selected_team)
        controls.addWidget(self.delete_selected_button)
        self.content.addLayout(controls)

        self.error_banner = QLabel()
        self.error_banner.setObjectName("teamError")
        self.error_banner.setWordWrap(True)
        self.error_banner.hide()
        self.content.addWidget(self.error_banner)

        team_card = Card("TIMES")
        team_card.body.setContentsMargins(0, 16, 0, 0)
        self.table_model = TeamTableModel(parent=self)
        self.table_view = self._make_table("teamTable", self.table_model, 48)
        self.table_view.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table_view.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        for column in (2, 3, 4, 5):
            self.table_view.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table_view.clicked.connect(self._team_table_clicked)
        self.team_state_label = self._state_label(245)
        team_card.body.addWidget(self.table_view)
        team_card.body.addWidget(self.team_state_label)
        self.content.addWidget(team_card)

        lower = QHBoxLayout()
        lower.setSpacing(16)

        members_card = Card("PARTICIPANTES DO TIME")
        self.member_count_label = QLabel("Total: 0 participantes")
        self.member_count_label.setObjectName("cardSubtitle")
        members_card.body.addWidget(self.member_count_label)
        self.member_model = TeamMemberTableModel(parent=self)
        self.member_table = self._make_table(
            "teamMemberTable",
            self.member_model,
            42,
        )
        self.member_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.member_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.member_table.clicked.connect(self._member_table_clicked)
        self.member_state_label = self._state_label(180)
        members_card.body.addWidget(self.member_table)
        members_card.body.addWidget(self.member_state_label)
        lower.addWidget(members_card, 3)

        ranking_card = Card("RANKING")
        self.ranking_model = TeamRankingTableModel(parent=self)
        self.ranking_table = self._make_table(
            "teamRankingTable",
            self.ranking_model,
            42,
        )
        self.ranking_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.ranking_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.ranking_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.ranking_table.clicked.connect(self._ranking_clicked)
        self.ranking_state_label = self._state_label(180)
        ranking_card.body.addWidget(self.ranking_table)
        ranking_card.body.addWidget(self.ranking_state_label)
        lower.addWidget(ranking_card, 2)
        self.content.addLayout(lower)

        self.total_label = QLabel()
        self.total_label.setObjectName("teamTotal")
        self.content.addWidget(self.total_label)
        self.content.addStretch(1)
        self.refresh_from_service()

    @staticmethod
    def _make_table(
        object_name: str,
        model,
        row_height: int,
    ) -> QTableView:
        table = QTableView()
        table.setObjectName(object_name)
        table.setModel(model)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(row_height)
        table.horizontalHeader().setMinimumHeight(42)
        return table

    @staticmethod
    def _state_label(minimum_height: int) -> QLabel:
        label = QLabel()
        label.setObjectName("teamState")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setMinimumHeight(minimum_height)
        return label

    def refresh_from_service(self) -> None:
        self.error_banner.hide()
        self.create_button.setEnabled(self._service.editable)
        self.search_field.setEnabled(bool(self._service.teams))
        self._refresh_team_table()
        self._refresh_ranking()

    def _load_state_message(self) -> str | None:
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
        self._clear_team_selection()
        self._refresh_team_table()

    def _refresh_team_table(self) -> None:
        total = len(self._service.teams)
        noun = "time" if total == 1 else "times"
        self.total_label.setText(f"Total de times: {total} {noun}")
        load_message = self._load_state_message()
        if load_message is not None:
            self.table_model.set_teams(())
            self.table_view.hide()
            self.team_state_label.setText(load_message)
            self.team_state_label.show()
            self._clear_team_selection()
            return

        filtered = filter_teams(self._service.teams, self.search_field.text())
        if not filtered:
            self.table_model.set_teams(())
            self.table_view.hide()
            self.team_state_label.setText(
                "Nenhum time encontrado para esta busca."
            )
            self.team_state_label.show()
            self._clear_team_selection()
            return

        self.table_model.set_teams(filtered)
        self.table_view.show()
        self.team_state_label.hide()
        self._restore_team_selection(filtered)

    def _refresh_ranking(self) -> None:
        entries = rank_teams(self._service.teams)
        self.ranking_model.set_entries(entries)
        if entries:
            self.ranking_table.show()
            self.ranking_state_label.hide()
        else:
            self.ranking_table.hide()
            self.ranking_state_label.setText("Não há times no ranking.")
            self.ranking_state_label.show()

    def _team_table_clicked(self, index: QModelIndex) -> None:
        team = self.table_model.team_at(index.row())
        if team is None:
            return
        self._select_team(team)
        if index.column() == TeamTableModel.ACTION_COLUMN:
            self._confirm_delete_team(team)

    def _ranking_clicked(self, index: QModelIndex) -> None:
        entry = self.ranking_model.entry_at(index.row())
        if entry is None:
            return
        if self.search_field.text():
            self.search_field.clear()
        self._select_team(entry.team)
        for row in range(self.table_model.rowCount()):
            team = self.table_model.team_at(row)
            if team and team.source_index == entry.team.source_index:
                self.table_view.selectRow(row)
                break

    def _select_team(self, team: Team) -> None:
        self._selected_source_index = team.source_index
        self._selected_member_source_index = None
        self.selected_name_label.setText(team.name)
        self.selected_meta_label.setText(
            f"Líder: {team.leader}   •   Cor: {team.color}"
        )
        self.selected_score_label.setText(
            f"Pontuação atual: {team.score_value}"
        )
        editable = self._service.editable
        self.add_participant_button.setEnabled(
            editable and team.members_writable
        )
        self.remove_participant_button.setEnabled(False)
        self.add_points_button.setEnabled(editable)
        self.remove_points_button.setEnabled(editable)
        self.delete_selected_button.setEnabled(editable)
        self._refresh_member_panel(team)

    def _clear_team_selection(self) -> None:
        self._selected_source_index = None
        self._selected_member_source_index = None
        self.table_view.clearSelection()
        self.selected_name_label.setText("Selecione uma equipe.")
        self.selected_meta_label.setText("Líder: —   •   Cor: —")
        self.selected_score_label.setText("Pontuação: —")
        for button in (
            self.add_participant_button,
            self.remove_participant_button,
            self.add_points_button,
            self.remove_points_button,
            self.delete_selected_button,
        ):
            button.setEnabled(False)
        self.member_model.set_members(())
        self.member_table.hide()
        self.member_count_label.setText("Total: 0 participantes")
        self.member_state_label.setText(
            "Selecione uma equipe para gerenciar participantes e pontuação."
        )
        self.member_state_label.show()

    def _restore_team_selection(self, teams: tuple[Team, ...]) -> None:
        if self._selected_source_index is None:
            self._clear_team_selection()
            return
        for row, team in enumerate(teams):
            if team.source_index == self._selected_source_index:
                self.table_view.selectRow(row)
                self._select_team(team)
                return
        self._clear_team_selection()

    def _refresh_member_panel(self, team: Team) -> None:
        count = team.participant_count
        if count is None:
            self.member_count_label.setText("Total: —")
            self.member_model.set_members(())
            self.member_table.hide()
            self.member_state_label.setText(
                "A lista de participantes desta equipe é inválida."
            )
            self.member_state_label.show()
            return

        noun = "participante" if count == 1 else "participantes"
        self.member_count_label.setText(f"Total: {count} {noun}")
        self.member_model.set_members(team.members)
        self._selected_member_source_index = None
        self.remove_participant_button.setEnabled(False)
        if team.members:
            self.member_table.show()
            self.member_state_label.hide()
        else:
            self.member_table.hide()
            self.member_state_label.setText(
                "Esta equipe ainda não possui participantes."
            )
            self.member_state_label.show()

    def _member_table_clicked(self, index: QModelIndex) -> None:
        member = self.member_model.member_at(index.row())
        if member is None:
            return
        self._selected_member_source_index = member.source_index
        self.remove_participant_button.setEnabled(
            self._service.editable and self._selected_source_index is not None
        )

    def _selected_team(self) -> Team | None:
        if self._selected_source_index is None:
            return None
        return self._service.team_by_source_index(
            self._selected_source_index
        )

    def _open_create_dialog(self) -> None:
        AddTeamDialog(self._create_team, self).exec()

    def _create_team(self, draft: TeamDraft) -> TeamOperationResult:
        result = self._service.create_team(draft)
        self._finish_mutation(result, preserve_selection=True)
        return result

    def _open_add_member_dialog(self) -> None:
        team = self._selected_team()
        if team is None:
            self._show_action_error("Selecione uma equipe.")
            return
        AddTeamMemberDialog(team.name, self._add_member, self).exec()

    def _add_member(self, draft: TeamMemberDraft) -> TeamOperationResult:
        if self._selected_source_index is None:
            result = TeamOperationResult(False, "Selecione uma equipe.")
        else:
            result = self._service.add_member(
                self._selected_source_index,
                draft,
            )
        self._finish_mutation(result, preserve_selection=True)
        return result

    def _remove_selected_member(self) -> None:
        team = self._selected_team()
        if team is None:
            self._show_action_error("Selecione uma equipe.")
            return
        if self._selected_member_source_index is None:
            self._show_action_error(
                "Selecione um participante para remover."
            )
            return
        member = next(
            (
                candidate
                for candidate in team.members
                if candidate.source_index
                == self._selected_member_source_index
            ),
            None,
        )
        if member is None:
            self._show_action_error(
                "Selecione um participante para remover."
            )
            return

        confirmed = confirm_destructive(
            self,
            title="Remover participante",
            message=f'Remover "{member.name}" do time "{team.name}"?',
            confirm_text="Remover",
        )
        if not confirmed:
            return
        result = self._service.remove_member(
            team.source_index,
            member.source_index,
        )
        self._finish_mutation(result, preserve_selection=True)

    def _open_score_dialog(self, *, adding: bool) -> None:
        team = self._selected_team()
        if team is None:
            self._show_action_error("Selecione uma equipe.")
            return
        ScoreChangeDialog(
            team.name,
            adding=adding,
            submit=self._change_score,
            parent=self,
        ).exec()

    def _change_score(self, delta: int) -> TeamOperationResult:
        if self._selected_source_index is None:
            result = TeamOperationResult(False, "Selecione uma equipe.")
        else:
            result = self._service.change_score(
                self._selected_source_index,
                delta,
            )
        self._finish_mutation(result, preserve_selection=True)
        return result

    def _delete_selected_team(self) -> None:
        team = self._selected_team()
        if team is None:
            self._show_action_error("Selecione uma equipe.")
            return
        self._confirm_delete_team(team)

    def _confirm_delete_team(self, team: Team) -> None:
        confirmed = confirm_destructive(
            self,
            title="Excluir time",
            message=f'Deseja realmente excluir o time "{team.name}"?',
            confirm_text="Excluir",
        )
        if not confirmed:
            return
        result = self._service.delete_team(team.source_index)
        if result.succeeded:
            self._selected_source_index = None
        self._finish_mutation(result, preserve_selection=False)

    def _finish_mutation(
        self,
        result: TeamOperationResult,
        *,
        preserve_selection: bool,
    ) -> None:
        if not result.succeeded:
            self._show_action_error(result.message)
            return
        if not preserve_selection:
            self._selected_source_index = None
        self.refresh_from_service()
        self.teams_changed.emit()

    def _show_action_error(self, message: str) -> None:
        self.error_banner.setText(
            message or "Não foi possível salvar as alterações."
        )
        self.error_banner.show()
