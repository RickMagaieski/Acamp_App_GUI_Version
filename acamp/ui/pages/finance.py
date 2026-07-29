"""Read-only financial overview based on shared application state."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from acamp.models import format_currency
from acamp.pricing import (
    INITIAL_BALANCE,
    REGISTRATION_LABELS,
    REGISTRATION_PRICES,
    PaymentStatus,
)
from acamp.repositories import InventoryLoadStatus, ParticipantLoadStatus
from acamp.services import FinanceService
from acamp.ui.dialogs import PaymentDetailsDialog

from ..widgets import Card, PageScaffold, PrimaryButton


def _value_row(label: str) -> tuple[QWidget, QLabel]:
    row = QWidget()
    row.setObjectName("financeValueRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 7, 0, 7)
    name_label = QLabel(label)
    name_label.setObjectName("financeLabel")
    value_label = QLabel("—")
    value_label.setObjectName("financeValue")
    value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
    layout.addWidget(name_label, 1)
    layout.addWidget(value_label)
    return row, value_label


class FinancePage(PageScaffold):
    STATUS_ORDER = (
        PaymentStatus.PAID,
        PaymentStatus.PARTIAL,
        PaymentStatus.PENDING,
        PaymentStatus.SPECIAL,
        PaymentStatus.UNCLASSIFIED,
    )

    def __init__(self, service: FinanceService):
        super().__init__(
            "FINANÇAS",
            "Acompanhe preços, pagamentos e o resumo financeiro do acampamento.",
            "▥",
        )
        self._service = service
        self._payments = ()

        self.warning_banner = QLabel()
        self.warning_banner.setObjectName("financeWarning")
        self.warning_banner.setWordWrap(True)
        self.warning_banner.hide()
        self.content.addWidget(self.warning_banner)

        columns = QHBoxLayout()
        columns.setSpacing(16)

        prices = Card("LISTA DE PREÇOS")
        for canonical_type, amount in REGISTRATION_PRICES.items():
            row, value_label = _value_row(
                f"•  {REGISTRATION_LABELS[canonical_type]}"
            )
            value_label.setText(format_currency(amount))
            prices.body.addWidget(row)
        columns.addWidget(prices, 1)

        payments = Card("PAGAMENTOS")
        self.status_labels: dict[PaymentStatus, QLabel] = {}
        for status in self.STATUS_ORDER:
            row, value_label = _value_row(status.value)
            self.status_labels[status] = value_label
            payments.body.addWidget(row)
        separator = QFrame()
        separator.setObjectName("separator")
        payments.body.addWidget(separator)
        remaining_row, self.remaining_label = _value_row("Total pendente")
        payments.body.addWidget(remaining_row)
        self.payment_empty_label = QLabel("Não há pagamentos para exibir.")
        self.payment_empty_label.setObjectName("financeEmptyState")
        self.payment_empty_label.setWordWrap(True)
        self.payment_empty_label.hide()
        payments.body.addWidget(self.payment_empty_label)
        self.details_button = PrimaryButton("Ver todos os pagamentos  →")
        self.details_button.clicked.connect(self._open_payment_details)
        payments.body.addWidget(self.details_button)
        columns.addWidget(payments, 1)

        summary = Card("RESUMO FINANCEIRO")
        self.summary_labels: dict[str, QLabel] = {}
        for key, label in (
            ("initial", "Saldo inicial"),
            ("entries", "Entradas"),
            ("expenses", "Gastos"),
            ("result", "Resultado do evento"),
            ("available", "Saldo disponível"),
        ):
            row, value_label = _value_row(label)
            self.summary_labels[key] = value_label
            summary.body.addWidget(row)
        columns.addWidget(summary, 1)
        self.content.addLayout(columns)

        lower = QHBoxLayout()
        available_card = Card("SALDO DISPONÍVEL")
        self.available_amount = QLabel("$0.00")
        self.available_amount.setObjectName("metricValue")
        available_card.body.addWidget(self.available_amount)
        clarification = QLabel(
            "Saldo inicial + entradas − gastos"
        )
        clarification.setObjectName("cardSubtitle")
        available_card.body.addWidget(clarification)
        lower.addWidget(available_card, 3)

        quote = Card(
            "“ Tudo posso naquele que me fortalece. ”",
            "Filipenses 4:13",
        )
        lower.addWidget(quote, 2)
        self.content.addLayout(lower)
        self.content.addStretch(1)
        self.refresh_from_service()

    def refresh_from_service(self) -> None:
        snapshot = self._service.snapshot()
        self._payments = snapshot.payments

        for status, label in self.status_labels.items():
            label.setText(str(snapshot.status_counts[status]))
        self.remaining_label.setText(format_currency(snapshot.remaining_owed))

        self.summary_labels["initial"].setText(format_currency(INITIAL_BALANCE))
        self.summary_labels["entries"].setText(format_currency(snapshot.entries))
        self.summary_labels["expenses"].setText(format_currency(snapshot.expenses))
        self.summary_labels["result"].setText(
            format_currency(snapshot.event_result)
        )
        self.summary_labels["available"].setText(
            format_currency(snapshot.available_balance)
        )
        self.available_amount.setText(
            format_currency(snapshot.available_balance)
        )
        self.details_button.setEnabled(bool(snapshot.payments))
        self.payment_empty_label.setVisible(not snapshot.payments)
        self._update_warning(snapshot.status_counts[PaymentStatus.UNCLASSIFIED])

    def _update_warning(self, unclassified_count: int) -> None:
        participant_status = self._service.participant_result.status
        inventory_status = self._service.inventory_result.status
        loading = (
            participant_status == ParticipantLoadStatus.LOADING
            or inventory_status == InventoryLoadStatus.LOADING
        )
        messages: list[str] = []
        if loading:
            messages.append("Carregando dados financeiros...")
        else:
            participants_available = self._service.participant_result.succeeded
            inventory_available = self._service.inventory_result.succeeded
            if not participants_available and not inventory_available:
                messages.append("Não foi possível carregar os dados financeiros.")
            elif not participants_available:
                messages.append(
                    "Os dados de participantes não estão disponíveis."
                )
            elif not inventory_available:
                messages.append(
                    "Os dados do inventário não estão disponíveis."
                )
        if unclassified_count:
            messages.append("Alguns registros não puderam ser classificados.")

        if messages:
            self.warning_banner.setText(" ".join(messages))
            self.warning_banner.show()
        else:
            self.warning_banner.hide()

    def _open_payment_details(self) -> None:
        PaymentDetailsDialog(self._payments, self).exec()
