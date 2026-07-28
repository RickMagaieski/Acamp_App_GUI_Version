"""Entry point for the standalone ACAMP desktop interface."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from acamp.config import GoogleSheetsConfig
from acamp.repositories import (
    InventoryRepository,
    ParticipantLoadResult,
    ParticipantRepository,
    TeamRepository,
)
from acamp.services import (
    InventoryService,
    SynchronizationService,
    TeamService,
)
from acamp.sheets_gateway import GoogleSheetsGateway
from acamp.ui.main_window import MainWindow
from acamp.ui.theme import APP_STYLESHEET


def create_application(
    *,
    load_participants: bool = True,
    load_inventory: bool = True,
    load_teams: bool = True,
) -> tuple[QApplication, MainWindow]:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("ACAMP WBSDAC 2026")
    app.setOrganizationName("WBSDAC")
    app.setStyleSheet(APP_STYLESHEET)

    project_root = Path(__file__).resolve().parent
    participant_repository = ParticipantRepository(
        project_root / "participants.json"
    )
    participant_state = (
        ParticipantLoadResult.loading()
        if load_participants
        else ParticipantLoadResult.empty()
    )
    inventory_service = InventoryService(
        InventoryRepository(project_root / "items.json")
    )
    team_service = TeamService(
        TeamRepository(project_root / "teams.json")
    )
    synchronization_service = SynchronizationService(
        GoogleSheetsGateway(GoogleSheetsConfig(project_root)),
        participant_repository,
    )
    window = MainWindow(
        participant_state,
        inventory_service,
        team_service,
        synchronization_service,
    )

    def load_local_state() -> None:
        if load_participants:
            window.set_participant_result(participant_repository.load())
        if load_inventory:
            inventory_service.load()
            window.refresh_inventory_page()
        if load_teams:
            team_service.load()
            window.refresh_activities_page()

    QTimer.singleShot(0, load_local_state)
    return app, window


def main() -> int:
    smoke_test = "--smoke-test" in sys.argv
    app, window = create_application(
        load_participants=not smoke_test,
        load_inventory=not smoke_test,
        load_teams=True,
    )
    window.show()

    # A non-interactive startup check used by development verification.
    if smoke_test:
        QTimer.singleShot(250, app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
