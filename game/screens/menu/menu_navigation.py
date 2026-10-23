"""
menu_navigation.py — Bindings clavier/souris et handlers de navigation.
"""


def bind_menu_navigation(app, root, move_up_callback=None, move_down_callback=None, wheel_callback=None, activate_callback=None):
    """Attacher les bindings clavier sur le frame racine.

    La molette est volontairement désactivée sur le menu principal ici,
    car son gestionnaire Tkinter est instable sur cette build et provoque
    la fermeture du jeu après un simple scroll.
    """
    sequences = ["<Up>", "<Down>", "<Return>", "<KP_Enter>"]
    for sequence in sequences:
        try:
            root.unbind(sequence)
        except Exception:
            pass

    if move_up_callback is not None:
        root.bind("<Up>", move_up_callback)
    if move_down_callback is not None:
        root.bind("<Down>", move_down_callback)
    if activate_callback is not None:
        root.bind("<Return>", activate_callback)
        root.bind("<KP_Enter>", activate_callback)


def bind_card_clicks(card, active_frame, label, arrow_label, activate_callback, move_up_callback, move_down_callback):
    """Attacher les bindings de clic sur la carte de sélection."""
    card.bind("<Button-1>", activate_callback)
    active_frame.bind("<Button-1>", activate_callback)
    label.bind("<Button-1>", activate_callback)
    arrow_label.bind("<Button-1>", activate_callback)
    # Clic sur les labels haut/bas pour naviguer
    move_up_cb = lambda e: move_up_callback(e) if callable(move_up_callback) else None
    move_down_cb = lambda e: move_down_callback(e) if callable(move_down_callback) else None
    # On retourne les handlers plutôt que de bind directement (appelé par build)
    return card, active_frame, label, arrow_label, move_up_cb, move_down_cb


def on_up(event=None):
    """Handler flèche haut."""
    return "break"


def on_down(event=None):
    """Handler flèche bas."""
    return "break"


def on_enter(event=None):
    """Handler Entrée."""
    return "break"


def on_mousewheel(event):
    """Handler molette de souris."""
    if hasattr(event, 'delta') and event.delta != 0:
        # delta > 0 = scroll up, delta < 0 = scroll down
        pass  # La logique réelle est dans le callback passé par build()
    elif getattr(event, 'num', None) == 4:
        pass  # scroll up
    elif getattr(event, 'num', None) == 5:
        pass  # scroll down
    return "break"
