#!/usr/bin/env python3
"""
DeFi Guardian - Desktop Launcher Application
Working version for defi_guardian directory
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import sys
import webbrowser
import threading
import time
import socket
from pathlib import Path

STREAMLIT_START_TIMEOUT = float(os.environ.get("DG_STREAMLIT_START_TIMEOUT", "120"))


def _wait_for_tcp_port(host: str, port: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2.0):
                return True
        except OSError:
            time.sleep(0.25)
    return False


class DeFiGuardianLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DeFi Guardian Launcher")
        self.root.geometry("800x550")
        self.root.resizable(False, False)
        
        # Get the directory where this script is located
        self.base_dir = Path(__file__).parent.absolute()
        
        # Variables
        self.dashboard_process = None
        self.desktop_process = None
        self.dashboard_running = False
        self.desktop_running = False
        
        # Find app files
        self.desktop_path = self.base_dir / "desktop_app.py"
        self.dashboard_path = self.base_dir / "app.py"
        
        # Check if files exist
        if not self.desktop_path.exists():
            # Try alternative names
            alt_names = ["desktop_app_complete.py", "defi_guardian_desktop.py"]
            for name in alt_names:
                alt_path = self.base_dir / name
                if alt_path.exists():
                    self.desktop_path = alt_path
                    break
        
        if not self.dashboard_path.exists():
            alt_names = ["dashboard.py", "app_final.py", "app_complete.py"]
            for name in alt_names:
                alt_path = self.base_dir / name
                if alt_path.exists():
                    self.dashboard_path = alt_path
                    break
        
        # Center window
        self.center_window()
        
        # Configure style
        self.root.configure(bg="#0a0a0a")
        
        # Create UI
        self.create_ui()
        
        # Start status update
        self.update_status()
        
        # Set up close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_ui(self):
        """Create the main UI"""
        # Main container
        main_container = tk.Frame(self.root, bg="#0a0a0a")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        title = tk.Label(
            main_container,
            text="🛡️ DeFi Guardian",
            font=("Segoe UI", 28, "bold"),
            fg="#00ffcc",
            bg="#0a0a0a"
        )
        title.pack(pady=(0, 10))
        
        subtitle = tk.Label(
            main_container,
            text="Formal Verification Suite",
            font=("Segoe UI", 12),
            fg="#888888",
            bg="#0a0a0a"
        )
        subtitle.pack()
        
        # Description
        desc = tk.Label(
            main_container,
            text="Powered by SPIN Model Checker | LTL Properties | Coq Theorem Prover",
            font=("Segoe UI", 10),
            fg="#666666",
            bg="#0a0a0a",
            justify="center"
        )
        desc.pack(pady=10)
        
        # Info frame
        info_frame = tk.Frame(main_container, bg="#1a1a2e", relief="solid", bd=1)
        info_frame.pack(fill="x", pady=10)
        
        tk.Label(
            info_frame,
            text=f"📁 Working Directory: {self.base_dir}",
            font=("Courier", 10),
            fg="#00ffcc",
            bg="#1a1a2e"
        ).pack(anchor="w", padx=10, pady=5)
        
        # Desktop app status
        if self.desktop_path.exists():
            tk.Label(
                info_frame,
                text=f"✅ Desktop App: {self.desktop_path.name}",
                font=("Courier", 10),
                fg="#00ffcc",
                bg="#1a1a2e"
            ).pack(anchor="w", padx=10, pady=2)
        else:
            tk.Label(
                info_frame,
                text="❌ Desktop App: Not Found",
                font=("Courier", 10),
                fg="#ff4444",
                bg="#1a1a2e"
            ).pack(anchor="w", padx=10, pady=2)
        
        # Dashboard status
        if self.dashboard_path.exists():
            tk.Label(
                info_frame,
                text=f"✅ Dashboard: {self.dashboard_path.name}",
                font=("Courier", 10),
                fg="#00ffcc",
                bg="#1a1a2e"
            ).pack(anchor="w", padx=10, pady=2)
        else:
            tk.Label(
                info_frame,
                text="❌ Dashboard: Not Found",
                font=("Courier", 10),
                fg="#ff4444",
                bg="#1a1a2e"
            ).pack(anchor="w", padx=10, pady=2)
        
        # Buttons frame
        buttons_frame = tk.Frame(main_container, bg="#0a0a0a")
        buttons_frame.pack(pady=20)
        
        # Desktop App Button
        self.desktop_btn = tk.Button(
            buttons_frame,
            text="Launch Desktop App",
            font=("Segoe UI", 14, "bold"),
            bg="#27ae60" if self.desktop_path.exists() else "#555555",
            fg="white",
            activebackground="#2e7d32",
            cursor="hand2" if self.desktop_path.exists() else "arrow",
            bd=0,
            padx=30,
            pady=15,
            command=self.launch_desktop if self.desktop_path.exists() else None,
            state="normal" if self.desktop_path.exists() else "disabled"
        )
        self.desktop_btn.pack(pady=10)
        
        # Dashboard Button
        self.dashboard_btn = tk.Button(
            buttons_frame,
            text="Launch Dashboard",
            font=("Segoe UI", 14, "bold"),
            bg="#9b59b6" if self.dashboard_path.exists() else "#555555",
            fg="white",
            activebackground="#8e44ad",
            cursor="hand2" if self.dashboard_path.exists() else "arrow",
            bd=0,
            padx=30,
            pady=15,
            command=self.launch_dashboard if self.dashboard_path.exists() else None,
            state="normal" if self.dashboard_path.exists() else "disabled"
        )
        self.dashboard_btn.pack(pady=10)
        
        # Status text
        self.status_text = tk.Text(
            main_container,
            height=12,
            bg="#1a1a2e",
            fg="#00ff00",
            font=("Courier", 10),
            bd=1,
            relief="solid",
            wrap="word"
        )
        self.status_text.pack(fill="both", expand=True, pady=10)
        
        # Footer buttons
        footer = tk.Frame(main_container, bg="#0a0a0a")
        footer.pack(fill="x", pady=(10, 0))
        
        tk.Button(
            footer,
            text="Stop All",
            font=("Segoe UI", 10),
            bg="#721c24",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=5,
            command=self.stop_all
        ).pack(side="left", padx=5)
        
        tk.Button(
            footer,
            text="Refresh",
            font=("Segoe UI", 10),
            bg="#555555",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=5,
            command=self.refresh
        ).pack(side="left", padx=5)
        
        tk.Button(
            footer,
            text="Exit",
            font=("Segoe UI", 10),
            bg="#555555",
            fg="white",
            cursor="hand2",
            bd=0,
            padx=15,
            pady=5,
            command=self.on_closing
        ).pack(side="right", padx=5)
        
        # Initial status
        self.status_text.insert(tk.END, "✅ DeFi Guardian Launcher Ready\n")
        self.status_text.insert(tk.END, f"📁 Directory: {self.base_dir}\n\n")
        
        if self.desktop_path.exists():
            self.status_text.insert(tk.END, f"✅ Found: {self.desktop_path.name}\n")
        else:
            self.status_text.insert(tk.END, "❌ desktop_app.py not found!\n")
        
        if self.dashboard_path.exists():
            self.status_text.insert(tk.END, f"✅ Found: {self.dashboard_path.name}\n")
        else:
            self.status_text.insert(tk.END, "❌ app.py not found!\n")
        
        self.status_text.insert(tk.END, "\nClick buttons above to launch applications.\n")
    
    def update_status(self):
        """Update status display"""
        # Clear and update running status
        current = self.status_text.get("1.0", tk.END)
        
        # Find where to insert status
        if "Running:" in current:
            # Remove old running status lines
            lines = current.split('\n')
            new_lines = []
            for line in lines:
                if not any(x in line for x in ["Desktop App: Running", "Dashboard: Running"]):
                    new_lines.append(line)
            current = '\n'.join(new_lines)
            self.status_text.delete("1.0", tk.END)
            self.status_text.insert("1.0", current)
        
        # Add current running status
        if self.desktop_running:
            self.status_text.insert(tk.END, f"🟢 Desktop App: Running (PID: {self.desktop_process.pid if self.desktop_process else 'N/A'})\n")
            self.desktop_btn.config(text="Desktop App Running", bg="#555555", state="disabled")
        else:
            self.desktop_btn.config(text="Launch Desktop App", bg="#27ae60", state="normal")
        
        if self.dashboard_running:
            self.status_text.insert(tk.END, f"🟢 Dashboard: Running on http://localhost:8501\n")
            self.dashboard_btn.config(text="Dashboard Running", bg="#555555", state="disabled")
        else:
            self.dashboard_btn.config(text="Launch Dashboard", bg="#9b59b6", state="normal")
        
        self.root.after(2000, self.update_status)
    
    def launch_desktop(self):
        """Launch the desktop application"""
        if self.desktop_running:
            messagebox.showinfo("Already Running", "Desktop app is already running!")
            return
        
        def run():
            try:
                self.status_text.insert(tk.END, f"\n🚀 Launching: {self.desktop_path.name}\n")
                self.status_text.see(tk.END)
                
                self.desktop_process = subprocess.Popen(
                    [sys.executable, str(self.desktop_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.base_dir)
                )
                self.desktop_running = True
                self.status_text.insert(tk.END, "✅ Desktop app launched successfully!\n")
                self.status_text.see(tk.END)
                
                # Monitor process
                def monitor():
                    self.desktop_process.wait()
                    self.desktop_running = False
                    self.status_text.insert(tk.END, "⚠️ Desktop app closed\n")
                    self.status_text.see(tk.END)
                
                threading.Thread(target=monitor, daemon=True).start()
                
            except Exception as e:
                self.status_text.insert(tk.END, f"❌ Failed to launch: {e}\n")
                messagebox.showerror("Launch Error", f"Failed to launch:\n{e}")
        
        threading.Thread(target=run, daemon=True).start()
    
    def launch_dashboard(self):
        """Launch the Streamlit dashboard"""
        if self.dashboard_running:
            messagebox.showinfo("Already Running", "Dashboard is already running!")
            return
        
        def run():
            try:
                self.status_text.insert(tk.END, f"\n🚀 Launching: {self.dashboard_path.name}\n")
                self.status_text.see(tk.END)
                
                # Kill existing streamlit
                try:
                    subprocess.run(["pkill", "-f", "streamlit"], stderr=subprocess.DEVNULL)
                    time.sleep(1)
                except:
                    pass
                
                # Launch streamlit
                cmd = [
                    sys.executable, "-m", "streamlit", "run", str(self.dashboard_path),
                    "--server.port", "8501",
                    "--server.address", "localhost",
                    "--server.headless", "true",
                    "--browser.gatherUsageStats", "false"
                ]
                
                self.dashboard_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.base_dir)
                )
                self.dashboard_running = True

                self.status_text.insert(
                    tk.END,
                    "⏳ Waiting for Streamlit on :8501 (first run may take 30–90s)…\n",
                )
                self.status_text.see(tk.END)

                ready = _wait_for_tcp_port("localhost", 8501, STREAMLIT_START_TIMEOUT)
                webbrowser.open("http://localhost:8501")
                if ready:
                    self.status_text.insert(
                        tk.END, "✅ Dashboard ready at http://localhost:8501\n"
                    )
                else:
                    self.status_text.insert(
                        tk.END,
                        "⚠️ Port not ready in time; browser opened — refresh if blank.\n",
                    )
                self.status_text.see(tk.END)
                
                # Monitor process
                def monitor():
                    self.dashboard_process.wait()
                    self.dashboard_running = False
                    self.status_text.insert(tk.END, "⚠️ Dashboard stopped\n")
                    self.status_text.see(tk.END)
                
                threading.Thread(target=monitor, daemon=True).start()
                
            except Exception as e:
                self.status_text.insert(tk.END, f"❌ Failed to launch: {e}\n")
                messagebox.showerror("Launch Error", f"Failed to launch:\n{e}")
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_all(self):
        """Stop all running processes"""
        try:
            if self.desktop_process and self.desktop_process.poll() is None:
                self.desktop_process.terminate()
                self.desktop_process.wait(timeout=5)
                self.desktop_running = False
                self.status_text.insert(tk.END, "✅ Desktop app stopped\n")
            
            if self.dashboard_process and self.dashboard_process.poll() is None:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=5)
                self.dashboard_running = False
                self.status_text.insert(tk.END, "✅ Dashboard stopped\n")
            
            # Kill any remaining streamlit
            try:
                subprocess.run(["pkill", "-f", "streamlit"], stderr=subprocess.DEVNULL)
            except:
                pass
            
        except Exception as e:
            self.status_text.insert(tk.END, f"⚠️ Error stopping: {e}\n")
    
    def refresh(self):
        """Refresh file detection"""
        # Re-check files
        self.desktop_path = self.base_dir / "desktop_app.py"
        self.dashboard_path = self.base_dir / "app.py"
        
        if not self.desktop_path.exists():
            alt_names = ["desktop_app_complete.py", "defi_guardian_desktop.py"]
            for name in alt_names:
                alt_path = self.base_dir / name
                if alt_path.exists():
                    self.desktop_path = alt_path
                    break
        
        if not self.dashboard_path.exists():
            alt_names = ["dashboard.py", "app_final.py", "app_complete.py"]
            for name in alt_names:
                alt_path = self.base_dir / name
                if alt_path.exists():
                    self.dashboard_path = alt_path
                    break
        
        self.status_text.insert(tk.END, "\n🔄 Refreshed...\n")
        
        if self.desktop_path.exists():
            self.status_text.insert(tk.END, f"✅ Found desktop app: {self.desktop_path.name}\n")
            self.desktop_btn.config(state="normal", bg="#27ae60")
        else:
            self.status_text.insert(tk.END, "❌ desktop_app.py not found!\n")
            self.desktop_btn.config(state="disabled", bg="#555555")
        
        if self.dashboard_path.exists():
            self.status_text.insert(tk.END, f"✅ Found dashboard: {self.dashboard_path.name}\n")
            self.dashboard_btn.config(state="normal", bg="#9b59b6")
        else:
            self.status_text.insert(tk.END, "❌ app.py not found!\n")
            self.dashboard_btn.config(state="disabled", bg="#555555")
        
        self.status_text.see(tk.END)
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Stop all processes and exit?"):
            self.stop_all()
            self.root.destroy()
    
    def run(self):
        """Run the launcher"""
        self.root.mainloop()

if __name__ == "__main__":
    launcher = DeFiGuardianLauncher()
    launcher.run()
