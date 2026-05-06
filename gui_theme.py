# gui_theme.py
import customtkinter as ctk

# Color Palette: Faigijoon Design Language
COLORS = {
    "bg": "#0A0A0C",           # Deep obsidian background
    "purple": "#BF5AF2",       # Electric Purple
    "cyan": "#5AC8FA",         # Neon Cyan
    "blue": "#5856D6",         # Cobalt Blue
    "card_bg": "#1A1A1E",      # Translucent-look dark glass
    "sidebar_bg": "#121214",   # Slightly different dark for sidebar
    "text": "#FFFFFF",         # High-contrast white
    "text_dim": "#8E8E93",     # Muted grey text
    "success": "#32D74B",      # Vibrant Green
    "info": "#0A84FF",         # System Blue
    "warning": "#FF9F0A",      # System Orange
    "error": "#FF453A"         # System Red
}

# UI Component Specifications
STYLES = {
    "corner_radius": 14,
    "border_width": 2,
    "font_family": "Segoe UI" if ctk.get_appearance_mode() == "Windows" else "SF Pro Display",
    "title_size": 32,
    "header_size": 20,
    "body_size": 13,
    "log_size": 12
}

def get_font(size, weight="normal"):
    # Fallback to standard fonts if preferred ones aren't available
    return ("Arial", size, weight)
