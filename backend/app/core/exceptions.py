from typing import Any


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


class NotFoundError(AppError):
    def __init__(
        self, message: str = "Resource not found", details: list[Any] | None = None
    ) -> None:
        super().__init__("NOT_FOUND", message, 404, details)


class UnauthorizedError(AppError):
    def __init__(
        self, message: str = "Not authenticated", details: list[Any] | None = None
    ) -> None:
        super().__init__("UNAUTHORIZED", message, 401, details)


class ForbiddenError(AppError):
    def __init__(
        self, message: str = "Not authorized", details: list[Any] | None = None
    ) -> None:
        super().__init__("FORBIDDEN", message, 403, details)


class ConflictError(AppError):
    def __init__(self, message: str, details: list[Any] | None = None) -> None:
        super().__init__("CONFLICT", message, 409, details)


class ValidationAppError(AppError):
    def __init__(self, message: str, details: list[Any] | None = None) -> None:
        super().__init__("VALIDATION_ERROR", message, 422, details)


class PayloadTooLargeError(AppError):
    def __init__(
        self, message: str = "File is too large", details: list[Any] | None = None
    ) -> None:
        super().__init__("PAYLOAD_TOO_LARGE", message, 413, details)


class UnavailableError(AppError):
    def __init__(
        self,
        message: str = "Graph store is unavailable",
        details: list[Any] | None = None,
    ) -> None:
        super().__init__("UNAVAILABLE", message, 503, details)


class RateLimitError(AppError):
    def __init__(
        self,
        message: str = "Too many requests. Try again shortly.",
        details: list[Any] | None = None,
    ) -> None:
        super().__init__("RATE_LIMIT_EXCEEDED", message, 429, details)
