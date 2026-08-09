"""Aggregate, read-only reports built from shared application state."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
)

from acamp.models import format_currency
from acamp.reporting import CategoryCount, ReportSnapshot
from acamp.services import ReportingService

from ..widgets import CampLandscape, Card, PageScaffold, ReportChartCard


def _chart_values(
    entries: tuple[CategoryCount, ...],
) -> tuple[tuple[str, int], ...]:
    return tuple((entry.label, entry.count) for entry in entries)


def _financial_metric(label: str) -> tuple[QFrame, QLabel]:
    metric = QFrame()
    metric.setObjectName("reportMetric")
    layout = QHBoxLayout(metric)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(12)

    label_widget = QLabel(label)
    label_widget.setObjectName("reportFinanceLabel")
    value_widget = QLabel("—")
    value_widget.setObjectName("reportFinanceValue")
    value_widget.setWordWrap(True)
    value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
    layout.addWidget(label_widget, 1)
    layout.addWidget(value_widget)
    return metric, value_widget


class ReportsPage(PageScaffold):
    def __init__(self, service: ReportingService):
        super().__init__(
            "Reports",
            "Acompanhe os principais indicadores do acampamento.",
            "reports",
        )
        self._service = service
        self.last_snapshot: ReportSnapshot | None = None

        self.total_label = QLabel("—", self.canvas)
        self.total_label.setObjectName("reportTotal")
        self.total_label.hide()

        top_charts = QGridLayout()
        top_charts.setHorizontalSpacing(14)
        top_charts.setVerticalSpacing(14)
        for column in range(3):
            top_charts.setColumnStretch(column, 1)

        self.age_chart = ReportChartCard(
            "1. FAIXAS ETÁRIAS",
        )
        self.age_chart.setFixedHeight(285)
        top_charts.addWidget(self.age_chart, 0, 0)

        self.food_chart = ReportChartCard(
            "2. ALIMENTAÇÃO",
        )
        self.food_chart.setFixedHeight(285)
        top_charts.addWidget(self.food_chart, 0, 1)

        self.accommodation_chart = ReportChartCard("3. ACOMODAÇÃO")
        self.accommodation_chart.setFixedHeight(285)
        top_charts.addWidget(self.accommodation_chart, 0, 2)
        self.content.addLayout(top_charts)

        self.transportation_chart = ReportChartCard(
            "4. TRANSPORTE",
        )
        self.transportation_chart.setFixedHeight(265)

        financial = Card("5. FINANCEIRO", icon_name="finance")
        financial.setFixedHeight(265)
        self.financial_labels: dict[str, QLabel] = {}
        for key, label in (
            ("entries", "Entradas"),
            ("expenses", "Gastos"),
            ("result", "Saldo atual"),
        ):
            metric, value_label = _financial_metric(label)
            self.financial_labels[key] = value_label
            financial.body.addWidget(metric)
        available_label = QLabel("—", self.canvas)
        available_label.hide()
        self.financial_labels["available"] = available_label

        middle = QHBoxLayout()
        middle.setSpacing(14)
        middle.addWidget(self.transportation_chart, 3)
        middle.addWidget(financial, 2)
        self.content.addLayout(middle)

        self.payment_chart = ReportChartCard("6. PAGAMENTOS")
        self.payment_chart.setFixedHeight(245)
        self.content.addWidget(self.payment_chart)

        self.content.addWidget(CampLandscape())

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

        self.age_chart.set_pie_data(
            _chart_values(snapshot.age_groups)
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
        self.payment_chart.set_pie_data(
            _chart_values(snapshot.payment_statuses)
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
