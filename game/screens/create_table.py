"""
Create table screen for normal multiplayer rooms.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from ..auth.client import APIClient


def build(app):
    app._clear()
    f = app._container

    client = getattr(app, "api", None) or APIClient(
        host=app.data.get("server", {}).get("host", APIClient().host),
        port=app.data.get("server", {}).get("port", 8000),
    )

    title = tk.Label(
        f,
        text="Create a table",
        bg=app.BG_DARK,
        fg=app.GOLD,
        font=app.f_title,
    )
    title.pack(pady=(28, 8))

    subtitle = tk.Label(
        f,
        text="Name the table, choose the player count, then decide if it needs a password.",
        bg=app.BG_DARK,
        fg=app.SILVER,
        font=app.f_small,
        wraplength=640,
        justify="center",
    )
    subtitle.pack(pady=(0, 18))

    status_var = tk.StringVar(value="")
    tk.Label(
        f,
        textvariable=status_var,
        bg=app.BG_DARK,
        fg=app.SILVER,
        font=app.f_small,
    ).pack(pady=(0, 10))

    form = tk.Frame(f, bg=app.BG_DARK)
    form.pack(fill="x", padx=34, pady=10)

    def current_player_name() -> str:
        return app.data.get("active_profile") or "Player"

    table_name_var = tk.StringVar(value=f"{current_player_name()}'s Table")
    players_var = tk.StringVar(value="4")
    use_password_var = tk.BooleanVar(value=False)
    password_var = tk.StringVar(value="")

    def _add_field(label: str):
        tk.Label(form, text=label, bg=app.BG_DARK, fg=app.GOLD, font=app.f_small).pack(anchor="w", pady=(10, 4))

    _add_field("Table name")
    tk.Entry(form, textvariable=table_name_var, font=app.f_small, width=42).pack(anchor="w", fill="x")

    _add_field("Number of players")
    player_count = ttk.Combobox(form, textvariable=players_var, values=("2", "3", "4"), state="readonly", width=18)
    player_count.pack(anchor="w")

    password_check = tk.Checkbutton(
        form,
        text="Use a password",
        variable=use_password_var,
        bg=app.BG_DARK,
        fg=app.WHITE,
        selectcolor=app.BG_MID,
        activebackground=app.BG_DARK,
        activeforeground=app.GOLD,
        font=app.f_small,
    )
    password_check.pack(anchor="w", pady=(12, 0))

    password_entry_row = tk.Frame(form, bg=app.BG_DARK)
    tk.Label(password_entry_row, text="Password", bg=app.BG_DARK, fg=app.GOLD, font=app.f_small).pack(anchor="w")
    password_entry = tk.Entry(password_entry_row, textvariable=password_var, font=app.f_small, width=30, show="*")
    password_entry.pack(anchor="w", pady=(2, 0))

    def _toggle_password(*_):
        if use_password_var.get():
            password_entry.configure(state="normal")
            password_entry_row.pack(anchor="w", pady=(8, 0))
        else:
            password_var.set("")
            password_entry_row.pack_forget()
            password_entry.configure(state="disabled")

    use_password_var.trace_add("write", _toggle_password)
    _toggle_password()

    buttons = tk.Frame(f, bg=app.BG_DARK)
    buttons.pack(pady=24)

    def _back():
        app.show_multiplayer_normal()

    def _create():
        table_name = table_name_var.get().strip()
        if not table_name:
            messagebox.showwarning("", "Please enter a table name.", parent=app)
            return

        max_players = int(players_var.get())
        password = password_var.get().strip() if use_password_var.get() else None
        if use_password_var.get() and not password:
            messagebox.showwarning("", "Please enter a password or disable the password option.", parent=app)
            return

        status_var.set("Creating table...")
        create_btn.config(state="disabled")

        def worker():
            try:
                result = client.create_normal_room(table_name, current_player_name(), max_players=max_players, password=password)
                if isinstance(result, dict) and result.get("error"):
                    raise RuntimeError(result["error"])
                app._pending_normal_room = result
                app.after(0, lambda: app.show_multiplayer_normal())
            except Exception as exc:
                app.after(0, lambda: status_var.set(f"Could not create table: {exc}"))
                app.after(0, lambda: create_btn.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    create_btn = tk.Button(
        buttons,
        text="Create this table",
        bg=app.MENU_BTN_ACT,
        fg=app.BG_DARK,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        padx=14,
        pady=6,
        command=_create,
    )
    create_btn.pack(side="left", padx=6)

    tk.Button(
        buttons,
        text=app.s("back_menu"),
        bg=app.MENU_BTN_BG,
        fg=app.MENU_BTN_FG,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        padx=14,
        pady=6,
        command=_back,
    ).pack(side="left", padx=6)
