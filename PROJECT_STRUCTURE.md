# DeFi Guardian: System Architecture & Workflow

DeFi Guardian is an integrated formal verification suite designed to provide a professional-grade experience for smart contract auditing. It bridges the gap between low-level formal methods tools (like SPIN, Coq, and Lean) and high-level user interfaces.

## How It Works (The "Big Picture")

1.  **Orchestration Layer (`desktop_app.py`)**: This is the heart of the system. It acts as an IDE where you load your Solidity or Rust code. It manages the lifecycle of a verification job—from auto-generating LTL specifications using AI and Slither, to translating the code into formal models, and finally invoking the underlying verification engines.
2.  **Formal Translation (`translator.py`)**: Since most formal verifiers don't speak Solidity or Rust natively, this module translates your source code into **Promela** (for SPIN model checking) or generates **Coq/Lean** proof scripts.
3.  **Unified Data Lake (`verification_state.json`, `audit_log.json`, SQLite)**: Regardless of which tool you run (SPIN, Certora, Kani, etc.), the results are normalized into a common format. This allows different dashboards to display results consistently.
4.  **Visualization & Monitoring (`app.py` - Streamlit)**: This service provides a real-time "cockpit" for your protocol. It visualizes the state-space graph (how many ways the contract can transition) and provides financial risk metrics (like liquidation sensitivity).
5.  **Collaboration & Audit Management (`web_portal/`)**: This is the user-facing web interface. It allows you to log in, track your audit history over time, and use the professional **Counterexample Analysis** dashboard to surgically debug property violations.

---

## Directory Structure

| Directory | Description |
|-----------|-------------|
| `web_portal/` | Main Flask web application directory. |
| `web_portal/templates/` | Jinja2 HTML templates for the web portal UI. |
| `generated/` | Root for all files generated during verification (models, reports, images). |
| `models/` | Contains translated formal models (e.g., `.pml` for SPIN). |
| `logs/` | Organized logs for different tools (`spin/`, `certora/`, `coq/`, `lean/`, `rust_tools/`). |
| `certora/` | Certora-specific workspace containing contracts, specs, and configurations. |
| `benchmarks/` | Performance benchmark results for various verification tasks. |
| `console_exports/` | Exported terminal outputs from the Desktop App. |
| `scripts/` | Helper utility scripts. |

## Core System Files

| File | Role |
|------|------|
| `desktop_app.py` | The main IDE-like Desktop Application. It coordinates tool execution and provides the primary UI. |
| `app.py` (root) | A high-performance Streamlit dashboard for real-time verification visualization. |
| `web_portal/app.py` | The backend for the Web Portal. It manages user accounts, audit history, and provides APIs for the UI. |
| `translator.py` | Responsible for translating Solidity and Rust source code into Promela models. |
| `rust_verifiers.py` | Implements verification logic for Rust tools like Kani, Prusti, and Creusot. |
| `coq_verifier.py` | Handles Coq script generation and proof execution. |
| `lean_verifier.py` | Manages Lean 4 verification and theorem proving. |
| `counterexample_analyzer.py` | Parses SPIN trail files to generate structured execution traces for visualization. |

---

## Formal Verification Results Pipeline

The following diagram-like flow describes how results move from the verification tools to your dashboards:

### 1. Execution & Capture
Verification is usually triggered from the **Desktop App** (`desktop_app.py`).
- Methods like `save_verification_state` and `log_job_history` capture the raw output from tools (SPIN, Certora, Kani, etc.).

### 2. Data Persistence (Sources of Truth)
Results are written to several local data stores:
- **`verification_state.json`**: Stores the status, success/fail, and raw output of the *latest* run for every tool.
- **`generated/reports/audit_log.json`**: A JSON-based historical log of all verification jobs performed on the desktop.
- **`web_portal/defi_guardian.db`**: An SQLite database where `desktop_app.py` mirrors its job history via the `save_portal_audit_record` method.

### 3. Dashboard Integration
Dashboards consume the stored data in two ways:

#### **Streamlit Dashboard (port 5005)**
- Directly reads `verification_state.json` using the `load_verification_state()` function in the root `app.py`.
- It monitors this file for changes to provide real-time updates.

#### **Web Portal Dashboard (port 5000)**
- The **Backend** (`web_portal/app.py`) serves the data via several API endpoints:
    - `/api/state/current`: Returns the content of `verification_state.json`.
    - `/api/desktop-runs`: Returns historical data from `audit_log.json`.
    - `/api/counterexample/<id>` & `/api/trace/<id>`: Serve detailed trace data for visual analysis.
- The **Frontend** templates (`dashboard.html`, `counterexample.html`) perform `fetch()` calls to these endpoints to populate the UI.

## Web Portal Templates Overview

| Template | Description |
|----------|-------------|
| `base.html` | The master layout containing common CSS (Bootstrap), JS, and navigation. |
| `index.html` | Landing page for unauthenticated users. |
| `dashboard.html` | User's main cockpit showing personal audit history and desktop sync data. |
| `counterexample.html` | The redesigned Certora-style analysis tool (three-panel layout). |
| `trace.html` | Dedicated execution trace viewer. |
| `visualization.html` | 3D state space graph explorer (Three.js). |
| `desktop_app.html` | A specialized template for the Desktop App's embedded web components. |

## System Rebuild & Startup Guide

To rebuild or run the complete DeFi Guardian system, follow these steps:

### 1. Environment Setup
- Install Python dependencies: `pip install -r requirements.txt`.
- Install verification tools: `spin`, `coqc`, `lean`, `slither`, etc. (See `install.sh`).

### 2. Launching the Components
The system consists of three main integrated services:

- **Desktop IDE**: `python desktop_app.py`
  - *Provides*: Main tool coordination, code editing, and background job execution.
- **Web Portal (API/User DB)**: `python web_portal/app.py` (Default: port 5000)
  - *Provides*: User auth, persistence for all results, and the primary high-end UI.
- **Streamlit Dashboard**: `streamlit run app.py` (Default: port 5005)
  - *Provides*: Real-time state-space visualization and risk monitoring.

### 3. Data Flow Integrity
To ensure the system works as a whole:
- The **Desktop IDE** must be able to write to the root `verification_state.json`.
- The **Web Portal** must have read access to `audit_log.json` and the shared SQLite database `web_portal/defi_guardian.db`.

## Expected Functional Behavior (Ideal State)

If all features are functioning as intended, the following end-to-end lifecycle should be expected:

### 1. Specification Engineering
- **Action**: User loads a contract in the **Desktop IDE** and clicks **AI Generate Specs**.
- **Result**: The system performs a static analysis of the source code (using Slither for Solidity or custom heuristics for Rust) and automatically populates the **Specifications & LTL** tab with safety properties (e.g., reentrancy guards, overflow checks) and liveness properties.

### 2. Multi-Engine Verification
- **Action**: User clicks **Run SPIN Verification** or **Verify with Certora**.
- **Process**:
    - The system translates high-level code into formal representations.
    - It executes parallel verification engines.
    - Results are unified into a standard JSON schema.
- **Result**: Success/failure statuses are immediately visible in the terminal, and the **Audit History** is updated in real-time.

### 3. Interactive Debugging (The "Certora" Experience)
- **Action**: Upon a verification failure, the user opens the **Web Portal** and selects the failing audit.
- **Result**: The **Counterexample Analysis** UI provides a surgical view of the bug:
    - **Rule Navigator**: Shows which specific properties were violated.
    - **Call Trace Workspace**: An interactive tree allowing the user to step through the execution.
    - **Variable Inspector**: Highlights exactly which variables changed at each step and by how much, pinpointing the root cause of the violation.

### 4. Risk & State-Space Visualization
- **Action**: User launches the **Streamlit Dashboard**.
- **Result**:
    - The system renders a **3D Interactive State Graph** representing all reachable states of the contract.
    - For lending protocols, it provides **Monte Carlo Simulations** and **Sensitivity Analysis** based on the verified parameters (price, collateral, debt), allowing users to stress-test the protocol's safety under volatile market conditions.
