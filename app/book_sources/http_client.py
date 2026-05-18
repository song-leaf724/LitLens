from typing import Any, Dict

from app.core.config import settings


def async_client_options(timeout: float, headers: Dict[str, str]) -> Dict[str, Any]:
    options: Dict[str, Any] = {"timeout": timeout, "headers": headers, "follow_redirects": True}
    if settings.book_source_proxy:
        options["proxy"] = settings.book_source_proxy
        options["trust_env"] = False
    return options
