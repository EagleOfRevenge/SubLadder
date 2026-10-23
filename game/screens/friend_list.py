"""
Friend list sidebar for the main menu.
"""

import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

from constants import BG_PANEL, BG_MID, BTN_DEFAULT, GOLD, MENU_BTN_ACT, SILVER, TEXT_DISABLED, WHITE
from ui_helpers import create_scrollable_frame
from utils import save_data

try:
    from ..auth.client import APIClient
except Exception:
    from ..auth.client import APIClient


STATUS_BUCKET_ORDER = ["online", "ingame", "away", "offline"]

STATUS_META = {
    "online": {"bucket": "online", "icon": "🟢", "label_en": "Online", "label_fr": "En ligne"},
    "lobby": {"bucket": "online", "icon": "🔵", "label_en": "Lobby", "label_fr": "Lobby"},
    "looking_for_match": {"bucket": "online", "icon": "🔎", "label_en": "Looking for match", "label_fr": "Recherche"},
    "match_found": {"bucket": "online", "icon": "⏳", "label_en": "Match found", "label_fr": "Match trouvé"},
    "loading_game": {"bucket": "online", "icon": "⬇️", "label_en": "Loading game", "label_fr": "Chargement"},
    "normal_game": {"bucket": "ingame", "icon": "🟠", "label_en": "Normal game", "label_fr": "Partie normale"},
    "ranked_game": {"bucket": "ingame", "icon": "🔴", "label_en": "Ranked game", "label_fr": "Partie classée"},
    "tutorial": {"bucket": "ingame", "icon": "📘", "label_en": "Tutorial", "label_fr": "Tutoriel"},
    "training": {"bucket": "ingame", "icon": "🧪", "label_en": "Training", "label_fr": "Entraînement"},
    "custom_game": {"bucket": "ingame", "icon": "🧩", "label_en": "Custom game", "label_fr": "Partie perso"},
    "away": {"bucket": "away", "icon": "🟡", "label_en": "Away", "label_fr": "Absent"},
    "offline": {"bucket": "offline", "icon": "⚫", "label_en": "Offline", "label_fr": "Hors ligne"},
}


def normalize_friend(friend: dict | None) -> dict:
    if not isinstance(friend, dict):
        friend = {}
    status = (friend.get("status") or friend.get("presence") or "offline").strip().lower()
    meta = STATUS_META.get(status, STATUS_META["offline"])
    display_name = friend.get("name") or friend.get("profile_name") or friend.get("game_name") or "Unknown"
    return {
        "id": friend.get("id") or display_name.lower(),
        "name": display_name,
        "avatar": friend.get("avatar"),
        "level": friend.get("level", friend.get("player_level", 0)),
        "rank": friend.get("rank", ""),
        "clan": friend.get("clan", ""),
        "tag": friend.get("tag", ""),
        "mode": friend.get("mode", ""),
        "message": friend.get("message", ""),
        "status": status,
        "bucket": meta["bucket"],
        "status_icon": meta["icon"],
        "status_label_en": meta["label_en"],
        "status_label_fr": meta["label_fr"],
        "notifications": friend.get("notifications", 0),
        "unread": bool(friend.get("unread", False)),
    }


def friend_bucket(friend: dict) -> str:
    return normalize_friend(friend)["bucket"]


def sort_friend_list(friends: list[dict]) -> list[dict]:
    normalized = [normalize_friend(friend) for friend in (friends or []) if isinstance(friend, dict)]
    order = {bucket: index for index, bucket in enumerate(STATUS_BUCKET_ORDER)}
    return sorted(
        normalized,
        key=lambda friend: (
            order.get(friend["bucket"], len(order)),
            friend["name"].casefold(),
        ),
    )


def filter_friend_list(friends: list[dict], query: str) -> list[dict]:
    needle = (query or "").strip().casefold()
    if not needle:
        return list(friends)

    filtered = []
    for friend in friends:
        haystack = " ".join(
            str(value)
            for value in [
                friend.get("name", ""),
                friend.get("clan", ""),
                friend.get("tag", ""),
                friend.get("rank", ""),
                friend.get("status", ""),
            ]
        ).casefold()
        if needle in haystack:
            filtered.append(friend)
    return filtered


class FriendListPanel:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent
        self.social = app.data.setdefault("social", {})
        self.options = app.data.setdefault("options", {})
        self.search_var = tk.StringVar(value="")
        self.friend_request_var = tk.StringVar(value="")
        self.section_state = self.social.setdefault("friendlist_sections", {bucket: True for bucket in STATUS_BUCKET_ORDER})
        self.collapsed = bool(self.options.get("friend_list_collapsed", False))
        self.hover_preview = bool(self.options.get("friend_list_hover_preview", True))
        self.target_width = 332
        self.top_margin = 96
        self.right_margin = 12
        self.bottom_margin = 56
        self._preview_after = None
        self._animation_after = None
        self._sync_after = None

        self.panel = tk.Frame(
            parent,
            bg=self._theme_color("BG_PANEL", BG_PANEL),
            highlightthickness=1,
            highlightbackground=self._theme_color("MENU_BTN_ACT", MENU_BTN_ACT),
        )
        self.panel.place_forget()

        self.open_button = tk.Button(
            parent,
            text="",
            bg=self._theme_color("BTN_DEFAULT", BTN_DEFAULT),
            fg=self._theme_color("GOLD", GOLD),
            font=app.f_small,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=8,
            command=self.expand,
        )
        self.open_button.bind("<Enter>", self._on_open_hover)
        self.open_button.bind("<Leave>", self._on_open_leave)

        self._place_widgets(initial=True)
        self._schedule_sync(initial_delay=1)

    def destroy(self):
        if self._sync_after is not None:
            self.parent.after_cancel(self._sync_after)
            self._sync_after = None
        for widget in (self.panel, self.open_button):
            if widget.winfo_exists():
                widget.destroy()

    def _language_code(self) -> str:
        return self.app._lang.get("code", "en") if hasattr(self.app, "_lang") else "en"

    def _theme_color(self, attr: str, fallback: str) -> str:
        return getattr(self.app, attr, fallback)

    def _friends(self) -> list[dict]:
        return sort_friend_list(self.social.get("friends", []))

    def _notification_count(self) -> int:
        notifications = self.social.get("notifications", [])
        unread = sum(1 for item in notifications if isinstance(item, dict) and not item.get("read", False))
        requests = len(self.social.get("friend_requests_in", []))
        return unread + requests

    def _panel_geometry(self) -> tuple[int, int, int, int]:
        width = self.target_width
        height = max(420, (self.parent.winfo_height() or 720) - self.top_margin - self.bottom_margin)
        x = max(10, (self.parent.winfo_width() or 900) - width - self.right_margin)
        y = self.top_margin
        return x, y, width, height

    def _button_geometry(self) -> tuple[int, int]:
        width = self.parent.winfo_width() or 900
        height = self.parent.winfo_height() or 720
        return width - 82, height - 62

    def _place_widgets(self, initial: bool = False):
        if self.collapsed:
            self._show_collapsed_button(initial=initial)
            return
        self._show_panel(initial=initial)

    def _show_panel(self, initial: bool = False):
        self._cancel_preview_timer()
        self.open_button.place_forget()
        x, y, width, height = self._panel_geometry()
        if initial:
            self.panel.place(x=x, y=y, width=width, height=height)
            self.render()
            return
        self.panel.place(x=x, y=y, width=0, height=height)
        self.render()
        self._animate_width(0, width)

    def _show_collapsed_button(self, initial: bool = False):
        self.panel.place_forget()
        x, y = self._button_geometry()
        badge = self._notification_count()
        text = f"👥 {badge}" if badge else "👥"
        self.open_button.config(
            text=text,
            fg=self._theme_color("GOLD", GOLD) if badge else self._theme_color("WHITE", WHITE),
        )
        self.open_button.place(x=x, y=y)
        if initial:
            return

    def _animate_width(self, start_width: int, end_width: int):
        if self._animation_after is not None:
            self.parent.after_cancel(self._animation_after)
            self._animation_after = None

        step = 28 if end_width >= start_width else -28
        current = start_width
        x, y, _, height = self._panel_geometry()

        def tick():
            nonlocal current
            if not self.panel.winfo_exists():
                return
            current += step
            finished = (step > 0 and current >= end_width) or (step < 0 and current <= end_width)
            if finished:
                current = end_width
            self.panel.place_configure(x=x, y=y, width=max(0, current), height=height)
            if not finished:
                self._animation_after = self.parent.after(12, tick)
            else:
                self._animation_after = None

        tick()

    def _cancel_preview_timer(self):
        if self._preview_after is not None:
            self.parent.after_cancel(self._preview_after)
            self._preview_after = None

    def _mark_notifications_read(self):
        changed = False
        for item in self.social.get("notifications", []):
            if isinstance(item, dict) and not item.get("read", False):
                item["read"] = True
                changed = True
        if changed:
            save_data(self.app.data, silent=True)

    def collapse(self):
        if self.collapsed:
            return
        self.collapsed = True
        self.options["friend_list_collapsed"] = True
        save_data(self.app.data, silent=True)
        current = self.panel.winfo_width() if self.panel.winfo_exists() else self.target_width
        self._animate_width(current, 0)
        self.parent.after(180, self._show_collapsed_button)

    def expand(self):
        if not self.collapsed:
            return
        self.collapsed = False
        self.options["friend_list_collapsed"] = False
        save_data(self.app.data, silent=True)
        self._mark_notifications_read()
        self._show_panel(initial=False)

    def toggle_section(self, bucket: str):
        self.section_state[bucket] = not self.section_state.get(bucket, True)
        save_data(self.app.data, silent=True)
        self.render()

    def refresh(self):
        if self.collapsed:
            self._show_collapsed_button()
        else:
            self.render()
        self._schedule_sync(initial_delay=30)

    def render(self):
        if not self.panel.winfo_exists():
            return
        for widget in self.panel.winfo_children():
            widget.destroy()

        self.panel.update_idletasks()
        x, y, width, height = self._panel_geometry()
        self.panel.place_configure(x=x, y=y, width=width, height=height)

        header = tk.Frame(self.panel, bg=self._theme_color("BG_PANEL", BG_PANEL))
        header.pack(fill="x", padx=12, pady=(10, 6))

        tk.Label(
            header,
            text="Friends" if self._language_code() == "en" else "Amis",
            bg=self._theme_color("BG_PANEL", BG_PANEL),
            fg=self._theme_color("GOLD", GOLD),
            font=self.app.f_menu_btn,
        ).pack(side="left")

        tk.Label(
            header,
            text=str(len(self._friends())),
            bg=self._theme_color("BG_PANEL", BG_PANEL),
            fg=self._theme_color("SILVER", SILVER),
            font=self.app.f_small,
        ).pack(side="left", padx=(8, 0))

        collapse_btn = tk.Button(
            header,
            text="−",
            bg=self._theme_color("BTN_DEFAULT", BTN_DEFAULT),
            fg=self._theme_color("WHITE", WHITE),
            font=self.app.f_menu_btn,
            relief="flat",
            cursor="hand2",
            width=2,
            command=self.collapse,
        )
        collapse_btn.pack(side="right")

        search_frame = tk.Frame(self.panel, bg=self._theme_color("BG_PANEL", BG_PANEL))
        search_frame.pack(fill="x", padx=12, pady=(0, 8))
        tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=self._theme_color("BG_MID", BG_MID),
            fg=self._theme_color("WHITE", WHITE),
            insertbackground=self._theme_color("WHITE", WHITE),
            relief="flat",
            font=self.app.f_small,
        ).pack(fill="x", ipady=5)

        request_frame = tk.Frame(self.panel, bg=self._theme_color("BG_PANEL", BG_PANEL))
        request_frame.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(
            request_frame,
            text="Add by name" if self._language_code() == "en" else "Ajouter par pseudo",
            bg=self._theme_color("BG_PANEL", BG_PANEL),
            fg=self._theme_color("GOLD", GOLD),
            font=self.app.f_small,
            anchor="w",
        ).pack(fill="x")

        request_row = tk.Frame(request_frame, bg=self._theme_color("BG_PANEL", BG_PANEL))
        request_row.pack(fill="x", pady=(4, 0))
        tk.Entry(
            request_row,
            textvariable=self.friend_request_var,
            bg=self._theme_color("BG_MID", BG_MID),
            fg=self._theme_color("WHITE", WHITE),
            insertbackground=self._theme_color("WHITE", WHITE),
            relief="flat",
            font=self.app.f_small,
        ).pack(side="left", fill="x", expand=True, ipady=5)
        tk.Button(
            request_row,
            text="Send",
            bg=self._theme_color("MENU_BTN_ACT", MENU_BTN_ACT),
            fg=self._theme_color("BG_PANEL", BG_PANEL),
            font=self.app.f_small,
            relief="flat",
            cursor="hand2",
            padx=10,
            command=self._send_friend_request,
        ).pack(side="left", padx=(6, 0))

        incoming_requests = self._incoming_requests()
        self._build_incoming_requests(request_frame, incoming_requests)

        summary = tk.Frame(self.panel, bg=self._theme_color("BG_PANEL", BG_PANEL))
        summary.pack(fill="x", padx=12, pady=(0, 8))
        counts = self._category_counts(self._friends())
        for bucket in STATUS_BUCKET_ORDER:
            tk.Label(
                summary,
                text=f"{self._bucket_label(bucket)} ({counts[bucket]})",
                bg=self._theme_color("BG_PANEL", BG_PANEL),
                fg=self._theme_color("SILVER", SILVER),
                font=self.app.f_small,
                anchor="w",
            ).pack(fill="x")

        canvas, content = create_scrollable_frame(self.panel, self._theme_color("BG_PANEL", BG_PANEL))
        canvas.pack(fill="both", expand=True, padx=0, pady=(0, 8))

        friends = filter_friend_list(self._friends(), self.search_var.get())
        grouped = self._group_friends(friends)

        for bucket in STATUS_BUCKET_ORDER:
            self._build_section(content, bucket, grouped[bucket])

        footer = tk.Frame(self.panel, bg=self._theme_color("BG_PANEL", BG_PANEL))
        footer.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(
            footer,
            text=self._footer_text(),
            bg=self._theme_color("BG_PANEL", BG_PANEL),
            fg=self._theme_color("TEXT_DISABLED", TEXT_DISABLED),
            font=self.app.f_small,
            wraplength=self.target_width - 28,
            justify="left",
        ).pack(anchor="w")

    def _footer_text(self) -> str:
        lang = self._language_code()
        if lang == "fr":
            return "Clic droit pour voir le profil, inviter, bloquer ou signaler."
        return "Right-click to view a profile, invite, block, or report."

    def _incoming_requests(self) -> list[dict]:
        return [item for item in self.social.get("friend_requests_in", []) if isinstance(item, dict)]

    def _category_counts(self, friends: list[dict]) -> dict[str, int]:
        counts = {bucket: 0 for bucket in STATUS_BUCKET_ORDER}
        for friend in friends:
            counts[friend["bucket"]] = counts.get(friend["bucket"], 0) + 1
        return counts

    def _group_friends(self, friends: list[dict]) -> dict[str, list[dict]]:
        grouped = {bucket: [] for bucket in STATUS_BUCKET_ORDER}
        for friend in friends:
            grouped[friend["bucket"]].append(friend)
        for bucket in grouped:
            grouped[bucket] = sorted(grouped[bucket], key=lambda item: item["name"].casefold())
        return grouped

    def _bucket_label(self, bucket: str) -> str:
        labels = {
            "online": ("Online", "En ligne"),
            "ingame": ("In game", "En partie"),
            "away": ("Away", "Absent"),
            "offline": ("Offline", "Hors ligne"),
        }
        en, fr = labels[bucket]
        return en if self._language_code() == "en" else fr

    def _status_label(self, friend: dict) -> str:
        lang = self._language_code()
        return friend[f"status_label_{lang}"]

    def _build_section(self, parent, bucket: str, friends: list[dict]):
        section = tk.Frame(parent, bg=self._theme_color("BG_PANEL", BG_PANEL))
        section.pack(fill="x", padx=12, pady=(0, 8))

        header = tk.Button(
            section,
            text=f"{self._bucket_label(bucket)} ({len(friends)})",
            bg=self._theme_color("BTN_DEFAULT", BTN_DEFAULT),
            fg=self._theme_color("GOLD", GOLD) if friends else self._theme_color("SILVER", SILVER),
            font=self.app.f_small,
            relief="flat",
            cursor="hand2",
            anchor="w",
            command=lambda b=bucket: self.toggle_section(b),
        )
        header.pack(fill="x", ipady=5)

        if not self.section_state.get(bucket, True):
            return

        body = tk.Frame(section, bg=self._theme_color("BG_PANEL", BG_PANEL))
        body.pack(fill="x", pady=(4, 0))

        if not friends:
            tk.Label(
                body,
                text="—",
                bg=self._theme_color("BG_PANEL", BG_PANEL),
                fg=self._theme_color("TEXT_DISABLED", TEXT_DISABLED),
                font=self.app.f_small,
            ).pack(anchor="w", padx=6, pady=2)
            return

        for index, friend in enumerate(friends):
            self._build_friend_row(body, friend, index)

    def _build_friend_row(self, parent, friend: dict, index: int):
        row_bg = self._theme_color("BG_MID", BG_MID) if index % 2 == 0 else self._theme_color("BG_PANEL", BG_PANEL)
        row = tk.Frame(parent, bg=row_bg, highlightthickness=1, highlightbackground=row_bg)
        row.pack(fill="x", padx=2, pady=2)

        avatar = tk.Frame(row, bg=row_bg)
        avatar.pack(side="left", padx=(6, 8), pady=6)
        avatar_icon = tk.Label(
            avatar,
            text=friend["status_icon"],
            bg=row_bg,
            fg=WHITE,
            font=self.app.f_label,
            width=2,
        )
        avatar_icon.pack()

        body = tk.Frame(row, bg=row_bg)
        body.pack(side="left", fill="x", expand=True, pady=6)

        top_line = tk.Frame(body, bg=row_bg)
        top_line.pack(fill="x")
        tk.Label(
            top_line,
            text=friend["name"],
            bg=row_bg,
            fg=WHITE,
            font=self.app.f_small,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        if friend.get("level"):
            tk.Label(
                top_line,
                text=f"Lv {friend['level']}",
                bg=row_bg,
                fg=self._theme_color("GOLD", GOLD),
                font=self.app.f_small,
            ).pack(side="right", padx=(4, 0))

        bottom_bits = [self._status_label(friend)]
        if friend.get("mode"):
            bottom_bits.append(friend["mode"])
        if friend.get("clan"):
            bottom_bits.append(f"[{friend['clan']}]")
        if friend.get("tag"):
            bottom_bits.append(f"#{friend['tag']}")

        tk.Label(
            body,
            text="  ·  ".join(bottom_bits),
            bg=row_bg,
            fg=SILVER,
            font=self.app.f_small,
            anchor="w",
            justify="left",
        ).pack(fill="x")

        if friend.get("message"):
            tk.Label(
                body,
                text=friend["message"],
                bg=row_bg,
                fg=TEXT_DISABLED,
                font=self.app.f_small,
                anchor="w",
                wraplength=self.target_width - 94,
                justify="left",
            ).pack(fill="x")

        row.bind("<Button-3>", lambda event, current=friend: self._open_context_menu(event, current))
        for widget in row.winfo_children():
            widget.bind("<Button-3>", lambda event, current=friend: self._open_context_menu(event, current))

    def _get_token(self) -> str | None:
        auth = self.app.data.get("auth", {})
        tokens = auth.get("tokens", {})
        active = self.app.data.get("active_profile")
        return tokens.get(active)

    def _schedule_sync(self, initial_delay: int = 30):
        if self._sync_after is not None:
            self.parent.after_cancel(self._sync_after)
            self._sync_after = None

        def tick():
            self._sync_after = None
            self._sync_from_server()

        delay_ms = max(1, int(initial_delay)) * 1000
        self._sync_after = self.parent.after(delay_ms, tick)

    def _sync_from_server(self):
        token = self._get_token()
        if not token:
            self._schedule_sync()
            return

        def worker():
            try:
                api = APIClient(
                    host=self.app.data.get("server", {}).get("host", "45.156.84.114"),
                    port=self.app.data.get("server", {}).get("port", 8000),
                )
                snapshot = api.get_social_snapshot(token)
                if not isinstance(snapshot, dict) or snapshot.get("error"):
                    return
                self.parent.after(0, lambda: self._apply_snapshot(snapshot))
            finally:
                self.parent.after(0, self._schedule_sync)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_snapshot(self, snapshot: dict):
        social = self.app.data.setdefault("social", {})
        profile = snapshot.get("profile", {})
        if profile:
            social["profile"] = profile
        social["friends"] = snapshot.get("friends", social.get("friends", []))
        social["friend_requests_in"] = snapshot.get("incoming_requests", social.get("friend_requests_in", []))
        social["friend_requests_out"] = snapshot.get("outgoing_requests", social.get("friend_requests_out", []))
        social["blocked_players"] = snapshot.get("blocked_players", social.get("blocked_players", []))
        save_data(self.app.data, silent=True)
        self.refresh()

    def _open_context_menu(self, event, friend: dict):
        menu = tk.Menu(self.panel, tearoff=0)
        menu.add_command(label="Voir le profil" if self._language_code() == "fr" else "View profile", command=lambda: self._view_profile(friend))
        menu.add_command(label="Inviter" if self._language_code() == "fr" else "Invite", command=lambda: self._invite_friend(friend))
        menu.add_command(label="Supprimer" if self._language_code() == "fr" else "Remove friend", command=lambda: self._remove_friend(friend))
        menu.add_command(label="Bloquer" if self._language_code() == "fr" else "Block", command=lambda: self._block_player(friend))
        menu.add_command(label="Signaler" if self._language_code() == "fr" else "Report", command=lambda: self._report_player(friend))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _view_profile(self, friend: dict):
        self.app.show_profile(friend["name"])

    def _invite_friend(self, friend: dict):
        messagebox.showinfo("", f"Invite sent to {friend['name']}", parent=self.parent)

    def _send_friend_request(self):
        token = self._get_token()
        target_name = self.friend_request_var.get().strip()
        if not token:
            messagebox.showwarning("", "You need to be online to send a friend request.", parent=self.parent)
            return
        if not target_name:
            return

        self.friend_request_var.set("")

        def worker():
            try:
                api = APIClient(
                    host=self.app.data.get("server", {}).get("host", "45.156.84.114"),
                    port=self.app.data.get("server", {}).get("port", 8000),
                )
                result = api.send_friend_request(token, target_name)
                if isinstance(result, dict) and result.get("error"):
                    raise RuntimeError(result["error"])

                status = result.get("status")
                if status == "pending":
                    message = "demande envoyé !"
                elif status == "accepted":
                    message = "Friend request accepted automatically." if self._language_code() == "en" else "Demande d'ami acceptée automatiquement."
                else:
                    message = "Request sent."
                self.parent.after(0, lambda: messagebox.showinfo("", message, parent=self.parent))
                self.parent.after(0, self._sync_from_server)
            except Exception as exc:
                detail = str(exc)
                if "Ce nom n'est pas utilisé par un joueur" in detail:
                    detail = "Ce nom n'est pas utilisé par un joueur !"
                self.parent.after(0, lambda: messagebox.showwarning("", detail, parent=self.parent))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_request_action(self, request: dict, action: str):
        token = self._get_token()
        requestor_name = request.get("name") or request.get("profile_name") or request.get("requestor_profile_name")
        if not token or not requestor_name:
            return

        def worker():
            try:
                api = APIClient(
                    host=self.app.data.get("server", {}).get("host", "45.156.84.114"),
                    port=self.app.data.get("server", {}).get("port", 8000),
                )
                if action == "accept":
                    result = api.accept_friend_request(token, requestor_name)
                else:
                    result = api.decline_friend_request(token, requestor_name)
                if isinstance(result, dict) and result.get("error"):
                    raise RuntimeError(result["error"])
                self.parent.after(0, self._sync_from_server)
            except Exception as exc:
                self.parent.after(0, lambda: messagebox.showwarning("", str(exc), parent=self.parent))

        threading.Thread(target=worker, daemon=True).start()

    def _build_incoming_requests(self, parent, requests: list[dict]):
        container = tk.Frame(parent, bg=self._theme_color("BG_PANEL", BG_PANEL))
        container.pack(fill="x", pady=(6, 6))

        title = tk.Label(
            container,
            text=("Incoming requests" if self._language_code() == "en" else "Demandes reçues"),
            bg=self._theme_color("BG_PANEL", BG_PANEL),
            fg=self._theme_color("SILVER", SILVER),
            font=self.app.f_small,
            anchor="w",
        )
        title.pack(fill="x")

        if not requests:
            tk.Label(
                container,
                text=("No pending friend requests" if self._language_code() == "en" else "Aucune demande en attente"),
                bg=self._theme_color("BG_PANEL", BG_PANEL),
                fg=self._theme_color("TEXT_DISABLED", TEXT_DISABLED),
                font=self.app.f_small,
                anchor="w",
            ).pack(fill="x", pady=(2, 0))
            return

        for index, request in enumerate(requests):
            row_bg = self._theme_color("BG_MID", BG_MID) if index % 2 == 0 else self._theme_color("BG_PANEL", BG_PANEL)
            row = tk.Frame(container, bg=row_bg)
            row.pack(fill="x", pady=2)

            name = request.get("name") or request.get("profile_name") or request.get("requestor_profile_name") or "?"
            tk.Label(
                row,
                text=name,
                bg=row_bg,
                fg=self._theme_color("WHITE", WHITE),
                font=self.app.f_small,
                anchor="w",
            ).pack(side="left", padx=8, pady=5, fill="x", expand=True)

            tk.Button(
                row,
                text="Accept" if self._language_code() == "en" else "Accepter",
                bg=self._theme_color("MENU_BTN_ACT", MENU_BTN_ACT),
                fg=self._theme_color("BG_PANEL", BG_PANEL),
                font=self.app.f_small,
                relief="flat",
                cursor="hand2",
                padx=8,
                command=lambda current=request: self._handle_request_action(current, "accept"),
            ).pack(side="right", padx=(4, 8))

            tk.Button(
                row,
                text="Decline" if self._language_code() == "en" else "Refuser",
                bg=self._theme_color("BTN_DEFAULT", BTN_DEFAULT),
                fg=self._theme_color("WHITE", WHITE),
                font=self.app.f_small,
                relief="flat",
                cursor="hand2",
                padx=8,
                command=lambda current=request: self._handle_request_action(current, "decline"),
            ).pack(side="right")

    def _remove_friend(self, friend: dict):
        removed = self._remove_from_list("friends", friend["id"], friend["name"])
        if removed:
            save_data(self.app.data, silent=True)
            self.render()

    def _block_player(self, friend: dict):
        blocked = self.social.setdefault("blocked_players", [])
        if not any(item.get("name") == friend["name"] or item.get("id") == friend["id"] for item in blocked):
            blocked.append({"id": friend["id"], "name": friend["name"], "created_at": None})
        self._remove_from_list("friends", friend["id"], friend["name"])
        save_data(self.app.data, silent=True)
        self.render()

    def _report_player(self, friend: dict):
        reason = simpledialog.askstring("Report", "Reason for report:", parent=self.parent)
        if not reason:
            return
        description = simpledialog.askstring("Report", "Description:", parent=self.parent)
        reports = self.social.setdefault("reports", [])
        reports.append({"reported": friend["name"], "reason": reason, "description": description or "", "created_at": None})
        save_data(self.app.data, silent=True)
        messagebox.showinfo("", f"Report sent for {friend['name']}", parent=self.parent)

    def _remove_from_list(self, key: str, friend_id, friend_name: str) -> bool:
        entries = self.social.setdefault(key, [])
        before = len(entries)
        self.social[key] = [
            item
            for item in entries
            if not (
                item.get("id") == friend_id
                or item.get("name") == friend_name
                or item.get("profile_name") == friend_name
            )
        ]
        return len(self.social[key]) != before

    def _on_open_hover(self, event=None):
        if not self.hover_preview or not self.collapsed:
            return
        self._cancel_preview_timer()
        self._preview_after = self.parent.after(180, self.expand)

    def _on_open_leave(self, event=None):
        if not self.hover_preview or not self.collapsed:
            return
        self._cancel_preview_timer()
        self._preview_after = self.parent.after(280, self.collapse)


def build(app, parent):
    panel = FriendListPanel(app, parent)
    app._friend_list_panel = panel
    return panel


__all__ = ["build", "FriendListPanel", "sort_friend_list", "filter_friend_list", "friend_bucket"]
