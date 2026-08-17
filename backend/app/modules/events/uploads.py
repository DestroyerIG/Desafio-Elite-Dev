from io import BytesIO
from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.exceptions import AppError


IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
PIL_IMAGE_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
MAX_EVENT_IMAGE_PIXELS = 40_000_000
EVENT_UPLOAD_PREFIX = PurePosixPath("/uploads/events")


def _detect_image_type(content: bytes) -> str | None:
    try:
        with Image.open(BytesIO(content)) as image:
            image_type = PIL_IMAGE_TYPES.get(image.format or "")
            if image_type is None or image.width * image.height > MAX_EVENT_IMAGE_PIXELS:
                return None
            image.verify()
            return image_type
    except (Image.DecompressionBombError, OSError):
        return None


def _write_file(destination: Path, content: bytes) -> None:
    temporary = destination.with_suffix(f"{destination.suffix}.tmp")
    try:
        temporary.write_bytes(content)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


async def save_event_image(upload: UploadFile, settings: Settings) -> str:
    content = await upload.read(settings.upload_max_bytes + 1)
    if len(content) > settings.upload_max_bytes:
        raise AppError(
            "EVENT_IMAGE_TOO_LARGE",
            "A imagem deve ter no máximo 5 MB.",
            413,
        )

    image_type = _detect_image_type(content)
    if image_type is None:
        raise AppError(
            "INVALID_EVENT_IMAGE",
            "Envie uma imagem JPEG, PNG ou WebP válida.",
            422,
        )

    event_directory = settings.upload_directory / "events"
    await run_in_threadpool(event_directory.mkdir, parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{IMAGE_EXTENSIONS[image_type]}"
    await run_in_threadpool(_write_file, event_directory / filename, content)
    return str(EVENT_UPLOAD_PREFIX / filename)


async def delete_event_image(image_url: str | None, settings: Settings) -> None:
    if not image_url:
        return

    url_path = PurePosixPath(image_url)
    if url_path.parent != EVENT_UPLOAD_PREFIX or url_path.name != Path(url_path.name).name:
        return

    destination = settings.upload_directory / "events" / url_path.name
    await run_in_threadpool(destination.unlink, missing_ok=True)
