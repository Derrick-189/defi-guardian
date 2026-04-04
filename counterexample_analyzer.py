#!/usr/bin/env python3
"""
Counterexample Analyzer for DeFi Guardian
Parses SPIN trail files and generates readable reports
"""

import os
import re
import subprocess
from pathlib import Path

class CounterexampleAnalyzer:
    def __init__(self, project_dir=None):
        self.project_dir = project_dir or os.path.dirname(os.path.abspath(__file__))
        self.trail_file = os.path.join(self.project_dir, "translated_output.pml.trail")

    # ------------------------------------------------------------------
    # FIX: Call this before every new verification run so that a trail
    # left over from a previous run is never mistaken for a current one.
    # SPIN only writes a new trail when it finds an error; if the model
    # passes cleanly the old file stays on disk, causing the "file is
    # newer than trail" warning and a false counterexample report.
    # ------------------------------------------------------------------
    def clear_stale_trail(self):
        """Delete the trail file if it exists so the next run starts clean."""
        if os.path.exists(self.trail_file):
            try:
                os.unlink(self.trail_file)
            except OSError as e:
                print(f"Warning: could not remove stale trail file: {e}")

    def has_counterexample(self):
        """Check if a counterexample trail exists"""
        return os.path.exists(self.trail_file) and os.path.getsize(self.trail_file) > 0
    
    def analyze_with_spin(self, pml_file=None):
        """Use SPIN to analyze the counterexample trail"""
        if pml_file is None:
            pml_file = os.path.join(self.project_dir, "translated_output.pml")
        
        if not os.path.exists(pml_file):
            return "No Promela model found for counterexample analysis"
        
        if not self.has_counterexample():
            return "No counterexample trail found"

        # FIX: Warn explicitly if the trail pre-dates the model so the
        # caller can see the trail is stale rather than silently replaying
        # an old execution.
        pml_mtime = os.path.getmtime(pml_file)
        trail_mtime = os.path.getmtime(self.trail_file)
        if pml_mtime > trail_mtime:
            return (
                "⚠️  Stale trail detected: the Promela model is newer than the "
                "trail file. The trail was produced by a previous model and does "
                "not apply to the current one. Run clear_stale_trail() before "
                "re-verifying to avoid this."
            )
        
        try:
            result = subprocess.run(
                ["spin", "-t", "-p", pml_file],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_dir
            )
            return result.stdout if result.stdout else result.stderr
        except Exception as e:
            return f"Error analyzing counterexample: {e}"
    
    def parse_trail_file(self):
        """Parse the trail file directly"""
        if not self.has_counterexample():
            return None
        
        trace = []
        with open(self.trail_file, 'r') as f:
            content = f.read()
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'state' in line.lower():
                    trace.append({
                        'step': i,
                        'raw': line.strip()
                    })
        
        return trace
    
    def generate_report(self, pml_file=None):
        """Generate a comprehensive counterexample report"""
        report = []
        report.append("="*70)
        report.append("COUNTEREXAMPLE ANALYSIS REPORT")
        report.append("="*70)
        report.append("")
        
        if not self.has_counterexample():
            report.append("✅ No counterexample found - All properties verified!")
            return "\n".join(report)
        
        report.append("❌ COUNTEREXAMPLE FOUND!")
        report.append("")
        
        spin_output = self.analyze_with_spin(pml_file)
        if spin_output:
            report.append("📋 SPIN GUIDED SIMULATION:")
            report.append("-"*50)
            report.append(spin_output)
            report.append("")
        
        trace = self.parse_trail_file()
        if trace:
            report.append("📊 EXECUTION TRACE:")
            report.append("-"*50)
            for step in trace[:50]:
                report.append(f"  Step {step['step']}: {step['raw']}")
            report.append("")
        
        report.append("🔧 RECOMMENDATIONS:")
        report.append("-"*50)
        report.append("1. Review the LTL properties for correctness")
        report.append("2. Check if the model accurately represents the system")
        report.append("3. Verify that invariants are properly defined")
        report.append("4. Consider adding more constraints to the model")
        
        return "\n".join(report)
    
    def save_report(self, filename="counterexample_report.txt"):
        """Save the counterexample report to a file"""
        report = self.generate_report()
        report_path = os.path.join(self.project_dir, filename)
        with open(report_path, 'w') as f:
            f.write(report)
        return report_path


def analyze_counterexample_from_file(pml_path, trail_path=None):
    """Convenience function to analyze counterexample from given files"""
    analyzer = CounterexampleAnalyzer(os.path.dirname(pml_path))
    return analyzer.generate_report(pml_path)