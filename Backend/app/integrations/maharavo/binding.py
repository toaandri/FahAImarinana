"""Adapter boundary awaiting a real, inspectable Maharavo HTTP specification."""
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol
from pydantic import SecretStr
from .contracts import TaskRequest


@dataclass(frozen=True)
class WireRequest:
    method: Literal['GET', 'POST']
    path: str
    headers: dict[str, str] = field(repr=False)
    payload: dict[str, Any] | None = field(default=None, repr=False)
    # Set only when the actual provider documents this guarantee and header.
    idempotency_header: str | None = None


class DocumentedAdapter(Protocol):
    documentation_reference: str
    api_version: str

    def encode(self, request: TaskRequest, api_key: SecretStr) -> WireRequest: ...

    def normalize(self, payload: Any) -> dict: ...


# No concrete HTTP routes, authentication headers or vendor adapter are invented here.
