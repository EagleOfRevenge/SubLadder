"""
multiplayer/anticheat.py — Sub Ladder
Local anti-cheat entrypoint for multiplayer game state validation.
"""

from anticheat_shared import (
    sign_save,
    verify_save,
    validate_profile,
    validate_data,
    validate_game_state,
    log_suspicious_activity,
    flag_profile,
    get_profile_flags,
)
