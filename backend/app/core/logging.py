import logging
import re


SHARED_TICKET_PATH = re.compile(r"(/api/v1/shared-tickets/)[^/?\s]+")


class SensitivePathFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple) and len(record.args) >= 3:
            arguments = list(record.args)
            path = arguments[2]
            if isinstance(path, str):
                arguments[2] = SHARED_TICKET_PATH.sub(r"\1[REDACTED]", path)
                record.args = tuple(arguments)
        return True


def configure_logging(environment: str) -> None:
    level = logging.DEBUG if environment == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # HTTPX inclui a URL completa nos logs; a Ticketmaster autentica por query string.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").addFilter(SensitivePathFilter())
