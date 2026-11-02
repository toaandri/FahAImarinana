"""Explicit simulator; no message is delivered to an operator."""
import logging
from typing import Protocol
from fastapi import Depends
from ...core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class SmsGateway(Protocol):
    def send(self, phone: str, message: str) -> None: ...


class SimulationSmsGateway:
    def send(self, phone: str, message: str) -> None:
        # Never log personal phone numbers or editorial contents.
        logger.info("SMS simulated; no provider delivery (%d characters)", len(message))


def get_sms_gateway(settings: Settings = Depends(get_settings)) -> SmsGateway:
    return SimulationSmsGateway()


def send_sms_via_gateway(phone: str, message: str) -> None:
    """Legacy simulator entry point."""
    SimulationSmsGateway().send(phone, message)
