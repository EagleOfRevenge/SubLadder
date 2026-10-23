"""
screens/streamer_config.py — Sub Ladder
Streamer session configuration screen.
"""

import tkinter as tk
from tkinter import messagebox

from constants import (
    BG_DARK, GOLD, SILVER, TEXT_DISABLED,
    BTN_DEFAULT, BTN_HOVER, MENU_BTN_BG, MENU_BTN_FG, MENU_BTN_ACT,
    f_title, f_label, f_small, f_menu_btn
)


def build(app):
    """Build the streamer configuration screen."""
    app._clear()
    app._timer_stop()
    
    f = app._container
    
    # Background image
    bg_img = app.images.background(
        "menu", size=(app.winfo_width() or 900, app.winfo_height() or 720))
    if bg_img:
        lbl = tk.Label(f, image=bg_img, bg=app.BG_DARK)
        lbl.place(x=0, y=0, relwidth=1, relheight=1)
        # lbl._img_ref = bg_img
    
    app.title(app.s("streamer_config_title"))
    
    # Title
    tk.Label(f, text="✦  Sub Ladder  ✦",
             bg=app.BG_DARK, fg=app.GOLD, font=f_title()).pack(pady=(40, 6))
    
    # Configuration frame
    config_frame = tk.Frame(f, bg=app.BG_DARK)
    config_frame.pack(pady=20)
    
    # Stream URL
    tk.Label(config_frame, text=app.s("stream_url"), 
             bg=app.BG_DARK, fg=app.SILVER, font=f_label()).pack(pady=(10, 0))
    
    stream_url_var = tk.StringVar()
    url_entry = tk.Entry(config_frame, textvariable=stream_url_var,
                         bg=app.BTN_DEFAULT, fg=app.WHITE, font=f_small(),
                         relief="flat", bd=0, highlightthickness=1,
                         highlightbackground=app.BTN_DEFAULT,
                         insertbackground=app.WHITE, width=50)
    url_entry.pack(pady=(0, 10))
    
    # Question delay
    tk.Label(config_frame, text=app.s("question_delay"), 
             bg=app.BG_DARK, fg=app.SILVER, font=f_label()).pack(pady=(10, 0))
    
    delay_var = tk.StringVar(value="30")
    delay_entry = tk.Entry(config_frame, textvariable=delay_var,
                          bg=app.BTN_DEFAULT, fg=app.WHITE, font=f_small(),
                          relief="flat", bd=0, highlightthickness=1,
                          highlightbackground=app.BTN_DEFAULT,
                          insertbackground=app.WHITE, width=20)
    delay_entry.pack(pady=(0, 10))
    
    # Question time
    tk.Label(config_frame, text=app.s("question_time"), 
             bg=app.BG_DARK, fg=app.SILVER, font=f_label()).pack(pady=(10, 0))
    
    time_var = tk.StringVar(value="15")
    time_entry = tk.Entry(config_frame, textvariable=time_var,
                         bg=app.BTN_DEFAULT, fg=app.WHITE, font=f_small(),
                         relief="flat", bd=0, highlightthickness=1,
                         highlightbackground=app.BTN_DEFAULT,
                         insertbackground=app.WHITE, width=20)
    time_entry.pack(pady=(0, 20))
    
    # Buttons frame
    buttons_frame = tk.Frame(f, bg=app.BG_DARK)
    buttons_frame.pack(pady=20)
    
    def _on_save():
        """Save configuration and start streamer game."""
        try:
            delay = int(delay_var.get())
            time = int(time_var.get())
            
            if delay <= 0 or time <= 0:
                messagebox.showerror(
                    app.s("error"), 
                    app.s("invalid_values")
                )
                return
                
            # Save configuration
            config = {
                "stream_url": stream_url_var.get().strip(),
                "question_delay": delay,
                "question_time": time
            }
            
            app.data["streamer_config"] = config
            
            # Navigate to streamer game screen
            from .streamer_game_streamer import build as streamer_build
            streamer_build(app)
            
        except ValueError:
            messagebox.showerror(
                app.s("error"), 
                app.s("invalid_numbers")
            )
    
    def _on_cancel():
        """Cancel and return to main menu."""
        app.show_menu()
    
    # Save button
    save_btn = tk.Button(
        buttons_frame, text=app.s("save"),
        bg=app.GOLD, fg=app.BG_DARK, font=f_menu_btn(),
        relief="flat", cursor="hand2", padx=20, pady=8,
        activebackground=app.BTN_HOVER, activeforeground=app.BG_DARK,
        highlightbackground=app.GOLD, highlightthickness=0,
        command=_on_save
    )
    save_btn.pack(side="left", padx=10)
    
    # Cancel button
    cancel_btn = tk.Button(
        buttons_frame, text=app.s("cancel"),
        bg=app.MENU_BTN_BG, fg=app.MENU_BTN_FG, font=f_small(),
        relief="flat", cursor="hand2", padx=12, pady=6,
        activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
        highlightbackground=app.MENU_BTN_BG, highlightthickness=0,
        command=_on_cancel
    )
    cancel_btn.pack(side="left", padx=10)
    
    # Back to menu button
    tk.Button(f, text=app.s("back_menu"),
              bg=app.MENU_BTN_BG, fg=app.MENU_BTN_FG, font=f_small(),
              relief="flat", cursor="hand2", padx=12, pady=6,
              activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
              highlightbackground=app.MENU_BTN_BG, highlightthickness=0,
              command=app.show_menu).pack(pady=(20, 10))