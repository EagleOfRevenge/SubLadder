"""
screens/auth.py — Sub Ladder
Login and signup screens for online profiles.
"""

import tkinter as tk
from tkinter import messagebox
import re


def show_login_dialog(app, on_success, on_cancel):
    """
    Show login dialog for online profiles.
    on_success(email, token, user_data) called if login succeeds.
    on_cancel() called if user cancels.
    """
    root = tk.Toplevel(app)
    root.title("Sub Ladder — Login")
    root.configure(bg=app.BG_DARK)
    root.resizable(False, False)
    root.geometry("400x300")
    
    # Center on parent
    root.update_idletasks()
    x = app.winfo_x() + (app.winfo_width() - 400) // 2
    y = app.winfo_y() + (app.winfo_height() - 300) // 2
    root.geometry(f"400x300+{x}+{y}")
    
    lang = app._lang.get("code", "en")
    
    # Title
    tk.Label(root, text="🔒  Online Login",
             bg=app.BG_DARK, fg=app.GOLD, font=app.f_title).pack(pady=(20, 12))
    
    # Email field
    tk.Label(root, text="Email:", bg=app.BG_DARK, fg=app.SILVER,
             font=app.f_small).pack(anchor="w", padx=30, pady=(0, 2))
    email_entry = tk.Entry(root, bg=app.BG_MID, fg=app.WHITE,
                           insertbackground=app.WHITE, font=app.f_body,
                           width=28, justify="center", relief="flat")
    email_entry.pack(padx=30, pady=(0, 12), ipady=4)
    email_entry.focus_set()
    
    # Password field
    tk.Label(root, text="Password:", bg=app.BG_DARK, fg=app.SILVER,
             font=app.f_small).pack(anchor="w", padx=30, pady=(0, 2))
    pwd_entry = tk.Entry(root, bg=app.BG_MID, fg=app.WHITE,
                         insertbackground=app.WHITE, font=app.f_body,
                         width=28, justify="center", relief="flat", show="•")
    pwd_entry.pack(padx=30, pady=(0, 12), ipady=4)
    
    # Error label
    err_lbl = tk.Label(root, text="", bg=app.BG_DARK, fg="#e05050",
                       font=app.f_small)
    err_lbl.pack(pady=4)
    
    # Status label
    status_lbl = tk.Label(root, text="", bg=app.BG_DARK, fg=app.SILVER,
                          font=app.f_small)
    status_lbl.pack(pady=2)
    
    def _login():
        email = email_entry.get().strip()
        password = pwd_entry.get().strip()
        
        if not email or not password:
            err_lbl.config(text="Email and password required")
            return
        
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            err_lbl.config(text="Invalid email format")
            return
        
        # Disable buttons during login
        login_btn.config(state="disabled")
        cancel_btn.config(state="disabled")
        status_lbl.config(text="Logging in...")
        err_lbl.config(text="")
        root.update()
        
        # Call API
        result = app.api.login(email, password)
        
        if result.get("error"):
            err_lbl.config(text=result["error"])
            status_lbl.config(text="")
            login_btn.config(state="normal")
            cancel_btn.config(state="normal")
        else:
            # Success
            token = result.get("access_token", "")
            user = result.get("user", {})
            on_success(email, token, user)
            root.destroy()
    
    # Buttons
    btn_frame = tk.Frame(root, bg=app.BG_DARK)
    btn_frame.pack(pady=16)
    
    login_btn = tk.Button(btn_frame, text="Login",
                          bg=app.GOLD, fg=app.BG_DARK, font=app.f_body,
                          relief="flat", cursor="hand2", padx=16, pady=6,
                          command=_login)
    login_btn.pack(side="left", padx=4)
    
    cancel_btn = tk.Button(btn_frame, text="Cancel",
                           bg=app.BTN_DEFAULT, fg=app.SILVER, font=app.f_body,
                           relief="flat", cursor="hand2", padx=16, pady=6,
                           command=lambda: [root.destroy(), on_cancel()])
    cancel_btn.pack(side="left", padx=4)
    
    pwd_entry.bind("<Return>", lambda e: _login())


def show_signup_dialog(app, on_success, on_cancel):
    """
    Show signup dialog for new online profiles.
    on_success(email, token, user_data) called if signup succeeds.
    on_cancel() called if user cancels.
    """
    root = tk.Toplevel(app)
    root.title("Sub Ladder — Create Online Account")
    root.configure(bg=app.BG_DARK)
    root.resizable(False, False)
    root.geometry("400x380")
    
    # Center on parent
    root.update_idletasks()
    x = app.winfo_x() + (app.winfo_width() - 400) // 2
    y = app.winfo_y() + (app.winfo_height() - 380) // 2
    root.geometry(f"400x380+{x}+{y}")
    
    lang = app._lang.get("code", "en")
    
    # Title
    tk.Label(root, text="✦  Create Online Account",
             bg=app.BG_DARK, fg=app.GOLD, font=app.f_title).pack(pady=(20, 12))
    
    # Email field
    tk.Label(root, text="Email:", bg=app.BG_DARK, fg=app.SILVER,
             font=app.f_small).pack(anchor="w", padx=30, pady=(0, 2))
    email_entry = tk.Entry(root, bg=app.BG_MID, fg=app.WHITE,
                           insertbackground=app.WHITE, font=app.f_body,
                           width=28, justify="center", relief="flat")
    email_entry.pack(padx=30, pady=(0, 8), ipady=4)
    email_entry.focus_set()
    
    # Password field
    tk.Label(root, text="Password:", bg=app.BG_DARK, fg=app.SILVER,
             font=app.f_small).pack(anchor="w", padx=30, pady=(0, 2))
    pwd_entry = tk.Entry(root, bg=app.BG_MID, fg=app.WHITE,
                         insertbackground=app.WHITE, font=app.f_body,
                         width=28, justify="center", relief="flat", show="•")
    pwd_entry.pack(padx=30, pady=(0, 8), ipady=4)
    
    # Confirm password field
    tk.Label(root, text="Confirm:", bg=app.BG_DARK, fg=app.SILVER,
             font=app.f_small).pack(anchor="w", padx=30, pady=(0, 2))
    confirm_entry = tk.Entry(root, bg=app.BG_MID, fg=app.WHITE,
                             insertbackground=app.WHITE, font=app.f_body,
                             width=28, justify="center", relief="flat", show="•")
    confirm_entry.pack(padx=30, pady=(0, 8), ipady=4)
    
    # Username/game name field
    tk.Label(root, text="Username:", bg=app.BG_DARK, fg=app.SILVER,
             font=app.f_small).pack(anchor="w", padx=30, pady=(0, 2))
    username_entry = tk.Entry(root, bg=app.BG_MID, fg=app.WHITE,
                              insertbackground=app.WHITE, font=app.f_body,
                              width=28, justify="center", relief="flat")
    username_entry.pack(padx=30, pady=(0, 8), ipady=4)
    
    # Error label
    err_lbl = tk.Label(root, text="", bg=app.BG_DARK, fg="#e05050",
                       font=app.f_small)
    err_lbl.pack(pady=4)
    
    # Status label
    status_lbl = tk.Label(root, text="", bg=app.BG_DARK, fg=app.SILVER,
                          font=app.f_small)
    status_lbl.pack(pady=2)
    
    def _signup():
        email = email_entry.get().strip()
        password = pwd_entry.get().strip()
        confirm = confirm_entry.get().strip()
        username = username_entry.get().strip()
        
        if not email or not password or not username:
            err_lbl.config(text="All fields required")
            return
        
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            err_lbl.config(text="Invalid email format")
            return
        
        if len(password) < 6:
            err_lbl.config(text="Password must be at least 6 characters")
            return
        
        if password != confirm:
            err_lbl.config(text="Passwords do not match")
            return
        
        if len(username) < 3:
            err_lbl.config(text="Username must be at least 3 characters")
            return
        
        # Disable buttons during signup
        signup_btn.config(state="disabled")
        cancel_btn.config(state="disabled")
        status_lbl.config(text="Creating account...")
        err_lbl.config(text="")
        root.update()
        
        # Call API
        result = app.api.register(email, password, username)
        
        if result.get("error"):
            err_lbl.config(text=result["error"])
            status_lbl.config(text="")
            signup_btn.config(state="normal")
            cancel_btn.config(state="normal")
        else:
            # Success
            token = result.get("access_token", "")
            user = result.get("user", {})
            on_success(email, token, user)
            root.destroy()
    
    # Buttons
    btn_frame = tk.Frame(root, bg=app.BG_DARK)
    btn_frame.pack(pady=12)
    
    signup_btn = tk.Button(btn_frame, text="Create Account",
                           bg=app.GOLD, fg=app.BG_DARK, font=app.f_body,
                           relief="flat", cursor="hand2", padx=14, pady=6,
                           command=_signup)
    signup_btn.pack(side="left", padx=4)
    
    cancel_btn = tk.Button(btn_frame, text="Cancel",
                           bg=app.BTN_DEFAULT, fg=app.SILVER, font=app.f_body,
                           relief="flat", cursor="hand2", padx=16, pady=6,
                           command=lambda: [root.destroy(), on_cancel()])
    cancel_btn.pack(side="left", padx=4)
    
    confirm_entry.bind("<Return>", lambda e: _signup())
