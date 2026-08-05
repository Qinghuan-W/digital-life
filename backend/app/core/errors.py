from typing import Any

from fastapi import status


class AppError(Exception):
    def __init__(self, error: str, message: str, status_code: int) -> None:
        self.error = error
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def error_payload(error: str, message: str) -> dict[str, str]:
    return {"error": error, "message": message}


def validation_message(errors: list[dict[str, Any]]) -> str:
    if not errors:
        return "请求数据无效"
    location = ".".join(str(part) for part in errors[0].get("loc", [])[1:])
    return f"{location}: {errors[0].get('msg', '输入无效')}" if location else "请求数据无效"


INVALID_CREDENTIALS = AppError(
    "invalid_credentials",
    "邮箱或密码错误",
    status.HTTP_401_UNAUTHORIZED,
)
