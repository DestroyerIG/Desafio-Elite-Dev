from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.models.enums import PaymentStatus


@dataclass(frozen=True, slots=True)
class PaymentResult:
    status: PaymentStatus
    failure_reason: str | None = None


class PaymentGateway(Protocol):
    provider: str

    async def authorize(
        self,
        *,
        amount: Decimal,
        card_number: str,
    ) -> PaymentResult: ...


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


def get_payment_gateway() -> PaymentGateway:
    return FakePaymentGateway()
