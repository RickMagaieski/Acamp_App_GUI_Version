"""Central configuration for external services used by the GUI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .paths import ApplicationPaths


GOOGLE_SHEETS_SCOPES = (
    "https://www.googleapis.com/auth/spreadsheets",
)
GOOGLE_SPREADSHEET_ID = (
    "1wALF3JSAUKt-m8P8DTKonHvBS45ycQyCGKp_sxPW-uA"
)
GOOGLE_SHEET_RANGE = "Sheet1!A:Z"


@dataclass(frozen=True, slots=True)
class GoogleSheetsConfig:
    project_root: Path
    scopes: tuple[str, ...] = GOOGLE_SHEETS_SCOPES
    spreadsheet_id: str = GOOGLE_SPREADSHEET_ID
    sheet_range: str = GOOGLE_SHEET_RANGE
    request_timeout_seconds: int = 30
    oauth_timeout_seconds: int = 300

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "project_root",
            Path(self.project_root).resolve(),
        )

    @property
    def client_secret_path(self) -> Path:
        return ApplicationPaths(self.project_root).client_secret_file

    @property
    def token_path(self) -> Path:
        return ApplicationPaths(self.project_root).token_file
