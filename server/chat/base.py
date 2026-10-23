"""
Sub Ladder v4.0 — Chat connector base interfaces.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ChatMessage:
    provider: str
    channel_id: str
    sender: str
    content: str
    timestamp: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ChatConnector(ABC):
    """Base class for chat connector implementations."""

    provider_name: str = "base"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.connected = False

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the chat provider."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the chat provider."""

    @abstractmethod
    async def send_message(self, channel_id: str, message: str) -> None:
        """Send a message to a chat channel."""

    @abstractmethod
    async def fetch_messages(self, channel_id: str, limit: int = 50) -> List[ChatMessage]:
        """Fetch recent chat messages."""

    def is_connected(self) -> bool:
        return self.connected
