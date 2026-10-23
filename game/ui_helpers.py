"""
ui_helpers.py — Sub Ladder
Reusable UI components and helpers for all screens.
"""

import tkinter as tk
from tkinter import ttk


def enable_mousewheel_scroll(frame, canvas):
    """
    Enable mousewheel scrolling on a canvas with a packed frame inside.
    Works on Windows, macOS, and Linux.
    
    Args:
        frame: The parent frame containing the canvas
        canvas: The Canvas widget to scroll
    """
    def _on_mousewheel(event):
        # event.num: 4 (up), 5 (down) on Linux
        # event.delta: positive (up), negative (down) on Windows/macOS
        if event.num == 4 or event.delta > 0:
            canvas.yview_scroll(-3, "units")
        elif event.num == 5 or event.delta < 0:
            canvas.yview_scroll(3, "units")
    
    # Windows/macOS
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    # Linux
    canvas.bind_all("<Button-4>", _on_mousewheel)
    canvas.bind_all("<Button-5>", _on_mousewheel)


def create_scrollable_frame(parent_frame, bg_color):
    """
    Create a scrollable container: returns (canvas, inner_frame).
    
    The inner_frame is where you pack/grid your widgets.
    
    Usage:
        canvas, inner = create_scrollable_frame(parent, bg_color)
        tk.Label(inner, text="...").pack()
        # The canvas is already packed in parent
    
    Args:
        parent_frame: The frame to contain the canvas
        bg_color: Background color for both canvas and frame
        
    Returns:
        (canvas, inner_frame) tuple
    """
    # Create canvas with scrollbar
    canvas = tk.Canvas(parent_frame, bg=bg_color, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
    
    # Inner frame that will contain all widgets
    inner_frame = tk.Frame(canvas, bg=bg_color)
    inner_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    # Create window in canvas with full width
    canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw", width=canvas.winfo_width() or 1)
    
    def on_canvas_configure(event):
        # Update window width to match canvas width
        canvas.itemconfig(canvas_window, width=event.width)
    
    canvas.bind("<Configure>", on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Enable mousewheel scrolling
    enable_mousewheel_scroll(parent_frame, canvas)
    
    return canvas, inner_frame


# ══════════════════════════════════════════════════════════════════
# Pygame helpers (used by streamer screens)
# ══════════════════════════════════════════════════════════════════

def draw_text(surface, text, font, color, x, y, center=False):
    import pygame
    if center:
        rect = font.render(text, True, color).get_rect()
        rect.center = (x, y)
        surface.blit(font.render(text, True, color), rect)
    else:
        surface.blit(font.render(text, True, color), (x, y))


def draw_button(surface, text, pos, size, bg_color, fg_color, font=None):
    import pygame
    x, y = pos
    w, h = size
    pygame.draw.rect(surface, bg_color, (x, y, w, h))
    pygame.draw.rect(surface, fg_color, (x, y, w, h), 2)
    if font is None:
        font = pygame.font.Font(None, 24)
    txt_rect = font.render(text, True, fg_color).get_rect()
    txt_rect.center = (x + w // 2, y + h // 2)
    surface.blit(font.render(text, True, fg_color), txt_rect)


def draw_progress_bar(surface, x, y, width, height, progress, bg_color=(100, 100, 100), fg_color=(50, 180, 80)):
    import pygame
    pygame.draw.rect(surface, bg_color, (x, y, width, height))
    fill_w = max(0, width * progress / 100)
    pygame.draw.rect(surface, fg_color, (x, y, fill_w, height))
