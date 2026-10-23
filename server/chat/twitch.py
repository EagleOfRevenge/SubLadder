"""
Sub Ladder v4.0 — Twitch chat connector (real implementation).

Connects to Twitch IRC (via tmi.py) for live chat message reception
and uses the Twitch Helix API for sending messages.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Awaitable

import httpx
from tmi import Client as TMIClient

from .base import ChatConnector, ChatMessage

logger = logging.getLogger(__name__)

# Callback type for incoming messages
MessageCallback = Callable[[ChatMessage], Awaitable[None]]


class TwitchChatConnector(ChatConnector):
    """Real Twitch IRC chat connector with Helix API message sending."""

    provider_name = "twitch"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.channel: Optional[str] = self.config.get("channel")
        self._bot_username: Optional[str] = self.config.get("bot_username")
        self._oauth_token: Optional[str] = self.config.get("oauth_token")
        self._client: Optional[TMIClient] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._message_callback: Optional[MessageCallback] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._last_messages: List[ChatMessage] = []
        self._max_history = 200  # keep last N messages in memory

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Connect to Twitch IRC and start listening for chat messages."""
        if self.connected:
            return

        if not self.channel:
            raise ValueError("Twitch connector requires a 'channel' configuration.")
        if not self._oauth_token:
            raise ValueError("Twitch connector requires an 'oauth_token' configuration.")
        if not self._bot_username:
            raise ValueError("Twitch connector requires a 'bot_username' configuration.")

        # HTTP client for Helix API
        self._http_client = httpx.AsyncClient(
            base_url="https://api.twitch.tv/helix",
            headers={"Authorization": f"Bearer {self._oauth_token}", "Client-Id": self._bot_username},
            timeout=10.0,
        )

        # IRC client
        self._client = TMIClient(
            username=self._bot_username,
            password=self._oauth_token,
            channels=[self.channel],
        )
        self._client.add_message_callback(self._on_twitch_message)
        self._client.connect()

        self.connected = True
        logger.info("TwitchChatConnector connected to #%s", self.channel)

        # Start background reconnect loop
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def disconnect(self) -> None:
        """Disconnect from Twitch IRC."""
        if not self.connected:
            return

        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None

        if self._client:
            self._client.disconnect()
            self._client = None

        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        self.connected = False
        logger.info("TwitchChatConnector disconnected")

    # ------------------------------------------------------------------
    # Send / Fetch
    # ------------------------------------------------------------------

    async def send_message(self, channel_id: str, message: str) -> None:
        """Send a message to a Twitch channel via Helix API (deprecated but still works) or IRC."""
        if not self.connected:
            raise RuntimeError("Twitch connector is not connected.")

        target = channel_id or self.channel
        if not target:
            raise ValueError("channel_id is required for send_message.")

        # Try sending via IRC (more reliable for bots)
        if self._client and self._client.ws:
            irc_message = f"PRIVMSG #{target} :{message}"
            self._client.send(irc_message)
            logger.debug("Sent IRC message to #%s: %s", target, message[:50])
        else:
            raise RuntimeError("Cannot send message: IRC connection is not available.")

    async def fetch_messages(self, channel_id: Optional[str] = None, limit: int = 50) -> List[ChatMessage]:
        """Return recently received messages from memory."""
        if not self.connected:
            raise RuntimeError("Twitch connector is not connected.")
        # Return the most recent messages up to `limit`
        history = self._last_messages[-limit:]
        return list(history)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def set_message_callback(self, callback: MessageCallback) -> None:
        """Register a callback for incoming chat messages."""
        self._message_callback = callback

    async def _on_twitch_message(self, channel: str, user: str, message: str) -> None:
        """Handle incoming Twitch IRC messages."""
        now = datetime.now(timezone.utc).isoformat()
        chat_msg = ChatMessage(
            provider="twitch",
            channel_id=channel.lstrip("#"),
            sender=user,
            content=message,
            timestamp=now,
        )

        # Keep in memory
        self._last_messages.append(chat_msg)
        if len(self._last_messages) > self._max_history:
            self._last_messages = self._last_messages[-self._max_history:]

        # Dispatch to callback
        if self._message_callback:
            try:
                await self._message_callback(chat_msg)
            except Exception as exc:
                logger.error("Error in Twitch message callback: %s", exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _reconnect_loop(self) -> None:
        """Reconnect to Twitch IRC if the connection drops."""
        while self.connected:
            try:
                if self._client and not self._client.ws:
                    logger.warning("Twitch IRC connection lost. Reconnecting…")
                    self._client.reconnect()
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Twitch reconnect error: %s", exc)
                await asyncio.sleep(10)
