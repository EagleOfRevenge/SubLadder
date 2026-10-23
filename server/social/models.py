"""
Shared models for the social graph / friend list system.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PlayerStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    AWAY = "away"
    LOBBY = "lobby"
    LOOKING_FOR_MATCH = "looking_for_match"
    MATCH_FOUND = "match_found"
    LOADING_GAME = "loading_game"
    NORMAL_GAME = "normal_game"
    RANKED_GAME = "ranked_game"
    TUTORIAL = "tutorial"
    TRAINING = "training"
    CUSTOM_GAME = "custom_game"


class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class FriendRequestCreate(BaseModel):
    target_profile_name: str = Field(min_length=1, max_length=64)


class FriendRequestAction(BaseModel):
    requestor_profile_name: str = Field(min_length=1, max_length=64)


class BlockRequest(BaseModel):
    blocked_profile_name: str = Field(min_length=1, max_length=64)


class PresenceUpdate(BaseModel):
    status: PlayerStatus
    message: Optional[str] = Field(default=None, max_length=255)


class ReportRequest(BaseModel):
    reported_profile_name: str = Field(min_length=1, max_length=64)
    reason: str = Field(min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, max_length=2000)
