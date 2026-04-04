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
        
        try:
            # Run SPIN in guided simulation mode
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
            
            # Extract state transitions
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
        
        # Get SPIN analysis
        spin_output = self.analyze_with_spin(pml_file)
        if spin_output:
            report.append("📋 SPIN GUIDED SIMULATION:")
            report.append("-"*50)
            report.append(spin_output)
            report.append("")
        
        # Parse raw trail
        trace = self.parse_trail_file()
        if trace:
            report.append("📊 EXECUTION TRACE:")
            report.append("-"*50)
            for step in trace[:50]:  # Limit to first 50 steps
                report.append(f"  Step {step['step']}: {step['raw']}")
            report.append("")
        
        # Add recommendations
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