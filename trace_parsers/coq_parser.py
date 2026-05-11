"""Coq proof assistant trace parser."""

import re
import os
from typing import Dict, List, Optional
from events import ExecutionTrace, TraceStep
from trace_parsers import TraceParser


class CoqParser(TraceParser):
    """Parser for Coq verification output"""

    def parse_rules(self, log_path: str) -> List[Dict]:
        """Extract theorems and their proof status from Coq log"""
        if not log_path or not os.path.exists(log_path):
            return []

        rules = []
        try:
            with open(log_path, "r", errors="replace") as f:
                content = f.read()
        except Exception:
            return []

        # Patterns for theorem/lemma definitions
        thm_pattern = re.compile(r"^(Theorem|Lemma)\s+(\w+)", re.MULTILINE | re.IGNORECASE)
        qed_pattern = re.compile(r"\bQed\b|\bDefined\b")
        adm_pattern = re.compile(r"\bAdmitted\b|Error:", re.IGNORECASE)

        current_thm = None
        for line in content.splitlines():
            thm_match = thm_pattern.search(line)
            if thm_match:
                current_thm = thm_match.group(2)
                continue

            if current_thm:
                if qed_pattern.search(line):
                    rules.append(
                        {
                            "name": current_thm,
                            "status": "PASS",
                            "formula": f"Theorem {current_thm}",
                            "errors": 0,
                            "tool_specific": {"proof_status": "Qed"},
                        }
                    )
                    current_thm = None
                elif adm_pattern.search(line):
                    rules.append(
                        {
                            "name": current_thm,
                            "status": "FAIL",
                            "formula": f"Theorem {current_thm}",
                            "errors": 1,
                            "tool_specific": {"proof_status": "Admitted"},
                        }
                    )
                    current_thm = None

        if not rules:
            if "Error" in content or "error" in content:
                rules.append(
                    {
                        "name": "Coq Verification",
                        "status": "FAIL",
                        "formula": "Coq proof assistant",
                        "errors": 1,
                        "tool_specific": {},
                    }
                )
            else:
                rules.append(
                    {
                        "name": "Coq Verification",
                        "status": "PASS",
                        "formula": "Coq proof assistant",
                        "errors": 0,
                        "tool_specific": {},
                    }
                )

        return rules

    def parse_trace(
        self, log_path: str, trail_path: Optional[str] = None
    ) -> ExecutionTrace:
        """Extract error messages as trace steps"""
        trace = ExecutionTrace()

        if not log_path or not os.path.exists(log_path):
            return trace

        try:
            with open(log_path, "r", errors="replace") as f:
                content = f.read()
        except Exception:
            return trace

        # Extract error lines
        for i, line in enumerate(content.splitlines()):
            if "error" in line.lower() or "failed" in line.lower():
                step = TraceStep(
                    step_num=i + 1,
                    proc="Coq",
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
        """Coq-specific recommendations"""
        if status == "FAIL":
            return [
                "Check that all Prop definitions are well-typed",
                "Replace admit/Admitted with concrete proof tactics (lia, omega, auto)",
                "Ensure bool fields use = true / = false comparisons, not >= 0",
                "Use native_decide for decidable propositions",
            ]
        return ["Proof verified successfully"]
