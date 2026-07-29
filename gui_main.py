"""Entry point for the standalone ACAMP desktop interface."""

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from acamp.config import GoogleSheetsConfig
from acamp.paths import ApplicationPaths
from acamp.repositories import (
    InventoryRepository,
    ParticipantLoadResult,
    ParticipantRepository,
    TeamRepository,
)
from acamp.services import (
    InventoryService,
    ParticipantDeletionService,
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
    application_paths: ApplicationPaths | None = None,
) -> tuple[QApplication, MainWindow]:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("ACAMP WBSDAC 2026")
    app.setOrganizationName("WBSDAC")
    app.setStyleSheet(APP_STYLESHEET)

    paths = application_paths or ApplicationPaths.from_runtime()
    participant_repository = ParticipantRepository(
        paths.participants_file
    )
    participant_state = (
        participant_repository.load()
        if load_participants
        else ParticipantLoadResult.empty()
    )
    inventory_service = InventoryService(
        InventoryRepository(paths.inventory_file)
    )
    team_service = TeamService(
        TeamRepository(paths.teams_file)
    )
    if load_inventory:
        inventory_service.load()
    if load_teams:
        team_service.load()

    sheets_gateway = GoogleSheetsGateway(GoogleSheetsConfig(paths.root))
    synchronization_service = SynchronizationService(
        sheets_gateway,
        participant_repository,
    )
    participant_deletion_service = ParticipantDeletionService(
        sheets_gateway,
        participant_repository,
    )
    window = MainWindow(
        participant_state,
        inventory_service,
        team_service,
        synchronization_service,
        participant_deletion_service,
    )

    return app, window


def main() -> int:
    smoke_test = "--smoke-test" in sys.argv
    app, window = create_application(
        load_participants=not smoke_test,
        load_inventory=not smoke_test,
        load_teams=not smoke_test,
    )
    window.show()

    # A non-interactive startup check used by development verification.
    if smoke_test:
        QTimer.singleShot(250, app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
