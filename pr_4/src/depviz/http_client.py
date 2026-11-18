"""HTTP-загрузка с повторами и таймаутом.

Модуль обслуживает этап 2: любые
обращения к удалённому репозиторию идут
через ``fetch``, чтобы повторы, таймауты
и коды ошибок обрабатывались в одном
месте.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request

HTTP_NOT_FOUND = 404
HTTP_TOO_MANY = 429
HTTP_SERVER_ERROR = 500
ATTEMPTS = 3
TIMEOUT_SECONDS = 30
FIRST_PAUSE = 1
USER_AGENT = "depviz"


class NotFoundError(ValueError):
    """Ресурс на сервере отсутствует (HTTP 404)."""


def is_retryable(code: int) -> bool:
    """Истина для кодов, где нужен повтор."""
    return code == HTTP_TOO_MANY or code >= HTTP_SERVER_ERROR


def check_http_error(error: urllib.error.HTTPError, url: str) -> None:
    """Преобразует HTTP-ошибку
    в исключение приложения."""
    if error.code == HTTP_NOT_FOUND:
        raise NotFoundError(
            f"ничего не найдено по адресу {url} (404)"
        )
    if not is_retryable(error.code):
        raise ValueError(
            f"сервер вернул ошибку {error.code} для {url}"
        )


def request_once(url: str) -> bytes:
    """Одна попытка запроса.

    Возвращает тело ответа.
    """
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Connection": "close",
        },
    )
    with urllib.request.urlopen(
        request, timeout=TIMEOUT_SECONDS
    ) as response:
        return response.read()


def fetch(url: str) -> bytes:
    """Загружает URL с повторами.

    Все сетевые проблемы превращаются в
    ``ValueError`` с понятным текстом.
    """
    last_error = ""
    for attempt in range(ATTEMPTS):
        try:
            return request_once(url)
        except urllib.error.HTTPError as error:
            check_http_error(error, url)
            last_error = f"сервер вернул ошибку {error.code}"
        except urllib.error.URLError as error:
            reason = error.reason
            last_error = (
                f"не удалось подключиться: {reason}"
            )
        except OSError as error:
            last_error = f"соединение прервано: {error}"
        time.sleep(FIRST_PAUSE + attempt)
    raise ValueError(
        f"{url}: {last_error} (попыток: {ATTEMPTS})"
    )
