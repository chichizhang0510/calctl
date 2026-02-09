class CalctlError(Exception):
    exit_code = 1

class InvalidInputError(CalctlError):
    exit_code = 2

class NotFoundError(CalctlError):
    exit_code = 3

class StorageError(CalctlError):
    exit_code = 1

class ConflictError(CalctlError):
    exit_code = 4
