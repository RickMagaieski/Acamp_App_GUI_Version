"""Main window and working sidebar navigation for the GUI shell."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from acamp.repositories import ParticipantLoadResult
from acamp.services import InventoryService

from .pages.activities import ActivitiesPage
from .pages.dashboard import DashboardPage
from .pages.finance import FinancePage
from .pages.inventory import InventoryPage
from .pages.registrations import RegistrationsPage
from .pages.reports import ReportsPage
from .widgets import SidebarButton


class MainWindow(QMainWindow):
    PAGE_DEFINITIONS = (
        ("⌂", "Dashboard", DashboardPage),
        ("♙", "Inscrições", RegistrationsPage),
        ("$", "Finanças", FinancePage),
        ("◇", "Inventário", InventoryPage),
        ("♜", "Atividades", ActivitiesPage),
        ("▥", "Relatórios", ReportsPage),
    )

    def __init__(
        self,
        participant_result: ParticipantLoadResult | None = None,
        inventory_service: InventoryService | None = None,
    ):
        super().__init__()
        self.setWindowTitle("ACAMP WBSDAC 2026")
        self.resize(1440, 900)
        self.setMinimumSize(1040, 680)

        root = QWidget()
        root.setObjectName("applicationRoot")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        content_panel = QWidget()
        content_panel.setObjectName("contentPanel")
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("pageStack")
        content_layout.addWidget(self.page_stack)
        root_layout.addWidget(content_panel, 1)

        participant_result = participant_result or ParticipantLoadResult.empty()
        inventory_service = inventory_service or InventoryService()
        self.registrations_page: RegistrationsPage | None = None
        self.inventory_page: InventoryPage | None = None
        for _icon, _label, page_class in self.PAGE_DEFINITIONS:
            if page_class is RegistrationsPage:
                page = page_class(participant_result)
                self.registrations_page = page
            elif page_class is InventoryPage:
                page = page_class(inventory_service)
                self.inventory_page = page
            else:
                page = page_class()
            self.page_stack.addWidget(page)

        self.navigation_buttons[0].setChecked(True)
        self.navigate_to(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(24, 28, 24, 24)
        layout.setSpacing(8)

        camp_symbol = QLabel("♠  △")
        camp_symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camp_symbol.setStyleSheet("color: #cbd2be; font-size: 24px;")
        layout.addWidget(camp_symbol)

        brand = QLabel("ACAMP")
        brand.setObjectName("brandTitle")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand)

        year = QLabel("WBSDAC  <span style='color:#d55a17'>2026</span>")
        year.setObjectName("brandYear")
        year.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(year)

        tagline = QLabel("—  JUNTOS EM CRISTO  —")
        tagline.setObjectName("brandTagline")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tagline)
        layout.addSpacing(34)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.navigation_buttons: list[SidebarButton] = []

        for index, (icon, label, _page_class) in enumerate(self.PAGE_DEFINITIONS):
            button = SidebarButton(icon, label)
            button.setProperty("pageIndex", index)
            button.clicked.connect(lambda _checked=False, page=index: self.navigate_to(page))
            self.button_group.addButton(button, index)
            self.navigation_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch(1)

        footer = QLabel("♡\n\nServindo, amando\ne fazendo a diferença!")
        footer.setObjectName("sidebarFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        footer.setWordWrap(True)
        footer.setMinimumHeight(110)
        footer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        footer.setStyleSheet(
            "background: rgba(255,255,255,0.08); border-radius: 14px;"
            "padding: 16px; color: #eef1e9;"
        )
        layout.addWidget(footer)
        return sidebar

    def navigate_to(self, index: int) -> None:
        if not 0 <= index < self.page_stack.count():
            return
        self.page_stack.setCurrentIndex(index)
        self.navigation_buttons[index].setChecked(True)

    def set_participant_result(self, result: ParticipantLoadResult) -> None:
        if self.registrations_page is not None:
            self.registrations_page.set_load_result(result)

    def refresh_inventory_page(self) -> None:
        if self.inventory_page is not None:
            self.inventory_page.refresh_from_service()

    @property
    def current_page_index(self) -> int:
        return self.page_stack.currentIndex()
