"""Business errors independent from HTTP adapters."""
class DomainError(ValueError):
    status_code = 400


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class ForbiddenError(DomainError):
    status_code = 403


class AuthenticationError(DomainError):
    status_code = 401


class IntegrationUnavailableError(DomainError):
    status_code = 503
