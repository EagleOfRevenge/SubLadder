"""
screens/streamer_game_viewvers.py — Sub Ladder
Streamer game screen for Viewvers.
"""

import tkinter as tk
from tkinter import messagebox
import time

from constants import (
    BG_DARK, GOLD, SILVER, TEXT_DISABLED,
    BTN_DEFAULT, BTN_HOVER, MENU_BTN_BG, MENU_BTN_FG, MENU_BTN_ACT,
    f_title, f_label, f_small, f_menu_btn
)
from game_state import GameState


def build(app):
    """Build the streamer game screen for Viewvers."""
    app._clear()
    app._timer_stop()
    
    # Initialize game state if not already done
    if not hasattr(app, 'game_state') or app.game_state is None:
        app.game_state = GameState()
    
    f = app._container
    
    # Background image
    bg_img = app.images.background(
        "menu", size=(app.winfo_width() or 900, app.winfo_height() or 720))
    if bg_img:
        lbl = tk.Label(f, image=bg_img, bg=app.BG_DARK)
        lbl.place(x=0, y=0, relwidth=1, relheight=1)
        # lbl._img_ref = bg_img
    
    app.title(app.s("streamer_game_title"))
    
    # Title
    tk.Label(f, text="✦  Sub Ladder  ✦",
             bg=app.BG_DARK, fg=app.GOLD, font=f_title()).pack(pady=(40, 6))
    
    # Game info frame
    game_info_frame = tk.Frame(f, bg=app.BG_DARK)
    game_info_frame.pack(pady=20)
    
    # Question counter
    app.question_counter = tk.Label(
        game_info_frame, 
        text=app.s("question") + " 1/15", 
        bg=app.BG_DARK, fg=app.SILVER, font=f_label()
    )
    app.question_counter.pack()
    
    # Question display
    question_frame = tk.Frame(f, bg=app.BG_DARK)
    question_frame.pack(pady=20)
    
    # Question text
    app.question_text = tk.Label(
        question_frame,
        text=app.s("waiting_for_question"), 
        bg=app.BG_DARK, fg=app.WHITE, font=f_label,
        wraplength=600, justify="center"
    )
    app.question_text.pack(pady=(0, 20))
    
    # Options frame
    options_frame = tk.Frame(f, bg=app.BG_DARK)
    options_frame.pack(pady=10)
    
    # Initialize options variables
    app.options_vars = []
    app.option_buttons = []
    
    # Create 4 option buttons (initially disabled)
    for i in range(4):
        var = tk.StringVar()
        app.options_vars.append(var)
        
        btn = tk.Button(
            options_frame, 
            textvariable=var,
            bg=app.BTN_DEFAULT, fg=app.WHITE, font=f_small(),
            relief="flat", cursor="hand2", padx=20, pady=10,
            activebackground=app.BTN_HOVER, activeforeground=app.WHITE,
            highlightbackground=app.BTN_DEFAULT, highlightthickness=0,
            state="disabled"
        )
        btn.pack(pady=5)
        app.option_buttons.append(btn)
    
    # Timer frame
    timer_frame = tk.Frame(f, bg=app.BG_DARK)
    timer_frame.pack(pady=20)
    
    # Timer display
    app.timer_label = tk.Label(
        timer_frame,
        text="00:00", 
        bg=app.BG_DARK, fg=app.GOLD, font=f_title
    )
    app.timer_label.pack()
    
    # Progress bar frame
    progress_frame = tk.Frame(f, bg=app.BG_DARK)
    progress_frame.pack(pady=20)
    
    # Progress bar (initially empty)
    app.progress_bar = tk.Canvas(
        progress_frame, 
        width=600, height=20,
        bg=app.BTN_DEFAULT, highlightthickness=0
    )
    app.progress_bar.pack()
    
    # Current question index (will be updated during game)
    app.current_question_index = 0
    
    # Timer variables
    app.timer_running = False
    app.time_left = 0
    app.timer_job = None
    
    # Viewvers responses tracking
    app.viewvers_responses = {}
    
    def start_question(question_data):
        """Start a new question."""
        app.current_question_index += 1
        
        # Update question counter
        app.question_counter.config(
            text=f"{app.s('question')} {app.current_question_index}/15"
        )
        
        # Display question text
        app.question_text.config(text=question_data["text"])
        
        # Enable options for Viewvers to select
        for i, option in enumerate(question_data["options"]):
            if i < len(app.option_buttons):
                app.options_vars[i].set(option)
                app.option_buttons[i].config(state="normal")
        
        # Update progress bar
        update_progress_bar()
        
        # Start timer with time from config
        start_timer(
            app.data.get("streamer_config", {}).get("question_time", 15)
        )
    
    def update_progress_bar():
        """Update the progress bar to show current question."""
        # Clear canvas
        app.progress_bar.delete("all")
        
        # Draw progress bar
        width = 600
        height = 20
        bar_width = width * (app.current_question_index / 15)
        
        # Background
        app.progress_bar.create_rectangle(0, 0, width, height, fill=app.BTN_DEFAULT, outline="")
        
        # Progress
        app.progress_bar.create_rectangle(0, 0, bar_width, height, fill=app.GOLD, outline="")
    
    def start_timer(seconds):
        """Start the question timer."""
        app.timer_running = True
        app.time_left = seconds
        update_timer_display()
        
        # Cancel any existing timer job
        if app.timer_job:
            app.after_cancel(app.timer_job)
        
        # Start new timer
        countdown_timer()
    
    def countdown_timer():
        """Count down the timer."""
        if not app.timer_running:
            return
            
        if app.time_left > 0:
            app.time_left -= 1
            update_timer_display()
            app.timer_job = app.after(1000, countdown_timer)
        else:
            # Time's up - disable options and move to next question or streamer response
            timer_finished()
    
    def update_timer_display():
        """Update the timer display."""
        minutes = app.time_left // 60
        seconds = app.time_left % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        app.timer_label.config(text=time_str)
    
    def timer_finished():
        """Handle when timer finishes."""
        app.timer_running = False
        
        # Disable all option buttons
        for btn in app.option_buttons:
            btn.config(state="disabled")
        
        # Show current question results to streamer (for them to answer)
        show_question_results()
    
    def show_question_results():
        """Show the question results to streamer."""
        # This will be implemented when we integrate with server
        pass
    
    def on_option_click(option_index):
        """Handle Viewvers selecting an option."""
        if not app.timer_running:
            return
            
        # In a real implementation, this would send the response to the server
        # For now, just show that the response was recorded
        
        messagebox.showinfo(
            app.s("response_recorded"), 
            f"{app.s('your_response')} {option_index + 1} {app.s('recorded')}"
        )
    
    def next_question():
        """Move to next question."""
        # In a real implementation, this would get the next question from server
        pass
    
    def end_game():
        """End the game and show results."""
        # Navigate to results screen
        from .streamer_results import build as results_build
        results_build(app)
    
    # Bind option buttons to click events
    for i, btn in enumerate(app.option_buttons):
        btn.config(command=lambda idx=i: on_option_click(idx))
    
    # Start first question (in a real implementation this would come from server)
    # For now, we'll simulate with sample data
    sample_question = {
        "text": app.s("sample_question"),
        "options": [
            app.s("option_a"), 
            app.s("option_b"), 
            app.s("option_c"), 
            app.s("option_d")
        ]
    }
    
    start_question(sample_question)
    
    # Navigation buttons frame
    nav_frame = tk.Frame(f, bg=app.BG_DARK)
    nav_frame.pack(pady=20)
    
    def _on_back():
        """Return to main menu."""
        app.show_menu()
    
    back_btn = tk.Button(
        nav_frame, text=app.s("back_menu"),
        bg=app.MENU_BTN_BG, fg=app.MENU_BTN_FG, font=f_small(),
        relief="flat", cursor="hand2", padx=12, pady=6,
        activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
        highlightbackground=app.MENU_BTN_BG, highlightthickness=0,
        command=_on_back
    )
    back_btn.pack(side="left", padx=10)
    
    # Add a button to end the game early (for testing purposes)
    def _on_end():
        """End the game."""
        if messagebox.askyesno(
            app.s("end_game"), 
            app.s("confirm_end_game")
        ):
            end_game()
    
    end_btn = tk.Button(
        nav_frame, text=app.s("end_game"),
        bg=app.MENU_BTN_BG, fg=app.MENU_BTN_FG, font=f_small(),
        relief="flat", cursor="hand2", padx=12, pady=6,
        activebackground=app.BTN_HOVER, activeforeground=app.MENU_BTN_ACT,
        highlightbackground=app.MENU_BTN_BG, highlightthickness=0,
        command=_on_end
    )
    end_btn.pack(side="left", padx=10)