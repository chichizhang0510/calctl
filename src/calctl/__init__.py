''' 
calctl - A command-line calendar manager
'''

__version__ = "0.1.0"


from .errors import InvalidInputError, NotFoundError, StorageError, CalctlError
from .models import Event

__all__ = [
    "InvalidInputError",
    "NotFoundError",
    "StorageError",
    "CalctlError",
    "Event",
]