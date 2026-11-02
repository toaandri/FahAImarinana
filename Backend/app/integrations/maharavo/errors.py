"""Safe backend errors: remote bodies, headers and API keys are never included."""
from ...core.errors import DomainError


class MaharavoError(DomainError):
    status_code = 502
    code = 'maharavo_error'


class MaharavoNotConfigured(MaharavoError):
    status_code = 503
    code = 'interface_not_documented'

    def __init__(self):
        super().__init__('Interface HTTP Maharavo non documentée ou non configurée ; aucune connexion externe effectuée.')


class MaharavoProtocolError(MaharavoError):
    code = 'invalid_response'


class MaharavoLimitError(MaharavoError):
    code = 'result_limit_exceeded'


class MaharavoTimeout(MaharavoError):
    status_code = 504
    code = 'timeout'


class MaharavoUnavailable(MaharavoError):
    status_code = 503
    code = 'unavailable'


class MaharavoCredentialsError(MaharavoError):
    code = 'credentials_rejected'
