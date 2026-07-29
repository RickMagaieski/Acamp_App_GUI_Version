"""Functional aggregate overview using the shared application state."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from acamp.models import format_currency
from acamp.reporting import ReportSnapshot
from acamp.services import (
    ParticipantSynchronizationResult,
    ReportingService,
)

from ..widgets import (
    CampLandscape,
    Card,
    MetricCard,
    PageScaffold,
    PrimaryButton,
)


def _summary_row(label: str) -> tuple[QWidget, QLabel]:
    row = QWidget()
    row.setObjectName("dashboardSummaryRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 7, 0, 7)
    layout.setSpacing(12)
    name_label = QLabel(label)
    name_label.setObjectName("dashboardSummaryLabel")
    value_label = QLabel("—")
    value_label.setObjectName("dashboardSummaryValue")
    value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
    layout.addWidget(name_label, 1)
    layout.addWidget(value_label)
    return row, value_label


class DashboardPage(PageScaffold):
    navigate_requested = Signal(int)
    sync_requested = Signal()

    REGISTRATIONS_PAGE = 1
    FINANCE_PAGE = 2
    INVENTORY_PAGE = 3
    ACTIVITIES_PAGE = 4
    REPORTS_PAGE = 5

    def __init__(self, service: ReportingService):
        self._service = service
        self.last_snapshot: ReportSnapshot | None = None
        self._last_sync_status_text = (
            "Ainda não sincronizado nesta sessão."
        )
        self._cache_reconciliation_message = ""

        sync_panel = QWidget()
        sync_layout = QVBoxLayout(sync_panel)
        sync_layout.setContentsMargins(0, 0, 0, 0)
        sync_layout.setSpacing(5)
        self.sync_button = PrimaryButton("▣  Sincronizar Google Sheets")
        self.sync_button.setToolTip(
            "Baixar manualmente as inscrições da planilha configurada."
        )
        self.sync_status_label = QLabel(
            self._last_sync_status_text
        )
        self.sync_status_label.setObjectName("dashboardSyncStatus")
        self.sync_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sync_layout.addWidget(self.sync_button)
        sync_layout.addWidget(self.sync_status_label)

        super().__init__(
            "Dashboard (Visão Geral)",
            "Acompanhe os principais indicadores do acampamento.",
            "⌁",
            sync_panel,
        )
        self.sync_button.clicked.connect(self.sync_requested.emit)

        self.warning_banner = QLabel()
        self.warning_banner.setObjectName("dashboardWarning")
        self.warning_banner.setWordWrap(True)
        self.warning_banner.hide()
        self.content.addWidget(self.warning_banner)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(14)
        metrics.setVerticalSpacing(14)
        self.metric_cards: dict[str, MetricCard] = {}
        definitions = (
            (
                "participants",
                "TOTAL DE INSCRITOS",
                "#64784a",
                "♙",
                self.REGISTRATIONS_PAGE,
                "Abrir Inscrições",
            ),
            (
                "paid",
                "PAGAMENTOS COMPLETOS",
                "#4f6f39",
                "✓",
                self.FINANCE_PAGE,
                "Abrir Finanças",
            ),
            (
                "pending",
                "PAGAMENTOS PENDENTES",
                "#de921e",
                "!",
                self.FINANCE_PAGE,
                "Abrir Finanças",
            ),
            (
                "inventory",
                "ITENS NO INVENTÁRIO",
                "#4d758a",
                "◇",
                self.INVENTORY_PAGE,
                "Abrir Inventário",
            ),
            (
                "teams",
                "EQUIPES CADASTRADAS",
                "#315b40",
                "♜",
                self.ACTIVITIES_PAGE,
                "Abrir Atividades",
            ),
        )
        for column, (
            key,
            title,
            accent,
            icon,
            destination,
            tooltip,
        ) in enumerate(definitions):
            card = MetricCard(title, accent, icon)
            card.set_clickable(tooltip)
            card.clicked.connect(
                lambda page=destination: self.navigate_requested.emit(page)
            )
            self.metric_cards[key] = card
            metrics.addWidget(card, 0, column)
            metrics.setColumnStretch(column, 1)
        self.content.addLayout(metrics)

        summaries = QGridLayout()
        summaries.setHorizontalSpacing(14)
        summaries.setVerticalSpacing(14)
        for column in range(3):
            summaries.setColumnStretch(column, 1)

        financial = Card(
            "RESUMO FINANCEIRO",
            "Valores compartilhados com Finanças e Relatórios.",
        )
        self.financial_labels: dict[str, QLabel] = {}
        for key, label in (
            ("entries", "Entradas"),
            ("expenses", "Gastos"),
            ("result", "Resultado do evento"),
            ("available", "Saldo disponível"),
        ):
            row, value_label = _summary_row(label)
            self.financial_labels[key] = value_label
            financial.body.addWidget(row)
        summaries.addWidget(financial, 0, 0)

        quick = Card("INFORMAÇÕES RÁPIDAS")
        self.quick_labels: dict[str, QLabel] = {}
        for key, label in (
            ("transportation", "Precisam de transporte"),
            ("partial", "Pagamentos parciais"),
            ("inventory_units", "Unidades no inventário"),
        ):
            row, value_label = _summary_row(label)
            self.quick_labels[key] = value_label
            quick.body.addWidget(row)
        self.reports_button = PrimaryButton("Ver Relatórios  →")
        self.reports_button.clicked.connect(
            lambda: self.navigate_requested.emit(self.REPORTS_PAGE)
        )
        quick.body.addWidget(self.reports_button)
        summaries.addWidget(quick, 0, 1)

        teams = Card("DESTAQUE DAS EQUIPES")
        self.team_leader_label = QLabel("—")
        self.team_leader_label.setObjectName("dashboardTeamLeader")
        self.team_leader_label.setWordWrap(True)
        self.team_score_label = QLabel("Pontuação: —")
        self.team_score_label.setObjectName("dashboardTeamScore")
        self.team_members_label = QLabel("Participantes nos times: —")
        self.team_members_label.setObjectName("cardSubtitle")
        self.ranking_preview = QLabel()
        self.ranking_preview.setObjectName("dashboardRankingPreview")
        self.ranking_preview.setWordWrap(True)
        teams.body.addWidget(self.team_leader_label)
        teams.body.addWidget(self.team_score_label)
        teams.body.addWidget(self.team_members_label)
        teams.body.addWidget(self.ranking_preview, 1)
        self.activities_button = PrimaryButton("Ver Atividades  →")
        self.activities_button.clicked.connect(
            lambda: self.navigate_requested.emit(self.ACTIVITIES_PAGE)
        )
        teams.body.addWidget(self.activities_button)
        summaries.addWidget(teams, 0, 2)
        self.content.addLayout(summaries)

        welcome = Card()
        welcome.setMinimumHeight(210)
        welcome_layout = QHBoxLayout()
        welcome_text = QVBoxLayout()
        title = QLabel("Que bom te ver por aqui!")
        title.setObjectName("dashboardWelcomeTitle")
        message = QLabel(
            "Que tudo o que fazemos aqui seja para a glória de Deus!"
        )
        message.setObjectName("cardSubtitle")
        message.setWordWrap(True)
        welcome_text.addWidget(title)
        welcome_text.addWidget(message)
        welcome_text.addStretch(1)
        welcome_layout.addLayout(welcome_text, 2)
        welcome_layout.addWidget(CampLandscape(), 3)
        welcome.body.addLayout(welcome_layout)
        self.content.addWidget(welcome)
        self.content.addStretch(1)
        self.refresh_from_service()

    def refresh_from_service(self) -> None:
        snapshot = self._service.snapshot()
        self.last_snapshot = snapshot
        self._refresh_primary_metrics(snapshot)
        self._refresh_financial_summary(snapshot)
        self._refresh_quick_information(snapshot)
        self._refresh_team_summary(snapshot)
        self._refresh_warning(snapshot)

    def _refresh_primary_metrics(self, snapshot: ReportSnapshot) -> None:
        if snapshot.participants_available:
            self.metric_cards["participants"].set_value(
                str(snapshot.participant_total)
            )
            self.metric_cards["paid"].set_value(str(snapshot.paid_count))
            self.metric_cards["pending"].set_value(
                str(snapshot.pending_count)
            )
            if snapshot.participant_total:
                self.metric_cards["participants"].set_details(
                    "Abrir Inscrições"
                )
                self.metric_cards["paid"].set_details("Classificação: Pago")
                self.metric_cards["pending"].set_details(
                    f"Parciais: {snapshot.partial_count}"
                )
            else:
                self.metric_cards["participants"].set_details(
                    "Nenhum participante cadastrado"
                )
                self.metric_cards["paid"].set_details(
                    "Não há pagamentos para resumir."
                )
                self.metric_cards["pending"].set_details(
                    "Não há pagamentos para resumir."
                )
        else:
            for key in ("participants", "paid", "pending"):
                self.metric_cards[key].set_value("—")
            self.metric_cards["participants"].set_details(
                "Dados de participantes indisponíveis."
            )
            self.metric_cards["paid"].set_details(
                "Dados de pagamentos indisponíveis."
            )
            self.metric_cards["pending"].set_details(
                "Dados de pagamentos indisponíveis."
            )

        if snapshot.inventory_available:
            self.metric_cards["inventory"].set_value(
                str(snapshot.inventory_item_count)
            )
            inventory_details = (
                f"Unidades: {snapshot.inventory_unit_count}"
                if snapshot.inventory_item_count
                else "O inventário está vazio."
            )
            self.metric_cards["inventory"].set_details(inventory_details)
        else:
            self.metric_cards["inventory"].set_value("—")
            self.metric_cards["inventory"].set_details(
                "Dados do inventário indisponíveis."
            )

        if snapshot.teams_available:
            self.metric_cards["teams"].set_value(str(snapshot.team_count))
            team_details = (
                f"Membros: {snapshot.team_member_count}"
                if snapshot.team_count
                else "Ainda não há equipes cadastradas."
            )
            self.metric_cards["teams"].set_details(team_details)
        else:
            self.metric_cards["teams"].set_value("—")
            self.metric_cards["teams"].set_details(
                "Dados de equipes indisponíveis."
            )

    def _refresh_financial_summary(
        self,
        snapshot: ReportSnapshot,
    ) -> None:
        financial = snapshot.financial
        self.financial_labels["entries"].setText(
            format_currency(financial.entries)
        )
        self.financial_labels["expenses"].setText(
            format_currency(financial.expenses)
        )
        self.financial_labels["result"].setText(
            format_currency(financial.event_result)
        )
        self.financial_labels["available"].setText(
            format_currency(financial.available_balance)
        )

    def _refresh_quick_information(
        self,
        snapshot: ReportSnapshot,
    ) -> None:
        if snapshot.participants_available:
            self.quick_labels["transportation"].setText(
                str(snapshot.transportation_help_count)
            )
            self.quick_labels["partial"].setText(
                str(snapshot.partial_count)
            )
        else:
            self.quick_labels["transportation"].setText("—")
            self.quick_labels["partial"].setText("—")

        self.quick_labels["inventory_units"].setText(
            str(snapshot.inventory_unit_count)
            if snapshot.inventory_available
            else "—"
        )

    def _refresh_team_summary(self, snapshot: ReportSnapshot) -> None:
        if not snapshot.teams_available:
            self.team_leader_label.setText(
                "Dados de equipes indisponíveis."
            )
            self.team_score_label.setText("Pontuação: —")
            self.team_members_label.setText("Participantes nos times: —")
            self.ranking_preview.clear()
            return

        self.team_members_label.setText(
            f"Participantes nos times: {snapshot.team_member_count}"
        )
        leader = snapshot.leading_team
        if leader is None:
            self.team_leader_label.setText(
                "Ainda não há equipes cadastradas."
            )
            self.team_score_label.setText("Pontuação: —")
            self.ranking_preview.clear()
            return

        self.team_leader_label.setText(leader.team.name)
        self.team_score_label.setText(
            f"Pontuação da líder: {leader.team.score_value}"
        )
        preview_lines = tuple(
            f"{entry.position}º  {entry.team.name} — "
            f"{entry.team.score_value} pontos"
            for entry in snapshot.team_ranking[:3]
        )
        self.ranking_preview.setText("\n".join(preview_lines))

    def _refresh_warning(self, snapshot: ReportSnapshot) -> None:
        messages: list[str] = []
        if self._cache_reconciliation_message:
            messages.append(self._cache_reconciliation_message)
        if not snapshot.participants_available:
            messages.append("Dados de participantes indisponíveis.")
        if not snapshot.inventory_available:
            messages.append("Dados do inventário indisponíveis.")
        if not snapshot.teams_available:
            messages.append("Dados de equipes indisponíveis.")
        if snapshot.has_unclassified_records:
            messages.append(
                "Alguns registros não puderam ser contabilizados."
            )
        self.warning_banner.setText("  •  ".join(messages))
        self.warning_banner.setVisible(bool(messages))

    def set_participant_operation(self, operation: str | None) -> None:
        self.sync_button.setEnabled(operation is None)
        if operation == "synchronization":
            self.sync_button.setText("Sincronizando...")
            self.sync_status_label.setText("Sincronizando...")
        elif operation == "deletion":
            self.sync_button.setText("▣  Sincronizar Google Sheets")
            self.sync_status_label.setText("Removendo inscrição...")
        else:
            self.sync_button.setText("▣  Sincronizar Google Sheets")
            self.sync_status_label.setText(self._last_sync_status_text)

    def set_sync_busy(self, busy: bool) -> None:
        self.set_participant_operation(
            "synchronization" if busy else None
        )

    def mark_cache_reconciliation_required(self, message: str) -> None:
        self._cache_reconciliation_message = message
        self._last_sync_status_text = (
            "Sincronização necessária antes de fechar o aplicativo."
        )
        if self.last_snapshot is not None:
            self._refresh_warning(self.last_snapshot)

    def clear_cache_reconciliation_warning(self) -> None:
        self._cache_reconciliation_message = ""
        if self.last_snapshot is not None:
            self._refresh_warning(self.last_snapshot)

    def show_sync_success(
        self,
        result: ParticipantSynchronizationResult,
        completed_at: datetime,
    ) -> None:
        self._last_sync_status_text = (
            "Última sincronização nesta sessão: "
            f"{completed_at.astimezone().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        self.sync_status_label.setText(self._last_sync_status_text)

        participant_label = (
            "participante carregado"
            if result.loaded_count == 1
            else "participantes carregados"
        )
        message = (
            "Sincronização concluída. "
            f"{result.loaded_count} {participant_label}."
        )
        details: list[str] = []
        if result.skipped_rows:
            row_label = (
                "linha ignorada"
                if result.skipped_rows == 1
                else "linhas ignoradas"
            )
            details.append(f"{result.skipped_rows} {row_label}")
        if result.warning_rows:
            row_label = (
                "linha ajustada"
                if result.warning_rows == 1
                else "linhas ajustadas"
            )
            details.append(f"{result.warning_rows} {row_label}")
        if details:
            message = (
                "Sincronização concluída com avisos. "
                f"{result.loaded_count} {participant_label}; "
                f"{' e '.join(details)}."
            )

        QMessageBox.information(
            self,
            "Google Sheets",
            message,
        )

    def show_sync_error(self, message: str) -> None:
        QMessageBox.warning(
            self,
            "Não foi possível sincronizar",
            message,
        )
