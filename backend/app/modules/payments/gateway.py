from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.models.enums import PaymentStatus, RefundStatus


@dataclass(frozen=True, slots=True)
class PaymentResult:
    status: PaymentStatus
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class RefundResult:
    status: RefundStatus
    failure_reason: str | None = None


class PaymentGateway(Protocol):
    provider: str

    async def authorize(
        self,
        *,
        amount: Decimal,
        card_number: str,
    ) -> PaymentResult: ...

    async def refund(
        self,
        *,
        payment_id: UUID,
        amount: Decimal,
    ) -> RefundResult: ...


class FakePaymentGateway:
    provider = "fake"

    async def authorize(
        self,
        *,
        amount: Decimal,
        card_number: str,
    ) -> PaymentResult:
        del amount
        if card_number.endswith("0000"):
            return PaymentResult(
                status=PaymentStatus.DECLINED,
                failure_reason="Pagamento recusado pelo simulador.",
            )
        return PaymentResult(status=PaymentStatus.APPROVED)

    async def refund(
        self,
        *,
        payment_id: UUID,
        amount: Decimal,
    ) -> RefundResult:
        del payment_id, amount
        return RefundResult(status=RefundStatus.APPROVED)


def get_payment_gateway() -> PaymentGateway:
    return FakePaymentGateway()
