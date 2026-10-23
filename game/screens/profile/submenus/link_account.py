"""
game/screens/profile/submenus/link_account.py — Sous-menu pour la liaison de compte en ligne.
Supporte : Email, Discord, Steam.
"""

import tkinter as tk
from tkinter import messagebox

from constants import (
    BG_DARK, BG_PANEL, GOLD, SILVER, WHITE,
    BTN_DEFAULT, BTN_HOVER, MENU_BTN_BG, MENU_BTN_ACT,
    LIFELINE_ON, LIFELINE_TEXT_ON, BTN_CORRECT
)


# Icônes et descriptions pour chaque type de lien
def promote_profile_to_online(profile: dict, provider: str, provider_id: str) -> dict:
    """Promote an offline profile to online when a linking provider is configured."""
    updated = dict(profile)
    updated["profile_type"] = "online"
    updated["linked_accounts"] = list(updated.get("linked_accounts", []))

    if provider == "discord":
        updated["linked_discord"] = True
        updated["discord_id"] = provider_id
        if "discord" not in updated["linked_accounts"]:
            updated["linked_accounts"].append("discord")
    elif provider == "steam":
        updated["linked_steam"] = True
        updated["steam_id"] = provider_id
        if "steam" not in updated["linked_accounts"]:
            updated["linked_accounts"].append("steam")
    else:
        updated["profile_type"] = "online"

    return updated


LINK_OPTIONS = [
    {
        "id": "email",
        "icon": "📧",
        "label": "Email",
        "description": "Lier votre adresse email au compte",
        "fields": [
            {"name": "email", "label": "Email :", "type": "entry"},
            {"name": "password", "label": "Mot de passe :", "type": "password"},
        ],
    },
    {
        "id": "discord",
        "icon": "🎮",
        "label": "Discord",
        "description": "Lier votre compte Discord",
        "fields": [
            {"name": "discord_tag", "label": "Discord Tag (ex: user#1234) :", "type": "entry"},
        ],
    },
    {
        "id": "steam",
        "icon": "🎯",
        "label": "Steam",
        "description": "Lier votre compte Steam",
        "fields": [
            {"name": "steam_id", "label": "Steam ID / URL :", "type": "entry"},
        ],
    },
]


def show_link_account(app):
    """Afficher l'écran de choix du type de compte à lier."""
    app._clear()

    f = app._container

    # Titre
    header = tk.Frame(f, bg=BG_DARK)
    header.pack(fill="x", pady=(24, 16))
    tk.Label(header, text="Lier un compte",
             bg=BG_DARK, fg=GOLD, font=app.f_title).pack()

    # Panneau de sélection du type
    picker_frame = tk.Frame(f, bg=BG_DARK)
    picker_frame.pack(expand=True, fill="both", padx=40, pady=20)

    tk.Label(picker_frame, text="Choisissez le type de compte :",
             bg=BG_DARK, fg=SILVER, font=app.f_label).pack(pady=(0, 16))

    for option in LINK_OPTIONS:
        btn = tk.Button(
            picker_frame,
            text=f"{option['icon']}  {option['label']}\n\n{option['description']}",
            bg=BTN_DEFAULT, fg=GOLD, font=app.f_prize_hl,
            relief="flat", cursor="hand2", padx=30, pady=20,
            width=28, height=4,
            command=lambda opt=option: _show_link_form(app, opt)
        )
        btn.pack(pady=8)
        _add_hover(btn, app)

    # Bouton retour
    tk.Button(f, text="← Retour",
              bg=MENU_BTN_BG, fg=SILVER, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=8,
              command=app.show_profile).pack(pady=16)


def _show_link_form(app, option: dict):
    """Afficher le formulaire de liaison pour un type de compte spécifique."""
    app._clear()

    f = app._container

    # Titre
    header = tk.Frame(f, bg=BG_DARK)
    header.pack(fill="x", pady=(24, 16))
    tk.Label(header, text=f"{option['icon']}  {option['label']} — Lier un compte",
             bg=BG_DARK, fg=GOLD, font=app.f_title).pack()

    # Formulaire
    form_frame = tk.Frame(f, bg=BG_DARK)
    form_frame.pack(expand=True, fill="both", padx=40, pady=20)

    entries = {}
    for field in option["fields"]:
        tk.Label(form_frame, text=field["label"],
                 bg=BG_DARK, fg=GOLD, font=app.f_label).pack(anchor="w", pady=(10, 2))

        if field["type"] == "password":
            entry = tk.Entry(form_frame, font=app.f_label, width=35, show="•", justify="left")
        else:
            entry = tk.Entry(form_frame, font=app.f_label, width=35, justify="left")

        entry.pack(fill="x", pady=(0, 8))
        entries[field["name"]] = entry

    if "email" in entries:
        entries["email"].focus_set()
    elif entries:
        list(entries.values())[0].focus_set()

    def on_enter(e=None):
        _do_link(app, option, entries)

    # Raccourci clavier
    for entry_widget in entries.values():
        entry_widget.bind("<Return>", on_enter)

    # Bouton lier
    link_btn = tk.Button(
        form_frame,
        text=f"🔗  Lier {option['label']}",
        bg=LIFELINE_ON, fg=LIFELINE_TEXT_ON, font=app.f_prize_hl,
        relief="flat", cursor="hand2", padx=20, pady=8,
        command=lambda: _do_link(app, option, entries)
    )
    link_btn.pack(pady=16)
    _add_hover(link_btn, app)

    # Infos de sécurité
    tk.Label(
        form_frame,
        text="🔒 Vos données sont envoyées de manière sécurisée via HTTPS.",
        bg=BG_DARK, fg=SILVER, font=app.f_small
    ).pack(pady=(8, 0))

    # Bouton retour
    tk.Button(f, text="← Retour",
              bg=BTN_DEFAULT, fg=SILVER, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=8,
              command=lambda a=app: show_link_account(a)).pack(pady=16)


def _do_link(app, option: dict, entries: dict):
    """Effectuer la liaison du compte via l'API."""
    # Collecter les données du formulaire
    data = {}
    for field in option["fields"]:
        value = entries[field["name"]].get().strip()
        if not value:
            messagebox.showerror("", f"{field['label']} ne peut pas être vide.", parent=app)
            return
        data[field["name"]] = value

    profile_name = app.data.get("active_profile", "")
    if not profile_name:
        messagebox.showerror("", "Aucun profil actif sélectionné.", parent=app)
        return

    # Récupérer le token d'authentification
    token = app.data.get("auth", {}).get("tokens", {}).get(profile_name)
    if not token:
        messagebox.showerror(
            "",
            "Vous devez être connecté pour lier un compte. Connectez-vous d'abord.",
            parent=app
        )
        return

    def link_thread():
        try:
            from game.auth.client import APIClient
            api = APIClient()

            # Mapper le type de liaison vers le nom de la méthode API
            method_name = f"link_{option['id']}"
            link_method = getattr(api, method_name, None)

            if link_method is None:
                app.after(0, lambda: messagebox.showerror(
                    "",
                    f"Méthode API non implémentée pour {option['label']}.",
                    parent=app
                ))
                return

            # Appeler la méthode de liaison
            result = link_method(token, **data)

            if result.get("error"):
                app.after(0, lambda err=result["error"]: _show_error(app, err))
                return

            # Sauvegarder les informations de compte lié
            profile = app.data["profiles"].get(profile_name, {})
            profile[f"linked_{option['id']}"] = True
            profile[f"{option['id']}_id"] = result.get("linked_id", data.get(list(data.keys())[0]))
            profile["linked_accounts"] = profile.get("linked_accounts", [])
            if option["id"] not in profile["linked_accounts"]:
                profile["linked_accounts"].append(option["id"])

            # Promote the local profile to online after successful external account linkage.
            if profile.get("profile_type") != "online":
                profile = promote_profile_to_online(profile, option["id"], profile[f"{option['id']}_id"])

            app.data["profiles"][profile_name] = profile
            from utils import save_data
            save_data(app.data, silent=True)

            app.after(0, lambda: _show_success(app, option))

        except Exception as e:
            app.after(0, lambda err=str(e): _show_error(app, err))

    # Lancer en thread pour ne pas bloquer l'UI
    import threading
    threading.Thread(target=link_thread, daemon=True).start()


def _show_success(app, option: dict):
    """Afficher un message de succès après liaison."""
    app._clear()
    f = app._container

    header = tk.Frame(f, bg=BG_DARK)
    header.pack(fill="x", pady=(24, 16))
    tk.Label(header, text="✅ Compte lié",
             bg=BG_DARK, fg="#44cc44", font=app.f_title).pack()

    panel = tk.Frame(f, bg=BG_DARK)
    panel.pack(expand=True, fill="both", padx=40, pady=20)

    tk.Label(
        panel,
        text=f"Votre compte {option['icon']} {option['label']} a été lié avec succès. Votre profil est désormais en ligne.",
        bg=BG_DARK,
        fg=SILVER,
        font=app.f_label,
    ).pack(pady=20)

    tk.Button(panel, text="✓ Continuer",
              bg=LIFELINE_ON, fg="white", font=app.f_prize_hl,
              relief="flat", cursor="hand2", padx=20, pady=8,
              command=app.show_profile).pack(pady=16)

    tk.Button(f, text="← Retour",
              bg=BTN_DEFAULT, fg=SILVER, font=app.f_small,
              relief="flat", cursor="hand2", padx=12, pady=8,
              command=show_link_account).pack(pady=16)


def _show_error(app, error_msg: str):
    """Afficher un message d'erreur."""
    from tkinter import messagebox
    messagebox.showerror("", f"Échec de la liaison : {error_msg}")


def _add_hover(btn, app):
    """Ajouter les effets de survol sur un bouton."""
    original_bg = btn.cget("bg")

    def _enter(e=None):
        btn.config(bg=BTN_HOVER, highlightbackground=MENU_BTN_ACT, highlightthickness=2)

    def _leave(e=None):
        btn.config(bg=original_bg, highlightthickness=0)

    btn.bind("<Enter>", _enter)
    btn.bind("<Leave>", _leave)
