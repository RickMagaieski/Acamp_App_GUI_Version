"""Application services for controlled inventory mutations."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping

from .models import InventoryDraft, InventoryItem
from .repositories import (
    InventoryLoadResult,
    InventoryRepository,
    ParticipantLoadResult,
    inventory_result_from_records,
)
from .pricing import FinancialSnapshot, calculate_financial_snapshot


@dataclass(frozen=True, slots=True)
class InventoryValidationResult:
    draft: InventoryDraft | None
    errors: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )

    @property
    def succeeded(self) -> bool:
        return self.draft is not None


@dataclass(frozen=True, slots=True)
class InventoryOperationResult:
    succeeded: bool
    message: str = ""


def validate_inventory_draft(
    item: Any,
    value: Any,
    quantity: Any,
    description: Any = "",
) -> InventoryValidationResult:
    errors: dict[str, str] = {}

    normalized_item = str(item).strip() if item is not None else ""
    if not normalized_item:
        errors["item"] = "Informe o nome do item."

    if isinstance(quantity, bool):
        normalized_quantity = None
    else:
        try:
            normalized_quantity = int(str(quantity).strip())
            if Decimal(str(quantity).strip()) != Decimal(normalized_quantity):
                normalized_quantity = None
        except (InvalidOperation, ValueError, TypeError, OverflowError):
            normalized_quantity = None
    if normalized_quantity is None or normalized_quantity <= 0:
        errors["quantity"] = "A quantidade deve ser um inteiro maior que zero."

    if isinstance(value, bool) or value is None or str(value).strip() == "":
        normalized_value = None
    else:
        try:
            normalized_value = Decimal(str(value).strip())
        except (InvalidOperation, ValueError, TypeError):
            normalized_value = None
    value_is_valid = (
        normalized_value is not None
        and normalized_value.is_finite()
        and normalized_value >= 0
    )
    if value_is_valid:
        try:
            value_is_valid = isfinite(float(normalized_value))
        except (OverflowError, ValueError):
            value_is_valid = False
    if not value_is_valid:
        errors["value"] = "Informe um valor válido, igual ou maior que zero."

    if errors:
        return InventoryValidationResult(
            draft=None,
            errors=MappingProxyType(errors),
        )

    normalized_description = (
        str(description).strip() if description is not None else ""
    )
    return InventoryValidationResult(
        draft=InventoryDraft(
            item=normalized_item,
            quantity=normalized_quantity,
            value=normalized_value,
            description=normalized_description,
        )
    )


class InventoryService:
    """Owns the in-memory inventory and persists proposed changes first."""

    SAVE_ERROR_MESSAGE = "Não foi possível salvar as alterações."

    def __init__(self, repository: InventoryRepository | None = None):
        self._repository = repository
        self._result = InventoryLoadResult.loading()

    @property
    def load_result(self) -> InventoryLoadResult:
        return self._result

    @property
    def items(self) -> tuple[InventoryItem, ...]:
        return self._result.items

    @property
    def editable(self) -> bool:
        return self._repository is not None and self._result.editable

    def load(self) -> InventoryLoadResult:
        if self._repository is None:
            return self._result
        self._result = self._repository.load()
        return self._result

    def add_item(self, draft: InventoryDraft) -> InventoryOperationResult:
        if not self.editable or self._repository is None:
            return InventoryOperationResult(False, self.SAVE_ERROR_MESSAGE)

        proposed_records = list(self._result.records)
        proposed_records.append(draft.to_record())
        saved = self._repository.save(proposed_records)
        if not saved.succeeded:
            return InventoryOperationResult(False, self.SAVE_ERROR_MESSAGE)

        self._result = inventory_result_from_records(proposed_records)
        return InventoryOperationResult(True)

    def delete_item(self, source_index: int) -> InventoryOperationResult:
        # Existing records have no stable IDs. Phase 2B therefore removes the
        # exact source-document index represented by the selected model row.
        if not self.editable or self._repository is None:
            return InventoryOperationResult(False, self.SAVE_ERROR_MESSAGE)

        proposed_records = list(self._result.records)
        if not 0 <= source_index < len(proposed_records):
            return InventoryOperationResult(False, self.SAVE_ERROR_MESSAGE)
        del proposed_records[source_index]

        saved = self._repository.save(proposed_records)
        if not saved.succeeded:
            return InventoryOperationResult(False, self.SAVE_ERROR_MESSAGE)

        self._result = inventory_result_from_records(proposed_records)
        return InventoryOperationResult(True)


class FinanceService:
    """Calculates finances from the shared participant and inventory state."""

    def __init__(
        self,
        participant_result: ParticipantLoadResult,
        inventory_service: InventoryService,
    ):
        self._participant_result = participant_result
        self._inventory_service = inventory_service

    def set_participant_result(self, result: ParticipantLoadResult) -> None:
        self._participant_result = result

    @property
    def participant_result(self) -> ParticipantLoadResult:
        return self._participant_result

    @property
    def inventory_result(self) -> InventoryLoadResult:
        return self._inventory_service.load_result

    def snapshot(self) -> FinancialSnapshot:
        return calculate_financial_snapshot(
            self._participant_result.participants,
            self._inventory_service.items,
            participants_available=self._participant_result.succeeded,
            inventory_available=self._inventory_service.load_result.succeeded,
        )
