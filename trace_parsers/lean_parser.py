"""Lean 4 theorem prover trace parser."""

import re
import os
from typing import Dict, List, Optional
from events import ExecutionTrace, TraceStep
from trace_parsers import TraceParser


class LeanParser(TraceParser):
    """Parser for Lean 4 verification output"""

    def parse_rules(self, log_path: str) -> List[Dict]:
        """Extract theorems from Lean log"""
        if not log_path or not os.path.exists(log_path):
            return []

        rules = []
        try:
            with open(log_path, "r", errors="replace") as f:
                content = f.read()
        except Exception:
            return []

        # Patterns for theorems
        thm_pattern = re.compile(
            r"^(theorem|lemma|def|#check)\s+(\w+)", re.MULTILINE | re.IGNORECASE
        )
        has_error = "error" in content.lower() or "failed" in content.lower()

        current_thm = None
        for line in content.splitlines():
            m = thm_pattern.search(line)
            if m:
                current_thm = m.group(2)
                rules.append(
                    {
                        "name": current_thm,
                        "status": "FAIL" if has_error else "PASS",
                        "formula": line.strip(),
                        "errors": 1 if has_error else 0,
                        "tool_specific": {"kind": m.group(1)},
                    }
                )

        if not rules:
            rules.append(
                {
                    "name": "Lean Verification",
                    "status": "FAIL" if has_error else "PASS",
                    "formula": "Lean theorem proving",
                    "errors": 1 if has_error else 0,
                    "tool_specific": {},
                }
            )

        return rules

    def parse_trace(
        self, log_path: str, trail_path: Optional[str] = None
    ) -> ExecutionTrace:
        """Extract error messages as trace"""
        trace = ExecutionTrace()

        if not log_path or not os.path.exists(log_path):
            return trace

        try:
            with open(log_path, "r", errors="replace") as f:
                content = f.read()
        except Exception:
            return trace

        # Extract errors
        for i, line in enumerate(content.splitlines()):
            if (
                "error" in line.lower()
                or "failed" in line.lower()
                or "unknown" in line.lower()
            ):
                step = TraceStep(
                    step_num=i + 1,
                    proc="Lean",
                    action=line.strip(),
                    state="error",
                    line=str(i),
                    file="",
                    is_error=True,
                )
                trace.steps.append(step)
                trace.error_line = i + 1
                trace.error_message = line.strip()

        return trace

    def get_recommendations(self, status: str) -> List[str]:
        if status == "FAIL":
            return [
                "Check theorem statement types match (Nat vs Int)",
                "Use decide or native_decide for decidable goals",
                "Ensure all imports are available",
            ]
        return ["Lean theorem verified successfully"]
