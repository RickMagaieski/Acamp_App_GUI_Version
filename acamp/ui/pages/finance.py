"""Finance page shell."""

from PySide6.QtWidgets import QHBoxLayout, QLabel

from ..widgets import Card, PageScaffold, PrimaryButton


class FinancePage(PageScaffold):
    def __init__(self):
        super().__init__(
            "FINANÇAS",
            "Acompanhe preços, pagamentos e o resumo financeiro do acampamento.",
            "▥",
        )

        columns = QHBoxLayout()
        columns.setSpacing(16)

        prices = Card("LISTA DE PREÇOS")
        prices.add_placeholder("Categorias e preços aparecerão aqui.")
        columns.addWidget(prices, 1)

        payments = Card("PAGAMENTOS")
        payments.add_placeholder("Pagos  —\n\nPendentes  —\n\nNão pagos  —")
        payments.body.addWidget(PrimaryButton("Ver todos os pagamentos  →"))
        columns.addWidget(payments, 1)

        summary = Card("RESUMO FINANCEIRO")
        summary.add_placeholder("Saldo inicial  —\n\nEntradas  —\n\nGastos  —\n\nTotal final  —")
        columns.addWidget(summary, 1)
        self.content.addLayout(columns)

        lower = QHBoxLayout()
        total = Card("TOTAL FINAL")
        amount = QLabel("$ —")
        amount.setObjectName("metricValue")
        total.body.addWidget(amount)
        lower.addWidget(total, 3)

        quote = Card("“ Tudo posso naquele que me fortalece. ”", "Filipenses 4:13")
        lower.addWidget(quote, 2)
        self.content.addLayout(lower)
        self.content.addStretch(1)

