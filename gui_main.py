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
from acamp.ui.setup_dialog import RuntimeDataSetupDialog
from acamp.ui.theme import APP_STYLESHEET


def initialize_qt_application() -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("ACAMP WBSDAC 2026")
    app.setOrganizationName("WBSDAC")
    app.setStyleSheet(APP_STYLESHEET)
    return app


def configure_packaged_runtime(
    paths: ApplicationPaths,
) -> ApplicationPaths:
    """Offer an explicit data setup flow only for packaged runs."""

    if not paths.needs_data_setup:
        return paths
    RuntimeDataSetupDialog(paths).exec()
    return ApplicationPaths.from_runtime()


def create_application(
    *,
    load_participants: bool = True,
    load_inventory: bool = True,
    load_teams: bool = True,
    application_paths: ApplicationPaths | None = None,
) -> tuple[QApplication, MainWindow]:
    app = initialize_qt_application()

    paths = application_paths or ApplicationPaths.from_runtime()
    paths.ensure_private_data_directory()
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
    initialize_qt_application()
    paths = ApplicationPaths.from_runtime()
    if paths.packaged and not smoke_test:
        paths = configure_packaged_runtime(paths)
    load_local_data = not smoke_test or paths.packaged
    app, window = create_application(
        load_participants=load_local_data,
        load_inventory=load_local_data,
        load_teams=load_local_data,
        application_paths=paths,
    )
    window.show()

    # A non-interactive startup/navigation check used by release verification.
    if smoke_test:
        for index in range(window.page_stack.count()):
            window.navigate_to(index)
            app.processEvents()
        window.navigate_to(0)
        QTimer.singleShot(250, window.close)
        QTimer.singleShot(500, app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
