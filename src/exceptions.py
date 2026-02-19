"""
Custom exceptions for the application.
Provides well-defined error types with context and chaining support.
"""

from typing import Any


class UARTControlError(Exception):
    """Base exception for UART Control application."""
    
    def __init__(
        self,
        message: str,
        *,
        port: str | None = None,
        baud_rate: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.port = port
        self.baud_rate = baud_rate
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.port:
            parts.append(f"port={self.port}")
        if self.baud_rate:
            parts.append(f"baud_rate={self.baud_rate}")
        if self.details:
            parts.append(f"details={self.details}")
        return ", ".join(parts)


class SerialConnectionError(UARTControlError):
    """Raised when serial port connection fails."""
    
    def __init__(
        self,
        message: str,
        *,
        port: str | None = None,
        baud_rate: int | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.cause = cause
        details = {"cause": str(cause)} if cause else {}
        super().__init__(
            message,
            port=port,
            baud_rate=baud_rate,
            details=details,
        )
        if cause:
            self.__cause__ = cause


class SerialWriteError(UARTControlError):
    """Raised when writing to serial port fails."""
    
    def __init__(
        self,
        message: str,
        *,
        port: str | None = None,
        bytes_written: int | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.bytes_written = bytes_written
        self.cause = cause
        details = {"bytes_written": bytes_written, "cause": str(cause)} if cause else {"bytes_written": bytes_written}
        super().__init__(message, port=port, details=details)
        if cause:
            self.__cause__ = cause


class SerialReadError(UARTControlError):
    """Raised when reading from serial port fails."""
    
    def __init__(
        self,
        message: str,
        *,
        port: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.cause = cause
        details = {"cause": str(cause)} if cause else {}
        super().__init__(message, port=port, details=details)
        if cause:
            self.__cause__ = cause


class ConfigurationError(UARTControlError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str,
        *,
        key: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.key = key
        self.cause = cause
        details = {"key": key, "cause": str(cause)} if cause else {"key": key}
        super().__init__(message, details=details)
        if cause:
            self.__cause__ = cause


__all__ = [
    "UARTControlError",
    "SerialConnectionError",
    "SerialWriteError",
    "SerialReadError",
    "ConfigurationError",
]
