"""
Sub Ladder v4.0 — YouTube live chat connector (real implementation).

Connects to YouTube Live Chat via the YouTube Data API v3 for receiving
and sending messages in real-time through long-polling + API calls.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Awaitable

import httpx

from .base import ChatConnector, ChatMessage

logger = logging.getLogger(__name__)

# Callback type for incoming messages
MessageCallback = Callable[[ChatMessage], Awaitable[None]]


class YouTubeChatConnector(ChatConnector):
    """Real YouTube Live Chat connector using YouTube Data API v3."""

    provider_name = "youtube"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.live_chat_id: Optional[str] = self.config.get("live_chat_id")
        self.api_key: Optional[str] = self.config.get("api_key")
        self._http_client: Optional[httpx.AsyncClient] = None
        self._message_callback: Optional[MessageCallback] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._next_page_token: Optional[str] = None
        self._last_messages: List[ChatMessage] = []
        self._max_history = 200
        self._poll_interval: float = self.config.get("poll_interval", 5.0)
        self._running = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Start polling YouTube Live Chat for new messages."""
        if self.connected:
            return

        if not self.live_chat_id:
            raise ValueError("YouTube connector requires a 'live_chat_id' configuration.")
        if not self.api_key:
            raise ValueError("YouTube connector requires an 'api_key' configuration.")

        self._http_client = httpx.AsyncClient(
            base_url="https://www.googleapis.com/youtube/v3",
            params={"key": self.api_key},
            timeout=15.0,
        )

        self._running = True
        self.connected = True
        logger.info("YouTubeChatConnector connected to live chat %s", self.live_chat_id)

        # Start background polling loop
        self._poll_task = asyncio.create_task(self._poll_chat_loop())

    async def disconnect(self) -> None:
        """Stop polling and close HTTP client."""
        if not self.connected:
            return

        self._running = False

        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None

        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        self.connected = False
        logger.info("YouTubeChatConnector disconnected")

    # ------------------------------------------------------------------
    # Send / Fetch
    # ------------------------------------------------------------------

    async def send_message(self, channel_id: str, message: str) -> None:
        """Send a message to a YouTube live chat via the API."""
        if not self.connected:
            raise RuntimeError("YouTube connector is not connected.")

        target_chat_id = channel_id or self.live_chat_id
        if not target_chat_id:
            raise ValueError("live_chat_id is required for send_message.")

        url = "/liveChatMessages"
        payload = {
            "liveChatId": target_chat_id,
            "messageMetadata": {
                "gid": f"subladder_{id(self)}_{int(asyncio.get_event_loop().time() * 1000)}"
            },
            "textMessageData": {"text": message},
        }

        try:
            response = await self._http_client.post(url, json=payload)
            if response.status_code in (200, 201, 204):
                logger.debug("Sent YouTube chat message to %s", target_chat_id)
            else:
                logger.error(
                    "Failed to send YouTube chat: %d — %s",
                    response.status_code,
                    response.text[:200],
                )
        except Exception as exc:
            logger.error("Error sending YouTube chat message: %s", exc)

    async def fetch_messages(self, channel_id: Optional[str] = None, limit: int = 50) -> List[ChatMessage]:
        """Return recently received messages from memory."""
        if not self.connected:
            raise RuntimeError("YouTube connector is not connected.")
        history = self._last_messages[-limit:]
        return list(history)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def set_message_callback(self, callback: MessageCallback) -> None:
        """Register a callback for incoming chat messages."""
        self._message_callback = callback

    async def _poll_chat_loop(self) -> None:
        """Continuously poll YouTube Live Chat API for new messages."""
        while self._running and self.connected:
            try:
                await self._poll_once()
                await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("YouTube chat poll error: %s", exc)
                await asyncio.sleep(self._poll_interval)

    async def _poll_once(self) -> None:
        """Fetch one batch of messages from YouTube Live Chat API."""
        url = "/liveChat/messages"
        params: Dict[str, Any] = {
            "liveChatId": self.live_chat_id,
            "part": "snippet,replies",
        }
        if self._next_page_token:
            params["pageToken"] = self._next_page_token

        try:
            response = await self._http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("YouTube API error: %s — %s", exc.response.status_code, exc.response.text[:200])
            return
        except Exception as exc:
            logger.error("Error polling YouTube chat: %s", exc)
            return

        # Store next page token for the next poll
        self._next_page_token = data.get("nextPageToken")

        items = data.get("items", [])
        if not items:
            return

        for item in items:
            snippet = item.get("snippet", {})
            metadata = snippet.get("liveChatMessageMetadata", {})
            display_message = metadata.get("displayMessage", "")
            if not display_message:
                continue

            author = snippet.get("topLevelComment", {}).get("snippet", {}).get("authorDisplayName", "Unknown")
            timestamp_str = snippet.get("publishedAt", "")
            # YouTube returns ISO-8601; normalise to UTC
            timestamp = timestamp_str if timestamp_str else datetime.now(timezone.utc).isoformat()

            chat_msg = ChatMessage(
                provider="youtube",
                channel_id=self.live_chat_id or "",
                sender=author,
                content=display_message,
                timestamp=timestamp,
            )

            self._last_messages.append(chat_msg)
            if len(self._last_messages) > self._max_history:
                self._last_messages = self._last_messages[-self._max_history:]

            if self._message_callback:
                try:
                    await self._message_callback(chat_msg)
                except Exception as exc:
                    logger.error("Error in YouTube message callback: %s", exc)
