#!/usr/bin/env python3
"""
Simple Tool Checker for DeFi Guardian
Checks all installed verification tools
"""

import subprocess
import sys
import os

# Define tools to check
TOOLS = {
    # Core verification tools
    "SPIN": "spin --version",
    "Coq": "coqc --version",
    "Lean": "lean --version",
    "GCC": "gcc --version",
    
    # Rust verification tools
    "Prusti": "prusti-rustc --version",
    "Kani": "kani --version",
    "Creusot": "creusot --version",
    
    # SMT solvers
    "Z3": "z3 --version",
    "CVC5": "cvc5 --version",
    
    # Build tools
    "Cargo": "cargo --version",
    "Rustc": "rustc --version",
    
    # Graphviz
    "Graphviz": "dot -V",
    
    # Elan (Lean version manager)
    "Elan": "elan --version",
}

def check_tool(name, command):
    """Check if a tool is installed"""
    try:
        # Split command for subprocess
        cmd_parts = command.split()
        result = subprocess.run(cmd_parts, 
                               capture_output=True, 
                               text=True, 
                               timeout=5)
        if result.returncode == 0:
            # Get first line of output
            output = result.stdout.split('\n')[0].strip()
            return True, output[:80]  # Truncate long output
        return False, result.stderr[:80] if result.stderr else "Unknown error"
    except FileNotFoundError:
        return False, "Not found"
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)[:80]

def main():
    print("=" * 60)
    print("🔧 DEFI GUARDIAN - TOOL CHECKER")
    print("=" * 60)
    print()
    
    installed = 0
    total = len(TOOLS)
    
    # Check each tool
    for name, command in TOOLS.items():
        success, output = check_tool(name, command)
        if success:
            print(f"✅ {name:12} - {output}")
            installed += 1
        else:
            print(f"❌ {name:12} - {output}")
    
    print()
    print("=" * 60)
    print(f"📊 SUMMARY: {installed}/{total} tools installed")
    print("=" * 60)
    
    # Show installation commands for missing tools
    missing = [name for name in TOOLS.keys() if not check_tool(name, TOOLS[name])[0]]
    if missing:
        print()
        print("🔧 To install missing tools:")
        print("-" * 40)
        for name in missing:
            if name == "Prusti":
                print(f"  {name}: cargo install prusti && prusti-rustc --setup")
            elif name == "Kani":
                print(f"  {name}: cargo install --locked kani-verifier && cargo kani setup")
            elif name == "Creusot":
                print(f"  {name}: cargo install creusot")
            elif name == "Coq":
                print(f"  {name}: sudo apt install coq")
            elif name == "Lean":
                print(f"  {name}: curl https://elan.lean-lang.org/elan-init.sh -sSf | sh")
            elif name == "Elan":
                print(f"  {name}: curl https://elan.lean-lang.org/elan-init.sh -sSf | sh")
            elif name == "Z3":
                print(f"  {name}: sudo apt install z3")
            elif name == "CVC5":
                print(f"  {name}: Download from https://github.com/cvc5/cvc5/releases")
            elif name == "Graphviz":
                print(f"  {name}: sudo apt install graphviz")
            else:
                print(f"  {name}: sudo apt install {name.lower()}")

if __name__ == "__main__":
    main()
