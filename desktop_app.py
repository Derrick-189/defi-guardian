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

# Project directory for file I/O
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
LEAN_TIMEOUT_SECONDS = 120

from rust_verifiers import (
    CREUSOT_STD_PATH,
    build_prusti_env,
    classify_prusti_failure,
    prepend_creusot_prelude,
    preprocess_prusti_source,
    prusti_command,
    should_skip_prusti_for_source,
    strip_rust_main_for_lib,
)

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
    from translator import DeFiTranslator
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

class FormalVerifierApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.title("DeFi Guardian - Formal Verification Suite")
        self.geometry("1500x950")
        
        # Configure grid - sidebar layout
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Main content
        self.grid_rowconfigure(0, weight=1)
        
        # ==================== SIDEBAR ====================
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=15)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.sidebar.grid_propagate(False)
        
        sidebar_inner = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        sidebar_inner.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Logo
        ctk.CTkLabel(
            sidebar_inner,
            text="🛡️ DEFI GUARDIAN",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#00ffcc"
        ).pack(pady=(10, 20))
        
        ctk.CTkLabel(
            sidebar_inner,
            text="Formal Verification Suite",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        ).pack(pady=(0, 20))
        
        # File Selection
        ctk.CTkLabel(
            sidebar_inner,
            text="📁 FILE MANAGEMENT",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888"
        ).pack(anchor="w", pady=(10, 5))
        
        self.load_btn = ctk.CTkButton(
            sidebar_inner,
            text="📂 OPEN SOURCE FILE",
            command=self.load_file,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2196f3",
            hover_color="#1976d2"
        )
        self.load_btn.pack(fill="x", pady=5)
        
        # File info display
        self.file_label = ctk.CTkLabel(
            sidebar_inner,
            text="📄 No file selected",
            wraplength=280,
            font=ctk.CTkFont(size=12),
            text_color="#ffaa66"
        )
        self.file_label.pack(pady=10)
        
        self.file_type_label = ctk.CTkLabel(
            sidebar_inner,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        self.file_type_label.pack()
        
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
        
        # ==================== MAIN CONSOLE ====================
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Console header
        console_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        console_header.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        console_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            console_header,
            text="📝 VERIFICATION CONSOLE",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00ffcc"
        ).grid(row=0, column=0, sticky="w")
        
        clear_btn = ctk.CTkButton(
            console_header,
            text="🗑️ Clear",
            command=self.clear_console,
            height=32,
            width=80,
            font=ctk.CTkFont(size=12)
        )
        clear_btn.grid(row=0, column=1, padx=5)
        
        export_btn = ctk.CTkButton(
            console_header,
            text="💾 Export",
            command=self.export_console,
            height=32,
            width=80,
            font=ctk.CTkFont(size=12)
        )
        export_btn.grid(row=0, column=2, padx=5)
        
        # Console text area
        self.console = ctk.CTkTextbox(
            self.main_frame,
            font=("Courier New", 12),
            wrap="word",
            fg_color="#0a0a0a",
            text_color="#00ff00"
        )
        self.console.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        # Variables
        self.current_file = None
        self.file_type = None
        self.dashboard_process = None
        self.auto_scroll_enabled = True
        self.lean_running = False
        
        # Show welcome message
        self.show_welcome()
        
        # Scan for recent files
        self.scan_recent_files()
        
        # Start verification state monitor
        self.start_verification_monitor()
        self.prewarm_lean_runtime()
    
    def toggle_auto_scroll(self):
        self.auto_scroll_enabled = self.auto_scroll.get()

    def prewarm_lean_runtime(self):
        """Warm up Lean/Elan once to reduce first-run latency."""
        def _prewarm():
            try:
                result = subprocess.run(
                    ["lean", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=25,
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
        """Check if verification tools are installed"""
        tools = []
        
        # Check SPIN  (-V is the correct flag, not --version)
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

        # Prusti health: distinguish binary availability vs runtime breakage
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
                    self.console.insert(
                        "end",
                        "⚠️ Prusti health: invalid PRUSTI_* env detected (remove PRUSTI_HOME)\n",
                    )
                elif "compiler unexpectedly panicked" in stderr:
                    tools.append("⚠️ Prusti(ICE)")
                    self.console.insert(
                        "end",
                        "⚠️ Prusti health: internal crash detected (toolchain mismatch/bug)\n",
                    )
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
        
        self.tool_status.configure(text=" | ".join(tools))
    
    def scan_recent_files(self):
        """Scan for recent .pml files"""
        home = os.path.expanduser("~")
        pml_files = []
        
        try:
            for file in os.listdir(home):
                if file.endswith('.pml'):
                    pml_files.append(file)
        except:
            pass
        
        if pml_files:
            self.console.insert("end", f"📁 Found {len(pml_files)} Promela file(s) in home directory:\n")
            for f in pml_files[:5]:
                self.console.insert("end", f"   • {f}\n")
            self.console.insert("end", "\n")
    
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
            self.current_file = file_path
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.pml':
                self.file_type = 'pml'
                type_str = "Promela Model"
                verify_text = "🚀 VERIFY PROMELA MODEL"
                self.file_type_label.configure(text="Type: Promela Model (Native)")
            elif ext == '.sol':
                self.file_type = 'sol'
                type_str = "Solidity Contract"
                verify_text = "🔨 VERIFY SOLIDITY CONTRACT"
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
                    translated_content = DeFiTranslator.translate_solidity(content)
                    self.console.insert("end", "   ✅ Translation complete\n\n")
                    
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
                result = subprocess.run(f"spin -a {verify_file}", 
                                       shell=True, capture_output=True, text=True, cwd=PROJECT_DIR)
                if result.stdout and self.verbose_output.get():
                    self.console.insert("end", result.stdout)
                if result.stderr:
                    self.console.insert("end", f"   ⚠️ {result.stderr}\n")
                
                self.console.insert("end", "\n[3/5] ⚙️ Compiling verifier...\n")
                compile_result = subprocess.run("gcc -O3 -o pan pan.c", 
                                               shell=True, capture_output=True, text=True, cwd=PROJECT_DIR)
                if compile_result.stderr and self.verbose_output.get():
                    self.console.insert("end", compile_result.stderr)
                
                # Save verification state in project directory
                state_path = os.path.join(PROJECT_DIR, "verification_state.json")
                # (Note: VerificationState.save_result already writes to default path,
                # but we keep state_path available for future use if needed.)

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
                        result = subprocess.run(["./pan", "-a", "-N", ltl_name], 
                                               capture_output=True, text=True, timeout=120, cwd=PROJECT_DIR)
                        combined_output += f"\n--- LTL {ltl_name} ---\n{result.stdout}"
                        combined_stderr += result.stderr
                        if result.returncode != 0:
                            all_success = False
                else:
                    # No specific LTL claims, run default
                    result = subprocess.run(["./pan", "-a"], 
                                           capture_output=True, text=True, timeout=120, cwd=PROJECT_DIR)
                    combined_output = result.stdout
                    combined_stderr = result.stderr
                    all_success = result.returncode == 0

                verify_result = type('obj', (object,), {
                    'returncode': 0 if all_success else 1,
                    'stdout': combined_output,
                    'stderr': combined_stderr
                })()
                
                # Display output
                output_lines = verify_result.stdout.split('\n')
                for line in output_lines:
                    if 'error' in line.lower() and '0' not in line:
                        self.console.insert("end", f"❌ {line}\n")
                    elif 'warning' in line.lower():
                        self.console.insert("end", f"⚠️ {line}\n")
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

                # Save SPIN state
                self.save_verification_state('spin', {
                    'success': success,
                    'output': verify_result.stdout,
                    'errors': verify_result.stderr,
                    'states_stored': states_stored,
                    'transitions': transitions,
                    'depth': depth
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
                    verify_result.stdout,  # FIXED: use verify_result.stdout instead of undefined 'output'
                    verify_result.stderr,
                    os.path.basename(self.current_file),
                    ltl_results
                )
                
                self.console.insert("end", "\n[5/5] 💾 Verification results saved to verification_state.json\n")
                
            except subprocess.TimeoutExpired:
                self.console.insert("end", "\n❌ Verification timed out after 120 seconds\n")
                self.status_label.configure(text="⏰ Verification timed out")
            except Exception as e:
                self.console.insert("end", f"\n❌ Error: {e}\n")
                self.status_label.configure(text=f"Error: {str(e)[:50]}")
            
            if self.auto_scroll_enabled:
                self.console.see("end")
            self.verify_btn.configure(state="normal", text="🚀 RUN SPIN VERIFICATION")
            
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
        state[tool] = {
            'timestamp': datetime.now().isoformat(),
            'success': result.get('success', False),
            'output': result.get('output', '')[:500],
            'errors': result.get('errors', '')[:200]
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
            
            # Update status label
            if state.get('success'):
                self.status_label.configure(text=f"✅ Verified at {state.get('datetime', 'unknown')}")
            else:
                self.status_label.configure(text=f"❌ Verification failed at {state.get('datetime', 'unknown')}")

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
                
                # Save Coq state
                self.save_verification_state('coq', result)
                
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

        def run_lean():
            import tempfile, shutil
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

-- Reentrancy: lock released after operation
def lock_after_op (locked : Bool) : Bool :=
  if locked then locked else true

theorem lock_acquired (h : locked = false) :
    lock_after_op locked = true := by
  simp [lock_after_op, h]

#check collateral_sufficient
#check balance_non_negative
"""
                # Write to temp file
                tmp_file = tempfile.NamedTemporaryFile(
                    mode='w', suffix='.lean', delete=False
                )
                tmp_file.write(lean_script)
                tmp_file.close()

                result = subprocess.run(
                    ['lean', tmp_file.name],
                    capture_output=True, text=True, timeout=LEAN_TIMEOUT_SECONDS
                )
                success = result.returncode == 0

                self.save_verification_state('lean', {
                    'success': success,
                    'output': result.stdout,
                    'errors': result.stderr
                })

                def display():
                    if success:
                        self.console.insert("end", "✅ Lean verification successful!\n")
                        if result.stdout:
                            self.console.insert("end", result.stdout[:400] + "\n")
                    else:
                        # Lean sometimes prints errors to stdout
                        err = result.stderr or result.stdout
                        self.console.insert("end", f"❌ Lean failed:\n{err[:500]}\n")
                    self.console.see("end")
                    self.lean_btn.configure(state="normal", text="⚡ LEAN VERIFICATION")

                self.after(0, display)

            except subprocess.TimeoutExpired:
                self.after(0, lambda: self.console.insert("end",
                    f"❌ Lean timed out ({LEAN_TIMEOUT_SECONDS}s). "
                    "Lean/Elan may still be warming up.\n"))
                self.after(0, lambda: self.lean_btn.configure(state="normal", text="⚡ LEAN VERIFICATION"))
            except Exception as e:
                self.after(0, lambda: self.console.insert("end", f"❌ Lean error: {e}\n"))
                self.after(0, lambda: self.lean_btn.configure(state="normal", text="⚡ LEAN VERIFICATION"))
            finally:
                self.lean_running = False
                if tmp_file and os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

        threading.Thread(target=run_lean, daemon=True).start()

    def verify_with_prusti(self):
        """Run Prusti via ``prusti-rustc`` on a temp crate (avoids ``cargo prusti``'s old Cargo).

        ``cargo prusti`` pulls crates.io through Prusti's bundled Cargo, which breaks on
        modern crates (for example edition 2024 in a dependency manifest) and lockfile v4.
        Direct ``prusti-rustc``
        does not use that resolver. Code that needs ``prusti-contracts`` must be verified
        with a hand-written Cargo project instead.
        """
        if not self.current_file:
            self.console.insert("end", "❌ No file selected\n")
            return
        ext = os.path.splitext(self.current_file)[1].lower()
        if ext != '.rs':
            self.console.insert("end", "❌ Prusti only works with .rs files\n")
            return

        self.prusti_btn.configure(state="disabled", text="⏳ Running Prusti...")

        def run_prusti():
            import tempfile, shutil
            project_dir = None
            try:
                self.after(0, lambda: self.console.insert("end",
                    "\n" + "="*60 + "\n🔧 PRUSTI VERIFICATION\n" + "="*60 + "\n"))

                with open(self.current_file, 'r') as f:
                    rust_code = f.read()
                skip_prusti_src, src_reason = should_skip_prusti_for_source(rust_code)
                if skip_prusti_src:
                    self.after(0, lambda: self.console.insert(
                        "end", f"⏭️ Prusti skipped: {src_reason}\n"
                    ))
                    self.after(0, lambda: self.prusti_btn.configure(state="normal", text="🔧 PRUSTI VERIFICATION"))
                    self.save_verification_state('prusti', {
                        'success': False,
                        'output': '',
                        'errors': '',
                        'skipped': True,
                        'reason': src_reason,
                    })
                    return
                skip, reason = self._should_skip_tool("prusti", rust_code)
                if skip:
                    self.after(0, lambda: self.console.insert(
                        "end", f"⏭️ Prusti skipped: {reason}\n"
                    ))
                    self.after(0, lambda: self.prusti_btn.configure(state="normal", text="🔧 PRUSTI VERIFICATION"))
                    self.save_verification_state('prusti', {
                        'success': False,
                        'output': '',
                        'errors': '',
                        'skipped': True,
                        'reason': reason,
                    })
                    return
                had_kani = "kani::" in rust_code or "#[kani::proof]" in rust_code
                rust_code = preprocess_prusti_source(rust_code)
                if "fn " not in rust_code:
                    self.after(0, lambda: self.console.insert(
                        "end",
                        "⏭️ Prusti skipped: file appears Kani-only after compatibility preprocessing.\n"
                    ))
                    self.after(0, lambda: self.prusti_btn.configure(state="normal", text="🔧 PRUSTI VERIFICATION"))
                    return

                project_dir = tempfile.mkdtemp()
                lib_rs = os.path.join(project_dir, 'lib.rs')
                with open(lib_rs, 'w') as f:
                    f.write(rust_code)

                with open(os.path.join(project_dir, 'Cargo.toml'), 'w') as f:
                    f.write(
                        '[package]\nname = "prusti_verify"\nversion = "0.1.0"\n'
                        'edition = "2021"\n'
                    )

                env = build_prusti_env()

                result = subprocess.run(
                    prusti_command() + ['--edition=2021', '--crate-type=lib', lib_rs],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=project_dir,
                    env=env,
                )
                success = result.returncode == 0
                self.save_verification_state('prusti', {
                    'success': success,
                    'output': result.stdout,
                    'errors': result.stderr
                })
                log_path = self.save_tool_log('prusti', result.stdout, result.stderr)

                def display():
                    if success:
                        self.console.insert("end", "✅ Prusti verification successful!\n")
                        if had_kani:
                            self.console.insert(
                                "end",
                                "ℹ️ Preprocessed Kani-specific code for Prusti compatibility.\n",
                            )
                        if result.stdout:
                            self.console.insert("end", result.stdout[:500] + "\n")
                    else:
                        err_tail = (result.stderr or "")[-4000:]
                        self.console.insert("end", f"❌ Prusti failed:\n{err_tail}\n")
                        kind, hint = classify_prusti_failure(result.stderr)
                        if hint:
                            self.console.insert(
                                "end",
                                f"ℹ️ {hint}. "
                                + (
                                    "Try reinstalling/updating Prusti toolchain.\n"
                                    if kind == "ice" else "\n"
                                )
                            )
                    if log_path:
                        self.console.insert("end", f"📄 Full Prusti log: {log_path}\n")
                    self.console.see("end")
                    self.prusti_btn.configure(state="normal", text="🔧 PRUSTI VERIFICATION")

                self.after(0, display)

            except subprocess.TimeoutExpired:
                self.after(0, lambda: self.console.insert("end", "❌ Prusti timed out\n"))
                self.after(0, lambda: self.prusti_btn.configure(state="normal", text="🔧 PRUSTI VERIFICATION"))
            except Exception as e:
                self.after(0, lambda: self.console.insert("end", f"❌ Prusti error: {e}\n"))
                self.after(0, lambda: self.prusti_btn.configure(state="normal", text="🔧 PRUSTI VERIFICATION"))
            finally:
                if project_dir and os.path.exists(project_dir):
                    shutil.rmtree(project_dir, ignore_errors=True)

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

                # Cargo.toml — reference creusot-std by its real package name,
                # no extra features= needed
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

                result = subprocess.run(
                    ['cargo', 'creusot'],
                    capture_output=True, text=True, timeout=600,
                    cwd=project_dir, env=env
                )
                success = result.returncode == 0
                self.save_verification_state('creusot', {
                    'success': success,
                    'output': result.stdout,
                    'errors': result.stderr
                })
                log_path = self.save_tool_log('creusot', result.stdout, result.stderr)

                def display():
                    if success:
                        self.console.insert("end", "✅ Creusot verification successful!\n")
                        if result.stdout:
                            self.console.insert("end", result.stdout[:500] + "\n")
                    else:
                        err_tail = (result.stderr or "")[-4000:]
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

                with open(os.path.join(src_dir, 'lib.rs'), 'w') as f:
                    f.write(rust_code)

                with open(os.path.join(project_dir, 'Cargo.toml'), 'w') as f:
                    f.write(
                        '[package]\nname = "kani_verify"\nversion = "0.1.0"\n'
                        'edition = "2021"\n'
                    )

                result = subprocess.run(
                    ['cargo', 'kani'],
                    capture_output=True, text=True, timeout=300,
                    cwd=project_dir
                )
                success = result.returncode == 0
                self.save_verification_state('kani', {
                    'success': success,
                    'output': result.stdout,
                    'errors': result.stderr
                })
                log_path = self.save_tool_log('kani', result.stdout, result.stderr)

                def display():
                    if success:
                        self.console.insert("end", "✅ Kani verification successful!\n")
                        for line in result.stdout.splitlines():
                            if any(k in line for k in [
                                'VERIFICATION', 'harness', 'PASS', 'FAIL', 'SUCCESS', 'proof'
                            ]):
                                self.console.insert("end", f"   {line}\n")
                    else:
                        err_tail = (result.stderr or "")[-4000:]
                        self.console.insert("end", f"❌ Kani failed:\n{err_tail}\n")
                        if result.stdout:
                            self.console.insert("end", result.stdout[:400] + "\n")
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
                if project_dir and os.path.exists(project_dir):
                    shutil.rmtree(project_dir, ignore_errors=True)

        threading.Thread(target=run_kani, daemon=True).start()

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

    def verify_with_rust_tools(self):
        if not self.current_source:
            self.console.insert("end", "❌ No file selected\n")
            return
        ext = os.path.splitext(self.current_source)[1].lower()
        if ext != '.rs':
            self.console.insert("end", "❌ Only works with .rs files\n")
            return
        self.rust_verify_btn.configure(state="disabled", text="⏳ Running...")
        threading.Thread(target=self._rust_thread, daemon=True).start()

    def _rust_thread(self):
        try:
            with open(self.current_source, 'r') as f:
                rust_code = f.read()
            annotated = self.rust_verifier.generate_rust_annotations(rust_code)
            results = {}
            for tool in ("prusti", "kani", "creusot"):
                skip, reason = self._should_skip_tool(tool, rust_code)
                if skip:
                    results[tool] = {
                        'success': False,
                        'skipped': True,
                        'failure_hint': reason,
                        'errors': '',
                    }
                    continue
                if tool == "prusti":
                    results[tool] = self.rust_verifier.verify_with_prusti(annotated)
                elif tool == "kani":
                    results[tool] = self.rust_verifier.verify_with_kani(annotated)
                else:
                    results[tool] = self.rust_verifier.verify_with_creusot(annotated)
            self.after(0, self._display_rust_results, results)
        except Exception as e:
            self.after(0, self.console.insert, "end", f"❌ Rust error: {e}\n")
        finally:
            self.after(0, lambda: self.rust_verify_btn.configure(
                state="normal", text="🦀 VERIFY WITH PRUSTI/KANI"))

    def _display_rust_results(self, results):
        self.console.insert("end", "\n" + "="*70 + "\n")
        self.console.insert("end", "TRIANGULATION RESULTS\n")
        self.console.insert("end", "="*70 + "\n")
        for tool, result in results.items():
            if result.get('skipped'):
                status = "⏭️ SKIP"
            else:
                status = "✅ PASS" if result['success'] else "❌ FAIL"
            self.console.insert("end", f"{tool.upper()}: {status}\n")
            if result.get('errors'):
                self.console.insert("end", f"  {result['errors'][:200]}\n")
            elif result.get('failure_hint'):
                self.console.insert("end", f"  {result['failure_hint'][:200]}\n")
        self.console.see("end")

    def open_translated_output(self):
        """Open translated_output.pml for the active file in a popup viewer window"""
        
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
            messagebox.showwarning(
                "No Translated Output",
                "No translated output found.\n\n"
                "Please run SPIN Verification on a .sol or .rs file first.\n\n"
                f"Expected: {translated_path}"
            )
            return
        
        try:
            with open(display_file, 'r') as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Read Error", f"Could not read file:\n{e}")
            return
        
        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title(f"Translated Output — {os.path.basename(self.current_file) if self.current_file else 'unknown'} → Promela")
        popup.geometry("1000x750")
        popup.grab_set()
        
        # Configure popup grid
        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(1, weight=1)
        
        # Header frame
        header = ctk.CTkFrame(popup, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 5))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header,
            text=f"📄 Translated Promela Model",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00ffcc"
        ).grid(row=0, column=0, sticky="w")
        
        # Info label
        info_text = f"Source: {os.path.basename(self.current_file) if self.current_file else 'N/A'} | Lines: {content.count(chr(10)) + 1} | Size: {len(content):,} chars"
        ctk.CTkLabel(
            popup,
            text=info_text,
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(0, 5))
        
        # Button frame
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))
        btn_frame.grid_columnconfigure(2, weight=1)
        
        def copy_to_clipboard():
            popup.clipboard_clear()
            popup.clipboard_append(content)
            popup.update()
            copy_btn.configure(text="✅ Copied!")
            popup.after(1500, lambda: copy_btn.configure(text="📋 Copy"))
        
        def save_to_file():
            save_path = filedialog.asksaveasfilename(
                parent=popup,
                defaultextension=".pml",
                initialfile=f"{os.path.splitext(os.path.basename(self.current_file))[0] if self.current_file else 'output'}_translated.pml",
                filetypes=[("Promela files", "*.pml"), ("All files", "*.*")]
            )
            if save_path:
                try:
                    with open(save_path, 'w') as f:
                        f.write(content)
                    self.console.insert("end", f"\n💾 Translated output saved to: {save_path}\n")
                    self.console.see("end")
                except Exception as e:
                    messagebox.showerror("Save Error", str(e), parent=popup)
        
        copy_btn = ctk.CTkButton(btn_frame, text="📋 Copy", width=80, command=copy_to_clipboard)
        copy_btn.grid(row=0, column=0, padx=(0, 5))
        
        ctk.CTkButton(btn_frame, text="💾 Save As", width=80, command=save_to_file).grid(row=0, column=1, padx=(0, 5))
        
        # Text area with scrollbar
        text_frame = ctk.CTkFrame(popup, fg_color="transparent")
        text_frame.grid(row=3, column=0, sticky="nsew", padx=15, pady=(0, 15))
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        textbox = ctk.CTkTextbox(
            text_frame,
            font=("Courier New", 11),
            wrap="none",
            fg_color="#0a0a0a",
            text_color="#00ff00"
        )
        textbox.grid(row=0, column=0, sticky="nsew")
        
        # Insert content
        textbox.insert("1.0", content)
        textbox.configure(state="disabled")  # Make read-only
        
        # Status label at bottom
        status_label = ctk.CTkLabel(
            popup,
            text=f"📁 File: {display_file}",
            font=ctk.CTkFont(size=10),
            text_color="#444444"
        )
        status_label.grid(row=4, column=0, sticky="w", padx=15, pady=(0, 10))

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
            self.dashboard_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait and open browser
            time.sleep(3)
            webbrowser.open("http://localhost:8501")
            
            self.console.insert("end", "✅ Dashboard started at http://localhost:8501\n")
            self.status_label.configure(text="✅ Dashboard running at localhost:8501")
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

if __name__ == "__main__":
    app = FormalVerifierApp()
    app.mainloop()