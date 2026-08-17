from io import BytesIO

import pytest
from fastapi import UploadFile
from PIL import Image

from app.core.config import Settings
from app.core.exceptions import AppError
from app.modules.events.uploads import delete_event_image, save_event_image


def create_png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color=(37, 99, 235)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_event_image_is_validated_stored_and_deleted(tmp_path) -> None:
    settings = Settings(upload_directory=tmp_path)
    upload = UploadFile(file=BytesIO(create_png()), filename="cartaz.png")

    image_url = await save_event_image(upload, settings)

    assert image_url.startswith("/uploads/events/")
    stored_image = tmp_path / "events" / image_url.rsplit("/", 1)[-1]
    assert stored_image.read_bytes().startswith(b"\x89PNG")

    await delete_event_image(image_url, settings)

    assert not stored_image.exists()


@pytest.mark.asyncio
async def test_event_image_rejects_invalid_content(tmp_path) -> None:
    settings = Settings(upload_directory=tmp_path)
    upload = UploadFile(
        file=BytesIO(b"<svg><script>alert(1)</script></svg>"),
        filename="cartaz.png",
    )

    with pytest.raises(AppError) as exc_info:
        await save_event_image(upload, settings)

    assert exc_info.value.code == "INVALID_EVENT_IMAGE"
    assert not (tmp_path / "events").exists()


@pytest.mark.asyncio
async def test_event_image_rejects_file_above_limit(tmp_path) -> None:
    settings = Settings(upload_directory=tmp_path, upload_max_bytes=10)
    upload = UploadFile(file=BytesIO(create_png()), filename="cartaz.png")

    with pytest.raises(AppError) as exc_info:
        await save_event_image(upload, settings)

    assert exc_info.value.code == "EVENT_IMAGE_TOO_LARGE"
