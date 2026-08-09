"""Qt workers for blocking external operations."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from .models import Participant
from .repositories import ParticipantLoadResult
from .services import (
    ParticipantDeletionService,
    SynchronizationService,
)


class ParticipantSynchronizationWorker(QObject):
    """Runs one explicit synchronization outside the GUI thread."""

    progress = Signal(str)
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        service: SynchronizationService,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._service = service

    @Slot()
    def run(self) -> None:
        self.progress.emit("Sincronizando...")
        try:
            result = self._service.synchronize()
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


class ParticipantDeletionWorker(QObject):
    """Runs one coordinated registration deletion outside the GUI thread."""

    progress = Signal(str)
    succeeded = Signal(object)
    partially_succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        service: ParticipantDeletionService,
        participant: Participant,
        current_result: ParticipantLoadResult,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._service = service
        self._participant = participant
        self._current_result = current_result

    @Slot()
    def run(self) -> None:
        self.progress.emit("Removendo inscrição...")
        try:
            result = self._service.delete(
                self._participant,
                self._current_result,
            )
            if result.succeeded:
                self.succeeded.emit(result)
            elif result.partially_succeeded:
                self.partially_succeeded.emit(result)
            else:
                self.failed.emit(result.message)
        except Exception:
            self.failed.emit(
                "Ocorreu uma falha durante a remoção da inscrição."
            )
        finally:
            self.finished.emit()
