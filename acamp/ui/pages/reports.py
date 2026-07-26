"""Reports page shell."""

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel

from ..widgets import Card, ChartPlaceholder, PageScaffold


class ReportsPage(PageScaffold):
    def __init__(self):
        super().__init__(
            "Relatórios",
            "Acompanhe os principais indicadores do acampamento.",
            "▥",
        )

        grid = QGridLayout()
        grid.setSpacing(14)
        for index, title in enumerate(("1. FAIXAS ETÁRIAS", "2. ALIMENTAÇÃO", "3. ACOMODAÇÃO")):
            card = Card(title)
            row = QHBoxLayout()
            row.addWidget(ChartPlaceholder())
            legend = QLabel("Legenda e indicadores\nserão exibidos aqui.")
            legend.setObjectName("placeholderText")
            row.addWidget(legend, 1)
            card.body.addLayout(row)
            grid.addWidget(card, 0, index)

        transport = Card("4. TRANSPORTE")
        transport.add_placeholder("Resumo e gráfico de transporte")
        grid.addWidget(transport, 1, 0, 1, 2)

        finance = Card("5. FINANCEIRO")
        finance.add_placeholder("Entradas  —\n\nGastos  —\n\nSaldo atual  —")
        grid.addWidget(finance, 1, 2)

        payments = Card("6. PAGAMENTOS")
        payment_row = QHBoxLayout()
        payment_row.addWidget(ChartPlaceholder())
        payment_legend = QLabel("Pagos  —\n\nPendentes  —\n\nNão pagos  —")
        payment_legend.setObjectName("placeholderText")
        payment_row.addWidget(payment_legend, 1)
        payments.body.addLayout(payment_row)
        grid.addWidget(payments, 2, 0, 1, 3)

        self.content.addLayout(grid)
        self.content.addStretch(1)
