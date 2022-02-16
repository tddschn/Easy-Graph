"""
**********
Exceptions
**********

Base exceptions and errors for EasyGraph.
"""

__all__ = [
    "EasyGraphException",
    "EasyGraphError"
]

class EasyGraphException(Exception):
    """Base class for exceptions in NetworkX."""


class EasyGraphError(EasyGraphException):
    """Exception for a serious error in NetworkX"""

