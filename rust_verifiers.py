import subprocess
import os
import tempfile
import shutil
import re

CREUSOT_STD_PATH = os.environ.get(
    "CREUSOT_STD_PATH", "/home/slade/creusot/creusot-std"
)

def build_prusti_env(base_env=None):
    """Build a clean environment for Prusti subprocesses.

    Prusti interprets PRUSTI_* variables as config flags, so inherited variables
    (e.g. PRUSTI_HOME) can crash it with "unknown configuration flag".
    """
    env = dict(base_env or os.environ)
    for key in list(env.keys()):
        if key.startswith("PRUSTI_"):
            env.pop(key, None)

    prusti_bin_result = subprocess.run(
        ['which', 'prusti-rustc'], capture_output=True, text=True
    )
    prusti_bin = prusti_bin_result.stdout.strip()
    if prusti_bin:
        prusti_home = os.path.dirname(os.path.realpath(prusti_bin))
        env['VIPER_HOME'] = os.path.join(prusti_home, 'viper_tools')
    return env


def prusti_command():
    """Build Prusti command with optional pinned toolchain isolation."""
    pinned = os.environ.get(
        "PRUSTI_TOOLCHAIN", "nightly-2023-08-15-x86_64-unknown-linux-gnu"
    )
    try:
        toolchains = subprocess.run(
            ["rustup", "toolchain", "list"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if pinned in (toolchains.stdout or ""):
            return ["rustup", "run", pinned, "prusti-rustc"]
    except Exception:
        pass
    return ["prusti-rustc"]


def _remove_kani_proof_attrs(lines):
    return [ln for ln in lines if ln.strip() != "#[kani::proof]"]


def _strip_functions_with_kani(lines):
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "fn " in line:
            j = i
            header = []
            while j < len(lines):
                header.append(lines[j])
                if "{" in lines[j]:
                    break
                if ";" in lines[j]:
                    break
                j += 1
            header_text = "".join(header)
            if "kani::" in header_text:
                i = j + 1
                depth = header_text.count("{") - header_text.count("}")
                while i < len(lines) and depth > 0:
                    depth += lines[i].count("{") - lines[i].count("}")
                    i += 1
                continue
        if "kani::" not in line:
            out.append(line)
        i += 1
    return out


def preprocess_prusti_source(rust_code):
    """Remove Kani-specific constructs from a temporary Prusti copy."""
    lines = rust_code.splitlines(keepends=True)
    lines = _remove_kani_proof_attrs(lines)
    lines = _strip_functions_with_kani(lines)
    code = "".join(lines)
    # Conservative cleanup for direct nondet calls outside removed functions.
    code = re.sub(r"\bkani::any\s*\(\s*\)", "Default::default()", code)
    return code


def classify_prusti_failure(stderr):
    err = stderr or ""
    if "unknown configuration flag `home`" in err:
        return "env", "Invalid PRUSTI_* environment variable detected"
    if "compiler unexpectedly panicked" in err:
        return "ice", "Prusti internal crash (toolchain incompatibility/bug)"
    if "use of undeclared crate or module `kani`" in err:
        return "incompatible", "Input contains Kani constructs incompatible with Prusti"
    if "timed out" in err.lower():
        return "timeout", "Prusti timed out"
    return "error", "Prusti verification failed"


def strip_rust_main_for_lib(rust_code: str) -> str:
    """Remove a top-level ``fn main() { ... }`` so the crate can be built as a library."""
    key = "fn main"
    idx = rust_code.find(key)
    if idx == -1:
        return rust_code
    paren = rust_code.find("(", idx)
    if paren == -1:
        return rust_code
    brace = rust_code.find("{", paren)
    if brace == -1:
        return rust_code
    depth = 0
    i = brace
    while i < len(rust_code):
        c = rust_code[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                head = rust_code[:idx].rstrip()
                tail = rust_code[end:].lstrip()
                out = (head + ("\n\n" if head and tail else "\n") + tail).strip()
                return out + ("\n" if out else "")
        i += 1
    return rust_code


def prepend_creusot_prelude(rust_code: str) -> str:
    """Insert ``use creusot_std::prelude::*`` after any leading ``//!`` crate docs.

    Prepending before inner docs would break E0753 (inner doc comments must appear
    before other items in the crate root).
    """
    if "creusot_contracts" in rust_code or "creusot_std" in rust_code:
        return rust_code
    lines = rust_code.splitlines(keepends=True)
    i = 0
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    while i < len(lines) and lines[i].lstrip().startswith("//!"):
        i += 1
    head = "".join(lines[:i])
    rest = "".join(lines[i:])
    join = "\n" if head and not head.endswith("\n") else ""
    return head + join + "use creusot_std::prelude::*;\n\n" + rest


class RustVerifier:
    """Integration with Rust verification tools"""

    def __init__(self):
        self.prusti_available = self._check_prusti()
        self.kani_available = self._check_kani()
        self.creusot_available = self._check_creusot()

    def _check_prusti(self):
        try:
            subprocess.run(["prusti-rustc", "--version"],
                           capture_output=True, check=True)
            return True
        except:
            return False

    def _check_kani(self):
        try:
            subprocess.run(["cargo", "kani", "--version"], capture_output=True, check=True)
            return True
        except:
            return False

    def _check_creusot(self):
        try:
            subprocess.run(["cargo", "creusot", "--help"],
                           capture_output=True, check=True)
            return True
        except:
            return False

    def generate_rust_annotations(self, rust_code):
        annotated_code = f"""
#![feature(register_tool)]
#![register_tool(prusti)]
#![register_tool(creusot)]

#[derive(Clone, Debug)]
pub struct ContractState {{
    pub collateral: u64,
    pub debt: u64,
    pub price: u64,
    pub lock: bool,
    pub health_factor: u64,
}}

impl ContractState {{
    #[ensures(result.collateral == 5000)]
    #[ensures(result.debt == 3000)]
    #[ensures(result.price == 100)]
    #[ensures(result.lock == false)]
    pub fn new() -> Self {{
        ContractState {{ collateral: 5000, debt: 3000, price: 100, lock: false, health_factor: 166 }}
    }}

    #[pure]
    #[ensures(result == (self.collateral * self.price >= self.debt))]
    pub fn invariant_collateral(&self) -> bool {{
        self.collateral * self.price >= self.debt
    }}

    #[pure]
    #[ensures(result == !self.lock)]
    pub fn safety_reentrancy(&self) -> bool {{ !self.lock }}

    #[pure]
    pub fn update_health_factor(&self) -> u64 {{
        if self.debt == 0 {{ u64::MAX }} else {{ (self.collateral * self.price) / self.debt }}
    }}

    pub fn safe_operation(&mut self) {{
        assert!(self.safety_reentrancy());
        self.lock = true;
        self.health_factor = self.update_health_factor();
        assert!(self.invariant_collateral());
        self.lock = false;
    }}

    #[pure]
    pub fn is_liquidatable(&self) -> bool {{ self.collateral * self.price < self.debt }}

    #[requires(self.is_liquidatable())]
    pub fn liquidate(&mut self) {{
        self.collateral = 0;
        self.debt = 0;
        self.health_factor = 0;
    }}
}}
"""
        return annotated_code

    def verify_with_prusti(self, rust_code):
        if not self.prusti_available:
            return {'success': False, 'error': 'Prusti not installed', 'output': '', 'errors': ''}
        
        project_dir = None
        try:
            rust_code = preprocess_prusti_source(rust_code)
            if "fn " not in rust_code:
                return {
                    'success': False,
                    'output': '',
                    'errors': '',
                    'error': 'Skipped: no Prusti-compatible functions after preprocessing',
                    'failure_kind': 'skipped',
                    'failure_hint': 'Input appears to be Kani-only; skipping Prusti run',
                    'skipped': True,
                }
            project_dir = tempfile.mkdtemp()
            src_file = os.path.join(project_dir, 'lib.rs')
            with open(src_file, 'w') as f:
                f.write(rust_code)

            # Create minimal Cargo.toml to avoid lock file issues
            with open(os.path.join(project_dir, 'Cargo.toml'), 'w') as f:
                f.write("""[package]
name = "prusti_verify"
version = "0.1.0"
edition = "2021"
""")

            # Delete any Cargo.lock that might interfere with prusti-rustc
            lock_file = os.path.join(project_dir, 'Cargo.lock')
            if os.path.exists(lock_file):
                os.remove(lock_file)

            # Set up environment
            env = build_prusti_env()

            result = subprocess.run(
                prusti_command() + ['--edition=2021', '--crate-type=lib', src_file],
                capture_output=True, text=True, timeout=180,
                cwd=project_dir, env=env
            )
            failure_kind, failure_hint = classify_prusti_failure(result.stderr)
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'error': '' if result.returncode == 0 else result.stderr[:500],
                'failure_kind': '' if result.returncode == 0 else failure_kind,
                'failure_hint': '' if result.returncode == 0 else failure_hint,
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Timeout', 'output': '', 'errors': 'Prusti timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'output': '', 'errors': str(e)}
        finally:
            if project_dir and os.path.exists(project_dir):
                shutil.rmtree(project_dir, ignore_errors=True)

    def verify_with_kani(self, rust_code):
        if not self.kani_available:
            return {'success': False, 'error': 'Kani not installed', 'output': '', 'errors': ''}
        
        project_dir = None
        try:
            project_dir = tempfile.mkdtemp()
            src_dir = os.path.join(project_dir, 'src')
            os.makedirs(src_dir)
            
            # Add Kani proof harness if not present
            if '#[kani::proof]' not in rust_code:
                rust_code += """

#[kani::proof]
fn kani_check_max() {
    let x: u64 = kani::any();
    let y: u64 = kani::any();
    let result = max(x, y);
    assert!(result >= x && result >= y);
}

#[kani::proof]
fn kani_check_add() {
    let x: u64 = kani::any();
    let y: u64 = kani::any();
    let result = add(x, y);
    // Check for overflow
    if x <= u64::MAX - y {
        assert!(result == x + y);
    }
}
"""
            
            with open(os.path.join(src_dir, 'lib.rs'), 'w') as f:
                f.write(rust_code)
                
            with open(os.path.join(project_dir, 'Cargo.toml'), 'w') as f:
                f.write("""[package]
name = "kani_verify"
version = "0.1.0"
edition = "2021"
""")
            
            result = subprocess.run(
                ["cargo", "kani"], capture_output=True, text=True, timeout=300, cwd=project_dir
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'error': '' if result.returncode == 0 else result.stderr[:500]
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Timeout', 'output': '', 'errors': 'Kani timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'output': '', 'errors': str(e)}
        finally:
            if project_dir and os.path.exists(project_dir):
                shutil.rmtree(project_dir, ignore_errors=True)

    def verify_with_creusot(self, rust_code):
        if not self.creusot_available:
            return {'success': False, 'error': 'Creusot not installed', 'output': '', 'errors': ''}
        
        project_dir = None
        try:
            rust_code = prepend_creusot_prelude(rust_code)
            rust_code = strip_rust_main_for_lib(rust_code)

            project_dir = tempfile.mkdtemp()
            src_dir = os.path.join(project_dir, 'src')
            os.makedirs(src_dir)
            with open(os.path.join(src_dir, 'lib.rs'), 'w') as f:
                f.write(rust_code)

            # Dependency key must be "creusot-std": cargo creusot passes -F creusot-std/creusot …
            with open(os.path.join(project_dir, 'Cargo.toml'), 'w') as f:
                f.write(
                    f"""[package]
name = "creusot_verify"
version = "0.1.0"
edition = "2021"

[dependencies]
creusot-std = {{ path = "{CREUSOT_STD_PATH}" }}
"""
                )

            env = os.environ.copy()
            nightly_lib = (
                '/home/slade/.rustup/toolchains/'
                'nightly-2026-02-27-x86_64-unknown-linux-gnu/lib'
            )
            env['LD_LIBRARY_PATH'] = nightly_lib + ':' + env.get('LD_LIBRARY_PATH', '')

            result = subprocess.run(
                ['cargo', 'creusot'], capture_output=True, text=True, timeout=180,
                cwd=project_dir, env=env
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'error': '' if result.returncode == 0 else result.stderr[:500]
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Timeout', 'output': '', 'errors': 'Creusot timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'output': '', 'errors': str(e)}
        finally:
            if project_dir and os.path.exists(project_dir):
                shutil.rmtree(project_dir, ignore_errors=True)
