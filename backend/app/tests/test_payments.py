from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.enums import PaymentStatus, RefundStatus
from app.modules.payments.gateway import FakePaymentGateway
from app.modules.payments.schemas import PaymentCreate


@pytest.mark.asyncio
async def test_fake_gateway_approves_regular_test_card() -> None:
    result = await FakePaymentGateway().authorize(
        amount=Decimal("50.00"),
        card_number="4242424242424242",
    )

    assert result.status == PaymentStatus.APPROVED
    assert result.failure_reason is None


@pytest.mark.asyncio
async def test_fake_gateway_declines_card_ending_in_0000() -> None:
    result = await FakePaymentGateway().authorize(
        amount=Decimal("50.00"),
        card_number="4000000000000000",
    )

    assert result.status == PaymentStatus.DECLINED
    assert result.failure_reason is not None


@pytest.mark.asyncio
async def test_fake_gateway_approves_full_refund() -> None:
    result = await FakePaymentGateway().refund(
        payment_id=uuid4(),
        amount=Decimal("50.00"),
    )

    assert result.status == RefundStatus.APPROVED
    assert result.failure_reason is None


def test_payment_input_normalizes_card_without_persisting_extra_data() -> None:
    payment = PaymentCreate(card_number="4242 4242-4242 4242")

    assert payment.card_number == "4242424242424242"
