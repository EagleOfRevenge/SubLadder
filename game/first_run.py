"""
first_run.py — Sub Ladder
Shows the first-run wizard when no data.json exists yet.
Must be called BEFORE creating the main App(tk.Tk) instance,
because tkinter only supports one Tk() root per process.
Returns (language_name, profile_name, profile_type).
"""

import os
import secrets
import traceback
import webbrowser
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

from .constants import BTN_DEFAULT
from .auth.client import APIClient

# ── Colors ──────────────────────────────────────────────────────────
BG_DARK  = "#0a0e1a"
BG_MID   = "#10192e"
GOLD     = "#f5c842"
SILVER   = "#aab4c8"
WHITE    = "#e8edf5"

_WIZARD_UI = {
    "English": {
        "welcome":       "Welcome to Sub Ladder!",
        "choose_lang":   "Choose your language:",
        "next":          "Next  ▶",
        "profile_type":  "Choose your profile type",
        "offline_title": "Offline Profile",
        "offline_desc":  "Play solo on your computer. All data saved locally.",
        "online_title":  "Online Profile",
        "online_desc":   "Link to server (email/Discord/Steam). Play with others.",
        "create_profile":"Create your profile",
        "enter_name":    "Enter your name or username:",
        "name_hint":     "(This will be your streamer / player profile)",
        "start":         "▶  Start playing!",
        "name_empty":    "Please enter a name.",
    },
    "Français": {
        "welcome":       "Bienvenue dans Sub Ladder !",
        "choose_lang":   "Choisissez votre langue :",
        "next":          "Suivant  ▶",
        "profile_type":  "Choisissez votre type de profil",
        "offline_title": "Profil Hors-ligne",
        "offline_desc":  "Jouer en solo sur votre ordinateur. Données enregistrées localement.",
        "online_title":  "Profil En ligne",
        "online_desc":   "Lier au serveur (mail/Discord/Steam). Jouer avec les autres.",
        "create_profile":"Créez votre profil",
        "enter_name":    "Entrez votre nom ou pseudo :",
        "name_hint":     "(Ce sera votre profil de streamer / joueur)",
        "start":         "▶  Commencer à jouer !",
        "name_empty":    "Veuillez entrer un nom.",
    },
}


def run_wizard(available_languages: list, flag_dir: str = None) -> tuple:
    """
    Standalone Tk wizard — must be called before App() is instantiated.
    Returns (language_name, profile_name, profile_type).
    profile_type is either "offline" or "online".
    """
    result = {"lang": available_languages[0], "profile": "", "profile_type": "offline"}

    root = tk.Tk()
    root.title("Sub Ladder — Setup")
    root.configure(bg=BG_DARK)
    root.resizable(False, False)
    root.update_idletasks()
    w, h = 500, 440
    x = (root.winfo_screenwidth()  - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")
    root.protocol("WM_DELETE_WINDOW", lambda: None)  # prevent accidental close

    def _wizard_callback_exception(exc, val, tb):
        log_dir = os.path.join(os.getenv("LOCALAPPDATA", ROOT_DIR), "SubLadder", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "wizard_error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 72 + "\n")
            f.write("Wizard callback failure\n")
            f.write("".join(traceback.format_exception(exc, val, tb)))
        try:
            messagebox.showerror(
                "Sub Ladder — Online Profile Error",
                f"An error occurred during the setup wizard.\n\nDetails were written to:\n{log_path}",
                parent=root,
            )
        except Exception:
            pass

    root.report_callback_exception = _wizard_callback_exception

    # Fonts
    fam  = next((f for f in tkfont.families()
                 if f in ["Georgia", "Palatino"]), "TkDefaultFont")
    body = next((f for f in tkfont.families()
                 if f in ["Helvetica", "Arial"]), "TkDefaultFont")
    f_title = tkfont.Font(family=fam,  size=16, weight="bold")
    f_body  = tkfont.Font(family=body, size=12)
    f_small = tkfont.Font(family=body, size=10)
    f_btn   = tkfont.Font(family=body, size=12, weight="bold")

    container = tk.Frame(root, bg=BG_DARK)
    container.pack(fill="both", expand=True)

    # Preload flag images (optional — needs PIL)
    _flag_imgs = {}
    if flag_dir and os.path.isdir(flag_dir):
        try:
            from PIL import Image, ImageTk
            for lang in available_languages:
                code = lang[:2].lower()
                path = os.path.join(flag_dir, f"{code}.png")
                if os.path.exists(path):
                    img = Image.open(path).resize((32, 20))
                    _flag_imgs[lang] = ImageTk.PhotoImage(img)
        except Exception:
            pass

    # ── Step 1: language ──────────────────────────────────────────

    def show_step1():
        for widget in container.winfo_children():
            widget.destroy()
        lang_ui = _WIZARD_UI.get(result["lang"], _WIZARD_UI["English"])

        tk.Label(container, text="✦  Sub Ladder  ✦",
                 bg=BG_DARK, fg=GOLD, font=f_title).pack(pady=(32, 4))
        tk.Label(container, text=lang_ui["welcome"],
                 bg=BG_DARK, fg=WHITE, font=f_body).pack(pady=(0, 20))
        tk.Label(container, text=lang_ui["choose_lang"],
                 bg=BG_DARK, fg=SILVER, font=f_small).pack()

        lang_var = tk.StringVar(master=root, value=result["lang"])
        lf = tk.Frame(container, bg=BG_DARK)
        lf.pack(pady=12)

        for lang in available_languages:
            row = tk.Frame(lf, bg=BG_DARK)
            row.pack(anchor="w", pady=3, padx=20)
            if lang in _flag_imgs:
                lbl = tk.Label(row, image=_flag_imgs[lang], bg=BG_DARK)
                lbl.pack(side="left", padx=(0, 8))
                lbl._img = _flag_imgs[lang]  # keep reference
            tk.Radiobutton(
                row, text=lang, variable=lang_var, value=lang,
                bg=BG_DARK, fg=WHITE, selectcolor=BG_MID,
                activebackground=BG_DARK, activeforeground=GOLD,
                font=f_body
            ).pack(side="left")

        def go_step2():
            result["lang"] = lang_var.get()
            show_step2()

        tk.Button(container, text=lang_ui["next"],
                  bg=GOLD, fg=BG_DARK, font=f_btn,
                  relief="flat", cursor="hand2", padx=20, pady=8,
                  command=go_step2).pack(pady=24)

    # ── Step 2: profile type (offline vs online) ──────────────────

    def show_step2():
        for widget in container.winfo_children():
            widget.destroy()
        lang_ui = _WIZARD_UI.get(result["lang"], _WIZARD_UI["English"])

        tk.Label(container, text=lang_ui["profile_type"],
                 bg=BG_DARK, fg=GOLD, font=f_title).pack(pady=(40, 30))

        def _select_offline():
            result["profile_type"] = "offline"
            show_step3()

        def _select_online():
            # For online, we need to show login/signup UI.
            result["profile_type"] = "online"

            # screens.auth expects a full App-like object.
            # The wizard root can host the required attributes directly.
            root.api = APIClient()
            root._lang = {"code": "fr" if result["lang"] == "Français" else "en"}
            root.BG_DARK = BG_DARK
            root.BG_MID = BG_MID
            root.WHITE = WHITE
            root.GOLD = GOLD
            root.SILVER = SILVER
            root.BTN_DEFAULT = BTN_DEFAULT
            root.f_title = f_title
            root.f_body = f_body
            root.f_small = f_small
            root.f_menu_btn = f_btn

            def _finalize_online(provider: str, account_id: str, display_name: str, email: str = "", token: str = "", user_id: int | None = None):
                result["online_provider"] = provider
                result["online_provider_id"] = account_id
                result["online_user_name"] = display_name or account_id
                if email:
                    result["online_email"] = email
                if token:
                    result["online_token"] = token
                if user_id is not None:
                    result["online_user_id"] = user_id
                show_step3()

            provider_root = tk.Toplevel(root)
            provider_root.title("Sub Ladder")
            provider_root.configure(bg=BG_DARK)
            provider_root.resizable(False, False)
            provider_root.geometry("420x260")
            provider_root.update_idletasks()
            pw, ph = provider_root.winfo_width(), provider_root.winfo_height()
            px = (provider_root.winfo_screenwidth() - pw) // 2
            py = (provider_root.winfo_screenheight() - ph) // 2
            provider_root.geometry(f"{pw}x{ph}+{px}+{py}")

            tk.Label(provider_root, text="Online Account",
                     bg=BG_DARK, fg=GOLD, font=f_title).pack(pady=(18, 8))
            tk.Label(provider_root, text="Choose how you want to create your online profile.",
                     bg=BG_DARK, fg=SILVER, font=f_body).pack(pady=(0, 16))

            status_var = tk.StringVar(value="")
            tk.Label(provider_root, textvariable=status_var,
                     bg=BG_DARK, fg=SILVER, font=f_small,
                     wraplength=360, justify="center").pack(pady=(0, 6))

            oauth_session = {"state": None, "provider": None}

            def _poll_provider_oauth():
                state = oauth_session.get("state")
                provider = oauth_session.get("provider")
                if not state or not provider:
                    return

                try:
                    result = root.api.poll_oauth_result(state)
                except Exception as exc:
                    status_var.set(f"Could not reach the OAuth result endpoint: {exc}")
                    return

                if result.get("status") != "ready":
                    provider_root.after(1200, _poll_provider_oauth)
                    return

                payload = result.get("result", {})
                user = payload.get("user", {})
                token = payload.get("access_token", "")
                account_id = str(user.get("discord_id") or user.get("steam_id") or user.get("id") or state)
                display_name = user.get("profile_name") or user.get("discord_username") or user.get("steam_id") or provider
                email = user.get("email", "")
                provider_root.destroy()
                _finalize_online(provider, account_id, display_name, email=email, token=token, user_id=user.get("id"))

            def _start_provider_oauth(provider: str):
                provider_label = "Discord" if provider == "discord" else "Steam"
                state = secrets.token_urlsafe(24)
                oauth_session["state"] = state
                oauth_session["provider"] = provider
                status_var.set(f"Opening {provider_label} authorization in your browser…")
                auth_url = f"{root.api.base_urls[0]}/auth/{provider}/login?state={state}"
                try:
                    webbrowser.open(auth_url)
                except Exception as exc:
                    status_var.set(f"Could not open the {provider_label} authorization page: {exc}")
                    return

                provider_root.after(1200, _poll_provider_oauth)

            def _cancel():
                result["profile_type"] = "offline"
                provider_root.destroy()
                show_step2()

            def _open_email_flow():
                try:
                    from .screens.auth import show_login_dialog, show_signup_dialog
                except Exception as exc:
                    status_var.set(f"Email flow could not be loaded: {exc}")
                    return

                email_root = tk.Toplevel(root)
                email_root.title("Sub Ladder")
                email_root.configure(bg=BG_DARK)
                email_root.resizable(False, False)
                email_root.geometry("360x210")
                email_root.update_idletasks()
                ew, eh = email_root.winfo_width(), email_root.winfo_height()
                ex = (email_root.winfo_screenwidth() - ew) // 2
                ey = (email_root.winfo_screenheight() - eh) // 2
                email_root.geometry(f"{ew}x{eh}+{ex}+{ey}")

                tk.Label(email_root, text="Email Account",
                         bg=BG_DARK, fg=GOLD, font=f_title).pack(pady=(18, 10))
                tk.Label(email_root, text="Do you already have an account?",
                         bg=BG_DARK, fg=SILVER, font=f_body).pack(pady=(0, 14))

                def _on_login_success(email, token, user_data):
                    provider_root.destroy()
                    email_root.destroy()
                    _finalize_online("email", email, user_data.get("game_name", email.split("@")[0]), email=email, token=token, user_id=user_data.get("id"))

                def _on_signup_success(email, token, user_data):
                    provider_root.destroy()
                    email_root.destroy()
                    _finalize_online("email", email, user_data.get("game_name", email.split("@")[0]), email=email, token=token, user_id=user_data.get("id"))

                def _login():
                    email_root.destroy()
                    show_login_dialog(root, _on_login_success, lambda: show_step2())

                def _signup():
                    email_root.destroy()
                    show_signup_dialog(root, _on_signup_success, lambda: show_step2())

                email_btn_frame = tk.Frame(email_root, bg=BG_DARK)
                email_btn_frame.pack(pady=8)

                tk.Button(email_btn_frame, text="Login",
                          bg="#3a5b6b", fg="white", font=f_btn,
                          relief="flat", cursor="hand2", padx=16, pady=8,
                          command=_login).pack(side="left", padx=6)

                tk.Button(email_btn_frame, text="Sign Up",
                          bg=GOLD, fg=BG_DARK, font=f_btn,
                          relief="flat", cursor="hand2", padx=16, pady=8,
                          command=_signup).pack(side="left", padx=6)

                tk.Button(email_root, text="Cancel",
                          bg=BG_MID, fg=SILVER, font=f_btn,
                          relief="flat", cursor="hand2", padx=16, pady=8,
                          command=lambda: [email_root.destroy(), show_step2()]).pack(pady=(8, 0))

            btn_frame = tk.Frame(provider_root, bg=BG_DARK)
            btn_frame.pack(pady=6)

            tk.Button(btn_frame, text="Email",
                      bg="#3a5b6b", fg="white", font=f_btn,
                      relief="flat", cursor="hand2", padx=16, pady=8,
                      command=_open_email_flow).pack(side="left", padx=6)

            tk.Button(btn_frame, text="Discord",
                      bg="#5865F2", fg="white", font=f_btn,
                      relief="flat", cursor="hand2", padx=16, pady=8,
                      command=lambda: _start_provider_oauth("discord")).pack(side="left", padx=6)

            tk.Button(btn_frame, text="Steam",
                      bg="black", fg="white", font=f_btn,
                      relief="flat", cursor="hand2", padx=16, pady=8,
                      command=lambda: _start_provider_oauth("steam")).pack(side="left", padx=6)

            tk.Button(provider_root, text="Cancel",
                      bg=BG_MID, fg=SILVER, font=f_btn,
                      relief="flat", cursor="hand2", padx=16, pady=8,
                      command=_cancel).pack(pady=(16, 0))

        # Offline button
        offline_frame = tk.Frame(container, bg=BG_DARK)
        offline_frame.pack(pady=12, padx=30, fill="x")
        tk.Label(offline_frame, text=lang_ui["offline_title"],
                 bg=BG_DARK, fg=GOLD, font=f_body).pack(anchor="w")
        tk.Label(offline_frame, text=lang_ui["offline_desc"],
                 bg=BG_DARK, fg=SILVER, font=f_small, wraplength=400, justify="left").pack(anchor="w", pady=(4, 8))
        tk.Button(offline_frame, text="▶  Offline Profile",
                  bg="#2a6b3a", fg=WHITE, font=f_btn,
                  relief="flat", cursor="hand2", padx=20, pady=8,
                  command=_select_offline).pack()

        # Spacing
        tk.Label(container, text="", bg=BG_DARK).pack(pady=8)

        # Online button (NOW ENABLED!)
        online_frame = tk.Frame(container, bg=BG_DARK)
        online_frame.pack(pady=12, padx=30, fill="x")
        tk.Label(online_frame, text=lang_ui["online_title"],
                 bg=BG_DARK, fg=GOLD, font=f_body).pack(anchor="w")
        tk.Label(online_frame, text=lang_ui["online_desc"],
                 bg=BG_DARK, fg=SILVER, font=f_small, wraplength=400, justify="left").pack(anchor="w", pady=(4, 8))
        tk.Button(online_frame, text="▶  Online Profile",
                  bg="#3a5b6b", fg=WHITE, font=f_btn,
                  relief="flat", cursor="hand2", padx=20, pady=8,
                  command=_select_online).pack()

    def go_step2():
        result["lang"] = lang_var.get()
        show_step2()

    # ── Step 3: profile name ──────────────────────────────────────

    def show_step3():
        for widget in container.winfo_children():
            widget.destroy()
        lang_ui = _WIZARD_UI.get(result["lang"], _WIZARD_UI["English"])

        # For online profiles, use server username; for offline, ask for name
        if result["profile_type"] == "online":
            # Online: Show server username and let user optionally rename
            tk.Label(container, text="✦  Online Profile Created!",
                     bg=BG_DARK, fg=GOLD, font=f_title).pack(pady=(40, 20))
            
            server_name = result.get("online_user_name", "Player")
            tk.Label(container, text=f"Email: {result.get('online_email', '...')}",
                     bg=BG_DARK, fg=SILVER, font=f_small).pack(pady=(0, 4))
            tk.Label(container, text=f"Username: {server_name}",
                     bg=BG_DARK, fg=GOLD, font=f_body).pack(pady=(0, 20))
            
            tk.Label(container, text="Create a local profile name (optional):",
                     bg=BG_DARK, fg=SILVER, font=f_small).pack()
            
            entry = tk.Entry(container,
                             bg=BG_MID, fg=WHITE, insertbackground=WHITE,
                             font=f_body, width=22, justify="center",
                             relief="flat")
            entry.pack(pady=10, ipady=6)
            entry.insert(0, server_name)  # Default to server username
            entry.focus_set()
            
            err_lbl = tk.Label(container, text="",
                               bg=BG_DARK, fg="#e05050", font=f_small)
            err_lbl.pack(pady=4)
            
            def finish(_event=None):
                name = entry.get().strip()
                if not name:
                    name = server_name
                result["profile"] = name
                root.destroy()
            
            entry.bind("<Return>", finish)
            tk.Button(container, text="Complete Setup",
                      bg=GOLD, fg=BG_DARK, font=f_btn,
                      relief="flat", cursor="hand2", padx=20, pady=8,
                      command=finish).pack(pady=24)
        else:
            # Offline: Normal name entry
            tk.Label(container, text=lang_ui["create_profile"],
                     bg=BG_DARK, fg=GOLD, font=f_title).pack(pady=(40, 20))
            tk.Label(container, text=lang_ui["enter_name"],
                     bg=BG_DARK, fg=SILVER, font=f_small).pack()

            entry = tk.Entry(container,
                             bg=BG_MID, fg=WHITE, insertbackground=WHITE,
                             font=f_body, width=22, justify="center",
                             relief="flat")
            entry.pack(pady=10, ipady=6)
            entry.focus_set()

            tk.Label(container, text=lang_ui["name_hint"],
                     bg=BG_DARK, fg=SILVER, font=f_small).pack()

            err_lbl = tk.Label(container, text="",
                               bg=BG_DARK, fg="#e05050", font=f_small)
            err_lbl.pack(pady=4)

            def finish(_event=None):
                name = entry.get().strip()
                if not name:
                    err_lbl.config(text=lang_ui["name_empty"])
                    return
                result["profile"] = name
                root.destroy()

            entry.bind("<Return>", finish)
            tk.Button(container, text=lang_ui["start"],
                      bg=GOLD, fg=BG_DARK, font=f_btn,
                      relief="flat", cursor="hand2", padx=20, pady=8,
                      command=finish).pack(pady=24)

    # ── Run ───────────────────────────────────────────────────────

    show_step1()
    root.mainloop()   # blocks until root.destroy() is called in finish()

    # Return complete result dict (includes online_token, online_email, etc.)
    return result
