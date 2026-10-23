"""
game/screens/pre_menu.py — Intro and profile selection screen shown before the main menu.
"""

import socket
import tkinter as tk
import webbrowser
from functools import partial
from tkinter import messagebox
from urllib.parse import urlparse

from ..constants import BG_DARK, BG_MID, BG_PANEL, GOLD, SILVER, WHITE
from ..constants import BTN_DEFAULT, BTN_HOVER, MENU_BTN_BG, LIFELINE_ON, LIFELINE_TEXT_ON
from ..utils import log_ui_exception, save_data


def build_intro_screen(app):
    """Show the startup intro with the Eagle Of Revenge branding."""
    app._clear()
    app._current_screen = "pre_menu_intro"
    app.sound.play_music("menu")

    f = app._container
    panel = tk.Frame(f, bg=app.BG_DARK)
    panel.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(
        panel,
        text="Eagle Of Revenge presents",
        bg=app.BG_DARK,
        fg=app.SILVER,
        font=app.f_small,
    ).pack(pady=(0, 8))

    tk.Label(
        panel,
        text="Sub Ladder",
        bg=app.BG_DARK,
        fg=app.GOLD,
        font=app.f_big,
    ).pack()

    tk.Label(
        panel,
        text="Loading your profile selection...",
        bg=app.BG_DARK,
        fg=app.TEXT_DISABLED,
        font=app.f_small,
    ).pack(pady=(14, 0))

    app.after(1400, lambda: app.show_pre_menu_profiles())


def build_profile_selection_screen(app):
    """Show the profile selection screen before entering the main menu."""
    app._clear()
    app._current_screen = "pre_menu_profiles"
    f = app._container

    header = tk.Frame(f, bg=app.BG_DARK)
    header.pack(fill="x", padx=28, pady=(24, 10))
    tk.Label(
        header,
        text="Choose your profile",
        bg=app.BG_DARK,
        fg=app.GOLD,
        font=app.f_title,
    ).pack(anchor="w")
    tk.Label(
        header,
        text="Select an existing profile or create a new one to start playing.",
        bg=app.BG_DARK,
        fg=app.SILVER,
        font=app.f_small,
        wraplength=640,
    ).pack(anchor="w", pady=(4, 0))

    content = tk.Frame(f, bg=app.BG_DARK)
    content.pack(fill="both", expand=True, padx=28, pady=12)

    profiles = app.data.get("profiles", {})
    if profiles:
        for profile_name, profile_data in profiles.items():
            card = tk.Frame(content, bg=BG_PANEL, bd=1, relief="flat")
            card.pack(fill="x", pady=6)

            left = tk.Frame(card, bg=BG_PANEL)
            left.pack(side="left", fill="x", expand=True, padx=16, pady=12)
            tk.Label(
                left,
                text=profile_name,
                bg=BG_PANEL,
                fg=app.GOLD,
                font=app.f_label,
                anchor="w",
            ).pack(anchor="w")
            status_text = "Online profile" if profile_data.get("profile_type") == "online" else "Offline profile"
            tk.Label(
                left,
                text=status_text,
                bg=BG_PANEL,
                fg=app.SILVER,
                font=app.f_small,
                anchor="w",
            ).pack(anchor="w", pady=(2, 0))

            btn = tk.Button(
                card,
                text="Select",
                bg=LIFELINE_ON,
                fg=LIFELINE_TEXT_ON,
                font=app.f_small,
                relief="flat",
                cursor="hand2",
                padx=12,
                pady=6,
                command=partial(_select_profile, app, profile_name),
            )
            btn.pack(side="right", padx=12, pady=12)
            _add_hover(btn, app)
    else:
        empty = tk.Frame(content, bg=app.BG_DARK)
        empty.pack(fill="x", pady=12)
        tk.Label(
            empty,
            text="No profiles yet — create one to begin.",
            bg=app.BG_DARK,
            fg=app.SILVER,
            font=app.f_small,
        ).pack(anchor="center")

    actions = tk.Frame(f, bg=app.BG_DARK)
    actions.pack(fill="x", padx=28, pady=(8, 20))

    create_btn = tk.Button(
        actions,
        text="Create profile",
        bg=app.GOLD,
        fg=app.BG_DARK,
        font=app.f_menu_btn,
        relief="flat",
        cursor="hand2",
        padx=14,
        pady=8,
        command=partial(build_profile_creation_screen, app),
    )
    create_btn.pack(side="left")
    _add_hover(create_btn, app, active_bg=app.GOLD_DARK if hasattr(app, "GOLD_DARK") else app.GOLD)

    skip_btn = tk.Button(
        actions,
        text="Skip to menu",
        bg=MENU_BTN_BG,
        fg=app.SILVER,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=8,
        command=app.show_menu,
    )
    skip_btn.pack(side="left", padx=(10, 0))
    _add_hover(skip_btn, app)


def build_profile_creation_screen(app):
    """Ask whether the new profile should be offline or online, then handle the flow."""
    app._clear()
    app._current_screen = "pre_menu_create"
    f = app._container

    header = tk.Frame(f, bg=app.BG_DARK)
    header.pack(fill="x", padx=28, pady=(24, 16))
    tk.Label(
        header,
        text="Create a new profile",
        bg=app.BG_DARK,
        fg=app.GOLD,
        font=app.f_title,
    ).pack(anchor="w")
    tk.Label(
        header,
        text="Choose whether this profile should stay local or use an online account.",
        bg=app.BG_DARK,
        fg=app.SILVER,
        font=app.f_small,
        wraplength=620,
    ).pack(anchor="w", pady=(4, 0))

    chooser = tk.Frame(f, bg=app.BG_DARK)
    chooser.pack(expand=True, fill="both", padx=40, pady=20)

    offline_btn = tk.Button(
        chooser,
        text="Offline profile",
        bg="#2f7a40",
        fg=WHITE,
        font=app.f_menu_btn,
        relief="flat",
        cursor="hand2",
        padx=24,
        pady=12,
        width=24,
        command=partial(_create_offline_profile, app),
    )
    offline_btn.pack(pady=10)
    _add_hover(offline_btn, app, active_bg="#3b8f50")

    online_btn = tk.Button(
        chooser,
        text="Online profile",
        bg="#3d5a80",
        fg=WHITE,
        font=app.f_menu_btn,
        relief="flat",
        cursor="hand2",
        padx=24,
        pady=12,
        width=24,
        command=partial(build_online_provider_screen, app),
    )
    online_btn.pack(pady=10)
    _add_hover(online_btn, app, active_bg="#4e6f97")

    back_btn = tk.Button(
        f,
        text="← Back",
        bg=MENU_BTN_BG,
        fg=app.SILVER,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=8,
        command=partial(build_profile_selection_screen, app),
    )
    back_btn.pack(pady=16)


def build_online_provider_screen(app):
    """Offer Discord or Steam connection buttons for a new online profile."""
    app._clear()
    app._current_screen = "pre_menu_online"
    f = app._container

    header = tk.Frame(f, bg=app.BG_DARK)
    header.pack(fill="x", padx=28, pady=(24, 20))
    tk.Label(
        header,
        text="Choose your online provider",
        bg=app.BG_DARK,
        fg=app.GOLD,
        font=app.f_title,
    ).pack(anchor="w")
    tk.Label(
        header,
        text="Choose the platform you want to use for your online profile.",
        bg=app.BG_DARK,
        fg=app.SILVER,
        font=app.f_small,
        wraplength=620,
    ).pack(anchor="w", pady=(4, 0))

    body = tk.Frame(f, bg=app.BG_DARK)
    body.pack(expand=True, fill="both")

    cards = tk.Frame(body, bg=app.BG_DARK)
    cards.pack(expand=True)

    discord_card = tk.Frame(cards, bg="#232b4d", bd=1, relief="flat")
    discord_card.pack(padx=20, pady=10, fill="x")
    tk.Label(discord_card, text="Discord", bg="#232b4d", fg="#FFFFFF", font=app.f_menu_btn, anchor="w").pack(anchor="w", padx=18, pady=(14, 4))
    tk.Label(discord_card, text="Connect your account through Discord and keep your profile online.", bg="#232b4d", fg=app.SILVER, font=app.f_small, wraplength=520, justify="left", anchor="w").pack(anchor="w", padx=18, pady=(0, 12))
    tk.Button(
        discord_card,
        text="Connect via your Discord account",
        bg="#5865F2",
        fg=WHITE,
        font=app.f_menu_btn,
        relief="flat",
        cursor="hand2",
        padx=24,
        pady=12,
        command=lambda: _open_provider_auth(app, "discord"),
    ).pack(anchor="w", padx=18, pady=(0, 16))
    _add_hover(discord_card.winfo_children()[-1], app, active_bg="#6a75f6")

    steam_card = tk.Frame(cards, bg="#1f1f1f", bd=1, relief="flat")
    steam_card.pack(padx=20, pady=10, fill="x")
    tk.Label(steam_card, text="Steam", bg="#1f1f1f", fg="#FFFFFF", font=app.f_menu_btn, anchor="w").pack(anchor="w", padx=18, pady=(14, 4))
    tk.Label(steam_card, text="Use Steam to create and manage your online profile with your game identity.", bg="#1f1f1f", fg=app.SILVER, font=app.f_small, wraplength=520, justify="left", anchor="w").pack(anchor="w", padx=18, pady=(0, 12))
    tk.Button(
        steam_card,
        text="Connect via your Steam account",
        bg="black",
        fg=WHITE,
        font=app.f_menu_btn,
        relief="flat",
        cursor="hand2",
        padx=24,
        pady=12,
        command=lambda: _open_provider_auth(app, "steam"),
    ).pack(anchor="w", padx=18, pady=(0, 16))
    _add_hover(steam_card.winfo_children()[-1], app, active_bg="#202020")

    back_btn = tk.Button(
        f,
        text="← Back",
        bg=MENU_BTN_BG,
        fg=app.SILVER,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=8,
        command=lambda: build_profile_creation_screen(app),
    )
    back_btn.pack(pady=16)


def build_online_connection_screen(app, provider: str):
    """Show an in-app connection screen for the chosen online provider."""
    app._clear()
    app._current_screen = f"pre_menu_{provider}"
    f = app._container

    header = tk.Frame(f, bg=app.BG_DARK)
    header.pack(fill="x", padx=28, pady=(24, 16))
    provider_label = "Discord" if provider == "discord" else "Steam"
    tk.Label(
        header,
        text=f"Connect with {provider_label}",
        bg=app.BG_DARK,
        fg=app.GOLD,
        font=app.f_title,
    ).pack(anchor="w")
    tk.Label(
        header,
        text=f"Sub Ladder will open the official {provider_label} authorization screen in your browser.",
        bg=app.BG_DARK,
        fg=app.SILVER,
        font=app.f_small,
        wraplength=620,
    ).pack(anchor="w", pady=(4, 0))

    form = tk.Frame(f, bg=app.BG_DARK)
    form.pack(expand=True, fill="both", padx=40, pady=20)

    info_text = (
        f"Authorize the connection in the browser and return here once {provider_label} confirms access."
    )
    tk.Label(form, text=info_text, bg=app.BG_DARK, fg=WHITE, font=app.f_small, wraplength=520, justify="left").pack(anchor="w", pady=(0, 16))

    status_label = tk.Label(form, text="Waiting for authorization…", bg=app.BG_DARK, fg=app.SILVER, font=app.f_small)
    status_label.pack(anchor="w", pady=(0, 8))

    auth_started = {"value": False}

    def _start_auth():
        if auth_started["value"]:
            return
        auth_started["value"] = True
        try:
            auth_url = _build_provider_auth_url(app, provider)
            opened = webbrowser.open(auth_url)
            if opened:
                status_label.config(text=f"Opened the {provider_label} authorization page in your browser.")
            else:
                status_label.config(text=f"Could not open the {provider_label} authorization page automatically.")
                auth_started["value"] = False
        except Exception as exc:
            status_label.config(text=f"Could not start the {provider_label} authorization flow: {exc}")
            auth_started["value"] = False
            messagebox.showerror("", str(exc), parent=app)

    connect_btn = tk.Button(
        form,
        text=f"Open {provider_label} authorization",
        bg=app.GOLD,
        fg=app.BG_DARK,
        font=app.f_menu_btn,
        relief="flat",
        cursor="hand2",
        padx=16,
        pady=8,
        command=_start_auth,
    )
    connect_btn.pack(pady=(8, 12))
    _add_hover(connect_btn, app, active_bg=app.GOLD_DARK if hasattr(app, "GOLD_DARK") else app.GOLD)

    app.after(0, _start_auth)

    back_btn = tk.Button(
        f,
        text="← Back",
        bg=MENU_BTN_BG,
        fg=app.SILVER,
        font=app.f_small,
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=8,
        command=lambda: build_online_provider_screen(app),
    )
    back_btn.pack(pady=16)


def _open_provider_auth(app, provider: str):
    """Open the provider OAuth page directly from the pre-menu."""
    try:
        webbrowser.open(_build_provider_auth_url(app, provider))
    except Exception as exc:
        messagebox.showerror("", f"Could not open the {provider} authorization page: {exc}", parent=app)


def _select_profile(app, profile_name: str):
    """Select an existing profile and continue to the main menu."""
    app.data["active_profile"] = profile_name
    save_data(app.data, silent=True)
    app.after_idle(partial(_safe_show_menu, app))


def _create_offline_profile(app):
    """Create an offline profile via the existing profile action flow."""
    from .profile.actions.profiles import create_offline_profile

    active_profile_name = app.data.get("active_profile")
    profile_name = create_offline_profile(app, active_profile_name)
    if profile_name:
        app.after_idle(partial(_safe_show_menu, app))


def _create_online_profile(app, provider: str, profile_name: str, account_id: str):
    """Create an online profile using the chosen provider and immediately switch to the main menu."""
    profile_name = profile_name.strip()
    if not profile_name:
        messagebox.showerror("", "Profile name cannot be empty.", parent=app)
        return
    if profile_name in app.data.get("profiles", {}):
        messagebox.showerror("", "This profile name already exists.", parent=app)
        return

    profile_data = _build_online_profile_data(provider, profile_name, account_id)
    app.data.setdefault("profiles", {})[profile_name] = profile_data
    app.data["active_profile"] = profile_name
    save_data(app.data, silent=True)
    app.after_idle(partial(_safe_show_menu, app))


def _safe_show_menu(app):
    """Open the main menu and log any exception that would otherwise be hidden."""
    try:
        app.show_menu()
    except Exception as exc:
        log_ui_exception("pre_menu.show_menu", exc)
        messagebox.showerror(
            "",
            "An error occurred while opening the main menu. Check the UI error log in AppData\\Roaming\\SubLadder.",
            parent=app,
        )


def _build_provider_auth_url(app, provider: str) -> str:
    """Build the server-side auth URL for the chosen provider."""
    base_url = _select_reachable_base_url(app)

    endpoint = "/auth/discord/login" if provider == "discord" else "/auth/steam/login"
    return f"{base_url}{endpoint}"


def _select_reachable_base_url(app) -> str:
    """Pick the first reachable server base URL, preferring DNS over the legacy IP."""
    api_client = getattr(app, "api", None)
    candidates = list(getattr(api_client, "base_urls", []) or [])
    if not candidates and getattr(api_client, "base_url", None):
        candidates = [api_client.base_url]

    if not candidates:
        server_cfg = app.data.get("server", {})
        host = server_cfg.get("host", "dedicated-zap1280014-1.zap-srv.com")
        port = server_cfg.get("port", 8000)
        candidates = [f"http://{host}:{port}", f"http://45.156.84.114:{port}"]

    for base_url in candidates:
        if _is_base_url_reachable(base_url):
            return base_url

    return candidates[0]


def _is_base_url_reachable(base_url: str) -> bool:
    """Return True when the server host and port accept TCP connections."""
    parsed = urlparse(base_url)
    if not parsed.hostname:
        return False

    port = parsed.port or 80
    try:
        with socket.create_connection((parsed.hostname, port), timeout=1.0):
            return True
    except OSError:
        return False


def _build_online_profile_data(provider: str, profile_name: str, account_id: str) -> dict:
    """Create the profile payload for an online account."""
    return {
        "games_played": 0,
        "total_subs": 0,
        "best_game": 0,
        "correct_answers": 0,
        "achievements": [],
        "scores": [],
        "win_streak": 0,
        "total_xp": 0,
        "player_level": 1,
        "avatar": None,
        "profile_type": "online",
        "linked_accounts": [provider],
        "provider": provider,
        "provider_account": account_id,
        "profile_name": profile_name,
    }


def _add_hover(btn, app, active_bg=None):
    """Add a simple hover effect to buttons."""
    default_bg = btn.cget("bg")

    def _enter(_event=None):
        btn.config(bg=active_bg or BTN_HOVER)

    def _leave(_event=None):
        btn.config(bg=default_bg)

    btn.bind("<<Enter>>", _enter)
    btn.bind("<<Leave>>", _leave)
