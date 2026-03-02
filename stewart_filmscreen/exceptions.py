"""Library exceptions."""


class StewartFilmscreenError(Exception):
    """Base error for the library."""


class ConnectionFailedError(StewartFilmscreenError):
    """Transport connection/authentication failed."""


class AuthenticationError(StewartFilmscreenError):
    """Authentication failed with provided credentials."""


class ProtocolParseError(StewartFilmscreenError):
    """Incoming frame could not be parsed."""
