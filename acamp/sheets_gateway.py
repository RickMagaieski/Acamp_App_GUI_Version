"""Google Sheets authentication, download, and privacy-safe row parsing."""

from __future__ import annotations

import os
import socket
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httplib2
from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import GoogleSheetsConfig


@dataclass(frozen=True, slots=True)
class SheetParseResult:
    records: tuple[dict[str, str | int | float], ...]
    skipped_rows: int = 0
    warning_rows: int = 0

    @property
    def loaded_count(self) -> int:
        return len(self.records)


class SheetsGatewayError(Exception):
    """Controlled error whose message is safe to display to the user."""

    def __init__(self, user_message: str, technical_code: str):
        super().__init__(user_message)
        self.user_message = user_message
        self.technical_code = technical_code


def _cell(row: Sequence[Any], index: int) -> str:
    if index >= len(row):
        return ""
    value = row[index]
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_age(value: str) -> tuple[int, bool]:
    if not value:
        return 0, True
    try:
        age = Decimal(value)
    except (InvalidOperation, ValueError):
        return 0, True
    if (
        not age.is_finite()
        or age < 0
        or age != age.to_integral_value()
    ):
        return 0, True
    return int(age), False


def _safe_payment(value: str) -> tuple[float, bool]:
    if not value:
        return 0.0, False
    normalized = value.replace(",", ".")
    try:
        payment = Decimal(normalized)
    except (InvalidOperation, ValueError):
        return 0.0, True
    if not payment.is_finite() or payment < 0:
        return 0.0, True
    try:
        return float(payment), False
    except (OverflowError, ValueError):
        return 0.0, True


def parse_sheet_values(values: Any) -> SheetParseResult:
    """Convert a Sheets values response into legacy-compatible records."""

    if not isinstance(values, list):
        raise SheetsGatewayError(
            "A planilha retornou dados em um formato inválido.",
            "sheet_values_not_list",
        )

    records: list[dict[str, str | int | float]] = []
    skipped_rows = 0
    warning_rows = 0
    for row in values[1:]:
        if not isinstance(row, (list, tuple)):
            skipped_rows += 1
            continue

        first_name = _cell(row, 0)
        last_name = _cell(row, 1)
        full_name = " ".join(
            part for part in (first_name, last_name) if part
        ).strip()
        if not full_name:
            skipped_rows += 1
            continue

        age, age_warning = _safe_age(_cell(row, 2))
        payment, payment_warning = _safe_payment(_cell(row, 9))
        row_has_warning = (
            len(row) <= 13
            or age_warning
            or payment_warning
        )
        if row_has_warning:
            warning_rows += 1

        accommodation = _cell(row, 7).casefold() or "cabine"
        records.append({
            "name": full_name.casefold(),
            "age": age,
            "phone": _cell(row, 3),
            "medical": _cell(row, 4),
            "transportation": _cell(row, 5).casefold(),
            "email": _cell(row, 6),
            "accommodation": accommodation,
            "inscription": _cell(row, 8).casefold(),
            "payment": payment,
            "food": _cell(row, 10).casefold(),
            "id": _cell(row, 13),
        })

    return SheetParseResult(
        records=tuple(records),
        skipped_rows=skipped_rows,
        warning_rows=warning_rows,
    )


class GoogleSheetsGateway:
    """Authenticates and downloads registration rows on explicit request."""

    def __init__(self, config: GoogleSheetsConfig):
        self._config = config

    def download_participants(self) -> SheetParseResult:
        credentials = self._authenticate()
        try:
            authorized_http = AuthorizedHttp(
                credentials,
                http=httplib2.Http(
                    timeout=self._config.request_timeout_seconds
                ),
            )
            service = build(
                "sheets",
                "v4",
                http=authorized_http,
                cache_discovery=False,
            )
            response = (
                service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self._config.spreadsheet_id,
                    range=self._config.sheet_range,
                )
                .execute()
            )
        except HttpError as error:
            raise self._http_error(error) from None
        except (
            TransportError,
            socket.timeout,
            TimeoutError,
            ConnectionError,
            OSError,
        ):
            raise SheetsGatewayError(
                "A conexão com a internet não está disponível.",
                "sheet_transport_failed",
            ) from None
        except SheetsGatewayError:
            raise
        except Exception:
            raise SheetsGatewayError(
                "Não foi possível conectar ao Google Sheets.",
                "sheet_request_failed",
            ) from None

        if not isinstance(response, Mapping):
            raise SheetsGatewayError(
                "A planilha retornou dados em um formato inválido.",
                "sheet_response_not_mapping",
            )
        return parse_sheet_values(response.get("values", []))

    def _authenticate(self):
        credentials = None
        token_path = self._config.token_path
        if token_path.exists():
            try:
                credentials = Credentials.from_authorized_user_file(
                    str(token_path),
                    self._config.scopes,
                )
            except (OSError, ValueError):
                credentials = None

        if credentials is not None and credentials.valid:
            return credentials

        if (
            credentials is not None
            and credentials.expired
            and credentials.refresh_token
        ):
            try:
                credentials.refresh(Request())
            except (RefreshError, TransportError, OSError):
                raise SheetsGatewayError(
                    "Não foi possível renovar a autorização do Google.",
                    "google_token_refresh_failed",
                ) from None
            if not credentials.valid:
                raise SheetsGatewayError(
                    "Não foi possível renovar a autorização do Google.",
                    "google_token_refresh_incomplete",
                )
            self._write_token(credentials)
            return credentials

        client_secret_path = self._config.client_secret_path
        if not client_secret_path.exists():
            raise SheetsGatewayError(
                "O arquivo client_secret.json não foi encontrado.",
                "client_secret_missing",
            )
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secret_path),
                self._config.scopes,
            )
        except (OSError, ValueError):
            raise SheetsGatewayError(
                "O arquivo client_secret.json é inválido.",
                "client_secret_invalid",
            ) from None

        try:
            credentials = flow.run_local_server(
                port=0,
                timeout_seconds=self._config.oauth_timeout_seconds,
            )
        except TimeoutError:
            raise SheetsGatewayError(
                "A sincronização foi cancelada.",
                "google_oauth_timeout",
            ) from None
        except Exception:
            raise SheetsGatewayError(
                "A autorização do Google não foi concluída.",
                "google_oauth_failed",
            ) from None
        if credentials is None or not credentials.valid:
            raise SheetsGatewayError(
                "A autorização do Google não foi concluída.",
                "google_oauth_incomplete",
            )
        self._write_token(credentials)
        return credentials

    def _write_token(self, credentials) -> None:
        token_path = self._config.token_path
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=token_path.parent,
                prefix=f".{token_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(credentials.to_json())
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, token_path)
        except (OSError, TypeError, ValueError):
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise SheetsGatewayError(
                "A autorização foi concluída, mas não pôde ser salva.",
                "google_token_save_failed",
            ) from None

    @staticmethod
    def _http_error(error: HttpError) -> SheetsGatewayError:
        status = getattr(error.resp, "status", None)
        if status == 403:
            return SheetsGatewayError(
                "Você não possui acesso à planilha configurada.",
                "sheet_permission_denied",
            )
        if status == 404:
            return SheetsGatewayError(
                "A planilha configurada não foi encontrada.",
                "sheet_not_found",
            )
        return SheetsGatewayError(
            "Não foi possível conectar ao Google Sheets.",
            "sheet_http_error",
        )
