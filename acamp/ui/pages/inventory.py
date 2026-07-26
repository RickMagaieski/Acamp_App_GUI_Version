"""Inventory page shell."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit

from ..widgets import PageScaffold, PlaceholderTable, PrimaryButton


class InventoryPage(PageScaffold):
    def __init__(self):
        super().__init__(
            "INVENTÁRIO",
            "Gerencie os itens do acampamento e mantenha o controle do inventário.",
            "◇",
        )

        actions = QHBoxLayout()
        search = QLineEdit()
        search.setObjectName("placeholderSearch")
        search.setPlaceholderText("Procurar item...")
        search.setReadOnly(True)
        actions.addWidget(search, 1)
        actions.addStretch(1)
        actions.addWidget(PrimaryButton("＋  Adicionar item"))
        self.content.addLayout(actions)

        table = PlaceholderTable(
            ["Item", "Quantidade", "Valor (unit.)", "Descrição", "Ação"],
            rows=6,
        )
        table.setMinimumHeight(390)
        self.content.addWidget(table)

        total = QLabel("Total de itens: —")
        total.setObjectName("cardSubtitle")
        self.content.addWidget(total)
        self.content.addStretch(1)

