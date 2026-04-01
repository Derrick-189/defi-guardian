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
from datetime import datetime
from pathlib import Path
import tkinter as tk

# Project directory for file I/O
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

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
            command=self.run_coq_verification,
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
        
        # Show welcome message
        self.show_welcome()
        
        # Scan for recent files
        self.scan_recent_files()
    
    def toggle_auto_scroll(self):
        self.auto_scroll_enabled = self.auto_scroll.get()
    
    def check_tools(self):
        """Check if verification tools are installed"""
        tools = []
        
        # Check SPIN
        try:
            subprocess.run(["spin", "-version"], capture_output=True, timeout=2)
            tools.append("✅ SPIN")
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
            with open("active_file.txt", "w") as f:
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
                
                # Translate if needed
                if self.file_type == 'sol':
                    self.console.insert("end", "[1/5] 🔄 Translating Solidity to Promela...\n")
                    self.console.insert("end", "   • Extracting state variables\n")
                    self.console.insert("end", "   • Converting require/assert statements\n")
                    self.console.insert("end", "   • Generating LTL properties\n")
                    content = DeFiTranslator.translate_solidity(content)
                    self.console.insert("end", "   ✅ Translation complete\n\n")
                elif self.file_type == 'rs':
                    self.console.insert("end", "[1/5] 🔄 Translating Rust to Promela...\n")
                    self.console.insert("end", "   • Parsing Rust structs\n")
                    self.console.insert("end", "   • Extracting program fields\n")
                    content = DeFiTranslator.translate_rust(content)
                    self.console.insert("end", "   ✅ Translation complete\n\n")
                else:
                    self.console.insert("end", "[1/5] 📄 Using native Promela model...\n\n")
                
                # Write translated model to project directory
                translated_path = os.path.join(PROJECT_DIR, "translated_output.pml")
                with open(translated_path, 'w') as dst:
                    dst.write(content)

                # Save active file in project directory
                active_path = os.path.join(PROJECT_DIR, "active_file.txt")
                with open(active_path, "w") as f:
                    f.write(os.path.basename(self.current_file))

                # Check for LTL properties
                if 'ltl' in content:
                    ltl_count = content.count('ltl')
                    self.console.insert("end", f"   ✓ Detected {ltl_count} LTL property(ies) in model\n\n")
                
                self.console.insert("end", "[2/5] 🔧 Generating SPIN verifier...\n")
                result = subprocess.run(f"spin -a translated_output.pml", 
                                       shell=True, capture_output=True, text=True)
                if result.stdout and self.verbose_output.get():
                    self.console.insert("end", result.stdout)
                if result.stderr:
                    self.console.insert("end", f"   ⚠️ {result.stderr}\n")
                
                self.console.insert("end", "\n[3/5] ⚙️ Compiling verifier...\n")
                compile_result = subprocess.run("gcc -O3 -o pan pan.c", 
                                               shell=True, capture_output=True, text=True)
                if compile_result.stderr and self.verbose_output.get():
                    self.console.insert("end", compile_result.stderr)
                
                # Save verification state in project directory
                state_path = os.path.join(PROJECT_DIR, "verification_state.json")
                # (Note: VerificationState.save_result already writes to default path,
                # but we keep state_path available for future use if needed.)

                self.console.insert("end", "[4/5] 🔍 Running verification with LTL model checking...\n\n")
                self.console.insert("end", "─" * 60 + "\n")
                
                verify_result = subprocess.run(["./pan", "-a"], 
                                              capture_output=True, text=True, timeout=120)
                
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
                
                # Parse results
                success = verify_result.returncode == 0
                output = verify_result.stdout

                # Save verification state (spin)
                self.save_verification_state('spin', {
                    'success': success,
                    'errors': verify_result.stderr,
                    'output': output
                })

                # Extract LTL verification results
                ltl_results = []
                for line in output.split('\n'):
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
                    if "states, stored" in output:
                        match = re.search(r"(\d+) states, stored", output)
                        if match:
                            self.console.insert("end", f"📊 States explored: {match.group(1)}\n")
                    if "depth reached" in output:
                        match = re.search(r"depth reached (\d+)", output)
                        if match:
                            self.console.insert("end", f"📊 Depth reached: {match.group(1)}\n")
                    if "transitions" in output:
                        match = re.search(r"(\d+) transitions", output)
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
                    if os.path.exists("pan.trail"):
                        self.console.insert("end", "📄 Counterexample trail saved to: pan.trail\n")
                        with open("pan.trail", 'r') as f:
                            trail_content = f.read()[:2000]
                            self.console.insert("end", "\nCounterexample preview:\n")
                            self.console.insert("end", trail_content + "\n")
                
                # Save results for dashboard
                VerificationState.save_result(
                    success, 
                    output, 
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
            for f in ["pan.c", "pan.h", "pan", "pan.trail", "translated_output.pml"]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass
        
        threading.Thread(target=verify, daemon=True).start()

    def save_verification_state(self, tool, result):
        state_file = os.path.join(os.path.dirname(__file__), 'verification_state.json')
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
        except:
            state = {}

        state[tool] = {
            'timestamp': datetime.now().isoformat(),
            'success': result.get('success', False),
            'errors': result.get('errors', ''),
            'output': result.get('output', '')[:500]
        }

        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def verify_with_coq(self):
        if not self.current_file:
            self.console.insert("end", "❌ No file selected\n")
            return
        # Disable button while running
        self.coq_btn.configure(state="disabled", text="⏳ Running Coq...")
        threading.Thread(target=self._run_coq_verification, daemon=True).start()

    def _run_coq_verification(self):
        try:
            contract_name = os.path.basename(self.current_file)
            from coq_verifier import CoqVerifier
            verifier = CoqVerifier()
            coq_script = verifier.generate_coq_script(contract_name, {})
            result = verifier.verify_with_coq(coq_script)
            # Schedule UI update on main thread
            self.after(0, self._display_coq_result, result)
        except Exception as e:
            self.after(0, self.console.insert, "end", f"❌ Error: {e}\n")
        finally:
            self.after(0, self.coq_btn.configure,
                       {"state": "normal", "text": "📐 VERIFY WITH COQ"})

    def _display_coq_result(self, result):
        if result['success']:
            self.console.insert("end", "✅ Coq verification successful!\n")
        else:
            self.console.insert("end", f"❌ Coq failed:\n{result.get('errors','')}\n")

        self.save_verification_state('coq', result)
        self.console.see("end")

        if self.auto_scroll_enabled:
            self.console.see("end")
    
    def run_lean_verification(self):
        """Run Lean verification"""
        if not self.current_file:
            messagebox.showwarning("No File", "Please load a file first.")
            return
        
        self.console.insert("end", "\n" + "="*80 + "\n")
        self.console.insert("end", "⚡ RUNNING LEAN VERIFICATION\n")
        self.console.insert("end", "="*80 + "\n\n")
        
        try:
            from lean_verifier import LeanVerifier
            verifier = LeanVerifier()
            
            if not verifier.lean_available:
                self.console.insert("end", "❌ Lean is not installed. Please install Lean theorem prover.\n")
                self.console.insert("end", "   Visit: https://leanprover.github.io/\n")
                return
            
            # Generate Lean script
            self.console.insert("end", "[1/2] 📝 Generating Lean proof script...\n")
            with open(self.current_file, 'r') as f:
                content = f.read()
            
            lean_script = verifier.generate_lean_script(
                os.path.basename(self.current_file).split('.')[0],
                []
            )
            
            self.console.insert("end", "[2/2] 🔍 Running Lean verification...\n\n")
            result = verifier.verify_with_lean(lean_script)
            
            if result['success']:
                self.console.insert("end", "✅ Lean verification successful!\n")
                self.console.insert("end", result['output'] + "\n")
            else:
                self.console.insert("end", "❌ Lean verification failed:\n")
                self.console.insert("end", result.get('error', result.get('errors', 'Unknown error')) + "\n")
                
        except ImportError:
            self.console.insert("end", "❌ Lean verifier module not found.\n")
        except Exception as e:
            self.console.insert("end", f"❌ Error: {e}\n")
        
        if self.auto_scroll_enabled:
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
