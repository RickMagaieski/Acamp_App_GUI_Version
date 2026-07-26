"""Dashboard page shell."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from ..theme import ORANGE
from ..widgets import CampLandscape, Card, MetricCard, PageScaffold, PrimaryButton


class DashboardPage(PageScaffold):
    def __init__(self):
        refresh = PrimaryButton("▣  Atualizar Dados")
        refresh.setToolTip("Sincronização será implementada em uma fase futura.")
        super().__init__(
            "Dashboard (Visão Geral)",
            "Acompanhe os principais indicadores do acampamento.",
            "⌁",
            refresh,
        )

        metrics = QHBoxLayout()
        metrics.setSpacing(14)
        for title, accent in (
            ("TOTAL DE INSCRITOS", "#64784a"),
            ("ENTRADAS", "#4f6f39"),
            ("GASTOS", "#c94f22"),
            ("PAGAMENTOS PENDENTES", "#de921e"),
            ("PRECISAM DE TRANSPORTE", "#4d758a"),
        ):
            metrics.addWidget(MetricCard(title, accent), 1)
        self.content.addLayout(metrics)

        welcome = Card()
        welcome.setMinimumHeight(210)
        title = QLabel("Que bom te ver por aqui!")
        title.setObjectName("pageTitle")
        title.setStyleSheet("font-size: 24px;")
        message = QLabel("Que tudo o que fazemos aqui seja para a glória de Deus!")
        message.setObjectName("cardSubtitle")
        welcome.body.addWidget(title)
        welcome.body.addWidget(message)
        welcome.body.addWidget(CampLandscape())
        self.content.addWidget(welcome)
        self.content.addStretch(1)

