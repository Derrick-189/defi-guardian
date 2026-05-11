"""Rust verification tools trace parser (Kani, Prusti, Creusot)."""

import re
import os
from typing import Dict, List, Optional
from events import ExecutionTrace, TraceStep
from trace_parsers import TraceParser


class RustParser(TraceParser):
    """Unified parser for Rust verification tools (Kani, Prusti, Creusot)"""

    def __init__(self, tool: str):
        self.tool = tool.upper()  # KANI, PRUSTI, or CREUSOT

    def parse_rules(self, log_path: str) -> List[Dict]:
        """Extract verification results based on tool type"""
        if not log_path or not os.path.exists(log_path):
            return []

        try:
            with open(log_path, "r", errors="replace") as f:
                content = f.read()
        except Exception:
            return []

        rules = []

        if self.tool == "KANI":
            rules = self._parse_kani_checks(content)
        elif self.tool == "PRUSTI":
            rules = self._parse_prusti_specs(content)
        elif self.tool == "CREUSOT":
            rules = self._parse_creusot_results(content)

        if not rules:
            status = "PASS" if "verified" in content.lower() else "FAIL"
            rules.append(
                {
                    "name": f"{self.tool} Verification",
                    "status": status,
                    "formula": f"{self.tool} verification",
                    "errors": 0 if status == "PASS" else 1,
                    "tool_specific": {"tool": self.tool},
                }
            )

        return rules

    def _parse_kani_checks(self, content: str) -> List[Dict]:
        """Parse Kani model checking results"""
        rules = []
        # Look for check results: "Check: ... PASSED/FAILED"
        check_pattern = re.compile(
            r"check\s+(\d+):\s+(\w+).*?(PASSED|FAILED)", re.IGNORECASE
        )
        for match in check_pattern.finditer(content):
            check_id = match.group(1)
            check_name = match.group(2)
            result = match.group(3).upper()
            rules.append(
                {
                    "name": f"check_{check_id}_{check_name}",
                    "status": "PASS" if result == "PASSED" else "FAIL",
                    "formula": f"{check_name} assertion",
                    "errors": 0 if result == "PASSED" else 1,
                    "tool_specific": {"check_id": check_id},
                }
            )
        return rules

    def _parse_prusti_specs(self, content: str) -> List[Dict]:
        """Parse Prusti spec verification results"""
        rules = []
        # Look for precondition/postcondition status
        spec_pattern = re.compile(r"(precondition|postcondition|invariant)\s+(\w+).*?.*?(error|verified)?", re.IGNORECASE | re.DOTALL)
        has_error = "error" in content.lower()

        for match in spec_pattern.finditer(content):
            spec_type = match.group(1)
            spec_name = match.group(2)
            rules.append(
                {
                    "name": f"{spec_type}_{spec_name}",
                    "status": "FAIL" if has_error else "PASS",
                    "formula": f"{spec_type} {spec_name}",
                    "errors": 1 if has_error else 0,
                    "tool_specific": {"spec_type": spec_type},
                }
            )

        return rules

    def _parse_creusot_results(self, content: str) -> List[Dict]:
        """Parse Creusot verification results"""
        rules = []
        has_error = "error" in content.lower() or "failed" in content.lower()

        rules.append(
            {
                "name": "Creusot Verification",
                "status": "FAIL" if has_error else "PASS",
                "formula": "Why3 deductive verification",
                "errors": 1 if has_error else 0,
                "tool_specific": {"backend": "Why3"},
            }
        )

        return rules

    def parse_trace(
        self, log_path: str, trail_path: Optional[str] = None
    ) -> ExecutionTrace:
        """Extract error/violation information as trace"""
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
            if (
                "error" in line.lower()
                or "panicked" in line.lower()
                or "failed" in line.lower()
                or "violation" in line.lower()
            ):
                step = TraceStep(
                    step_num=i + 1,
                    proc=self.tool,
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
        if self.tool == "KANI":
            if status == "FAIL":
                return [
                    "Check for panics in your code",
                    "Verify buffer bounds on array accesses",
                    "Ensure arithmetic operations don't overflow",
                ]
            return ["All checks passed - code is verified"]

        elif self.tool == "PRUSTI":
            if status == "FAIL":
                return [
                    "Check precondition specifications match function behavior",
                    "Verify postcondition specifications are achievable",
                    "Review loop invariants for completeness",
                ]
            return ["Prusti specifications verified"]

        elif self.tool == "CREUSOT":
            if status == "FAIL":
                return [
                    "Check Why3 backend integration",
                    "Verify proof annotations are correct",
                    "Review SMT solver output",
                ]
            return ["Creusot verification successful"]

        return ["Verification complete"]
