"""Aggregate, read-only reports built from shared application state."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from acamp.models import format_currency
from acamp.reporting import CategoryCount, ReportSnapshot
from acamp.services import ReportingService

from ..widgets import Card, PageScaffold, ReportChartCard


def _chart_values(
    entries: tuple[CategoryCount, ...],
) -> tuple[tuple[str, int], ...]:
    return tuple((entry.label, entry.count) for entry in entries)


def _financial_metric(label: str) -> tuple[QFrame, QLabel]:
    metric = QFrame()
    metric.setObjectName("reportMetric")
    layout = QVBoxLayout(metric)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(5)

    label_widget = QLabel(label)
    label_widget.setObjectName("reportFinanceLabel")
    value_widget = QLabel("—")
    value_widget.setObjectName("reportFinanceValue")
    value_widget.setWordWrap(True)
    layout.addWidget(label_widget)
    layout.addWidget(value_widget)
    return metric, value_widget


class ReportsPage(PageScaffold):
    def __init__(self, service: ReportingService):
        super().__init__(
            "RELATÓRIOS",
            "Acompanhe os principais indicadores do acampamento.",
            "▥",
        )
        self._service = service
        self.last_snapshot: ReportSnapshot | None = None

        self.warning_banner = QLabel()
        self.warning_banner.setObjectName("reportWarning")
        self.warning_banner.setWordWrap(True)
        self.warning_banner.hide()
        self.content.addWidget(self.warning_banner)

        overview = Card("VISÃO GERAL")
        overview_row = QHBoxLayout()
        overview_row.setContentsMargins(2, 0, 2, 0)
        overview_row.setSpacing(18)
        self.total_label = QLabel("—")
        self.total_label.setObjectName("reportTotal")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overview_row.addWidget(self.total_label)
        caption = QLabel(
            "participantes válidos disponíveis no estado compartilhado"
        )
        caption.setObjectName("reportTotalCaption")
        caption.setWordWrap(True)
        overview_row.addWidget(caption, 1)
        overview.body.addLayout(overview_row)
        self.content.addWidget(overview)

        charts = QGridLayout()
        charts.setHorizontalSpacing(14)
        charts.setVerticalSpacing(14)
        for column in range(3):
            charts.setColumnStretch(column, 1)

        self.age_chart = ReportChartCard(
            "1. FAIXAS ETÁRIAS",
            "Distribuição em intervalos mutuamente exclusivos.",
        )
        charts.addWidget(self.age_chart, 0, 0, 1, 2)

        self.food_chart = ReportChartCard(
            "2. ALIMENTAÇÃO",
            "Respostas sobre consumo de carne.",
        )
        charts.addWidget(self.food_chart, 0, 2)

        self.accommodation_chart = ReportChartCard("3. ACOMODAÇÃO")
        charts.addWidget(self.accommodation_chart, 1, 0)

        self.transportation_chart = ReportChartCard(
            "4. TRANSPORTE",
            "Necessidade de ajuda com transporte.",
        )
        charts.addWidget(self.transportation_chart, 1, 1)

        self.payment_chart = ReportChartCard(
            "5. SITUAÇÃO DOS PAGAMENTOS",
            "Classificação centralizada da página Finanças.",
        )
        charts.addWidget(self.payment_chart, 1, 2)
        self.content.addLayout(charts)

        financial = Card(
            "6. RESUMO FINANCEIRO",
            "Os mesmos cálculos e valores exibidos na página Finanças.",
        )
        financial_grid = QGridLayout()
        financial_grid.setHorizontalSpacing(12)
        financial_grid.setVerticalSpacing(12)
        self.financial_labels: dict[str, QLabel] = {}
        for index, (key, label) in enumerate((
            ("entries", "Entradas"),
            ("expenses", "Gastos"),
            ("result", "Resultado do evento"),
            ("available", "Saldo disponível"),
        )):
            metric, value_label = _financial_metric(label)
            self.financial_labels[key] = value_label
            financial_grid.addWidget(metric, 0, index)
            financial_grid.setColumnStretch(index, 1)
        financial.body.addLayout(financial_grid)
        self.content.addWidget(financial)

        self.team_chart = ReportChartCard(
            "7. PONTUAÇÃO DAS EQUIPES",
            "Ranking por pontuação, da maior para a menor.",
        )
        self.team_chart.setMinimumHeight(390)
        self.ranking_label = QLabel()
        self.ranking_label.setObjectName("reportRanking")
        self.ranking_label.setWordWrap(True)
        self.team_chart.body.insertWidget(
            self.team_chart.body.count() - 2,
            self.ranking_label,
        )
        self.content.addWidget(self.team_chart)
        self.content.addStretch(1)

        self.refresh_from_service()

    def refresh_from_service(self) -> None:
        snapshot = self._service.snapshot()
        self.last_snapshot = snapshot
        self.total_label.setText(
            str(snapshot.participant_total)
            if snapshot.participants_available
            else "—"
        )
        self._refresh_participant_charts(snapshot)
        self._refresh_financial_summary(snapshot)
        self._refresh_team_chart(snapshot)
        self._refresh_warning(snapshot)

    def _refresh_participant_charts(
        self,
        snapshot: ReportSnapshot,
    ) -> None:
        charts = (
            self.age_chart,
            self.food_chart,
            self.accommodation_chart,
            self.transportation_chart,
            self.payment_chart,
        )
        if not snapshot.participants_available:
            for chart in charts:
                chart.show_empty(
                    "Os dados de participantes não estão disponíveis."
                )
            return
        if snapshot.participant_total == 0:
            for chart in charts:
                chart.show_empty(
                    "Não há dados suficientes para gerar este relatório."
                )
            return

        self.age_chart.set_bar_data(
            _chart_values(snapshot.age_groups),
            label_angle=-18,
        )
        self.food_chart.set_pie_data(
            _chart_values(snapshot.food_categories)
        )
        self.accommodation_chart.set_pie_data(
            _chart_values(snapshot.accommodation_categories)
        )
        self.transportation_chart.set_pie_data(
            _chart_values(snapshot.transportation_categories)
        )
        self.payment_chart.set_bar_data(
            _chart_values(snapshot.payment_statuses),
            label_angle=-18,
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

    def _refresh_team_chart(self, snapshot: ReportSnapshot) -> None:
        if not snapshot.teams_available:
            self.ranking_label.clear()
            self.team_chart.show_empty(
                "Os dados de equipes não estão disponíveis."
            )
            return
        if not snapshot.team_ranking:
            self.ranking_label.clear()
            self.team_chart.show_empty(
                "Ainda não há equipes cadastradas."
            )
            return

        ranking_lines = []
        chart_values = []
        for entry in snapshot.team_ranking:
            score = entry.team.score_value
            point_label = "ponto" if abs(score) == 1 else "pontos"
            ranking_lines.append(
                f"{entry.position}º  {entry.team.name} — "
                f"{score} {point_label}"
            )
            chart_values.append(
                (f"{entry.position}º {entry.team.name}", score)
            )
        self.ranking_label.setText("\n".join(ranking_lines))
        self.team_chart.set_bar_data(
            tuple(chart_values),
            label_angle=-20,
        )

    def _refresh_warning(self, snapshot: ReportSnapshot) -> None:
        messages: list[str] = []
        if not snapshot.participants_available:
            messages.append(
                "Os dados de participantes não estão disponíveis."
            )
        if (
            not snapshot.participants_available
            or not snapshot.inventory_available
        ):
            messages.append(
                "Os dados financeiros não estão totalmente disponíveis."
            )
        if not snapshot.teams_available:
            messages.append("Os dados de equipes não estão disponíveis.")
        if snapshot.has_unclassified_records:
            messages.append(
                "Alguns registros não puderam ser classificados."
            )

        self.warning_banner.setText("  •  ".join(messages))
        self.warning_banner.setVisible(bool(messages))
