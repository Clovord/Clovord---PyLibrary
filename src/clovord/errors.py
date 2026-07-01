from __future__ import annotations


class ClovordError(Exception):
    """Base SDK exception with a stable Clovord error code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{self.code}] {self.message}")

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class ClovordHTTPError(ClovordError):
    def __init__(self, message: str) -> None:
        super().__init__("CLOVORD_HTTP_ERROR", message)


class ClovordInvalidTokenError(ClovordError):
    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__("CLOVORD_INVALID_TOKEN", message)


class ClovordGatewayDisconnectedError(ClovordError):
    def __init__(self, message: str = "Gateway disconnected") -> None:
        super().__init__("CLOVORD_GATEWAY_DISCONNECTED", message)


class ClovordExtensionError(ClovordError):
    def __init__(self, message: str) -> None:
        super().__init__("CLOVORD_EXTENSION_ERROR", message)
