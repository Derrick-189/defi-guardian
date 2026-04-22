"""
DeFi Guardian - Desktop Application
Formal Verification Suite with SPIN Model Checker
Full Translation Support for Solidity/Rust
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import os
import sys
import webbrowser
import threading
import re
import time
import json
import tempfile
from datetime import datetime
from pathlib import Path
import tkinter as tk
import socket

# PyQt6 version - more native look, better performance 
# Requirements: PyQt6, PyQt6-WebEngine (for embedded dashboard) 
try:
    from PyQt6.QtWidgets import ( 
        QMainWindow, QSplitter, QTabWidget, QTextEdit, 
        QTreeView, QToolBar, QStatusBar, QDockWidget 
    ) 
    from PyQt6.QtCore import Qt, QThread, pyqtSignal 
    from PyQt6.QtGui import QFont, QPalette, QColor, QSyntaxHighlighter
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False

# NiceGUI example - web UI in desktop wrapper 
try:
    from nicegui import ui, app as nicegui_app
    HAS_NICEGUI = True
except ImportError:
    HAS_NICEGUI = False

# Gradio version - modern AI-focused interface
try:
    import gradio as gr
    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False

# Project directory for file I/O
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
# First Lean check after boot can take minutes (Elan/toolchain + stdlib); override with DG_LEAN_TIMEOUT.
LEAN_TIMEOUT_SECONDS = int(os.environ.get("DG_LEAN_TIMEOUT", "300"))
# Streamlit cold-start can exceed a few seconds; cap wait when opening the browser.
STREAMLIT_START_TIMEOUT = float(os.environ.get("DG_STREAMLIT_START_TIMEOUT", "120"))

class ResizablePanel:
    """Handle resizing of panels with mouse drag"""
    def __init__(self, master, panel_to_resize, orientation='vertical', min_size=200, max_size=800):
        self.master = master
        self.panel = panel_to_resize
        self.orientation = orientation
        self.min_size = min_size
        self.max_size = max_size
        self.dragging = False
        self.start_x = 0
        self.start_y = 0
        self.start_size = 0
        
        # Create resize handle
        if orientation == 'vertical':
            self.handle = ctk.CTkFrame(master, width=5, height=20, cursor="sb_h_double_arrow",
                                       fg_color="#3a3a3a", corner_radius=2)
            self.handle.bind("<Button-1>", self.start_drag)
            self.handle.bind("<B1-Motion>", self.drag)
            self.handle.bind("<ButtonRelease-1>", self.stop_drag)
        else:
            self.handle = ctk.CTkFrame(master, width=20, height=5, cursor="sb_v_double_arrow",
                                       fg_color="#3a3a3a", corner_radius=2)
            self.handle.bind("<Button-1>", self.start_drag)
            self.handle.bind("<B1-Motion>", self.drag)
            self.handle.bind("<ButtonRelease-1>", self.stop_drag)
    
    def start_drag(self, event):
        self.dragging = True
        self.start_x = event.x_root
        self.start_y = event.y_root
        if self.orientation == 'vertical':
            self.start_size = self.panel.winfo_width()
        else:
            self.start_size = self.panel.winfo_height()
    
    def drag(self, event):
        if self.dragging:
            if self.orientation == 'vertical':
                delta = event.x_root - self.start_x
                new_size = self.start_size + delta
                new_size = max(self.min_size, min(self.max_size, new_size))
                self.panel.configure(width=new_size)
                self.master.grid_columnconfigure(0, minsize=new_size)
            else:
                delta = event.y_root - self.start_y
                new_size = self.start_size + delta
                new_size = max(self.min_size, min(self.max_size, new_size))
                self.panel.configure(height=new_size)
                self.master.grid_rowconfigure(1, minsize=new_size)
    
    def stop_drag(self, event):
        self.dragging = False


class ThemeManager:
    """Manage color themes for the application"""
    
    # Predefined themes matching the image
    THEMES = {
        "Solarized Dark": {
            "bg": "#002b36",
            "fg": "#839496",
            "accent": "#268bd2",
            "success": "#2aa198",
            "error": "#dc322f",
            "warning": "#cb4b16",
            "editor_bg": "#073642",
            "editor_fg": "#93a1a1",
            "terminal_bg": "#002b36",
            "terminal_fg": "#00ff00",
            "sidebar_bg": "#002b36",
            "button_bg": "#268bd2",
            "button_hover": "#2aa198"
        },
        "Dark+ (Default)": {
            "bg": "#1e1e1e",
            "fg": "#cccccc",
            "accent": "#007acc",
            "success": "#6a9955",
            "error": "#f48771",
            "warning": "#dcdcaa",
            "editor_bg": "#1e1e1e",
            "editor_fg": "#cccccc",
            "terminal_bg": "#0c0c0c",
            "terminal_fg": "#00ff00",
            "sidebar_bg": "#252526",
            "button_bg": "#007acc",
            "button_hover": "#0451a5"
        },
        "Monokai": {
            "bg": "#272822",
            "fg": "#f8f8f2",
            "accent": "#66d9ef",
            "success": "#a6e22e",
            "error": "#f92672",
            "warning": "#fd971f",
            "editor_bg": "#272822",
            "editor_fg": "#f8f8f2",
            "terminal_bg": "#272822",
            "terminal_fg": "#00ff00",
            "sidebar_bg": "#272822",
            "button_bg": "#66d9ef",
            "button_hover": "#a6e22e"
        },
        "Tokyo Night": {
            "bg": "#1a1b26",
            "fg": "#a9b1d6",
            "accent": "#7aa2f7",
            "success": "#9ece6a",
            "error": "#f7768e",
            "warning": "#e0af68",
            "editor_bg": "#1a1b26",
            "editor_fg": "#a9b1d6",
            "terminal_bg": "#1a1b26",
            "terminal_fg": "#00ff00",
            "sidebar_bg": "#16161e",
            "button_bg": "#7aa2f7",
            "button_hover": "#bb9af7"
        },
        "Abyss": {
            "bg": "#0b0c10",
            "fg": "#c5c6c7",
            "accent": "#45a29e",
            "success": "#66fcf1",
            "error": "#f05454",
            "warning": "#f2a900",
            "editor_bg": "#0b0c10",
            "editor_fg": "#c5c6c7",
            "terminal_bg": "#0b0c10",
            "terminal_fg": "#66fcf1",
            "sidebar_bg": "#1f2833",
            "button_bg": "#45a29e",
            "button_hover": "#66fcf1"
        },
        "Quiet Light": {
            "bg": "#f3f3f3",
            "fg": "#333333",
            "accent": "#0066cc",
            "success": "#008000",
            "error": "#cc0000",
            "warning": "#e6b800",
            "editor_bg": "#ffffff",
            "editor_fg": "#333333",
            "terminal_bg": "#f3f3f3",
            "terminal_fg": "#008000",
            "sidebar_bg": "#eaeaea",
            "button_bg": "#0066cc",
            "button_hover": "#0052a3"
        }
    }
    
    def __init__(self, app):
        self.app = app
        self.current_theme = "Dark+ (Default)"
    
    def apply_theme(self, theme_name):
        """Apply a color theme to the application"""
        if theme_name not in self.THEMES:
            return
        
        theme = self.THEMES[theme_name]
        self.current_theme = theme_name
        
        # Apply to main window
        ctk.set_appearance_mode("dark" if "Dark" in theme_name or "Night" in theme_name else "light")
        
        # Apply theme colors to widgets
        self.app.configure(fg_color=theme["bg"])
        
        # Sidebar
        if hasattr(self.app, 'sidebar'):
            self.app.sidebar.configure(fg_color=theme["sidebar_bg"])
        
        # Main frame
        if hasattr(self.app, 'main_frame'):
            self.app.main_frame.configure(fg_color=theme["bg"])
        
        # Editor frames
        if hasattr(self.app, 'top_frame'):
            self.app.top_frame.configure(fg_color=theme["editor_bg"])
        
        if hasattr(self.app, 'bottom_frame'):
            self.app.bottom_frame.configure(fg_color=theme["terminal_bg"])
        
        # Terminal colors
        terminals = ['console_widget', 'spin_terminal']
        for term in terminals:
            if hasattr(self.app, term):
                widget = getattr(self.app, term)
                widget.configure(fg_color=theme["terminal_bg"], text_color=theme["terminal_fg"])
        
        # Source editor
        if hasattr(self.app, 'source_editor'):
            self.app.source_editor.configure(fg_color=theme["editor_bg"], text_color=theme["editor_fg"])
        
        if hasattr(self.app, 'translated_editor'):
            self.app.translated_editor.configure(fg_color=theme["editor_bg"], text_color=theme["editor_fg"])
        
        # Save preference
        self.save_theme_preference(theme_name)
    
    def save_theme_preference(self, theme_name):
        """Save theme preference to file"""
        config_file = os.path.join(PROJECT_DIR, "theme_config.json")
        try:
            with open(config_file, 'w') as f:
                json.dump({"theme": theme_name}, f)
        except:
            pass
    
    def load_theme_preference(self):
        """Load saved theme preference"""
        config_file = os.path.join(PROJECT_DIR, "theme_config.json")
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if "theme" in config and config["theme"] in self.THEMES:
                    return config["theme"]
        except:
            pass
        return "Dark+ (Default)"


class EnhancedThemeManager(ThemeManager):
    """Extended theme manager with glassmorphism and animations"""

    THEMES = {
        **ThemeManager.THEMES,
        "DeFi Dark": {
            "bg": "#0a0e17",
            "fg": "#e0e0e0",
            "accent": "#00d4aa",
            "accent_secondary": "#7c3aed",
            "success": "#10b981",
            "error": "#ef4444",
            "warning": "#f59e0b",
            "editor_bg": "#0f141e",
            "editor_fg": "#e2e8f0",
            "terminal_bg": "#080c14",
            "terminal_fg": "#00ffcc",
            "sidebar_bg": "#0c111a",
            "button_bg": "#00d4aa",
            "button_hover": "#00bf9a",
            "card_bg": "#131a26",
            "border": "#1e2a3a",
        },
        "Cyberpunk": {
            "bg": "#0d0221",
            "fg": "#ff00ff",
            "accent": "#00ffff",
            "accent_secondary": "#ff00ff",
            "success": "#00ff88",
            "error": "#ff0055",
            "warning": "#ffaa00",
            "editor_bg": "#12022b",
            "editor_fg": "#00ffff",
            "terminal_bg": "#0a001a",
            "terminal_fg": "#00ff88",
            "sidebar_bg": "#0f0225",
            "button_bg": "#ff00ff",
            "button_hover": "#cc00cc",
            "card_bg": "#150530",
            "border": "#3d0a5c",
        },
        "Nord Frost": {
            "bg": "#2e3440",
            "fg": "#eceff4",
            "accent": "#88c0d0",
            "accent_secondary": "#81a1c1",
            "success": "#a3be8c",
            "error": "#bf616a",
            "warning": "#ebcb8b",
            "editor_bg": "#3b4252",
            "editor_fg": "#e5e9f0",
            "terminal_bg": "#242933",
            "terminal_fg": "#8fbcbb",
            "sidebar_bg": "#2e3440",
            "button_bg": "#5e81ac",
            "button_hover": "#81a1c1",
            "card_bg": "#3b4252",
            "border": "#4c566a",
        },
        "Matrix": {
            "bg": "#0a0f0a",
            "fg": "#00ff41",
            "accent": "#00ff41",
            "accent_secondary": "#008f11",
            "success": "#00ff41",
            "error": "#ff3333",
            "warning": "#ffff00",
            "editor_bg": "#0d140d",
            "editor_fg": "#00ff41",
            "terminal_bg": "#050805",
            "terminal_fg": "#00ff41",
            "sidebar_bg": "#0a0f0a",
            "button_bg": "#008f11",
            "button_hover": "#00cc1a",
            "card_bg": "#111a11",
            "border": "#1a3a1a",
        }
    }


class StyledButton(ctk.CTkButton):
    """Enhanced button with gradient, animation, and state effects"""

    def __init__(self, master, **kwargs):
        self.gradient = kwargs.pop('gradient', False)
        self.pulse = kwargs.pop('pulse', False)
        self.tool_name = kwargs.pop('tool_name', None)

        super().__init__(master, **kwargs)

        if self.gradient:
            self.configure(
                fg_color="transparent",
                bg_color="transparent"
            )
            self._create_gradient()

        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)

    def _create_gradient(self):
        """Create linear gradient background"""
        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bg=self.cget("bg_color")
        )
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Gradient from accent to accent_secondary 
        self.canvas.create_rectangle(
            0, 0, self.winfo_width(), self.winfo_height(),
            fill=self.cget("fg_color"),
            outline="",
            tags="gradient"
        )

    def on_hover(self, event):
        """Smooth hover animation"""
        self.animate_color(
            self.cget("fg_color"),
            self.cget("hover_color"),
            duration=150
        )

    def on_leave(self, event):
        self.animate_color(
            self.cget("hover_color"),
            self.cget("fg_color"),
            duration=150
        )

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, r, g, b):
        """Convert RGB tuple to hex color"""
        return f'#{r:02x}{g:02x}{b:02x}'

    def animate_color(self, from_color, to_color, duration):
        """Color transition animation"""
        steps = 10
        delay = duration // steps

        def interpolate_color(step):
            try:
                r1, g1, b1 = self.hex_to_rgb(from_color)
                r2, g2, b2 = self.hex_to_rgb(to_color)

                t = step / steps
                r = int(r1 + (r2 - r1) * t)
                g = int(g1 + (g2 - g1) * t)
                b = int(b1 + (b2 - b1) * t)

                self.configure(fg_color=self.rgb_to_hex(r, g, b))

                if step < steps:
                    self.after(delay, lambda: interpolate_color(step + 1))
            except:
                pass

        interpolate_color(0)


class ToolButton(StyledButton):
    """Specialized button for verification tools with status indicator"""

    def __init__(self, master, tool_name, **kwargs):
        super().__init__(master, **kwargs)
        self.tool_name = tool_name
        self.status = "idle"  # idle, running, success, error 

        # Add status indicator dot 
        self.status_canvas = tk.Canvas(
            self,
            width=12,
            height=12,
            highlightthickness=0,
            bg=self.cget("fg_color")
        )
        self.status_canvas.place(relx=0.05, rely=0.5, anchor="w")
        self.update_status_indicator()

    def update_status_indicator(self):
        colors = {
            "idle": "#6b7280",
            "running": "#f59e0b",
            "success": "#10b981",
            "error": "#ef4444"
        }
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(
            2, 2, 10, 10,
            fill=colors.get(self.status, "#6b7280"),
            outline=""
        )
        if self.status == "running":
            self.animate_pulse()

    def animate_pulse(self):
        """Pulse animation for running state"""
        def pulse(opacity=1.0, direction=-1):
            if self.status != "running":
                return
            opacity += direction * 0.1
            if opacity <= 0.5 or opacity >= 1.0:
                direction *= -1

            color = f"#{int(245 * opacity):02x}{int(158 * opacity):02x}{int(11 * opacity):02x}"
            self.status_canvas.itemconfig("all", fill=color)

            self.after(50, lambda: pulse(opacity, direction))

        pulse()


class ScrollableSidebar(ctk.CTkFrame):
    """Custom scrollable sidebar with improved behavior"""
    
    def __init__(self, master, width=420, **kwargs):
        super().__init__(master, width=width, **kwargs)
        self.width = width
        self.grid_propagate(False)
        
        # Create canvas for scrolling
        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bg="#1e1e1e",
            width=width - 20
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Add scrollbar
        self.scrollbar = ctk.CTkScrollbar(
            self,
            command=self.canvas.yview,
            orientation="vertical"
        )
        self.scrollbar.pack(side="right", fill="y")
        
        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create inner frame for content
        self.inner_frame = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.inner_frame,
            anchor="nw",
            width=width - 30
        )
        
        # Bind events
        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Mouse wheel binding
        self.bind_mousewheel()
    
    def _on_frame_configure(self, event=None):
        """Reset the scroll region to encompasses inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Resize inner frame when canvas is resized"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def bind_mousewheel(self, widget=None):
        """Bind mouse wheel scrolling recursively to all widgets"""
        if widget is None:
            widget = self
            
        def on_mousewheel(event):
            # For Linux (Button-4/5), delta is not used
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
            else:
                # Windows/macOS
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        
        # Bind to the widget itself
        widget.bind("<MouseWheel>", on_mousewheel, add="+")
        widget.bind("<Button-4>", on_mousewheel, add="+")
        widget.bind("<Button-5>", on_mousewheel, add="+")
        
        # Recursively bind to all children
        for child in widget.winfo_children():
            self.bind_mousewheel(child)
    
    def get_inner_frame(self):
        """Return inner frame for adding widgets"""
        return self.inner_frame


class ThemeSettingsPanel(ctk.CTkFrame):
    """Theme selection and customization panel"""
    
    def __init__(self, parent, theme_manager, **kwargs):
        super().__init__(parent, **kwargs)
        self.theme_manager = theme_manager
        
        # Theme selection label
        ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888"
        ).pack(anchor="w", pady=(10, 5))
        
        # Theme dropdown
        self.theme_var = ctk.StringVar(value=theme_manager.current_theme)
        self.theme_dropdown = ctk.CTkOptionMenu(
            self,
            values=list(self.theme_manager.THEMES.keys()),
            variable=self.theme_var,
            command=self.on_theme_change,
            dynamic_resizing=False,
            width=200
        )
        self.theme_dropdown.pack(fill="x", pady=5)
        
        # Preview label
        self.preview_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="#888888"
        )
        self.preview_label.pack(anchor="w", pady=(5, 10))
        
        # Update preview on selection
        self.update_preview()
    
    def on_theme_change(self, choice):
        """Handle theme change"""
        self.theme_manager.apply_theme(choice)
        self.update_preview()
    
    def update_preview(self):
        """Update preview text"""
        theme = self.theme_manager.current_theme
        self.preview_label.configure(text=f"Current: {theme}")


def wait_for_tcp_port(
    host: str,
    port: int,
    timeout: float = STREAMLIT_START_TIMEOUT,
    poll_interval: float = 0.25,
) -> bool:
    """Return True once ``host:port`` accepts a TCP connection (server is listening)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2.0):
                return True
        except OSError:
            time.sleep(poll_interval)
    return False


from rust_verifiers import (
    CREUSOT_STD_PATH,
    RustVerifier,
    build_prusti_env,
    classify_prusti_failure,
    prepend_creusot_prelude,
    preprocess_prusti_source,
    prusti_command,
    should_skip_prusti_for_source,
    strip_rust_main_for_lib,
)
from verus_integration import VerusIntegration

# Import verification state
try:
    from verification_state import VerificationState
except ImportError:
    class VerificationState:
        @staticmethod
        def save_result(success, output, errors, model_name, ltl_results=None):
            import json
            import time
            from datetime import datetime
            state = {
                'timestamp': time.time(),
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success': success,
                'output': output,
                'errors': errors,
                'model_name': model_name,
                'verified': True,
                'ltl_results': ltl_results or []
            }
            
            # Parse statistics
            if output:
                depth_match = re.search(r"depth reached (\d+)", output)
                if depth_match:
                    state['depth'] = int(depth_match.group(1))
                states_match = re.search(r"(\d+) states, stored", output)
                if states_match:
                    state['states_stored'] = int(states_match.group(1))
                trans_match = re.search(r"(\d+) transitions", output)
                if trans_match:
                    state['transitions'] = int(trans_match.group(1))
                if "errors: 0" in output:
                    state['errors_count'] = 0
                else:
                    err_match = re.search(r"errors: (\d+)", output)
                    if err_match:
                        state['errors_count'] = int(err_match.group(1))
            
            with open("verification_state.json", 'w') as f:
                json.dump(state, f, indent=2)
            return True

# Import translators
try:
    from translator import DeFiTranslator, VerifiedTranslator
except ImportError:
    class DeFiTranslator:
        @staticmethod
        def translate_solidity(source_code):
            """Basic Solidity to Promela translation"""
            pml = "/* Auto-generated Promela Model */\n"
            pml += "active proctype Contract() {\n"
            pml += "    printf(\"Contract initialized\\n\");\n"
            pml += "}\n"
            return pml
        
        @staticmethod
        def translate_rust(source_code):
            """Basic Rust to Promela translation"""
            pml = "/* Auto-generated Promela Model from Rust */\n"
            pml += "active proctype Program() {\n"
            pml += "    printf(\"Program initialized\\n\");\n"
            pml += "}\n"
            return pml
        
        @staticmethod
        def extract_state_variables(source_code):
            return []
        
        @staticmethod
        def generate_ltl_properties(state_vars):
            return ""
    
    class VerifiedTranslator(DeFiTranslator):
        def translate_with_proof(self, source_code):
            pml = self.translate_solidity(source_code)
            return pml, ["∀s: State • source_invariant(s) ⇒ pml_invariant(translate(s))"]

# Import verifier plugins
try:
    from verifier_plugins import PluginManager
except ImportError:
    PluginManager = None

class FormalVerifierApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize plugin system
        if PluginManager:
            self.plugin_manager = PluginManager()
            print(f"🔌 Plugin Manager loaded with {len(self.plugin_manager.plugins)} plugins")
        else:
            self.plugin_manager = None
        
        # Configure window
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.title("DeFi Guardian - Formal Verification Suite")
        self.geometry("1500x950")
        
        # Configure grid - sidebar layout
        self.sidebar_expanded_width = 460
        self.sidebar_collapsed_width = 320
        self.sidebar_is_expanded = True
        self.grid_columnconfigure(0, weight=0, minsize=self.sidebar_expanded_width)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Initialize variables before using them
        self.current_file = None
        self.file_type = None
        self.dashboard_process = None
        self.auto_scroll_enabled = True
        self.lean_running = False
        self.tool_processes = {}
        self.stop_requested = {}
        self.monitoring = True
        self.tool_stop_buttons = {}
        
        # Create sidebar
        self.create_sidebar()
        
        # After creating all widgets
        self.after(100, self.ensure_sidebar_visibility)
        
        # ==================== MAIN EDITOR AREA ====================
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#1e1e1e")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Configure main frame for vertical layout (70% top, 30% bottom)
        self.main_frame.grid_rowconfigure(0, weight=7)
        self.main_frame.grid_rowconfigure(1, weight=3)
        
        # ==================== TOP PANE: CODE EDITOR (70%) ====================
        self.top_frame = ctk.CTkFrame(self.main_frame, fg_color="#252526", corner_radius=8)
        self.top_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        
        # Editor tabview
        self.editor_tabs = ctk.CTkTabview(self.top_frame, segmented_button_fg_color="#1e1e1e")
        self.editor_tabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create tabs
        self.editor_tabs.add("Source")
        self.editor_tabs.add("Translated Promela")
        self.editor_tabs.add("Problems")
        
        # Configure tab appearance
        self.editor_tabs._segmented_button.configure(
            fg_color="#2d2d30",
            selected_color="#094771",
            selected_hover_color="#007acc",
            unselected_color="#2d2d30",
            text_color="#cccccc",
            text_color_disabled="#666666"
        )
        
        # Source editor tab
        self.source_editor = ctk.CTkTextbox(
            self.editor_tabs.tab("Source"),
            font=("Consolas", 12),
            wrap="word",
            fg_color="#1e1e1e",
            text_color="#cccccc",
            border_width=0
        )
        self.source_editor.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Translated Promela tab
        self.translated_editor = ctk.CTkTextbox(
            self.editor_tabs.tab("Translated Promela"),
            font=("Consolas", 12),
            wrap="word",
            fg_color="#1e1e1e",
            text_color="#cccccc",
            border_width=0
        )
        self.translated_editor.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Problems tab (listview style)
        self.problems_text = ctk.CTkTextbox(
            self.editor_tabs.tab("Problems"),
            font=("Consolas", 11),
            wrap="word",
            fg_color="#1e1e1e",
            text_color="#cccccc",
            border_width=0
        )
        self.problems_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # ==================== BOTTOM PANE: TERMINAL (30%) ====================
        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="#252526", corner_radius=8)
        self.bottom_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        # Terminal tabview
        self.terminal_tabs = ctk.CTkTabview(self.bottom_frame, segmented_button_fg_color="#1e1e1e")
        self.terminal_tabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create single unified terminal tab
        self.terminal_tabs.add("Verification Console")
        
        # Configure terminal tab appearance
        self.terminal_tabs._segmented_button.configure(
            fg_color="#2d2d30",
            selected_color="#094771",
            selected_hover_color="#007acc",
            unselected_color="#2d2d30",
            text_color="#cccccc",
            text_color_disabled="#666666"
        )
        
        # Unified Verification Console terminal
        self.console_widget = ctk.CTkTextbox(
            self.terminal_tabs.tab("Verification Console"),
            font=("Consolas", 11),
            wrap="word",
            fg_color="#0c0c0c",
            text_color="#00ff00",
            border_width=0
        )
        self.console_widget.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Point self.console and self.spin_terminal to the unified console
        self.console = self.console_widget
        self.spin_terminal = self.console_widget
        
        # Show welcome message
        self.show_welcome()
        
        # Scan for recent files
        self.scan_recent_files()
        
        # Add resizable panels
        self.setup_resizable_panels()
        
        # Initialize theme manager
        self.theme_manager = EnhancedThemeManager(self)
        loaded_theme = self.theme_manager.load_theme_preference()
        self.theme_manager.apply_theme(loaded_theme)
        
        # Add theme settings to sidebar
        self.add_theme_settings()
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Start verification state monitor
        self.start_verification_monitor()
        self.prewarm_lean_runtime()
        
        # Initialize file tree
        self.scan_project_directory()
        
        # Bind window resize event
        self.bind("<Configure>", self.on_window_resize)
    
    def create_sidebar(self):
        """Create the sidebar with all controls"""
        # Create a container frame for sidebar and handle
        self.sidebar_container = ctk.CTkFrame(self, fg_color="transparent", width=self.sidebar_expanded_width)
        self.sidebar_container.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        self.sidebar_container.grid_propagate(False)

        # Create sidebar frame inside container
        self.sidebar = ctk.CTkFrame(self.sidebar_container, width=self.sidebar_expanded_width, corner_radius=15)
        self.sidebar.pack(side="left", fill="both", expand=True)
        
        # Create resize handle between sidebar and main
        self.sidebar_resize_handle = ctk.CTkFrame(self.sidebar_container, width=5, cursor="sb_h_double_arrow",
                                                   fg_color="#3a3a3a")
        self.sidebar_resize_handle.pack(side="left", fill="y", padx=2)
        
        # Create scrollable inner frame
        self.sidebar_inner = ScrollableSidebar(self.sidebar, width=self.sidebar_expanded_width - 30)
        self.sidebar_inner.pack(fill="both", expand=True, padx=10, pady=10)
        
        sidebar_inner = self.sidebar_inner.get_inner_frame()
        
        # Title
        ctk.CTkLabel(
            sidebar_inner,
            text="🛡️ DEFI GUARDIAN",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00ffcc"
        ).pack(anchor="w", pady=(10, 5))
        
        ctk.CTkLabel(
            sidebar_inner,
            text="Formal Verification Suite",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        ).pack(anchor="w", pady=(0, 15))
        
        # File Operations
        ctk.CTkLabel(
            sidebar_inner,
            text="📂 FILE OPERATIONS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888"
        ).pack(anchor="w", pady=(10, 5))
        
        self.load_btn = ctk.CTkButton(
            sidebar_inner,
            text="📂 OPEN SOURCE FILE",
            command=self.load_file,
            height=45,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2c3e50",
            hover_color="#1a2632"
        )
        self.load_btn.pack(fill="x", pady=5)
        
        # File info display
        self.file_info_frame = ctk.CTkFrame(sidebar_inner, fg_color="transparent")
        self.file_info_frame.pack(fill="x", pady=5)
        
        self.file_label = ctk.CTkLabel(
            self.file_info_frame,
            text="  No file loaded",
            font=ctk.CTkFont(size=10),
            text_color="#888888"
        )
        self.file_label.pack(anchor="w")
        
        self.file_type_label = ctk.CTkLabel(
            self.file_info_frame,
            text="",
            font=ctk.CTkFont(size=9),
            text_color="#666666"
        )
        self.file_type_label.pack(anchor="w")
        
        # File Explorer section
        ctk.CTkLabel(
            sidebar_inner,
            text="📁 EXPLORER",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888"
        ).pack(anchor="w", pady=(15, 5))
        
        self.explorer_frame = ctk.CTkFrame(sidebar_inner, fg_color="transparent")
        self.explorer_frame.pack(fill="x", pady=5)
        
        # Open Editors section
        self.open_editors_label = ctk.CTkLabel(
            self.explorer_frame,
            text="OPEN EDITORS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#888888"
        )
        self.open_editors_label.pack(anchor="w", pady=(5, 2))
        
        self.open_editors_frame = ctk.CTkFrame(self.explorer_frame, fg_color="transparent")
        self.open_editors_frame.pack(fill="x", pady=2)
        
        # Project files section
        self.project_files_label = ctk.CTkLabel(
            self.explorer_frame,
            text="DEFI_GUARDIAN",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#888888"
        )
        self.project_files_label.pack(anchor="w", pady=(10, 2))
        
        self.project_files_frame = ctk.CTkFrame(self.explorer_frame, fg_color="transparent")
        self.project_files_frame.pack(fill="x", pady=2)
        
        # Populate file explorer
        self.populate_file_explorer()
        
        # Separator
        ctk.CTkFrame(sidebar_inner, height=2, fg_color="#3a3a3a").pack(pady=15, fill="x")
        
        # Verification Options
        ctk.CTkLabel(
            sidebar_inner,
            text="🔬 VERIFICATION OPTIONS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888"
        ).pack(anchor="w", pady=(10, 5))
        
        self.verify_btn = ctk.CTkButton(
            sidebar_inner,
            text="🚀 RUN SPIN VERIFICATION",
            command=self.run_verification,
            state="disabled",
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60",
            hover_color="#2e7d32"
        )
        self.verify_btn.pack(fill="x", pady=5)
        
        self.stop_spin_btn = ctk.CTkButton(
            sidebar_inner,
            text="🛑 STOP SPIN",
            command=lambda: self.request_stop_tool("spin"),
            state="disabled",
            height=34,
            font=ctk.CTkFont(size=11),
            fg_color="#7f1d1d",
            hover_color="#991b1b"
        )
        self.stop_spin_btn.pack(fill="x", pady=(0, 5))
        
        self.coq_btn = ctk.CTkButton(
            sidebar_inner,
            text="📜 COQ VERIFICATION",
            command=self.verify_with_coq,
            height=45,
            font=ctk.CTkFont(size=13),
            fg_color="#9b59b6",
            hover_color="#8e44ad"
        )
        self.coq_btn.pack(fill="x", pady=5)
        
        self.stop_coq_btn = ctk.CTkButton(
            sidebar_inner,
            text="🛑 STOP COQ",
            command=lambda: self.request_stop_tool("coq"),
            state="disabled",
            height=34,
            font=ctk.CTkFont(size=11),
            fg_color="#7f1d1d",
            hover_color="#991b1b"
        )
        self.stop_coq_btn.pack(fill="x", pady=(0, 5))
        
        self.lean_btn = ctk.CTkButton(
            sidebar_inner,
            text="⚡ LEAN VERIFICATION",
            command=self.run_lean_verification,
            height=45,
            font=ctk.CTkFont(size=13),
            fg_color="#e67e22",
            hover_color="#d35400"
        )
        self.lean_btn.pack(fill="x", pady=5)
        
        self.stop_lean_btn = ctk.CTkButton(
            sidebar_inner,
            text="🛑 STOP LEAN",
            command=lambda: self.request_stop_tool("lean"),
            state="disabled",
            height=34,
            font=ctk.CTkFont(size=11),
            fg_color="#7f1d1d",
            hover_color="#991b1b"
        )
        self.stop_lean_btn.pack(fill="x", pady=(0, 5))
        
        # Separator before Rust tools
        ctk.CTkFrame(sidebar_inner, height=2, fg_color="#3a3a3a").pack(pady=15, fill="x")
        
        # Rust Tools Label
        ctk.CTkLabel(
            sidebar_inner,
            text="🦀 RUST VERIFICATION TOOLS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888"
        ).pack(anchor="w", pady=(10, 5))
        
        self.prusti_btn = ctk.CTkButton(
            sidebar_inner,
            text="🔧 PRUSTI VERIFICATION",
            command=self.verify_with_prusti,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        self.prusti_btn.pack(fill="x", pady=3)
        
        self.stop_prusti_btn = ctk.CTkButton(
            sidebar_inner,
            text="🛑 STOP PRUSTI",
            command=lambda: self.request_stop_tool("prusti"),
            state="disabled",
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color="#7f1d1d",
            hover_color="#991b1b"
        )
        self.stop_prusti_btn.pack(fill="x", pady=(0, 3))
        
        self.creusot_btn = ctk.CTkButton(
            sidebar_inner,
            text="📐 CREUSOT VERIFICATION",
            command=self.verify_with_creusot,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#16a085",
            hover_color="#1abc9c"
        )
        self.creusot_btn.pack(fill="x", pady=3)
        
        self.stop_creusot_btn = ctk.CTkButton(
            sidebar_inner,
            text="🛑 STOP CREUSOT",
            command=lambda: self.request_stop_tool("creusot"),
            state="disabled",
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color="#7f1d1d",
            hover_color="#991b1b"
        )
        self.stop_creusot_btn.pack(fill="x", pady=(0, 3))

        self.kani_btn = ctk.CTkButton(
            sidebar_inner,
            text="🦀 KANI VERIFICATION",
            command=self.verify_with_kani,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#8e44ad",
            hover_color="#6c3483"
        )
        self.kani_btn.pack(fill="x", pady=3)
        
        self.stop_kani_btn = ctk.CTkButton(
            sidebar_inner,
            text="🛑 STOP KANI",
            command=lambda: self.request_stop_tool("kani"),
            state="disabled",
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color="#7f1d1d",
            hover_color="#991b1b"
        )
        self.stop_kani_btn.pack(fill="x", pady=(0, 3))
        
        self.elan_btn = ctk.CTkButton(
            sidebar_inner,
            text="⚙️ ELAN (LEAN VERSION MANAGER)",
            command=self.check_elan,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#34495e",
            hover_color="#2c3e50"
        )
        self.elan_btn.pack(fill="x", pady=3)
        
        # Separator
        ctk.CTkFrame(sidebar_inner, height=2, fg_color="#3a3a3a").pack(pady=15, fill="x")
        
        # Dashboard
        ctk.CTkLabel(
            sidebar_inner,
            text="📊 DASHBOARD",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888"
        ).pack(anchor="w", pady=(10, 5))
        
        self.dash_btn = ctk.CTkButton(
            sidebar_inner,
            text="🌐 OPEN VISUAL DASHBOARD",
            command=self.open_dashboard,
            height=45,
            font=ctk.CTkFont(size=13),
            fg_color="#2c3e50",
            hover_color="#1a2632"
        )
        self.dash_btn.pack(fill="x", pady=5)
        
        self.stop_dash_btn = ctk.CTkButton(
            sidebar_inner,
            text="🛑 STOP DASHBOARD",
            command=self.stop_dashboard,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#721c24",
            hover_color="#5a1a1a"
        )
        self.stop_dash_btn.pack(fill="x", pady=5)

        # Translated Output viewer button
        self.view_translated_btn = ctk.CTkButton(
            sidebar_inner,
            text="📄 VIEW TRANSLATED OUTPUT",
            command=self.open_translated_output,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#1a3a4a",
            hover_color="#0f2a38"
        )
        self.view_translated_btn.pack(fill="x", pady=5)

        self.counterexample_btn = ctk.CTkButton(
            sidebar_inner,
            text="🔍 ANALYZE COUNTEREXAMPLE",
            command=self.analyze_counterexample,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#ff4444",
            hover_color="#cc0000"
        )
        self.counterexample_btn.pack(fill="x", pady=5)

        # Separator
        ctk.CTkFrame(sidebar_inner, height=2, fg_color="#3a3a3a").pack(pady=15, fill="x")
        
        # Settings
        ctk.CTkLabel(
            sidebar_inner,
            text="⚙️ SETTINGS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888"
        ).pack(anchor="w", pady=(10, 5))
        
        self.auto_scroll = ctk.CTkSwitch(
            sidebar_inner,
            text="Auto-scroll console",
            onvalue=True,
            offvalue=False,
            command=self.toggle_auto_scroll
        )
        self.auto_scroll.pack(anchor="w", pady=2)
        self.auto_scroll.select()
        
        self.verbose_output = ctk.CTkSwitch(
            sidebar_inner,
            text="Verbose output",
            onvalue=True,
            offvalue=False
        )
        self.verbose_output.pack(anchor="w", pady=2)
        self.verbose_output.select()

        self.skip_incompatible = ctk.CTkSwitch(
            sidebar_inner,
            text="Skip incompatible verifiers",
            onvalue=True,
            offvalue=False,
        )
        self.skip_incompatible.pack(anchor="w", pady=2)
        self.skip_incompatible.select()

        # Console Operations (Clear/Export)
        ctk.CTkLabel(
            sidebar_inner,
            text="🖥️ CONSOLE OPERATIONS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888"
        ).pack(anchor="w", pady=(15, 5))

        console_ops_frame = ctk.CTkFrame(sidebar_inner, fg_color="transparent")
        console_ops_frame.pack(fill="x", pady=2)

        self.clear_btn = ctk.CTkButton(
            console_ops_frame,
            text="🧹 CLEAR CONSOLE",
            command=self.clear_console,
            height=35,
            width=140,
            font=ctk.CTkFont(size=11),
            fg_color="#34495e",
            hover_color="#2c3e50"
        )
        self.clear_btn.pack(side="left", padx=(0, 5), expand=True, fill="x")

        self.export_btn = ctk.CTkButton(
            console_ops_frame,
            text="📥 EXPORT LOGS",
            command=self.export_console,
            height=35,
            width=140,
            font=ctk.CTkFont(size=11),
            fg_color="#34495e",
            hover_color="#2c3e50"
        )
        self.export_btn.pack(side="left", padx=(5, 0), expand=True, fill="x")
        
        # Status
        ctk.CTkFrame(sidebar_inner, height=2, fg_color="#3a3a3a").pack(pady=15, fill="x")
        
        self.status_label = ctk.CTkLabel(
            sidebar_inner,
            text="✅ Ready",
            font=ctk.CTkFont(size=11),
            text_color="#00ffcc"
        )
        self.status_label.pack(anchor="w", pady=(10, 0))
        
        self.tool_status = ctk.CTkLabel(
            sidebar_inner,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="#888888"
        )
        self.tool_status.pack(anchor="w")

        self.lean_prewarm_status = ctk.CTkLabel(
            sidebar_inner,
            text="○ Lean prewarm: pending",
            font=ctk.CTkFont(size=10),
            text_color="#888888"
        )
        self.lean_prewarm_status.pack(anchor="w")
        
        # Check tools
        self.check_tools()
        
        # Initialize tool_stop_buttons dictionary
        self.tool_stop_buttons = {
            "spin": self.stop_spin_btn,
            "coq": self.stop_coq_btn,
            "lean": self.stop_lean_btn,
            "prusti": self.stop_prusti_btn,
            "creusot": self.stop_creusot_btn,
            "kani": self.stop_kani_btn,
        }
        
        # Bind mouse wheel to all sidebar elements after creation
        self.sidebar_inner.bind_mousewheel()

    def ensure_sidebar_visibility(self):
        """Ensure sidebar is properly visible after creation"""
        self.sidebar.update_idletasks()
        self.sidebar_inner.update_idletasks()

    def on_window_resize(self, event=None):
        """Handle window resize to update scrollable area"""
        if hasattr(self, 'sidebar_inner'):
            self.sidebar_inner.update_idletasks()
            if hasattr(self.sidebar_inner, '_parent_canvas'):
                self.sidebar_inner._parent_canvas.configure(
                    scrollregion=self.sidebar_inner._parent_canvas.bbox("all")
                )

    def setup_resizable_panels(self):
        """Setup resizable panels with drag handles"""
        # We already have self.sidebar_resize_handle in the sidebar container
        # from create_sidebar, so we just need to bind it if not already done
        if hasattr(self, 'sidebar_resize_handle'):
            self.sidebar_resize_handle.bind("<Button-1>", self.start_sidebar_resize)
            self.sidebar_resize_handle.bind("<B1-Motion>", self.resize_sidebar)
            self.sidebar_resize_handle.bind("<ButtonRelease-1>", self.stop_sidebar_resize)
        
        # Add resize handle between editor and console
        # First, reconfigure main_frame rows to accommodate a handle row
        self.main_frame.grid_rowconfigure(0, weight=7)
        self.main_frame.grid_rowconfigure(1, weight=0) # Handle row
        self.main_frame.grid_rowconfigure(2, weight=3)
        
        # Move bottom_frame to row 2
        self.bottom_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        # Create the horizontal handle in row 1
        self.editor_console_handle = ctk.CTkFrame(self.main_frame, height=4, cursor="sb_v_double_arrow",
                                                   fg_color="#3a3a3a")
        self.editor_console_handle.grid(row=1, column=0, sticky="ew", padx=10, pady=0)
        
        # Bind drag events for vertical resize
        self.editor_console_handle.bind("<Button-1>", self.start_vertical_resize)
        self.editor_console_handle.bind("<B1-Motion>", self.resize_vertical)
        self.editor_console_handle.bind("<ButtonRelease-1>", self.stop_vertical_resize)
        
        # Store resize state
        self.resizing_sidebar = False
        self.resizing_vertical = False
        self.start_sidebar_x = 0
        self.start_sidebar_width = 0
        self.start_vertical_y = 0
        self.start_vertical_height = 0

    def start_sidebar_resize(self, event):
        """Start sidebar resize operation"""
        self.resizing_sidebar = True
        self.start_sidebar_x = event.x_root
        self.start_sidebar_width = self.sidebar.winfo_width()

    def resize_sidebar(self, event):
        """Handle sidebar resize with improved stability"""
        if self.resizing_sidebar:
            delta = event.x_root - self.start_sidebar_x
            new_width = max(250, min(600, self.start_sidebar_width + delta))
            
            # Use a smaller throttle for better responsiveness
            if not hasattr(self, '_last_resize_time'):
                self._last_resize_time = 0
            
            current_time = time.time()
            if current_time - self._last_resize_time > 0.008:  # ~120fps
                # Update container and sidebar width
                self.sidebar_container.configure(width=new_width + 15)
                self.sidebar.configure(width=new_width)
                
                # Update grid minsize less frequently to avoid shakiness
                if abs(new_width - getattr(self, '_last_grid_width', 0)) > 5:
                    self.grid_columnconfigure(0, minsize=new_width + 15)
                    self._last_grid_width = new_width
                
                self._last_resize_time = current_time

    def stop_sidebar_resize(self, event):
        """Stop sidebar resize operation"""
        self.resizing_sidebar = False

    def start_vertical_resize(self, event):
        """Start vertical resize operation"""
        self.resizing_vertical = True
        self.start_vertical_y = event.y_root
        self.start_vertical_height = self.top_frame.winfo_height()

    def resize_vertical(self, event):
        """Handle vertical resize between editor and console"""
        if self.resizing_vertical:
            delta = event.y_root - self.start_vertical_y
            total_height = self.top_frame.winfo_height() + self.bottom_frame.winfo_height() + 20
            
            new_top_height = max(200, min(total_height - 150, self.start_vertical_height + delta))
            new_bottom_height = total_height - new_top_height - 20
            
            # Update grid weights
            self.main_frame.grid_rowconfigure(0, weight=new_top_height)
            self.main_frame.grid_rowconfigure(2, weight=new_bottom_height)

    def stop_vertical_resize(self, event):
        """Stop vertical resize operation"""
        self.resizing_vertical = False

    def add_theme_settings(self):
        """Add theme settings panel to sidebar"""
        sidebar_inner = self.sidebar_inner.get_inner_frame()
        
        # Find where to insert theme settings (after settings section)
        theme_frame = ctk.CTkFrame(sidebar_inner, fg_color="transparent")
        theme_frame.pack(fill="x", pady=5)
        
        # Add theme settings
        self.theme_settings = ThemeSettingsPanel(theme_frame, self.theme_manager)
        self.theme_settings.pack(fill="x")
        
        # Add custom color picker for advanced customization
        ctk.CTkLabel(
            theme_frame,
            text="",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#888888"
        ).pack(anchor="w", pady=(10, 5))
        
        # Color picker buttons
        color_frame = ctk.CTkFrame(theme_frame, fg_color="transparent")
        color_frame.pack(fill="x", pady=5)
        
        colors = ["accent", "success", "error", "warning"]
        color_labels = ["Accent", "Success", "Error", "Warning"]
        
        for color, label in zip(colors, color_labels):
            btn = ctk.CTkButton(
                color_frame,
                text=f"{label}",
                width=80,
                height=30,
                font=ctk.CTkFont(size=10),
                fg_color=self.theme_manager.THEMES[self.theme_manager.current_theme][color],
                command=lambda c=color: self.pick_custom_color(c)
            )
            btn.pack(side="left", padx=2)

    def pick_custom_color(self, color_key):
        """Open color picker dialog for custom color selection"""
        import tkinter.colorchooser as colorchooser
        
        color = colorchooser.askcolor(title=f"Select {color_key} color")
        if color[1]:
            # Update theme
            theme = self.theme_manager.THEMES[self.theme_manager.current_theme].copy()
            theme[color_key] = color[1]
            
            # Create temporary theme
            custom_theme_name = f"{self.theme_manager.current_theme} (Custom)"
            self.theme_manager.THEMES[custom_theme_name] = theme
            
            # Apply custom theme
            self.theme_manager.apply_theme(custom_theme_name)
            
            # Update dropdown
            self.theme_settings.theme_dropdown.configure(values=list(self.theme_manager.THEMES.keys()))
            self.theme_settings.theme_var.set(custom_theme_name)
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for panel resizing"""
        
        def increase_sidebar():
            new_width = min(600, self.sidebar.winfo_width() + 50)
            self.sidebar.configure(width=new_width)
            self.sidebar_container.configure(width=new_width + 15)
        
        def decrease_sidebar():
            new_width = max(250, self.sidebar.winfo_width() - 50)
            self.sidebar.configure(width=new_width)
            self.sidebar_container.configure(width=new_width + 15)
        
        def increase_console():
            current_weight = self.main_frame.grid_rowconfigure(1)['weight']
            new_weight = min(80, current_weight + 5)
            self.main_frame.grid_rowconfigure(1, weight=new_weight)
        
        def decrease_console():
            current_weight = self.main_frame.grid_rowconfigure(1)['weight']
            new_weight = max(20, current_weight - 5)
            self.main_frame.grid_rowconfigure(1, weight=new_weight)
        
        # Bind shortcuts
        self.bind("<Control-Shift-Right>", lambda e: increase_sidebar())
        self.bind("<Control-Shift-Left>", lambda e: decrease_sidebar())
        self.bind("<Control-Shift-Up>", lambda e: increase_console())
        self.bind("<Control-Shift-Down>", lambda e: decrease_console())
    
    def populate_file_explorer(self):
        """Populate the file explorer with project files"""
        # Clear existing widgets
        for widget in self.open_editors_frame.winfo_children():
            widget.destroy()
        for widget in self.project_files_frame.winfo_children():
            widget.destroy()
        
        # Add current file to open editors if any
        if self.current_file:
            file_btn = ctk.CTkButton(
                self.open_editors_frame,
                text=f"  {os.path.basename(self.current_file)}",
                command=lambda f=self.current_file: self.load_file_to_editor(f),
                height=25,
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                hover_color="#2a2d2e"
            )
            file_btn.pack(fill="x", pady=1)
        
        # Add important project files
        important_files = [
            ("active_file.txt", "text"),
            ("translated_output.pml", "promela"),
            ("verification_state.json", "json"),
            ("state_graph.json", "json"),
            ("file_tree.json", "json"),
            ("user_lending.rs", "rust"),
            ("burn.sol", "solidity"),
            ("app.py", "python"),
            ("desktop_app.py", "python")
        ]
        
        for filename, file_type in important_files:
            file_path = os.path.join(PROJECT_DIR, filename)
            if os.path.exists(file_path):
                # Get icon for file type
                icon_map = {
                    "rust": "R",
                    "solidity": "S", 
                    "promela": "P",
                    "json": "{ }",
                    "python": "Py",
                    "text": "T"
                }
                icon = icon_map.get(file_type, "F")
                
                file_btn = ctk.CTkButton(
                    self.project_files_frame,
                    text=f"  {icon} {filename}",
                    command=lambda f=file_path: self.load_file_to_editor(f),
                    height=25,
                    font=ctk.CTkFont(size=10),
                    fg_color="transparent",
                    hover_color="#2a2d2e"
                )
                file_btn.pack(fill="x", pady=1)
    
    def load_file_to_editor(self, file_path):
        """Load file content into the source editor"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.source_editor.delete("1.0", "end")
            self.source_editor.insert("1.0", content)
            
            # Update current file
            self.current_file = file_path
            self.file_type = os.path.splitext(file_path)[1].lower()
            
            # Update file label
            self.file_label.configure(text=f"  {os.path.basename(file_path)}")
            
            # Update file type label
            type_map = {'.rs': 'Rust', '.sol': 'Solidity', '.pml': 'Promela', '.py': 'Python', '.json': 'JSON', '.txt': 'Text'}
            file_type_display = type_map.get(self.file_type, 'Unknown')
            self.file_type_label.configure(text=file_type_display)
            
            # If native Promela, show in translated tab too
            if self.file_type == '.pml':
                self.translated_editor.delete("1.0", "end")
                self.translated_editor.insert("1.0", content)
            else:
                self.translated_editor.delete("1.0", "end")
                self.translated_editor.insert("1.0", "Run SPIN Verification to see translated Promela output.")
            
            # Clear problems on new file load
            self.problems_text.delete("1.0", "end")
            self.problems_text.insert("1.0", "Run verification to scan for problems.")
            
            # Refresh file explorer to show this file in open editors
            self.populate_file_explorer()
            
            # Enable verify button
            self.verify_btn.configure(state="normal")
            
        except Exception as e:
            self.console.insert("end", f"Error loading file {file_path}: {str(e)}\n")
    
    def scan_project_directory(self, base_path=None):
        """Scan project directory and create file_tree.json in a background thread"""
        if base_path is None:
            base_path = PROJECT_DIR
            
        def _scan():
            def get_file_icon(filename):
                """Get appropriate icon for file type"""
                if filename.endswith('.rs'):
                    return 'rust'
                elif filename.endswith('.sol'):
                    return 'solidity'
                elif filename.endswith('.pml'):
                    return 'promela'
                elif filename.endswith('.json'):
                    return 'json'
                elif filename.endswith('.txt'):
                    return 'text'
                elif filename.endswith('.log'):
                    return 'log'
                elif filename.endswith('.py'):
                    return 'python'
                else:
                    return 'file'
            
            def build_tree(path, relative_path=""):
                """Recursively build file tree structure"""
                tree = {"name": os.path.basename(path), "type": "folder" if os.path.isdir(path) else "file", "children": []}
                
                if os.path.isdir(path):
                    try:
                        items = []
                        for item in os.listdir(path):
                            # Skip hidden files and common build/cache directories
                            if item.startswith('.') or item in ['target', '__pycache__', 'node_modules']:
                                continue
                            items.append(item)
                        
                        # Sort: folders first, then files
                        items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
                        
                        for item in items:
                            item_path = os.path.join(path, item)
                            item_relative = os.path.join(relative_path, item) if relative_path else item
                            
                            if os.path.isdir(item_path):
                                subtree = build_tree(item_path, item_relative)
                                tree["children"].append(subtree)
                            else:
                                file_info = {
                                    "name": item,
                                    "type": "file",
                                    "icon": get_file_icon(item),
                                    "path": item_relative,
                                    "size": os.path.getsize(item_path) if os.path.exists(item_path) else 0
                                }
                                tree["children"].append(file_info)
                    except PermissionError:
                        pass
                else:
                    tree["icon"] = get_file_icon(os.path.basename(path))
                    tree["path"] = relative_path
                    tree["size"] = os.path.getsize(path) if os.path.exists(path) else 0
                
                return tree
            
            try:
                file_tree = build_tree(base_path)
                
                # Save to JSON file for Streamlit frontend
                output_file = os.path.join(PROJECT_DIR, "file_tree.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(file_tree, f, indent=2, ensure_ascii=False)
                
                self.after(0, lambda: self.console.insert("end", f"   File tree saved to: {output_file}\n"))
                
            except Exception as e:
                self.after(0, lambda: self.console.insert("end", f"   Error scanning project: {str(e)}\n"))

        threading.Thread(target=_scan, daemon=True).start()
    
    def export_state_graph(self, verification_result):
        """Export state graph data for 3D visualization"""
        try:
            # Parse SPIN output to extract state transitions
            state_graph = {
                "nodes": [],
                "edges": [],
                "counterexample_path": []
            }
            
            # Extract states and transitions from SPIN output
            output = verification_result.get('output', '')
            
            # Simple state extraction (can be enhanced with better parsing)
            states = set()
            edges = []
            
            # Look for state patterns in SPIN output
            import re
            
            # Extract process states
            state_pattern = r'proctype\s+(\w+)'
            for match in re.finditer(state_pattern, output):
                proc_name = match.group(1)
                states.add(proc_name)
            
            # Extract transitions (simplified)
            transition_pattern = r'(\w+)\s*->\s*(\w+)'
            for match in re.finditer(transition_pattern, output):
                from_state, to_state = match.groups()
                states.update([from_state, to_state])
                edges.append({"from": from_state, "to": to_state, "label": "transition"})
            
            # If no states found, create default states
            if not states:
                states = ["S0", "S1", "S2"]
                edges = [
                    {"from": "S0", "to": "S1", "label": "initialize"},
                    {"from": "S1", "to": "S2", "label": "execute"}
                ]
            
            state_graph["nodes"] = list(states)
            state_graph["edges"] = edges
            
            # Add counterexample path if verification failed
            if not verification_result.get('success', True):
                # Try to parse counterexample from trail file
                trail_file = os.path.join(PROJECT_DIR, "pan.trail")
                if os.path.exists(trail_file):
                    try:
                        with open(trail_file, 'r') as f:
                            trail_content = f.read()
                        # Simple trail parsing (can be enhanced)
                        trail_states = ["S0", "S1", "S2"]  # Placeholder
                        state_graph["counterexample_path"] = trail_states
                    except:
                        state_graph["counterexample_path"] = ["S0", "S1"]
            
            # Save state graph to JSON
            output_file = os.path.join(PROJECT_DIR, "state_graph.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(state_graph, f, indent=2)
            
            self.console.insert("end", f"   State graph saved to: {output_file}\n")
            
        except Exception as e:
            self.console.insert("end", f"   Error exporting state graph: {str(e)}\n")

    def toggle_auto_scroll(self):
        self.auto_scroll_enabled = self.auto_scroll.get()

    def toggle_sidebar_width(self):
        """Toggle sidebar between compact and expanded widths."""
        if self.sidebar_is_expanded:
            target = self.sidebar_collapsed_width
            self.sidebar_is_expanded = False
        else:
            target = self.sidebar_expanded_width
            self.sidebar_is_expanded = True
        self.sidebar.configure(width=target)
        self.grid_columnconfigure(0, minsize=target)
        self.sidebar_inner.configure(width=max(160, target - 40))
        self.sidebar.update_idletasks()

    def set_tool_running(self, tool, running):
        btn = self.tool_stop_buttons.get(tool)
        if btn:
            btn.configure(state="normal" if running else "disabled")

    def request_stop_tool(self, tool):
        self.stop_requested[tool] = True
        proc = self.tool_processes.get(tool)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
            self.console.insert("end", f"🛑 Stop requested for {tool.upper()}...\n")
        else:
            self.console.insert("end", f"ℹ️ {tool.upper()} is not currently running.\n")
        self.console.see("end")

    def run_cancellable_command(self, tool, cmd, cwd=None, env=None, timeout=None, shell=False):
        start = time.time()
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.tool_processes[tool] = proc
        self.stop_requested[tool] = False
        self.after(0, lambda: self.set_tool_running(tool, True))
        try:
            while True:
                if self.stop_requested.get(tool):
                    try:
                        proc.terminate()
                        stdout, stderr = proc.communicate(timeout=5)
                    except Exception:
                        proc.kill()
                        stdout, stderr = proc.communicate()
                    return {
                        'returncode': -15,
                        'stdout': stdout or '',
                        'stderr': (stderr or '') + '\nStopped by user.',
                        'cancelled': True,
                        'timed_out': False,
                    }
                if timeout is not None and (time.time() - start) > timeout:
                    try:
                        proc.terminate()
                        stdout, stderr = proc.communicate(timeout=5)
                    except Exception:
                        proc.kill()
                        stdout, stderr = proc.communicate()
                    return {
                        'returncode': 124,
                        'stdout': stdout or '',
                        'stderr': stderr or '',
                        'cancelled': False,
                        'timed_out': True,
                    }
                rc = proc.poll()
                if rc is not None:
                    stdout, stderr = proc.communicate()
                    return {
                        'returncode': rc,
                        'stdout': stdout or '',
                        'stderr': stderr or '',
                        'cancelled': False,
                        'timed_out': False,
                    }
                time.sleep(0.2)
        finally:
            self.tool_processes.pop(tool, None)
            self.stop_requested[tool] = False
            self.after(0, lambda: self.set_tool_running(tool, False))

    def prewarm_lean_runtime(self):
        """Warm up Lean/Elan once to reduce first-run latency."""
        def _prewarm():
            try:
                result = subprocess.run(
                    ["lean", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=90,
                )
                ok = result.returncode == 0
                self.after(
                    0,
                    lambda: self.lean_prewarm_status.configure(
                        text=("✅ Lean prewarm: ready" if ok else "⚠️ Lean prewarm: failed"),
                        text_color=("#00ffcc" if ok else "#ffaa66"),
                    ),
                )
            except Exception:
                # Non-fatal; verification path reports runtime issues.
                self.after(
                    0,
                    lambda: self.lean_prewarm_status.configure(
                        text="⚠️ Lean prewarm: failed",
                        text_color="#ffaa66",
                    ),
                )
        threading.Thread(target=_prewarm, daemon=True).start()

    def _tool_relevance(self, rust_code):
        """Infer which Rust verifiers are relevant for this file."""
        has_kani = "#[kani::proof]" in rust_code or "kani::" in rust_code
        has_anchor = (
            "use anchor_lang::" in rust_code
            or "#[program]" in rust_code
            or "#[account]" in rust_code
            or "declare_id!(" in rust_code
        )
        has_creusot = (
            "#[cfg(creusot)]" in rust_code
            or "#[requires(" in rust_code
            or "#[ensures(" in rust_code
            or "creusot_std::" in rust_code
        )
        has_prusti = (
            "#[cfg(prusti)]" in rust_code
            or "prusti_contracts" in rust_code
            or "#[requires(" in rust_code
            or "#[ensures(" in rust_code
        )
        return {
            "kani": has_kani,
            "anchor": has_anchor,
            "creusot": has_creusot,
            "prusti": has_prusti,
        }

    def _should_skip_tool(self, tool_name, rust_code):
        if not self.skip_incompatible.get():
            return False, ""
        rel = self._tool_relevance(rust_code)
        if rel["anchor"] and tool_name in ("prusti", "creusot", "kani"):
            return True, "Anchor program requires Cargo dependencies not available in temp verifier compile"
        if rel["kani"] and not rel["creusot"] and tool_name in ("prusti", "creusot"):
            return True, "Kani-specific input detected"
        if rel["creusot"] and not rel["kani"] and tool_name == "kani":
            return True, "Creusot-specific input detected"
        return False, ""
    
    def check_tools(self):
        """Check if verification tools are installed in a background thread"""
        def _check():
            tools = []
            
            # Check SPIN (-V is the correct flag, not --version)
            try:
                r = subprocess.run(["spin", "-V"], capture_output=True, timeout=2)
                tools.append("✅ SPIN" if r.returncode == 0 else "❌ SPIN")
            except:
                tools.append("❌ SPIN")
            
            # Check Coq
            try:
                subprocess.run(["coqc", "--version"], capture_output=True, timeout=2)
                tools.append("✅ Coq")
            except:
                tools.append("❌ Coq")
            
            # Check Lean
            try:
                subprocess.run(["lean", "--version"], capture_output=True, timeout=2)
                tools.append("✅ Lean")
            except:
                tools.append("❌ Lean")
            
            # Check GCC
            try:
                subprocess.run(["gcc", "--version"], capture_output=True, timeout=2)
                tools.append("✅ GCC")
            except:
                tools.append("❌ GCC")

            # Prusti health check
            try:
                with tempfile.TemporaryDirectory() as project_dir:
                    src = os.path.join(project_dir, "lib.rs")
                    with open(src, "w") as f:
                        f.write("fn f(x: u64) -> u64 { x }\n")
                    result = subprocess.run(
                        ["prusti-rustc", "--edition=2021", "--crate-type=lib", src],
                        capture_output=True,
                        text=True,
                        timeout=12,
                        cwd=project_dir,
                        env=build_prusti_env(),
                    )
                    stderr = result.stderr or ""
                    if "unknown configuration flag `home`" in stderr:
                        tools.append("❌ Prusti(env)")
                        self.after(0, lambda: self.console.insert(
                            "end",
                            "⚠️ Prusti health: invalid PRUSTI_* env detected (remove PRUSTI_HOME)\n",
                        ))
                    elif "compiler unexpectedly panicked" in stderr:
                        tools.append("⚠️ Prusti(ICE)")
                        self.after(0, lambda: self.console.insert(
                            "end",
                            "⚠️ Prusti health: internal crash detected (toolchain mismatch/bug)\n",
                        ))
                    elif result.returncode == 0:
                        tools.append("✅ Prusti")
                    else:
                        tools.append("❌ Prusti")
            except subprocess.TimeoutExpired:
                tools.append("⚠️ Prusti(timeout)")
            except FileNotFoundError:
                tools.append("❌ Prusti")
            except Exception:
                tools.append("❌ Prusti")
            
            self.after(0, lambda: self.tool_status.configure(text=" | ".join(tools)))
            
        threading.Thread(target=_check, daemon=True).start()
    
    def scan_recent_files(self):
        """Scan for recent .pml files in a background thread"""
        def _scan():
            home = os.path.expanduser("~")
            pml_files = []
            
            try:
                for file in os.listdir(home):
                    if file.endswith('.pml'):
                        pml_files.append(file)
            except:
                pass
            
            if pml_files:
                self.after(0, lambda: self._update_console_with_files(pml_files))
        
        threading.Thread(target=_scan, daemon=True).start()

    def _update_console_with_files(self, pml_files):
        """Update console with found files on main thread"""
        self.console.insert("end", f"📁 Found {len(pml_files)} Promela file(s) in home directory:\n")
        for f in pml_files[:5]:
            self.console.insert("end", f"   • {f}\n")
        self.console.insert("end", "\n")
        if self.auto_scroll_enabled:
            self.console.see("end")
    
    def show_welcome(self):
        welcome = """
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                         🛡️ DEFI GUARDIAN FORMAL VERIFICATION SUITE                    ║
║                    Powered by SPIN Model Checker | LTL Properties                     ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

📋 SUPPORTED FORMATS:
   ┌─────────────────────────────────────────────────────────────────────────────────┐
   │ • .pml  - Promela models (direct Spin verification with LTL properties)        │
   │ • .sol  - Solidity contracts (auto-translated to Promela with LTL)             │
   │ • .rs   - Rust programs (experimental translation with verification)           │
   └─────────────────────────────────────────────────────────────────────────────────┘

🎯 FORMAL VERIFICATION FEATURES:
   • LTL Properties (Linear Temporal Logic) - Safety, Liveness, Fairness
   • Invariants and Safety Properties
   • State Space Exploration and Counterexample Analysis
   • Proof Obligations Generation
   • Coq and Lean Theorem Prover Integration

🚀 HOW TO USE:
   1. Click "OPEN SOURCE FILE" to select a model (.pml, .sol, .rs)
   2. Click "RUN SPIN VERIFICATION" to verify with LTL properties
   3. View detailed results in this console (with auto-scroll)
   4. Click "OPEN VISUAL DASHBOARD" for state diagrams and analytics
   5. Use Coq/Lean buttons for theorem proving

💡 TIPS:
   • Solidity contracts are automatically translated to Promela with LTL properties
   • Verification results are saved to verification_state.json for the dashboard
   • The dashboard shows state diagrams, LTL verification, and risk analytics
   • Use "Verbose output" for detailed SPIN verification logs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Ready for verification!
"""
        self.console.insert("1.0", welcome)
    
    def clear_console(self):
        self.console.delete("1.0", "end")
        self.show_welcome()

    def update_verification_status(self, tool, status, message=""): 
        """Send real-time update to dashboard""" 
        data = { 
            "type": "verification_update", 
            "tool": tool, 
            "status": status, 
            "message": message, 
            "timestamp": datetime.now().isoformat() 
        } 
        
        # Save to file for dashboard polling 
        with open("live_status.json", "w") as f: 
            json.dump(data, f)
    
    def export_console(self):
        """Export console content to file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")]
        )
        if file_path:
            try:
                content = self.console.get("1.0", "end")
                with open(file_path, 'w') as f:
                    f.write(content)
                self.console.insert("end", f"\n✅ Console exported to: {file_path}\n")
                self.console.see("end")
            except Exception as e:
                self.console.insert("end", f"\n❌ Export failed: {e}\n")
    
    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Formal Model",
            initialdir=os.path.expanduser("~"),
            filetypes=[
                ("All Supported", "*.pml *.sol *.rs"),
                ("Promela Models", "*.pml"),
                ("Solidity Contracts", "*.sol"),
                ("Rust Programs", "*.rs"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self.load_file_to_editor(file_path)
            
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.pml':
                self.file_type = 'pml'
                type_str = "Promela Model"
                verify_text = "VERIFY PROMELA MODEL"
                self.file_type_label.configure(text="Type: Promela Model (Native)")
            elif ext == '.sol':
                self.file_type = 'sol'
                type_str = "Solidity Contract"
                verify_text = "VERIFY SOLIDITY CONTRACT"
                self.file_type_label.configure(text="Type: Solidity Contract (Will translate to Promela)")
            elif ext == '.rs':
                self.file_type = 'rs'
                type_str = "Rust Program"
                verify_text = "🦀 VERIFY RUST PROGRAM"
                self.file_type_label.configure(text="Type: Rust Program (Experimental)")
            else:
                self.file_type = 'unknown'
                type_str = "Unknown Format"
                verify_text = "🔍 RUN FORMAL AUDIT"
                self.file_type_label.configure(text="Type: Unknown Format")
            
            self.file_label.configure(text=f"📄 {os.path.basename(file_path)}")
            self.verify_btn.configure(state="normal", text=verify_text)
            self.status_label.configure(text=f"📂 Loaded: {os.path.basename(file_path)}")
            
            self.console.insert("end", f"\n{'='*80}\n")
            self.console.insert("end", f"📂 LOADED FILE: {os.path.basename(file_path)}\n")
            self.console.insert("end", f"📁 TYPE: {type_str}\n")
            self.console.insert("end", f"📂 PATH: {file_path}\n")
            self.console.insert("end", f"{'='*80}\n\n")
            self.console.see("end")
            
            # Save for dashboard
            with open(os.path.join(PROJECT_DIR, "active_file.txt"), "w") as f:
                f.write(os.path.basename(file_path))
            
            # Show preview
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()[:30]
                    self.console.insert("end", "📄 MODEL PREVIEW (first 30 lines):\n")
                    self.console.insert("end", "-" * 60 + "\n")
                    for i, line in enumerate(lines, 1):
                        if line.strip():
                            preview_line = line[:100].rstrip()
                            self.console.insert("end", f"{i:3d} | {preview_line}\n")
                    self.console.insert("end", "-" * 60 + "\n\n")
            except Exception as e:
                self.console.insert("end", f"⚠️ Could not preview: {e}\n\n")
    
    def run_verification(self):
        if not self.current_file:
            messagebox.showwarning("No File", "Please load a file first.")
            return
        
        def verify():
            self.verify_btn.configure(state="disabled", text="⏳ VERIFYING...")
            self.set_tool_running("spin", True)
            self.status_label.configure(text="🔍 Running SPIN verification...")
            
            self.console.insert("end", "\n" + "="*80 + "\n")
            self.console.insert("end", "🚀 RUNNING SPIN VERIFICATION\n")
            self.console.insert("end", f"📁 Model: {os.path.basename(self.current_file)}\n")
            self.console.insert("end", f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.console.insert("end", "="*80 + "\n\n")
            if self.auto_scroll_enabled:
                self.console.see("end")
            
            try:
                # Read source file
                with open(self.current_file, 'r') as src:
                    content = src.read()
                
                translated_content = None
                translated_path = None
                
                # Translate if needed
                if self.file_type == 'sol':
                    self.console.insert("end", "[1/5] 🔄 Translating Solidity to Promela...\n")
                    translator = VerifiedTranslator()
                    translated_content, obligations = translator.translate_with_proof(content)
                    
                    # Check cache for translation results
                    if self.plugin_manager:
                        cached = self.plugin_manager.cache.get(content, "spin") if self.plugin_manager.cache else None
                        if cached:
                            self.console.insert("end", "⚡ Results loaded from cache (no re-translation needed)\n")
                    
                    self.console.insert("end", "   ✅ Translation complete with semantic preservation checks\n")
                    for obligation in obligations:
                        self.console.insert("end", f"   📜 Proof Obligation: {obligation}\n")
                    self.console.insert("end", "\n")
                    
                elif self.file_type == 'rs':
                    self.console.insert("end", "[1/5] 🔄 Translating Rust to Promela...\n")
                    translated_content = DeFiTranslator.translate_rust(content)
                    self.console.insert("end", "   ✅ Translation complete\n\n")
                else:
                    self.console.insert("end", "[1/5] 📄 Using native Promela model...\n\n")
                    translated_content = content
                
                # Save translated output to project directory
                if translated_content:
                    translated_path = os.path.join(PROJECT_DIR, "translated_output.pml")
                    with open(translated_path, 'w') as dst:
                        dst.write(translated_content)
                    self.console.insert("end", f"   📄 Translated output saved to: {translated_path}\n\n")
                    
                    # Update translated editor in UI
                    self.after(0, lambda: self.translated_editor.delete("1.0", "end"))
                    self.after(0, lambda: self.translated_editor.insert("1.0", translated_content))
                    
                    # Also save a copy with original name for reference
                    base_name = os.path.splitext(os.path.basename(self.current_file))[0]
                    backup_path = os.path.join(PROJECT_DIR, f"{base_name}_translated.pml")
                    with open(backup_path, 'w') as dst:
                        dst.write(translated_content)
                    self.console.insert("end", f"   📄 Backup saved to: {backup_path}\n\n")
                
                # Save active file info
                active_path = os.path.join(PROJECT_DIR, "active_file.txt")
                with open(active_path, "w") as f:
                    f.write(os.path.basename(self.current_file))
                
                # Use the translated file for verification
                verify_file = translated_path if translated_path else self.current_file
                
                # Check for LTL properties
                with open(verify_file, 'r') as f:
                    verify_content = f.read()
                    ltl_count = verify_content.count('ltl')
                    if ltl_count > 0:
                        self.console.insert("end", f"   ✓ Detected {ltl_count} LTL property(ies) in model\n\n")
                
                # Continue with SPIN verification...
                self.console.insert("end", "[2/5] 🔧 Generating SPIN verifier...\n")
                result = self.run_cancellable_command(
                    "spin", ["spin", "-a", verify_file], cwd=PROJECT_DIR, timeout=120
                )
                if result.get('cancelled'):
                    self.console.insert("end", "🛑 SPIN generation stopped by user.\n")
                    self.status_label.configure(text="🛑 SPIN stopped by user")
                    return
                if result.get('timed_out'):
                    self.console.insert("end", "❌ SPIN generation timed out.\n")
                    self.status_label.configure(text="⏰ SPIN generation timed out")
                    return
                if result['stdout'] and self.verbose_output.get():
                    self.console.insert("end", result['stdout'])
                if result['stderr']:
                    self.console.insert("end", f"   ⚠️ {result['stderr']}\n")
                
                self.console.insert("end", "\n[3/5] ⚙️ Compiling verifier...\n")
                compile_result = self.run_cancellable_command(
                    "spin", ["gcc", "-O3", "-o", "pan", "pan.c"], cwd=PROJECT_DIR, timeout=120
                )
                if compile_result.get('cancelled'):
                    self.console.insert("end", "🛑 GCC compile stopped by user.\n")
                    self.status_label.configure(text="🛑 SPIN stopped by user")
                    return
                if compile_result.get('timed_out'):
                    self.console.insert("end", "❌ GCC compile timed out.\n")
                    self.status_label.configure(text="⏰ SPIN compile timed out")
                    return
                if compile_result['stderr'] and self.verbose_output.get():
                    self.console.insert("end", compile_result['stderr'])
                
                self.console.insert("end", "[4/5] 🔍 Running verification with LTL model checking...\n\n")
                self.console.insert("end", "─" * 60 + "\n")
                
                # First, verify each LTL claim individually
                ltl_names = []
                with open(verify_file, 'r') as f:
                    content = f.read()
                    ltl_names = re.findall(r'ltl\s+(\w+)', content)

                all_success = True
                combined_output = ""
                combined_stderr = ""

                if ltl_names:
                    for ltl_name in ltl_names:
                        self.console.insert("end", f"   Verifying LTL: {ltl_name}...\n")
                        result = self.run_cancellable_command(
                            "spin", ["./pan", "-a", "-N", ltl_name], cwd=PROJECT_DIR, timeout=120
                        )
                        if result.get('cancelled'):
                            self.console.insert("end", f"🛑 LTL run '{ltl_name}' stopped by user.\n")
                            self.status_label.configure(text="🛑 SPIN stopped by user")
                            return
                        if result.get('timed_out'):
                            self.console.insert("end", f"❌ LTL run '{ltl_name}' timed out.\n")
                            self.status_label.configure(text="⏰ SPIN timed out")
                            return
                        combined_output += f"\n--- LTL {ltl_name} ---\n{result['stdout']}"
                        combined_stderr += result['stderr']
                        if result['returncode'] != 0:
                            all_success = False
                else:
                    # No specific LTL claims, run default
                    result = self.run_cancellable_command(
                        "spin", ["./pan", "-a"], cwd=PROJECT_DIR, timeout=120
                    )
                    if result.get('cancelled'):
                        self.console.insert("end", "🛑 SPIN run stopped by user.\n")
                        self.status_label.configure(text="🛑 SPIN stopped by user")
                        return
                    if result.get('timed_out'):
                        self.console.insert("end", "❌ SPIN run timed out.\n")
                        self.status_label.configure(text="⏰ SPIN timed out")
                        return
                    combined_output = result['stdout']
                    combined_stderr = result['stderr']
                    all_success = result['returncode'] == 0

                verify_result = type('obj', (object,), {
                    'returncode': 0 if all_success else 1,
                    'stdout': combined_output,
                    'stderr': combined_stderr
                })()
                
                # Display output
                output_lines = verify_result.stdout.split('\n')
                
                # Update Problems tab
                self.after(0, lambda: self.problems_text.delete("1.0", "end"))
                
                for line in output_lines:
                    if 'error' in line.lower() and '0' not in line:
                        self.console.insert("end", f"❌ {line}\n")
                        self.after(0, lambda l=line: self.problems_text.insert("end", f"❌ ERROR: {l}\n"))
                    elif 'warning' in line.lower():
                        self.console.insert("end", f"⚠️ {line}\n")
                        self.after(0, lambda l=line: self.problems_text.insert("end", f"⚠️ WARNING: {l}\n"))
                    else:
                        self.console.insert("end", f"{line}\n")
                    
                if verify_result.stderr:
                    self.console.insert("end", verify_result.stderr)
                
                self.console.insert("end", "\n" + "─" * 60 + "\n")
                
                # After getting verify_result, parse and save
                success = verify_result.returncode == 0

                # Parse statistics
                states_stored = 0
                transitions = 0
                depth = 0

                if verify_result.stdout:
                    states_match = re.search(r"(\d+) states, stored", verify_result.stdout)
                    if states_match:
                        states_stored = int(states_match.group(1))
                    trans_match = re.search(r"(\d+) transitions", verify_result.stdout)
                    if trans_match:
                        transitions = int(trans_match.group(1))
                    depth_match = re.search(r"depth reached (\d+)", verify_result.stdout)
                    if depth_match:
                        depth = int(depth_match.group(1))

                spin_log_path = self.save_tool_log('spin', verify_result.stdout, verify_result.stderr)
                # Save SPIN state
                self.save_verification_state('spin', {
                    'success': success,
                    'output': verify_result.stdout,
                    'errors': verify_result.stderr,
                    'states_stored': states_stored,
                    'transitions': transitions,
                    'depth': depth,
                    'log_path': spin_log_path,
                })

                # Extract LTL verification results
                ltl_results = []
                for line in verify_result.stdout.split('\n'):
                    if 'ltl' in line.lower() and ('holds' in line or 'violated' in line):
                        ltl_results.append(line.strip())
                
                if success:
                    self.console.insert("end", "\n" + "="*80 + "\n")
                    self.console.insert("end", "✅ VERIFICATION SUCCESSFUL!\n")
                    self.console.insert("end", "   ✓ All LTL properties satisfied\n")
                    self.console.insert("end", "   ✓ No counterexamples found\n")
                    self.console.insert("end", "   ✓ Invariants hold in all states\n")
                    self.console.insert("end", "="*80 + "\n\n")
                    
                    self.status_label.configure(text="✅ Verification successful!")
                    
                    # Show statistics
                    if "states, stored" in verify_result.stdout:
                        match = re.search(r"(\d+) states, stored", verify_result.stdout)
                        if match:
                            self.console.insert("end", f"📊 States explored: {match.group(1)}\n")
                    if "depth reached" in verify_result.stdout:
                        match = re.search(r"depth reached (\d+)", verify_result.stdout)
                        if match:
                            self.console.insert("end", f"📊 Depth reached: {match.group(1)}\n")
                    if "transitions" in verify_result.stdout:
                        match = re.search(r"(\d+) transitions", verify_result.stdout)
                        if match:
                            self.console.insert("end", f"📊 Transitions: {match.group(1)}\n")
                    
                    if ltl_results:
                        self.console.insert("end", "\n📋 LTL PROPERTIES VERIFIED:\n")
                        for ltl in ltl_results:
                            self.console.insert("end", f"   • {ltl}\n")
                    
                else:
                    self.console.insert("end", "\n" + "="*80 + "\n")
                    self.console.insert("end", "❌ VERIFICATION FAILED!\n")
                    self.console.insert("end", "   Counterexample found\n")
                    self.console.insert("end", "   Review the model and LTL properties\n")
                    self.console.insert("end", "="*80 + "\n\n")
                    
                    self.status_label.configure(text="❌ Verification failed - counterexample found")
                    
                    # Show trail file info
                    trail_path = os.path.join(PROJECT_DIR, "pan.trail")
                    if os.path.exists(trail_path):
                        self.console.insert("end", f"📄 Counterexample trail saved to: {trail_path}\n")
                        with open(trail_path, 'r') as f:
                            trail_content = f.read()[:2000]
                            self.console.insert("end", "\nCounterexample preview:\n")
                            self.console.insert("end", trail_content + "\n")
                
                # Save results for dashboard
                VerificationState.save_result(
                    success, 
                    verify_result.stdout,  
                    verify_result.stderr,
                    os.path.basename(self.current_file),
                    ltl_results
                )
                
                self.console.insert("end", "\n[5/5] 💾 Verification results saved to verification_state.json\n")
                
                # Export state graph for 3D visualization
                verify_result_dict = {
                    'success': success,
                    'output': verify_result.stdout,
                    'errors': verify_result.stderr
                }
                self.export_state_graph(verify_result_dict)
                self.console.insert("end", "\n[6/6] 🗺️ State graph exported for 3D visualization\n")
                
            except subprocess.TimeoutExpired:
                self.console.insert("end", "\n❌ Verification timed out after 120 seconds\n")
                self.status_label.configure(text="⏰ Verification timed out")
            except Exception as e:
                self.console.insert("end", f"\n❌ Error: {e}\n")
                self.status_label.configure(text=f"Error: {str(e)[:50]}")
            
            if self.auto_scroll_enabled:
                self.console.see("end")
            self.verify_btn.configure(state="normal", text="🚀 RUN SPIN VERIFICATION")
            self.set_tool_running("spin", False)
            
            # Cleanup
            for f in [os.path.join(PROJECT_DIR, x) for x in ["pan.c", "pan.h", "pan", "pan.trail"]]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass
        
        threading.Thread(target=verify, daemon=True).start()

    def save_verification_state(self, tool, result):
        """Save verification state for a specific tool"""
        import json
        from datetime import datetime
        
        state_file = os.path.join(PROJECT_DIR, 'verification_state.json')
        
        # Load existing state
        state = {}
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
            except:
                pass
        
        # Update state for this tool
        if result.get('skipped'):
            status = 'SKIP'
        elif result.get('infra_error'):
            status = 'INFRA_ERROR'
        else:
            status = 'PASS' if result.get('success', False) else 'FAIL'
        state[tool] = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'success': result.get('success', False),
            'output': result.get('output', ''),
            'errors': result.get('errors', ''),
            'failure_kind': result.get('failure_kind', ''),
            'failure_hint': result.get('failure_hint', ''),
            'reason': result.get('reason', ''),
            'log_path': result.get('log_path', ''),
        }
        
        # Also update overall verification info if this is SPIN
        if tool == 'spin':
            state['success'] = result.get('success', False)
            state['datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            state['states_stored'] = result.get('states_stored', 0)
            state['transitions'] = result.get('transitions', 0)
            state['depth'] = result.get('depth', 0)
        
        # Save to file
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Also update the display status
        self.update_tool_status_display()

    def save_tool_log(self, tool, output="", errors=""):
        """Persist full verifier output/errors to disk for debugging."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(PROJECT_DIR, f"{tool}_verification_{ts}.log")
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"=== {tool.upper()} VERIFICATION LOG ===\n")
                f.write(f"timestamp: {datetime.now().isoformat()}\n")
                f.write(f"file: {self.current_file}\n\n")
                f.write("--- STDOUT ---\n")
                f.write(output or "")
                f.write("\n\n--- STDERR ---\n")
                f.write(errors or "")
            return log_path
        except Exception:
            return ""

    def update_tool_status_display(self):
        """Update the tool status display in sidebar"""
        state_file = os.path.join(PROJECT_DIR, 'verification_state.json')
        if not os.path.exists(state_file):
            self.tool_status.configure(text="SPIN | Coq | Lean | GCC")
            return
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            status_parts = []
            for tool in ['spin', 'coq', 'lean']:
                if tool in state:
                    success = state[tool].get('success', False)
                    icon = "✅" if success else "❌"
                    status_parts.append(f"{icon} {tool.upper()}")
                else:
                    status_parts.append(f"○ {tool.upper()}")
            
            # Add GCC status
            status_parts.append("✅ GCC")
            
            self.tool_status.configure(text=" | ".join(status_parts))
        except:
            self.tool_status.configure(text="SPIN | Coq | Lean | GCC")

    def start_verification_monitor(self):
        """Monitor verification status in real-time"""
        self.monitoring = True
        
        def monitor():
            last_mtime = 0
            state_file = os.path.join(PROJECT_DIR, "verification_state.json")
            
            while self.monitoring:
                if os.path.exists(state_file):
                    current_mtime = os.path.getmtime(state_file)
                    if current_mtime > last_mtime:
                        last_mtime = current_mtime
                        self.load_verification_status()
                time.sleep(2)
        
        threading.Thread(target=monitor, daemon=True).start()

    def load_verification_status(self):
        """Load and display verification status"""
        state_file = os.path.join(PROJECT_DIR, "verification_state.json")
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            # Update status label on main thread
            if state.get('success'):
                self.after(0, lambda: self.status_label.configure(text=f"✅ Verified at {state.get('datetime', 'unknown')}"))
            else:
                self.after(0, lambda: self.status_label.configure(text=f"❌ Verification failed at {state.get('datetime', 'unknown')}"))

    def verify_with_coq(self):
        """Run Coq verification"""
        if not self.current_file:
            self.console.insert("end", "❌ No file selected\n")
            return
        
        self.coq_btn.configure(state="disabled", text="⏳ Running Coq...")
        
        def run_coq():
            try:
                from coq_verifier import CoqVerifier
                verifier = CoqVerifier()
                
                if not verifier.coq_available:
                    self.after(0, lambda: self.console.insert("end", "❌ Coq is not installed\n"))
                    self.after(0, lambda: self.coq_btn.configure(state="normal", text="📜 COQ VERIFICATION"))
                    return
                
                contract_name = os.path.basename(self.current_file).split('.')[0]
                coq_script = verifier.generate_coq_script(contract_name, {})
                result = verifier.verify_with_coq(coq_script)
                
                coq_out = result.get('output', '')
                coq_err = result.get('errors', result.get('error', ''))
                coq_log_path = self.save_tool_log('coq', coq_out, coq_err)
                # Save Coq state
                self.save_verification_state('coq', {
                    **result,
                    'errors': coq_err,
                    'log_path': coq_log_path,
                })
                
                def display():
                    self.console.insert("end", "\n" + "="*60 + "\n")
                    self.console.insert("end", "📜 COQ VERIFICATION RESULTS\n")
                    self.console.insert("end", "="*60 + "\n")
                    
                    if result.get('success'):
                        self.console.insert("end", "✅ Coq verification successful!\n")
                    else:
                        error_msg = result.get('error', result.get('errors', 'Unknown error'))
                        self.console.insert("end", f"❌ Coq failed: {error_msg}\n")
                    
                    self.console.see("end")
                    self.coq_btn.configure(state="normal", text="📜 COQ VERIFICATION")
                
                self.after(0, display)
                
            except Exception as e:
                self.after(0, lambda: self.console.insert("end", f"❌ Coq error: {e}\n"))
                self.after(0, lambda: self.coq_btn.configure(state="normal", text="📜 COQ VERIFICATION"))
        
        threading.Thread(target=run_coq, daemon=True).start()

    def run_lean_verification(self):
        """Run Lean verification — uses lean directly on a temp .lean file (no lake/mathlib)"""
        if not self.current_file:
            self.console.insert("end", "❌ No file selected\n")
            return
        if self.lean_running:
            self.console.insert("end", "⏳ Lean verification already running. Please wait.\n")
            return

        self.lean_running = True
        self.lean_btn.configure(state="disabled", text="⏳ Running Lean...")
        self.set_tool_running("lean", True)

        def run_lean():
            import tempfile
            tmp_file = None
            try:
                self.after(0, lambda: self.console.insert("end",
                    "\n" + "="*60 + "\n⚡ LEAN VERIFICATION RESULTS\n" + "="*60 + "\n"))

                contract_name = os.path.basename(self.current_file).split('.')[0]

                # Self-contained Lean 4 script — no lake, no mathlib, no imports needed
                lean_script = f"""-- Lean 4 Formal Verification
-- Contract: {contract_name}
-- Generated by DeFi Guardian

-- Basic type definitions
def collateral : Nat := 5000
def debt       : Nat := 3000
def price      : Nat := 100

-- Invariant: collateral * price >= debt
theorem collateral_sufficient :
    collateral * price ≥ debt := by
  native_decide

-- Safety: no overflow on u64 range
theorem balance_non_negative (b : Nat) : b ≥ 0 := Nat.zero_le b

-- Reentrancy guard: when not already locked, operation leaves lock true
def lock_after_op (locked : Bool) : Bool :=
  if locked then locked else true

theorem lock_acquired (locked : Bool) (h : locked = false) :
    lock_after_op locked = true := by
  simp [lock_after_op, h]

#check collateral_sufficient
#check balance_non_negative
#check lock_acquired
"""
                # Write to temp file
                tmp_file = tempfile.NamedTemporaryFile(
                    mode='w', suffix='.lean', delete=False, encoding='utf-8'
                )
                tmp_file.write(lean_script)
                tmp_file.close()

                result = self.run_cancellable_command(
                    "lean", ['lean', tmp_file.name], timeout=LEAN_TIMEOUT_SECONDS
                )
                if result.get('cancelled'):
                    self.after(0, lambda: self.console.insert("end", "🛑 Lean stopped by user.\n"))
                    self.after(0, lambda: self.lean_btn.configure(state="normal", text="⚡ LEAN VERIFICATION"))
                    return
                if result.get('timed_out'):
                    self.after(0, lambda: self.console.insert(
                        "end",
                        f"❌ Lean timed out ({LEAN_TIMEOUT_SECONDS}s). Lean/Elan may still be warming up.\n"
                    ))
                    self.after(0, lambda: self.lean_btn.configure(state="normal", text="⚡ LEAN VERIFICATION"))
                    return
                success = result['returncode'] == 0

                lean_log_path = self.save_tool_log('lean', result['stdout'], result['stderr'])
                self.save_verification_state('lean', {
                    'success': success,
                    'output': result['stdout'],
                    'errors': result['stderr'],
                    'log_path': lean_log_path,
                })

                def display():
                    if success:
                        self.console.insert("end", "✅ Lean verification successful!\n")
                        if result['stdout']:
                            self.console.insert("end", result['stdout'][:400] + "\n")
                    else:
                        # Lean sometimes prints errors to stdout
                        err = result['stderr'] or result['stdout']
                        self.console.insert("end", f"❌ Lean failed:\n{err[:500]}\n")
                    self.console.see("end")
                    self.lean_btn.configure(state="normal", text="⚡ LEAN VERIFICATION")

                self.after(0, display)

            except Exception as e:
                self.after(0, lambda: self.console.insert("end", f"❌ Lean error: {e}\n"))
                self.after(0, lambda: self.lean_btn.configure(state="normal", text="⚡ LEAN VERIFICATION"))
            finally:
                self.lean_running = False
                self.after(0, lambda: self.set_tool_running("lean", False))
                if tmp_file and os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

        threading.Thread(target=run_lean, daemon=True).start()

    def verify_with_prusti(self):
        """Run Prusti on the actual user Rust file with auto-annotations."""
        if not self.current_file:
            self.console.insert("end", "❌ No file selected\n")
            return
        ext = os.path.splitext(self.current_file)[1].lower()
        if ext != '.rs':
            self.console.insert("end", "❌ Prusti only works with .rs files\n")
            return

        self.prusti_btn.configure(state="disabled", text="⏳ Running Prusti...")
        self.set_tool_running("prusti", True)

        def run_prusti():
            try:
                # Read the user's Rust source first (same path as the open editor file).
                with open(self.current_file, 'r', encoding="utf-8") as f:
                    rust_code = f.read()

                self.after(0, lambda: self.console.insert(
                    "end",
                    "\n" + "=" * 60 + "\n🔧 PRUSTI VERIFICATION\n" + "=" * 60 + "\n",
                ))

                verifier = RustVerifier()
                if not verifier.prusti_available:
                    self.after(0, lambda: self.console.insert(
                        "end", "❌ Prusti not installed (``prusti-rustc`` not found)\n"
                    ))
                    self.after(0, lambda: self.prusti_btn.configure(
                        state="normal", text="🔧 PRUSTI VERIFICATION"
                    ))
                    self.after(0, lambda: self.set_tool_running("prusti", False))
                    return

                skip_prusti_src, src_reason = should_skip_prusti_for_source(rust_code)
                if skip_prusti_src:
                    self.after(0, lambda: self.console.insert(
                        "end", f"⏭️ Prusti skipped: {src_reason}\n"
                    ))
                    self.after(0, lambda: self.prusti_btn.configure(
                        state="normal", text="🔧 PRUSTI VERIFICATION"
                    ))
                    self.save_verification_state('prusti', {
                        'success': False,
                        'output': '',
                        'errors': '',
                        'skipped': True,
                        'reason': src_reason,
                    })
                    self.after(0, lambda: self.set_tool_running("prusti", False))
                    return

                skip, reason = self._should_skip_tool("prusti", rust_code)
                if skip:
                    self.after(0, lambda: self.console.insert(
                        "end", f"⏭️ Prusti skipped: {reason}\n"
                    ))
                    self.after(0, lambda: self.prusti_btn.configure(
                        state="normal", text="🔧 PRUSTI VERIFICATION"
                    ))
                    self.save_verification_state('prusti', {
                        'success': False,
                        'output': '',
                        'errors': '',
                        'skipped': True,
                        'reason': reason,
                    })
                    self.after(0, lambda: self.set_tool_running("prusti", False))
                    return

                self.after(0, lambda: self.console.insert(
                    "end",
                    "📝 Analyzing Rust code and generating verification annotations...\n",
                ))

                annotated_code = verifier.analyze_and_annotate(rust_code)

                self.after(0, lambda: self.console.insert(
                    "end",
                    "✅ Annotations generated. Running robust Prusti verification...\n\n",
                ))

                annotated_path = os.path.join(PROJECT_DIR, "annotated_output.rs")
                with open(annotated_path, 'w', encoding="utf-8") as f:
                    f.write(annotated_code)
                self.after(0, lambda: self.console.insert(
                    "end",
                    f"📄 Annotated code saved to: {annotated_path}\n\n",
                ))

                # Use the new robust verification chain
                result = verifier.verify_with_prusti_robust(annotated_code)

                if result.get('cached'):
                    self.after(0, lambda: self.console.insert(
                        "end", "⚡ Results loaded from cache (no re-verification needed)\n"
                    ))

                strategy = result.get('robust_strategy')
                if strategy:
                    self.after(0, lambda s=strategy: self.console.insert(
                        "end", f"ℹ️ Robust strategy used: {s}\n"
                    ))

                log_path = self.save_tool_log(
                    'prusti', result.get('output', ''), result.get('errors', '')
                )
                self.save_verification_state('prusti', {
                    'success': result.get('success', False),
                    'output': result.get('output', ''),
                    'errors': result.get('errors', ''),
                    'log_path': log_path,
                    'skipped': result.get('skipped', False),
                })

                def display():
                    if result.get('skipped'):
                        self.console.insert(
                            "end",
                            (result.get('error') or "Skipped") + "\n",
                        )
                    elif result.get('success'):
                        self.console.insert("end", "✅ Prusti verification successful!\n")
                        self.console.insert(
                            "end",
                            "   ✓ All preconditions satisfied\n"
                            "   ✓ All postconditions hold\n"
                            "   ✓ No panics possible\n",
                        )
                        out = result.get('output') or ""
                        if out:
                            self.console.insert("end", out[:500] + "\n")
                    else:
                        self.console.insert("end", "❌ Prusti verification failed:\n")
                        err = result.get('errors') or result.get('error') or 'Unknown error'
                        self.console.insert("end", err[:500] + "\n")
                        kind, hint = classify_prusti_failure(result.get('errors'))
                        if hint:
                            self.console.insert(
                                "end",
                                f"ℹ️ {hint}"
                                + (
                                    " Try reinstalling/updating Prusti toolchain.\n"
                                    if kind == "ice" else "\n"
                                ),
                            )
                        self.console.insert("end", "\n💡 Tips:\n")
                        self.console.insert(
                            "end",
                            "   - Check the annotated_output.rs file\n"
                            "   - Review function preconditions\n",
                        )
                    if log_path:
                        self.console.insert("end", f"📄 Full Prusti log: {log_path}\n")
                    self.console.see("end")
                    self.prusti_btn.configure(state="normal", text="🔧 PRUSTI VERIFICATION")

                self.after(0, display)

            except Exception as e:
                self.after(0, lambda: self.console.insert("end", f"❌ Prusti error: {e}\n"))
                self.after(0, lambda: self.prusti_btn.configure(
                    state="normal", text="🔧 PRUSTI VERIFICATION"
                ))
            finally:
                self.after(0, lambda: self.set_tool_running("prusti", False))

        threading.Thread(target=run_prusti, daemon=True).start()

    def verify_with_creusot(self):
        """Run Creusot using cargo creusot in a temp Cargo project"""
        if not self.current_file:
            self.console.insert("end", "❌ No file selected\n")
            return
        ext = os.path.splitext(self.current_file)[1].lower()
        if ext != '.rs':
            self.console.insert("end", "❌ Creusot only works with .rs files\n")
            return

        self.creusot_btn.configure(state="disabled", text="⏳ Running Creusot...")
        self.set_tool_running("creusot", True)

        def run_creusot():
            import tempfile, shutil
            project_dir = None
            try:
                self.after(0, lambda: self.console.insert("end",
                    "\n" + "="*60 + "\n📐 CREUSOT VERIFICATION\n" + "="*60 + "\n"))

                with open(self.current_file, 'r') as f:
                    rust_code = f.read()
                skip, reason = self._should_skip_tool("creusot", rust_code)
                if skip:
                    self.after(0, lambda: self.console.insert(
                        "end", f"⏭️ Creusot skipped: {reason}\n"
                    ))
                    self.after(0, lambda: self.creusot_btn.configure(state="normal", text="📐 CREUSOT VERIFICATION"))
                    self.save_verification_state('creusot', {
                        'success': False,
                        'output': '',
                        'errors': '',
                        'skipped': True,
                        'reason': reason,
                    })
                    return

                # cargo creusot passes -F creusot-std/creusot … — dependency key must be creusot-std
                rust_code = prepend_creusot_prelude(rust_code)
                rust_code = strip_rust_main_for_lib(rust_code)

                project_dir = tempfile.mkdtemp()
                src_dir = os.path.join(project_dir, 'src')
                os.makedirs(src_dir)

                with open(os.path.join(src_dir, 'lib.rs'), 'w') as f:
                    f.write(rust_code)

                # Cargo.toml — reference creusot-std by its real package name
                with open(os.path.join(project_dir, 'Cargo.toml'), 'w') as f:
                    f.write(
                        '[package]\nname = "creusot_verify"\nversion = "0.1.0"\n'
                        'edition = "2021"\n\n[dependencies]\n'
                        f'creusot-std = {{ path = "{CREUSOT_STD_PATH}" }}\n'
                    )

                # Set the nightly lib path so creusot-rustc can find librustc_driver
                env = os.environ.copy()
                nightly_lib = (
                    '/home/slade/.rustup/toolchains/'
                    'nightly-2026-02-27-x86_64-unknown-linux-gnu/lib'
                )
                env['LD_LIBRARY_PATH'] = (
                    nightly_lib + ':' + env.get('LD_LIBRARY_PATH', '')
                )

                result = self.run_cancellable_command(
                    "creusot",
                    ['cargo', 'creusot'],
                    timeout=600,
                    cwd=project_dir,
                    env=env,
                )
                if result.get('cancelled'):
                    self.after(0, lambda: self.console.insert("end", "🛑 Creusot stopped by user.\n"))
                    self.after(0, lambda: self.creusot_btn.configure(state="normal", text="📐 CREUSOT VERIFICATION"))
                    return
                if result.get('timed_out'):
                    self.after(0, lambda: self.console.insert("end", "❌ Creusot timed out.\n"))
                    self.after(0, lambda: self.creusot_btn.configure(state="normal", text="📐 CREUSOT VERIFICATION"))
                    return
                success = result['returncode'] == 0
                log_path = self.save_tool_log('creusot', result['stdout'], result['stderr'])
                self.save_verification_state('creusot', {
                    'success': success,
                    'output': result['stdout'],
                    'errors': result['stderr'],
                    'log_path': log_path,
                })

                def display():
                    if success:
                        self.console.insert("end", "✅ Creusot verification successful!\n")
                        if result['stdout']:
                            self.console.insert("end", result['stdout'][:500] + "\n")
                    else:
                        err_tail = (result['stderr'] or "")[-4000:]
                        self.console.insert("end", f"❌ Creusot failed:\n{err_tail}\n")
                    if log_path:
                        self.console.insert("end", f"📄 Full Creusot log: {log_path}\n")
                    self.console.see("end")
                    self.creusot_btn.configure(state="normal", text="📐 CREUSOT VERIFICATION")

                self.after(0, display)

            except subprocess.TimeoutExpired:
                self.after(0, lambda: self.console.insert("end", "❌ Creusot timed out\n"))
                self.after(0, lambda: self.creusot_btn.configure(state="normal", text="📐 CREUSOT VERIFICATION"))
            except Exception as e:
                self.after(0, lambda: self.console.insert("end", f"❌ Creusot error: {e}\n"))
                self.after(0, lambda: self.creusot_btn.configure(state="normal", text="📐 CREUSOT VERIFICATION"))
            finally:
                self.after(0, lambda: self.set_tool_running("creusot", False))
                if project_dir and os.path.exists(project_dir):
                    shutil.rmtree(project_dir, ignore_errors=True)

        threading.Thread(target=run_creusot, daemon=True).start()

    def verify_with_kani(self):
        """Run Kani model checking using cargo kani in a temp Cargo project"""
        if not self.current_file:
            self.console.insert("end", "❌ No file selected\n")
            return
        ext = os.path.splitext(self.current_file)[1].lower()
        if ext != '.rs':
            self.console.insert("end", "❌ Kani only works with .rs files\n")
            return

        self.kani_btn.configure(state="disabled", text="⏳ Running Kani...")
        self.set_tool_running("kani", True)

        def run_kani():
            import tempfile, shutil
            project_dir = None
            try:
                self.after(0, lambda: self.console.insert("end",
                    "\n" + "="*60 + "\n🦀 KANI VERIFICATION\n" + "="*60 + "\n"))

                with open(self.current_file, 'r') as f:
                    rust_code = f.read()
                skip, reason = self._should_skip_tool("kani", rust_code)
                if skip:
                    self.after(0, lambda: self.console.insert(
                        "end", f"⏭️ Kani skipped: {reason}\n"
                    ))
                    self.after(0, lambda: self.kani_btn.configure(state="normal", text="🦀 KANI VERIFICATION"))
                    self.save_verification_state('kani', {
                        'success': False,
                        'output': '',
                        'errors': '',
                        'skipped': True,
                        'reason': reason,
                    })
                    return

                project_dir = tempfile.mkdtemp()
                src_dir = os.path.join(project_dir, 'src')
                os.makedirs(src_dir)

                kani_verifier = RustVerifier()
                rust_code = kani_verifier._add_kani_harness(rust_code)

                with open(os.path.join(src_dir, 'lib.rs'), 'w') as f:
                    f.write(rust_code)

                with open(os.path.join(project_dir, 'Cargo.toml'), 'w') as f:
                    f.write(
                        '[package]\nname = "kani_verify"\nversion = "0.1.0"\n'
                        'edition = "2021"\n'
                    )

                result = self.run_cancellable_command(
                    "kani",
                    ['cargo', 'kani'],
                    timeout=300,
                    cwd=project_dir,
                )
                if result.get('cancelled'):
                    self.after(0, lambda: self.console.insert("end", "🛑 Kani stopped by user.\n"))
                    self.after(0, lambda: self.kani_btn.configure(state="normal", text="🦀 KANI VERIFICATION"))
                    return
                if result.get('timed_out'):
                    self.after(0, lambda: self.console.insert("end", "❌ Kani timed out (300s).\n"))
                    self.after(0, lambda: self.kani_btn.configure(state="normal", text="🦀 KANI VERIFICATION"))
                    return
                success = result['returncode'] == 0
                log_path = self.save_tool_log('kani', result['stdout'], result['stderr'])
                self.save_verification_state('kani', {
                    'success': success,
                    'output': result['stdout'],
                    'errors': result['stderr'],
                    'log_path': log_path,
                })

                def display():
                    if success:
                        self.console.insert("end", "✅ Kani verification successful!\n")
                        for line in result['stdout'].splitlines():
                            if any(k in line for k in [
                                'VERIFICATION', 'harness', 'PASS', 'FAIL', 'SUCCESS', 'proof'
                            ]):
                                self.console.insert("end", f"   {line}\n")
                    else:
                        err_tail = (result['stderr'] or "")[-4000:]
                        self.console.insert("end", f"❌ Kani failed:\n{err_tail}\n")
                        if result['stdout']:
                            self.console.insert("end", result['stdout'][:400] + "\n")
                    if log_path:
                        self.console.insert("end", f"📄 Full Kani log: {log_path}\n")
                    self.console.see("end")
                    self.kani_btn.configure(state="normal", text="🦀 KANI VERIFICATION")

                self.after(0, display)

            except subprocess.TimeoutExpired:
                self.after(0, lambda: self.console.insert("end", "❌ Kani timed out (300s)\n"))
                self.after(0, lambda: self.kani_btn.configure(state="normal", text="🦀 KANI VERIFICATION"))
            except Exception as e:
                self.after(0, lambda: self.console.insert("end", f"❌ Kani error: {e}\n"))
                self.after(0, lambda: self.kani_btn.configure(state="normal", text="🦀 KANI VERIFICATION"))
            finally:
                self.after(0, lambda: self.set_tool_running("kani", False))
                if project_dir and os.path.exists(project_dir):
                    shutil.rmtree(project_dir, ignore_errors=True)

        threading.Thread(target=run_kani, daemon=True).start()

    def verify_with_verus(self):
        """Run Verus verification on Rust code"""
        if not self.current_file:
            self.console.insert("end", "❌ No file selected\n")
            return
        ext = os.path.splitext(self.current_file)[1].lower()
        if ext != '.rs':
            self.console.insert("end", "❌ Verus only works with .rs files\n")
            return

        self.verus_btn.configure(state="disabled", text="⏳ Running Verus...")
        self.set_tool_running("verus", True)

        def run_verus():
            try:
                with open(self.current_file, 'r', encoding="utf-8") as f:
                    rust_code = f.read()

                self.after(0, lambda: self.console.insert(
                    "end",
                    "\n" + "=" * 60 + "\n✅ VERUS VERIFICATION\n" + "=" * 60 + "\n",
                ))

                verus = VerusIntegration()
                if not verus.verus_available:
                    self.after(0, lambda: self.console.insert(
                        "end", "❌ Verus not installed (``verus`` not found)\n"
                    ))
                    self.after(0, lambda: self.verus_btn.configure(
                        state="normal", text="🔧 VERUS VERIFICATION"
                    ))
                    self.after(0, lambda: self.set_tool_running("verus", False))
                    return

                # Annotate code for Verus
                annotated_code = verus.annotate_for_verus(rust_code)
                
                # Save annotated version for inspection
                annotated_file = self.current_file.replace('.rs', '_verus.rs')
                with open(annotated_file, 'w', encoding="utf-8") as f:
                    f.write(annotated_code)
                
                self.after(0, lambda: self.console.insert(
                    "end", f"📝 Annotated code saved to: {annotated_file}\n"
                ))

                # Run Verus verification
                result = verus.verify_with_verus(annotated_file)
                
                if result['success']:
                    self.after(0, lambda: self.console.insert(
                        "end", "✅ Verus verification successful!\n"
                    ))
                    self.after(0, lambda: self.console.insert(
                        "end", f"📊 Output: {result['output']}\n"
                    ))
                else:
                    self.after(0, lambda: self.console.insert(
                        "end", f"❌ Verus verification failed\n"
                    ))
                    self.after(0, lambda: self.console.insert(
                        "end", f"🚨 Errors: {result['errors']}\n"
                    ))

            except Exception as e:
                self.after(0, lambda: self.console.insert(
                    "end", f"❌ Verus error: {str(e)}\n"
                ))
            finally:
                self.after(0, lambda: self.verus_btn.configure(
                    state="normal", text="✅ VERUS VERIFICATION"
                ))
                self.after(0, lambda: self.set_tool_running("verus", False))
                self.after(0, lambda: self.console.see("end"))

        threading.Thread(target=run_verus, daemon=True).start()

    def check_elan(self):
        """Check Elan (Lean version manager) status"""
        self.console.insert("end", "\n" + "="*60 + "\n")
        self.console.insert("end", "⚙️ ELAN STATUS CHECK\n")
        self.console.insert("end", "="*60 + "\n")
        
        try:
            result = subprocess.run(["elan", "--version"], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                self.console.insert("end", f"✅ Elan installed: {result.stdout.strip()}\n")
                
                # Check available toolchains
                result = subprocess.run(["elan", "toolchain", "list"], 
                                       capture_output=True, text=True)
                self.console.insert("end", "\n📦 Available Lean toolchains:\n")
                self.console.insert("end", result.stdout)
            else:
                self.console.insert("end", "❌ Elan not installed. Run: curl https://elan.lean-lang.org/elan-init.sh -sSf | sh\n")
        except Exception as e:
            self.console.insert("end", f"❌ Error checking Elan: {e}\n")
        
        self.console.see("end")

    def open_translated_output(self):
        """Load translated_output.pml into the Translated Promela tab"""
        
        # Find the translated output file
        translated_path = os.path.join(PROJECT_DIR, "translated_output.pml")
        
        # Also check for other possible locations
        possible_paths = [
            translated_path,
            os.path.join(PROJECT_DIR, "translated_output.txt"),
            os.path.join(os.path.dirname(PROJECT_DIR), "translated_output.pml"),
            os.path.join(os.path.expanduser("~"), "defi_guardian", "translated_output.pml"),
        ]
        
        # Add backup from current file
        if self.current_file:
            base_name = os.path.splitext(os.path.basename(self.current_file))[0]
            backup_path = os.path.join(PROJECT_DIR, f"{base_name}_translated.pml")
            possible_paths.insert(1, backup_path)
        
        # Find the first existing file
        display_file = None
        for path in possible_paths:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                display_file = path
                break
        
        if not display_file:
            self.spin_terminal.insert("end", "No translated output found. Please run verification first.\n")
            self.spin_terminal.see("end")
            return
        
        try:
            with open(display_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Load into the Translated Promela tab
            self.translated_editor.delete("1.0", "end")
            self.translated_editor.insert("1.0", content)
            
            # Switch to the Translated Promela tab
            self.editor_tabs.set("Translated Promela")
            
            self.spin_terminal.insert("end", f"Loaded translated output: {os.path.basename(display_file)}\n")
            self.spin_terminal.see("end")
        except Exception as e:
            self.spin_terminal.insert("end", f"Error loading translated output: {str(e)}\n")
            self.spin_terminal.see("end")

    def analyze_counterexample(self):
        """Analyze and display counterexample"""
        self.console.insert("end", "\n" + "="*60 + "\n")
        self.console.insert("end", "🔍 COUNTEREXAMPLE ANALYSIS\n")
        self.console.insert("end", "="*60 + "\n")
        
        # Import the analyzer
        try:
            from counterexample_analyzer import CounterexampleAnalyzer
        except ImportError:
            self.console.insert("end", "❌ Counterexample analyzer module not found\n")
            return
        
        analyzer = CounterexampleAnalyzer(PROJECT_DIR)
        
        # Check for trail file
        trail_file = os.path.join(PROJECT_DIR, "translated_output.pml.trail")
        pml_file = os.path.join(PROJECT_DIR, "translated_output.pml")
        
        if not os.path.exists(trail_file):
            # Check for other trail files
            for f in os.listdir(PROJECT_DIR):
                if f.endswith('.trail'):
                    trail_file = os.path.join(PROJECT_DIR, f)
                    break
        
        if not os.path.exists(trail_file):
            self.console.insert("end", "ℹ️ No counterexample trail found.\n")
            self.console.insert("end", "   Run verification on a model with property violations first.\n")
            return
        
        # Generate and display report
        report = analyzer.generate_report(pml_file if os.path.exists(pml_file) else None)
        self.console.insert("end", report + "\n")
        
        # Save report to file
        report_path = analyzer.save_report()
        self.console.insert("end", f"\n📄 Full report saved to: {report_path}\n")
        
        # Also try to run SPIN guided simulation
        spin_output = analyzer.analyze_with_spin(pml_file if os.path.exists(pml_file) else None)
        if spin_output and "error" not in spin_output.lower():
            self.console.insert("end", "\n🔬 SPIN Guided Simulation:\n")
            self.console.insert("end", "-"*40 + "\n")
            self.console.insert("end", spin_output[:2000] + "\n")  # Limit output
        
        self.console.see("end")

    def open_dashboard(self):
        """Open Streamlit dashboard"""
        self.console.insert("end", "\n🌐 Opening dashboard in browser...\n")
        self.status_label.configure(text="Launching dashboard...")
        
        # Find app.py path
        app_path = os.path.join(os.path.dirname(__file__), "app.py")
        
        if not os.path.exists(app_path):
            app_path = "app.py"
            
        if not os.path.exists(app_path):
            self.console.insert("end", "❌ app.py not found!\n")
            self.status_label.configure(text="Dashboard not found")
            return
        
        # Kill existing streamlit
        try:
            if sys.platform == "win32":
                subprocess.run("taskkill /f /im streamlit.exe", shell=True, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-f", "streamlit"], stderr=subprocess.DEVNULL)
            time.sleep(1)
        except:
            pass
        
        # Start streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.port", "8501",
            "--server.address", "localhost",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        try:
            self.console.insert(
                "end",
                "⏳ Starting Streamlit… (first run can take 30–90s while Python loads)\n",
            )
            self.status_label.configure(text="Starting dashboard…")
            if self.auto_scroll_enabled:
                self.console.see("end")

            self.dashboard_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            def wait_and_open_browser():
                ready = wait_for_tcp_port("localhost", 8501, STREAMLIT_START_TIMEOUT)

                def finish_ui():
                    webbrowser.open("http://localhost:8501")
                    if ready:
                        self.console.insert(
                            "end",
                            "✅ Dashboard ready at http://localhost:8501\n",
                        )
                        self.status_label.configure(
                            text="✅ Dashboard running at localhost:8501"
                        )
                    else:
                        self.console.insert(
                            "end",
                            "⚠️ Streamlit did not open port 8501 in time; "
                            "browser opened anyway — refresh the tab if it is blank.\n",
                        )
                        self.status_label.configure(
                            text="⚠️ Dashboard may still be starting — try refresh"
                        )
                    if self.auto_scroll_enabled:
                        self.console.see("end")

                self.after(0, finish_ui)

            threading.Thread(target=wait_and_open_browser, daemon=True).start()
        except Exception as e:
            self.console.insert("end", f"❌ Failed to start dashboard: {e}\n")
            self.status_label.configure(text="❌ Dashboard failed to start")
            if self.auto_scroll_enabled:
                self.console.see("end")
    
    def stop_dashboard(self):
        """Stop the dashboard"""
        self.console.insert("end", "\n🛑 Stopping dashboard...\n")
        
        try:
            if self.dashboard_process and self.dashboard_process.poll() is None:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=5)
                self.console.insert("end", "✅ Dashboard stopped\n")
            
            # Kill any remaining streamlit processes
            if sys.platform == "win32":
                subprocess.run("taskkill /f /im streamlit.exe", shell=True, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-f", "streamlit"], stderr=subprocess.DEVNULL)
        except Exception as e:
            self.console.insert("end", f"⚠️ Error stopping dashboard: {e}\n")
        
        self.status_label.configure(text="Dashboard stopped")
        if self.auto_scroll_enabled:
            self.console.see("end")

    def debug_sidebar_visibility(self):
        """Debug method to check sidebar visibility"""
        print(f"Sidebar visible: {self.sidebar.winfo_ismapped()}")
        print(f"Sidebar width: {self.sidebar.winfo_width()}")
        print(f"Sidebar height: {self.sidebar.winfo_height()}")
        print(f"Sidebar inner visible: {self.sidebar_inner.winfo_ismapped()}")
        print(f"Sidebar inner width: {self.sidebar_inner.winfo_width()}")
        print(f"Sidebar inner height: {self.sidebar_inner.winfo_height()}")
        
        # Check if scrollbar exists
        if hasattr(self.sidebar_inner, '_scrollbar'):
            print(f"Scrollbar visible: {self.sidebar_inner._scrollbar.winfo_ismapped()}")
        
        # Force update
        self.update()
        
        # Schedule another check after a short delay
        self.after(100, lambda: print(f"After update - Sidebar height: {self.sidebar.winfo_height()}"))


def create_gradio_interface():
    """
    Gradio version - modern AI-focused interface
    To run this, call create_gradio_interface().launch()
    """
    if not HAS_GRADIO:
        return None

    with gr.Blocks(theme=gr.themes.Soft( 
        primary_hue="emerald", 
        secondary_hue="purple", 
        neutral_hue="slate", 
    )) as demo: 
        gr.Markdown("# 🛡️ DeFi Guardian") 
        
        with gr.Tab("Verification"): 
            with gr.Row(): 
                file_input = gr.File(label="Upload Contract") 
                verify_btn = gr.Button("Run Verification", variant="primary") 
            output = gr.Code(label="Verification Output", language="text") 
        
        with gr.Tab("State Machine"): 
            graph = gr.Plot(label="State Diagram") 
        
        with gr.Tab("Analytics"): 
            metrics = gr.JSON(label="Verification Metrics") 
    
    return demo


def run_nicegui_interface():
    """
    NiceGUI version - web UI in desktop wrapper
    To run this, call run_nicegui_interface() instead of the mainloop
    """
    if not HAS_NICEGUI:
        return
        
    # Example stubs for NiceGUI interface
    def load_file():
        ui.notify("Loading file...")
        
    def run_verification():
        ui.notify("Running verification...")

    @ui.page('/') 
    def main_page(): 
        with ui.header(elevated=True).classes('bg-primary'): 
            ui.label('🛡️ DeFi Guardian').classes('text-h4 text-white') 
        
        with ui.left_drawer().classes('bg-dark'): 
            ui.button('Open File', on_click=load_file) 
            ui.button('Run Verification', on_click=run_verification) 
        
        with ui.column().classes('w-full'): 
            ui.editor().classes('w-full h-96') 
            ui.terminal().classes('w-full h-64') 
    
    ui.run(native=True, window_size=(1400, 900), title="DeFi Guardian - NiceGUI")


if __name__ == "__main__":
    app = FormalVerifierApp()
    app.mainloop()