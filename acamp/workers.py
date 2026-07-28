"""Qt workers for blocking external operations."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from .services import SynchronizationService


class ParticipantSynchronizationWorker(QObject):
    """Runs one explicit synchronization outside the GUI thread."""

    progress = Signal(str)
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        service: SynchronizationService,
        *,
        allow_damaged_cache_replacement: bool = False,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._service = service
        self._allow_damaged_cache_replacement = (
            allow_damaged_cache_replacement
        )

    @Slot()
    def run(self) -> None:
        self.progress.emit("Sincronizando...")
        try:
            result = self._service.synchronize(
                allow_damaged_cache_replacement=(
                    self._allow_damaged_cache_replacement
                )
            )
            if result.succeeded:
                self.succeeded.emit(result)
            else:
                self.failed.emit(result.message)
        except Exception:
            self.failed.emit(
                "Ocorreu uma falha durante a sincronização."
            )
        finally:
            self.finished.emit()
