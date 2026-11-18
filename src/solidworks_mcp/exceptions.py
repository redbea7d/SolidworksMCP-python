"""Custom exceptions for SolidWorks MCP Server."""


class SolidWorksMCPError(Exception):
    """Base exception for SolidWorks MCP Server errors."""

    pass


class SolidWorksConnectionError(SolidWorksMCPError):
    """Exception raised when SolidWorks connection fails."""

    pass


class SolidWorksNotRunningError(SolidWorksConnectionError):
    """No SolidWorks is running to attach to, and the server won't start one.

    Not a malfunction: the circuit breaker doesn't count it, so the first
    call after the user starts SolidWorks connects at once.
    """


class SolidWorksOperationError(SolidWorksMCPError):
    """Exception raised when SolidWorks operation fails."""

    pass


class ConfigurationError(SolidWorksMCPError):
    """Exception raised for configuration issues."""

    pass


class AuthenticationError(SolidWorksMCPError):
    """Exception raised for authentication failures."""

    pass


class RateLimitError(SolidWorksMCPError):
    """Exception raised when rate limit is exceeded."""

    pass


class InputRefused(ValueError):
    """The adapter checked an input against the document and refused it.

    An expected answer, not a fault: a section line that misses its view, a
    point with nothing to dimension. It is logged as one line, without a
    traceback, and the tools classify it as ``invalid_input``.
    """
