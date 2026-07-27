"""Application services for controlled inventory mutations."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping

from .models import (
    InventoryDraft,
    InventoryItem,
    Team,
    TeamDraft,
    TeamMemberDraft,
)
from .repositories import (
    InventoryLoadResult,
    InventoryRepository,
    ParticipantLoadResult,
    TeamLoadResult,
    TeamRepository,
    team_result_from_records,
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


@dataclass(frozen=True, slots=True)
class TeamValidationResult:
    draft: TeamDraft | None
    errors: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )

    @property
    def succeeded(self) -> bool:
        return self.draft is not None


@dataclass(frozen=True, slots=True)
class TeamOperationResult:
    succeeded: bool
    message: str = ""


@dataclass(frozen=True, slots=True)
class TeamMemberValidationResult:
    draft: TeamMemberDraft | None
    error: str = ""

    @property
    def succeeded(self) -> bool:
        return self.draft is not None


@dataclass(frozen=True, slots=True)
class ScoreValidationResult:
    amount: int | None
    error: str = ""

    @property
    def succeeded(self) -> bool:
        return self.amount is not None


def validate_team_draft(
    name: Any,
    leader: Any,
    color: Any,
) -> TeamValidationResult:
    normalized_name = str(name).strip() if name is not None else ""
    normalized_leader = str(leader).strip() if leader is not None else ""
    normalized_color = str(color).strip() if color is not None else ""
    errors: dict[str, str] = {}
    if not normalized_name:
        errors["name"] = "Informe o nome do time."
    if not normalized_leader:
        errors["leader"] = "Informe o nome do capitão."
    if not normalized_color:
        errors["color"] = "Informe a cor do time."
    if errors:
        return TeamValidationResult(
            draft=None,
            errors=MappingProxyType(errors),
        )
    return TeamValidationResult(
        draft=TeamDraft(
            name=normalized_name,
            leader=normalized_leader,
            color=normalized_color,
        )
    )


def validate_team_member_name(name: Any) -> TeamMemberValidationResult:
    normalized_name = str(name).strip() if name is not None else ""
    if not normalized_name:
        return TeamMemberValidationResult(
            draft=None,
            error="Digite o nome do participante.",
        )
    return TeamMemberValidationResult(TeamMemberDraft(normalized_name))


def validate_score_amount(value: Any) -> ScoreValidationResult:
    if isinstance(value, bool) or value is None:
        return ScoreValidationResult(
            amount=None,
            error="Digite uma pontuação válida.",
        )
    text = str(value).strip()
    try:
        amount = int(text)
        if Decimal(text) != Decimal(amount):
            raise ValueError
    except (InvalidOperation, ValueError, TypeError, OverflowError):
        return ScoreValidationResult(
            amount=None,
            error="Digite uma pontuação válida.",
        )
    if amount <= 0:
        return ScoreValidationResult(
            amount=None,
            error="Digite uma pontuação válida maior que zero.",
        )
    return ScoreValidationResult(amount=amount)


class TeamService:
    """Owns team state and persists create/delete proposals first."""

    SAVE_ERROR_MESSAGE = "Não foi possível salvar as alterações."

    def __init__(self, repository: TeamRepository | None = None):
        self._repository = repository
        self._result = TeamLoadResult.loading()

    @property
    def load_result(self) -> TeamLoadResult:
        return self._result

    @property
    def teams(self) -> tuple[Team, ...]:
        return self._result.teams

    @property
    def editable(self) -> bool:
        return self._repository is not None and self._result.editable

    def load(self) -> TeamLoadResult:
        if self._repository is not None:
            self._result = self._repository.load()
        return self._result

    def create_team(self, draft: TeamDraft) -> TeamOperationResult:
        if not self.editable or self._repository is None:
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)
        proposed_records = list(self._result.records)
        proposed_records.append(draft.to_record())
        saved = self._repository.save(proposed_records)
        if not saved.succeeded:
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)
        self._result = team_result_from_records(proposed_records)
        return TeamOperationResult(True)

    def delete_team(self, source_index: int) -> TeamOperationResult:
        # Teams have no stable IDs in Phase 2D1; selection maps to the exact
        # source-document index represented by the current table model.
        if not self.editable or self._repository is None:
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)
        proposed_records = list(self._result.records)
        if not 0 <= source_index < len(proposed_records):
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)
        del proposed_records[source_index]
        saved = self._repository.save(proposed_records)
        if not saved.succeeded:
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)
        self._result = team_result_from_records(proposed_records)
        return TeamOperationResult(True)

    def add_member(
        self,
        team_source_index: int,
        draft: TeamMemberDraft,
    ) -> TeamOperationResult:
        team_record = self._editable_team_record(team_source_index)
        if team_record is None:
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)

        if "pessoas" not in team_record:
            people: list[Any] = []
        else:
            existing_people = team_record.get("pessoas")
            if not isinstance(existing_people, list):
                return TeamOperationResult(
                    False,
                    "A lista de participantes desta equipe é inválida.",
                )
            people = list(existing_people)
        people.append(draft.to_record())
        proposed_team = dict(team_record)
        proposed_team["pessoas"] = people
        return self._persist_team_change(team_source_index, proposed_team)

    def remove_member(
        self,
        team_source_index: int,
        member_source_index: int,
    ) -> TeamOperationResult:
        team_record = self._editable_team_record(team_source_index)
        if team_record is None:
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)
        people = team_record.get("pessoas")
        if (
            not isinstance(people, list)
            or not 0 <= member_source_index < len(people)
        ):
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)

        proposed_people = list(people)
        del proposed_people[member_source_index]
        proposed_team = dict(team_record)
        proposed_team["pessoas"] = proposed_people
        return self._persist_team_change(team_source_index, proposed_team)

    def change_score(
        self,
        team_source_index: int,
        delta: int,
    ) -> TeamOperationResult:
        if isinstance(delta, bool) or not isinstance(delta, int) or delta == 0:
            return TeamOperationResult(False, "Digite uma pontuação válida.")
        team_record = self._editable_team_record(team_source_index)
        team = self.team_by_source_index(team_source_index)
        if team_record is None or team is None:
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)

        proposed_team = dict(team_record)
        proposed_team["score"] = team.score_value + delta
        return self._persist_team_change(team_source_index, proposed_team)

    def team_by_source_index(self, source_index: int) -> Team | None:
        return next(
            (
                team
                for team in self._result.teams
                if team.source_index == source_index
            ),
            None,
        )

    def _editable_team_record(self, source_index: int) -> dict | None:
        if (
            not self.editable
            or self._repository is None
            or not 0 <= source_index < len(self._result.records)
        ):
            return None
        record = self._result.records[source_index]
        return record if isinstance(record, dict) else None

    def _persist_team_change(
        self,
        source_index: int,
        proposed_team: dict,
    ) -> TeamOperationResult:
        if self._repository is None:
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)
        proposed_records = list(self._result.records)
        if not 0 <= source_index < len(proposed_records):
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)
        proposed_records[source_index] = proposed_team
        saved = self._repository.save(proposed_records)
        if not saved.succeeded:
            return TeamOperationResult(False, self.SAVE_ERROR_MESSAGE)
        self._result = team_result_from_records(proposed_records)
        return TeamOperationResult(True)
