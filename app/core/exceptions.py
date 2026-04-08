from typing import Any

from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(self, status_code: int, detail: Any = None) -> None:
        super().__init__(status_code=status_code, detail=detail)


class DuplicatedError(AppError):
    def __init__(self, detail: Any = None) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)


class AuthError(AppError):
    def __init__(self, detail: Any = None) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)


class NotFoundError(AppError):
    def __init__(self, detail: Any = None) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class ValidationError(AppError):
    def __init__(self, detail: Any = None) -> None:
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)
