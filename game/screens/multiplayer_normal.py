"""
game/screens/multiplayer_normal.py — Normal multiplayer lobby.
Shows server-backed normal rooms and lets the player create a 2/3/4 player table.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

from ..auth.client import APIClient


def _room_name(room: dict) -> str:
    return room.get("room_name") or room.get("table_name") or "Table"


def _creator_name(room: dict) -> str:
    return room.get("creator_name") or room.get("host_player") or "?"


def _room_summary(room: dict) -> str:
    max_players = room.get("max_players", 4)
    current_players = room.get("player_count", 1)
    lock_status = "locked" if room.get("is_private") or room.get("requires_password") else "open"
    return (
        f"{_room_name(room)} • host {_creator_name(room)} • "
        f"{current_players}/{max_players} players • {lock_status}"
    )
def format_table_summary(room: dict) -> str:
    max_players = room.get("max_players", 4)
    current_players = room.get("player_count", 1)
    lock_status = "locked" if room.get("is_private") or room.get("requires_password") or room.get("locked") else "open"
    return (
        f"{_room_name(room)} • host {_creator_name(room)} • "
        f"{current_players} players • {max_players} max • {lock_status}"
    )


def build(app):
    """Build the normal multiplayer menu backed by the server normal-rooms API."""
    app._clear()
    f = app._container

    client = getattr(app, "api", None) or APIClient(
        host=app.data.get("server", {}).get("host", APIClient().host),
        port=app.data.get("server", {}).get("port", 8000),
    )

    title = tk.Label(
        f,
        text="✦  Normal Multiplayer  ✦",
        bg=app.BG_DARK,
        fg=app.GOLD,
        font=app.f_title,
    )
    title.pack(pady=(24, 8))

    subtitle = tk.Label(
        f,
        text="Create a table, wait in room, then start when ready",
        bg=app.BG_DARK,
        fg=app.SILVER,
        font=app.f_small,
    )
    subtitle.pack(pady=(0, 14))

    status_var = tk.StringVar(value="")
    status_label = tk.Label(
        f,
        textvariable=status_var,
        bg=app.BG_DARK,
        fg=app.SILVER,
        font=app.f_small,
    )
    status_label.pack(pady=(0, 8))

    current_room_id = {"value": None}
    current_room_cache = {"value": None}
    refresh_after = {"value": None}
    room_state = app.data.setdefault("multiplayer", {})

    actions_top = tk.Frame(f, bg=app.BG_DARK)
    actions_top.pack(fill="x", padx=24, pady=(4, 8))

    tk.Button(
        actions_top,
        text="Create a table",
        bg=app.MENU_BTN_ACT,
        fg=app.BG_DARK,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=6,
        command=lambda: app.show_create_table(),
    ).pack(side="left")

    tk.Button(
        actions_top,
        text="Refresh",
        bg=app.MENU_BTN_BG,
        fg=app.MENU_BTN_FG,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        command=lambda: refresh_rooms(),
    ).pack(side="right")

    waiting_frame = tk.LabelFrame(
        f,
        text="Waiting room",
        bg=app.BG_DARK,
        fg=app.GOLD,
        font=app.f_small,
        bd=1,
        relief="flat",
    )
    waiting_frame.pack(fill="x", padx=24, pady=(6, 10))

    waiting_title_var = tk.StringVar(value="Not in a room")
    waiting_info_var = tk.StringVar(value="Create or join a table to wait for players.")
    waiting_status_var = tk.StringVar(value="")

    tk.Label(waiting_frame, textvariable=waiting_title_var, bg=app.BG_DARK, fg=app.WHITE, font=app.f_label).pack(anchor="w", padx=10, pady=(8, 2))
    tk.Label(waiting_frame, textvariable=waiting_info_var, bg=app.BG_DARK, fg=app.SILVER, font=app.f_small).pack(anchor="w", padx=10)
    tk.Label(waiting_frame, textvariable=waiting_status_var, bg=app.BG_DARK, fg=app.SILVER, font=app.f_small, justify="left").pack(anchor="w", padx=10, pady=(4, 2))

    waiting_players_container = tk.Frame(waiting_frame, bg=app.BG_DARK)
    waiting_players_container.pack(fill="x", padx=10, pady=(4, 8))

    waiting_buttons = tk.Frame(waiting_frame, bg=app.BG_DARK)
    waiting_buttons.pack(anchor="w", padx=10, pady=(0, 10))

    start_btn = tk.Button(
        waiting_buttons,
        text="Start game",
        bg=app.MENU_BTN_ACT,
        fg=app.BG_DARK,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        state="disabled",
        command=lambda: start_room(),
    )
    start_btn.pack(side="left", padx=(0, 6))

    ready_btn = tk.Button(
        waiting_buttons,
        text="Ready",
        bg=app.MENU_BTN_BG,
        fg=app.MENU_BTN_FG,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        state="disabled",
        command=lambda: toggle_ready_state(),
    )
    ready_btn.pack(side="left", padx=(0, 6))

    leave_btn = tk.Button(
        waiting_buttons,
        text="Leave room",
        bg=app.MENU_BTN_BG,
        fg=app.MENU_BTN_FG,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        state="disabled",
        command=lambda: leave_room(),
    )
    leave_btn.pack(side="left")

    rooms_frame = tk.Frame(f, bg=app.BG_DARK)
    rooms_frame.pack(fill="both", expand=True, padx=24, pady=(8, 10))

    def set_status(text: str):
        status_var.set(text)

    def current_player_name() -> str:
        return app.data.get("active_profile") or "Player"

    def _display_room_in_waiting(room: dict | None):
        current_room_cache["value"] = room
        player_name = current_player_name()
        if not room:
            waiting_title_var.set("Not in a room")
            waiting_info_var.set("Create or join a table to wait for players.")
            waiting_status_var.set("")
            for widget in waiting_players_container.winfo_children():
                widget.destroy()
            start_btn.config(state="disabled")
            ready_btn.config(state="disabled", text="Ready")
            leave_btn.config(state="disabled")
            return

        room_name = _room_name(room)
        room_state = room.get("status", "waiting")
        lock_icon = "🔒 " if room.get("is_private") or room.get("requires_password") else ""
        waiting_title_var.set(f"{lock_icon}{room_name}")
        waiting_info_var.set(
            f"Host: {_creator_name(room)} • {room.get('player_count', 1)}/{room.get('max_players', 4)} players • {room_state}"
        )

        current_ready_ids = set(room.get("ready_player_ids") or [])
        waiting_status_var.set("Everyone is ready" if room.get("all_ready") else "Waiting for players to ready up")

        for widget in waiting_players_container.winfo_children():
            widget.destroy()

        players = room.get("players") or []
        if players:
            for index, player in enumerate(players):
                row = tk.Frame(waiting_players_container, bg=app.BG_MID if index % 2 == 0 else app.BG_PANEL)
                row.pack(fill="x", pady=2)

                player_name_value = player.get("game_name", "?")
                player_ready = player.get("profile_id") in current_ready_ids
                tk.Label(
                    row,
                    text=f"{player_name_value} {'(ready)' if player_ready else '(not ready)'}",
                    bg=row.cget("bg"),
                    fg=app.WHITE,
                    font=app.f_small,
                    anchor="w",
                ).pack(side="left", padx=8, pady=6, fill="x", expand=True)

                if player_name_value == player_name:
                    ready_btn.config(
                        state="normal",
                        text="Cancel ready" if player_ready else "Ready",
                    )
                else:
                    tk.Label(
                        row,
                        text="Ready" if player_ready else "Waiting",
                        bg=row.cget("bg"),
                        fg=app.GOLD if player_ready else app.SILVER,
                        font=app.f_small,
                    ).pack(side="right", padx=8)
        else:
            tk.Label(
                waiting_players_container,
                text="Players list unavailable",
                bg=app.BG_DARK,
                fg=app.SILVER,
                font=app.f_small,
            ).pack(anchor="w")
            ready_btn.config(state="disabled")

        is_creator = _creator_name(room) == player_name
        can_start = is_creator and room_state == "waiting" and room.get("all_ready") and room.get("player_count", 0) >= 2
        start_btn.config(state=("normal" if can_start else "disabled"))
        leave_btn.config(state="normal")

    def _schedule_refresh():
        if refresh_after["value"] is not None:
            try:
                app.after_cancel(refresh_after["value"])
            except Exception:
                pass
            refresh_after["value"] = None

        def tick():
            refresh_after["value"] = None
            if f.winfo_exists():
                refresh_rooms()

        refresh_after["value"] = app.after(4000, tick)

    def _render_rooms(rooms: list[dict]):
        for widget in rooms_frame.winfo_children():
            widget.destroy()

        header = tk.Frame(rooms_frame, bg=app.BG_DARK)
        header.pack(fill="x", pady=(0, 8))
        tk.Label(
            header,
            text="Visible rooms",
            bg=app.BG_DARK,
            fg=app.GOLD,
            font=app.f_small,
        ).pack(side="left")

        if not rooms:
            tk.Label(
                rooms_frame,
                text="No visible tables yet. Create one to start.",
                bg=app.BG_DARK,
                fg=app.SILVER,
                font=app.f_small,
            ).pack(pady=18)
            return

        for room in rooms:
            row = tk.Frame(rooms_frame, bg=app.BG_DARK, bd=1, relief="flat")
            row.pack(fill="x", pady=4)

            info = tk.Frame(row, bg=app.BG_DARK)
            info.pack(side="left", fill="x", expand=True, padx=10, pady=8)
            tk.Label(
                info,
                text=("🔒 " if room.get("is_private") or room.get("requires_password") else "🔓 ") + _room_summary(room),
                bg=app.BG_DARK,
                fg=app.SILVER,
                font=app.f_small,
                anchor="w",
                justify="left",
                wraplength=560,
            ).pack(anchor="w")

            join_btn = tk.Button(
                row,
                text="Join this table",
                bg=app.MENU_BTN_BG,
                fg=app.MENU_BTN_FG,
                font=app.f_small,
                relief="flat",
                cursor="hand2",
                command=lambda r=room: join_room(r),
            )
            join_btn.pack(side="right", padx=10, pady=10)

            if room.get("status") != "waiting" or room.get("is_full"):
                join_btn.config(state="disabled")

    def refresh_rooms():
        set_status("Loading rooms...")

        def worker():
            try:
                result = client.get_normal_rooms()
                if isinstance(result, dict) and result.get("error"):
                    raise RuntimeError(result["error"])
                rooms = result if isinstance(result, list) else []

                room_id = current_room_id["value"] or room_state.get("normal_room_id")
                if room_id:
                    current = client.get_normal_room(room_id)
                    if isinstance(current, dict) and not current.get("error"):
                        current_room_id["value"] = room_id
                        app.after(0, lambda r=current: _display_room_in_waiting(r))
                    else:
                        current_room_id["value"] = None
                        room_state.pop("normal_room_id", None)
                        app.after(0, lambda: _display_room_in_waiting(None))

                app.after(0, lambda: (_render_rooms(rooms), set_status(f"{len(rooms)} room(s) found"), _schedule_refresh()))
            except Exception as exc:
                app.after(0, lambda: set_status(f"Could not load rooms: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _send_create_room(table_name: str, max_players: int, password: str | None):
        player_name = current_player_name()
        set_status(f"Creating a {max_players}-player table...")

        def worker():
            try:
                result = client.create_normal_room(table_name, player_name, max_players=max_players, password=password)
                if isinstance(result, dict) and result.get("error"):
                    raise RuntimeError(result["error"])
                room_id = result.get("room_id")
                if room_id:
                    current_room_id["value"] = room_id
                    room_state["normal_room_id"] = room_id
                room_state["normal_room"] = result
                app.after(0, lambda r=result: (_display_room_in_waiting(r), set_status(f"Created {table_name} ({max_players} players)"), refresh_rooms()))
            except Exception as exc:
                app.after(0, lambda: set_status(f"Could not create table: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def toggle_ready_state():
        room = current_room_cache["value"]
        room_id = current_room_id["value"]
        if not room_id or not room:
            return

        player_name = current_player_name()
        current_ready_ids = set(room.get("ready_player_ids") or [])
        current_player = next((player for player in room.get("players", []) if player.get("game_name") == player_name), None)
        is_ready = bool(current_player and current_player.get("profile_id") in current_ready_ids)

        set_status("Updating ready state...")

        def worker():
            try:
                result = client.set_normal_room_ready(room_id, player_name, ready=not is_ready)
                if isinstance(result, dict) and result.get("error"):
                    raise RuntimeError(result["error"])
                room_state["normal_room"] = result
                app.after(0, lambda r=result: (_display_room_in_waiting(r), set_status("Ready state updated"), refresh_rooms()))
            except Exception as exc:
                app.after(0, lambda: set_status(f"Could not update ready state: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def join_room(room: dict):
        player_name = current_player_name()
        room_name = _room_name(room)
        table_id = room.get("room_id") or room.get("table_id")
        if not table_id:
            messagebox.showerror("", "This room is missing an identifier.", parent=app)
            return

        password = None
        if room.get("is_private") or room.get("requires_password"):
            password = simpledialog.askstring("Join private table", f"Enter password for {room_name}", parent=app, show="*")
            if password is None:
                return

        set_status(f"Joining {room_name}...")

        def worker():
            try:
                result = client.join_normal_room(table_id, player_name, password=password)
                if isinstance(result, dict) and result.get("error"):
                    raise RuntimeError(result["error"])
                current_room_id["value"] = table_id
                room_state["normal_room_id"] = table_id
                room_state["normal_room"] = result
                app.after(0, lambda r=result: (_display_room_in_waiting(r), set_status(f"Joined {room_name}"), refresh_rooms()))
            except Exception as exc:
                app.after(0, lambda: set_status(f"Could not join table: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def leave_room():
        room_id = current_room_id["value"]
        if not room_id:
            return

        player_name = current_player_name()
        set_status("Leaving room...")

        def worker():
            try:
                result = client.leave_normal_room(room_id, player_name)
                if isinstance(result, dict) and result.get("error"):
                    raise RuntimeError(result["error"])
                current_room_id["value"] = None
                room_state.pop("normal_room_id", None)
                room_state.pop("normal_room", None)
                app.after(0, lambda: (_display_room_in_waiting(None), set_status("Left room"), refresh_rooms()))
            except Exception as exc:
                app.after(0, lambda: set_status(f"Could not leave room: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def start_room():
        room = current_room_cache["value"]
        room_id = current_room_id["value"]
        if not room_id or not room:
            return

        if room.get("creator_name") != current_player_name():
            set_status("Only the table creator can start the game")
            return

        set_status("Starting room...")

        def worker():
            try:
                result = client.start_normal_room(room_id, current_player_name())
                if isinstance(result, dict) and result.get("error"):
                    raise RuntimeError(result["error"])
                room_state["normal_room"] = result
                app.after(0, lambda r=result: (_display_room_in_waiting(r), set_status("Game started for this table"), refresh_rooms()))
            except Exception as exc:
                app.after(0, lambda: set_status(f"Could not start game: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    actions = tk.Frame(f, bg=app.BG_DARK)
    actions.pack(pady=(8, 18))

    tk.Button(
        actions,
        text=app.s("back_menu"),
        bg=app.MENU_BTN_BG,
        fg=app.MENU_BTN_FG,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        command=app.show_menu,
    ).pack(side="left", padx=6)

    pending_room = getattr(app, "_pending_normal_room", None)
    if pending_room:
        app._pending_normal_room = None
        current_room_id["value"] = pending_room.get("room_id")
        room_state["normal_room_id"] = pending_room.get("room_id")
        room_state["normal_room"] = pending_room
        _display_room_in_waiting(pending_room)

    cached_room = room_state.get("normal_room")
    cached_room_id = room_state.get("normal_room_id")
    if not pending_room and cached_room and cached_room_id:
        current_room_id["value"] = cached_room_id
        _display_room_in_waiting(cached_room)

    refresh_rooms()
