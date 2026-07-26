"""Registrations page shell."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit

from ..widgets import PageScaffold, PlaceholderTable, PrimaryButton


class RegistrationsPage(PageScaffold):
    def __init__(self):
        super().__init__(
            "INSCRIÇÕES",
            "Gerencie os participantes inscritos no acampamento.",
            "♙",
        )

        search_row = QHBoxLayout()
        search = QLineEdit()
        search.setObjectName("placeholderSearch")
        search.setPlaceholderText("Pesquisar por nome...")
        search.setReadOnly(True)
        search.setToolTip("A pesquisa será conectada aos dados em uma fase futura.")
        search_row.addWidget(search, 1)
        search_button = PrimaryButton("⌕  Pesquisa")
        search_row.addWidget(search_button)
        self.content.addLayout(search_row)

        table = PlaceholderTable(
            ["Nome", "Idade", "Inscrição", "Acomodação", "Pago", "Ação"],
            rows=7,
        )
        table.setMinimumHeight(430)
        self.content.addWidget(table)

        total = QLabel("♙  Total: — inscritos")
        total.setObjectName("cardSubtitle")
        self.content.addWidget(total)
        self.content.addStretch(1)

