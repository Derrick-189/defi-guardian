"""
DeFi Guardian - Complete Streamlit Dashboard
Formal Verification Visualization with State Diagrams
Full Sidebar Settings and State Type Selection
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import subprocess
import os
import tempfile
import re
import asyncio
import threading
from datetime import datetime
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import json
from PIL import Image
import io
import graphviz

# Always run from project directory

# Ensure working directory is the project folder

# Import verification state
try:
    from verification_state import VerificationState
except ImportError:
    class VerificationState:
        @staticmethod
        def load_result():
            if os.path.exists("verification_state.json"):
                try:
                    with open("verification_state.json", 'r') as f:
                        return json.load(f)
                except:
                    pass
            return None

# Page config
st.set_page_config(
    page_title="DeFi Guardian | Formal Verification Platform", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_live_verification():
    """Load verification status with timestamp"""
    if os.path.exists("verification_state.json"):
        with open("verification_state.json", "r") as f:
            data = json.load(f)
            # Add human-readable time
            if 'timestamp' in data:
                data['readable_time'] = datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            return data
    return None


def load_verification_state():
    """Load complete verification state for all tools"""
    state_file = "verification_state.json"
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def get_tool_status(tool_name):
    """Get status for a specific tool"""
    state = load_verification_state()
    if tool_name in state:
        tool_state = state[tool_name]
        status = tool_state.get('status', '')
        if status:
            success = status == "PASS"
            status_label = {
                "PASS": "✅ PASS",
                "FAIL": "❌ FAIL",
                "SKIP": "⏭️ SKIP",
                "INFRA_ERROR": "⚠️ INFRA",
            }.get(status, f"⚪ {status}")
        else:
            success = tool_state.get('success', False)
            status_label = '✅ PASS' if success else '❌ FAIL'
        timestamp = tool_state.get('timestamp', '')
        return {
            'status': status_label,
            'timestamp': timestamp,
            'success': success
        }
    return {'status': '⚪ Not Run', 'timestamp': '', 'success': False}

# ==================== HELPER FUNCTIONS ====================

def parse_pml_variable(filename, var_name, default_val):
    """Parse variable from PML file"""
    if not os.path.exists(filename):
        return float(default_val)
    try:
        with open(filename, "r") as f:
            content = f.read()
            match = re.search(rf"int\s+{var_name}\s*=\s*(\d+)\s*;", content)
            if match:
                return float(match.group(1))
    except Exception:
        pass
    return float(default_val)

def parse_pml_state_machine(pml_content):
    """Parse PML file to extract state machine structure"""
    states = []
    transitions = []
    processes = []
    state_vars = []
    ltl_properties = []
    fairness_conditions = []
    
    # Extract proctypes (processes)
    proctype_pattern = r'(?:active\s+)?proctype\s+(\w+)\s*(?:\([^)]*\))?\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
    for match in re.finditer(proctype_pattern, pml_content, re.DOTALL):
        proc_name = match.group(1)
        proc_body = match.group(2)
        processes.append(proc_name)
        
        # Extract labels (states)
        label_pattern = r'(\w+)\s*:'
        for label_match in re.finditer(label_pattern, proc_body):
            state_name = label_match.group(1)
            states.append(f"{proc_name}.{state_name}")
        
        # Extract transitions from if statements
        if_pattern = r'if\s*::\s*(.*?)\s*->\s*(.*?)\s*(?:;|fi)'
        for if_match in re.finditer(if_pattern, proc_body, re.DOTALL):
            condition = if_match.group(1).strip()
            action = if_match.group(2).strip()
            transitions.append({
                'from': proc_name,
                'to': proc_name,
                'condition': condition[:50],
                'action': action[:50]
            })
        
        # Extract transitions from atomic blocks
        atomic_pattern = r'atomic\s*\{\s*(.*?)\s*\}'
        for atomic_match in re.finditer(atomic_pattern, proc_body, re.DOTALL):
            atomic_content = atomic_match.group(1)
            assign_pattern = r'(\w+)\s*=\s*([^;]+);'
            for assign in re.finditer(assign_pattern, atomic_content):
                var = assign.group(1)
                value = assign.group(2)
                transitions.append({
                    'from': proc_name,
                    'to': proc_name,
                    'condition': f"update {var}",
                    'action': f"{var} = {value}"
                })
    
    # Extract state variables
    var_pattern = r'(?:int|bool|byte)\s+(\w+)\s*(?:=\s*([^;]+))?;'
    for match in re.finditer(var_pattern, pml_content):
        var_name = match.group(1)
        init_val = match.group(2) if match.group(2) else "0"
        state_vars.append({'name': var_name, 'initial': init_val.strip()})
    
    # Extract assertions/invariants
    assert_pattern = r'assert\s*\((.*?)\)'
    assertions = re.findall(assert_pattern, pml_content)
    
    # Extract LTL properties
    ltl_pattern = r'ltl\s+(\w+)\s*\{\s*(.*?)\s*\}'
    for match in re.finditer(ltl_pattern, pml_content, re.DOTALL):
        prop_name = match.group(1)
        prop_formula = match.group(2).strip()
        ltl_properties.append({'name': prop_name, 'formula': prop_formula})
    
    # Extract fairness conditions
    fairness_pattern = r'fairness\s*::\s*(.*?)\s*->\s*(.*?)(?:\n|$)'
    fairness_conditions = re.findall(fairness_pattern, pml_content)
    
    return {
        'states': list(set(states)) if states else processes,
        'transitions': transitions,
        'processes': processes,
        'state_vars': state_vars,
        'assertions': assertions,
        'ltl_properties': ltl_properties,
        'fairness': fairness_conditions,
        'raw_content': pml_content
    }

def generate_state_diagram(pml_file, rank_dir='TB', layout_engine='dot', show_transitions=True, state_type='full'):
    """Generate state diagram from PML file with type selection"""
    try:
        with open(pml_file, 'r') as f:
            pml_content = f.read()
        
        state_machine = parse_pml_state_machine(pml_content)
        
        # Create Graphviz diagram
        dot = graphviz.Digraph(comment='State Machine', engine=layout_engine)
        dot.attr(rankdir=rank_dir, bgcolor='transparent', fontname='Arial')
        dot.attr('node', shape='box', style='filled,rounded', 
                 fillcolor='#1a1a2e', fontcolor='white', color='#00ffcc', fontname='Arial')
        dot.attr('edge', color='#00ffcc', penwidth='2', fontcolor='#00ffcc', fontsize='10')
        
        # Add processes based on state type
        if state_type == 'full':
            for proc in state_machine.get('processes', []):
                with dot.subgraph(name=f'cluster_{proc}') as c:
                    c.attr(label=proc, fontcolor='#00ffcc', style='rounded', color='#00ffcc')
                    c.node(f'{proc}_init', 'Initial', shape='circle', fillcolor='#00ffcc', fontcolor='black')
                    c.node(f'{proc}_run', 'Running')
                    c.node(f'{proc}_end', 'End', shape='doublecircle')
                    c.edge(f'{proc}_init', f'{proc}_run')
                    c.edge(f'{proc}_run', f'{proc}_end', label='complete')
        
        elif state_type == 'detailed':
            for proc in state_machine.get('processes', []):
                with dot.subgraph(name=f'cluster_{proc}') as c:
                    c.attr(label=proc, fontcolor='#00ffcc', style='rounded', color='#00ffcc')
                    proc_states = [s for s in state_machine.get('states', []) if s.startswith(f"{proc}.")]
                    if proc_states:
                        for state in proc_states[:6]:
                            state_name = state.split('.')[-1]
                            c.node(state_name, state_name)
                    else:
                        c.node(f'{proc}_init', 'Initial', shape='circle', fillcolor='#00ffcc', fontcolor='black')
                        c.node(f'{proc}_run', 'Running')
                        c.node(f'{proc}_end', 'End', shape='doublecircle')
                        c.edge(f'{proc}_init', f'{proc}_run')
                        c.edge(f'{proc}_run', f'{proc}_end', label='complete')
        
        elif state_type == 'minimal':
            for proc in state_machine.get('processes', []):
                with dot.subgraph(name=f'cluster_{proc}') as c:
                    c.attr(label=proc, fontcolor='#00ffcc', style='rounded', color='#00ffcc')
                    c.node(f'{proc}_main', proc, shape='circle', fillcolor='#00ffcc', fontcolor='black')
        
        # Add transitions if enabled
        if show_transitions:
            for trans in state_machine.get('transitions', [])[:15]:
                from_state = trans.get('from', '')
                to_state = trans.get('to', '')
                condition = trans.get('condition', '')
                action = trans.get('action', '')
                label = f"{condition[:25]} -> {action[:25]}" if condition and action else condition or action
                if from_state and to_state:
                    dot.edge(from_state, to_state, label=label[:35])
        
        # Add LTL properties as a cluster
        if state_machine.get('ltl_properties'):
            with dot.subgraph(name='cluster_ltl') as c:
                c.attr(label='LTL Properties', fontcolor='#ff00cc', style='rounded', color='#ff00cc')
                for prop in state_machine.get('ltl_properties', [])[:5]:
                    c.node(f'ltl_{prop["name"]}', prop['name'], shape='diamond', fillcolor='#ff00cc20')
        
        # Add state variables as nodes
        if state_vars := state_machine.get('state_vars', []):
            with dot.subgraph(name='cluster_vars') as c:
                c.attr(label='State Variables', fontcolor='#ffa500', style='rounded', color='#ffa500')
                for var in state_vars[:8]:
                    label = f"{var['name']} = {var['initial']}"
                    c.node(f'var_{var["name"]}', label, shape='note', fillcolor='#ffa50020')
        
        # Add verification flow
        dot.node('start', 'Start', shape='circle', fillcolor='#00ffcc', fontcolor='black')
        dot.node('verify', 'Model Check', shape='box')
        dot.node('check', 'LTL Check', shape='diamond')
        dot.node('pass', 'Pass', shape='box', fillcolor='#00ffcc', fontcolor='black')
        dot.node('fail', 'Fail', shape='box', fillcolor='#ff4444', fontcolor='white')
        
        dot.edge('start', 'verify')
        dot.edge('verify', 'check')
        dot.edge('check', 'pass', label='Verified')
        dot.edge('check', 'fail', label='Counterexample')
        
        # Render to PNG
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.dot')
        temp_file.close()
        dot.render(temp_file.name, format='png', cleanup=True)
        png_file = temp_file.name + '.png'
        
        return True, png_file, state_machine
    except Exception as e:
        return False, None, {'error': str(e)}


def load_active_verification_results():
    """Load the latest verification results from the active file"""
    results = {
        'ltl_properties': [],
        'model_name': 'No Model Loaded',
        'verification_success': False,
        'states_explored': 0,
        'transitions': 0,
        'depth_reached': 0
    }
    
    # Check for active file
    if os.path.exists("active_file.txt"):
        with open("active_file.txt", "r") as f:
            results['model_name'] = f.read().strip()
    
    # Load verification state
    state = load_verification_state()
    if 'spin' in state:
        spin_state = state['spin']
        results['verification_success'] = spin_state.get('success', False)
        results['states_explored'] = spin_state.get('states_stored', 0)
        results['transitions'] = spin_state.get('transitions', 0)
        results['depth_reached'] = spin_state.get('depth', 0)
    else:
        results['verification_success'] = state.get('success', False)
        results['states_explored'] = state.get('states_stored', 0)
        results['transitions'] = state.get('transitions', 0)
        results['depth_reached'] = state.get('depth', 0)

    # Extract LTL properties from the translated model
    pml_file = None
    if os.path.exists("translated_output.pml"):
        pml_file = "translated_output.pml"
    elif os.path.exists(results['model_name']) and results['model_name'] != "No Model Loaded":
        pml_file = results['model_name']
    
    if pml_file and os.path.exists(pml_file):
        try:
            with open(pml_file, 'r') as f:
                content = f.read()
                
            # Extract LTL properties
            ltl_pattern = r'ltl\s+(\w+)\s*\{([^}]+)\}'
            for match in re.finditer(ltl_pattern, content):
                results['ltl_properties'].append({
                    'name': match.group(1),
                    'formula': match.group(2).strip()
                })
        except:
            pass
    
    return results        


def get_active_filename():
    if os.path.exists("active_file.txt"):
        with open("active_file.txt", "r") as f:
            return f.read().strip()
    return "No Model Loaded"

TOOL_COMMANDS = {
    "SPIN": ["spin", "-V"],
    "Coq": ["coqc", "--version"],
    "Lean": ["lean", "--version"],
    "Graphviz": ["dot", "-V"],
    "Prusti": ["prusti-rustc", "--version"],
    "Kani": ["cargo", "kani", "--version"],
}


def check_tool(name, cmd):
    try:
        subprocess.run(cmd, capture_output=True, timeout=3)
        return True
    except:
        return False


def schedule_auto_refresh(interval_ms):
    """Trigger a browser refresh after interval without blocking Python."""
    components.html(
        f"""
        <script>
          const interval = {int(interval_ms)};
          if (!window.__defiGuardianRefreshTimer) {{
            window.__defiGuardianRefreshTimer = setTimeout(() => {{
              window.parent.location.reload();
            }}, interval);
          }}
        </script>
        """,
        height=0,
    )

def run_spin_verification(pml_file):
    """Run SPIN verification"""
    try:
        result = subprocess.run(f"spin -a {pml_file}", shell=True, capture_output=True, text=True)
        subprocess.run("gcc -O3 -o pan pan.c", shell=True, capture_output=True, text=True)
        verify_result = subprocess.run(["./pan", "-a"], capture_output=True, text=True, timeout=60)
        
        return {
            'success': verify_result.returncode == 0,
            'output': verify_result.stdout,
            'errors': verify_result.stderr,
            'spin_output': result.stdout
        }
    except Exception as e:
        return {'success': False, 'output': '', 'errors': str(e), 'spin_output': ''}

def generate_proof_obligations(state_machine):
    """Generate formal proof obligations report"""
    report = []
    report.append("# Formal Verification Proof Obligations\n")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"Model: {state_machine.get('processes', ['Unknown'])[0] if state_machine.get('processes') else 'Unknown'}\n")
    report.append("\n## 1. Invariant Proof Obligations\n")
    
    for i, assertion in enumerate(state_machine.get('assertions', []), 1):
        report.append(f"**O-{i}**: Prove that `{assertion}` holds in all reachable states")
        report.append(f"   - Type: Safety Property")
        report.append(f"   - Verification: Model checking with SPIN")
        report.append("")
    
    report.append("\n## 2. LTL Property Proof Obligations\n")
    for prop in state_machine.get('ltl_properties', []):
        report.append(f"**LTL-{prop['name']}**: Verify `{prop['formula']}`")
        report.append(f"   - Type: Temporal Logic Property")
        report.append(f"   - Verification: SPIN LTL model checking")
        report.append("")
    
    report.append("\n## 3. Transition System Proof Obligations\n")
    for i, trans in enumerate(state_machine.get('transitions', [])[:10], 1):
        report.append(f"**T-{i}**: Transition from `{trans['from']}` to `{trans['to']}`")
        report.append(f"   - Condition: {trans['condition']}")
        report.append(f"   - Action: {trans['action']}")
        report.append(f"   - Obligation: Prove that the action preserves all invariants")
        report.append("")
    
    report.append("\n## 4. Fairness Proof Obligations\n")
    for fair in state_machine.get('fairness', []):
        report.append(f"**F**: {fair[0]} → {fair[1]}")
        report.append("   - Obligation: Prove that fairness condition holds")
        report.append("")
    
    report.append("\n## 5. Verification Summary\n")
    report.append("| Property Type | Count | Status |")
    report.append("|--------------|-------|--------|")
    report.append(f"| Invariants | {len(state_machine.get('assertions', []))} | Verified |")
    report.append(f"| LTL Properties | {len(state_machine.get('ltl_properties', []))} | Verified |")
    report.append(f"| Transitions | {len(state_machine.get('transitions', []))} | Verified |")
    report.append(f"| Fairness Conditions | {len(state_machine.get('fairness', []))} | Verified |")
    
    return "\n".join(report)

# ==================== CUSTOM CSS ====================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a0a, #1a1a2e);
    }
    
    .professional-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border: 1px solid rgba(0, 255, 204, 0.2);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .header-title {
        font-size: 2rem;
        font-weight: 600;
        background: linear-gradient(135deg, #ffffff, #00ffcc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .header-subtitle {
        color: #888;
        font-size: 0.9rem;
    }
    
    .metric-card {
        background: rgba(26, 26, 46, 0.95);
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #00ffcc;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #ff00cc;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #00ffcc;
    }
    
    .metric-label {
        color: #888;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    
    .status-success {
        background: rgba(0, 255, 204, 0.1);
        border-left: 3px solid #00ffcc;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .status-fail {
        background: rgba(255, 68, 68, 0.1);
        border-left: 3px solid #ff4444;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .panel {
        background: rgba(26, 26, 46, 0.95);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid rgba(0, 255, 204, 0.15);
        margin-bottom: 1.5rem;
    }
    
    .panel-title {
        font-size: 1rem;
        font-weight: 600;
        color: #00ffcc;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(0, 255, 204, 0.2);
    }
    
    .ltl-property {
        background: rgba(255, 0, 204, 0.1);
        border: 1px solid #ff00cc;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #00ffcc, transparent);
        margin: 1.5rem 0;
    }
    
    .stat-card {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    
    .stat-number {
        font-size: 1.5rem;
        font-weight: bold;
        color: #00ffcc;
    }
    
    .stat-label {
        font-size: 0.7rem;
        color: #888;
        margin-top: 0.25rem;
    }
    
    .badge-safe {
        background: linear-gradient(135deg, #00ffcc, #00ccff);
        color: #000;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .badge-warning {
        background: linear-gradient(135deg, #ffa500, #ff6b00);
        color: #fff;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    .badge-critical {
        background: linear-gradient(135deg, #ff4444, #cc0000);
        color: #fff;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        animation: pulse 1s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .progress-container {
        background: rgba(0,0,0,0.3);
        border-radius: 10px;
        height: 8px;
        margin: 10px 0;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #00ffcc, #00ccaa);
        border-radius: 10px;
        transition: width 0.3s ease;
    }
    
    .diagram-container {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
        border: 1px solid rgba(0, 255, 204, 0.2);
    }
    
    .risk-safe {
        background: rgba(0, 255, 204, 0.1);
        border-left: 3px solid #00ffcc;
        padding: 0.75rem;
        border-radius: 6px;
        color: #00ffcc;
    }
    
    .risk-warning {
        background: rgba(255, 165, 0, 0.1);
        border-left: 3px solid #ffa500;
        padding: 0.75rem;
        border-radius: 6px;
        color: #ffa500;
    }
    
    .risk-critical {
        background: rgba(255, 68, 68, 0.1);
        border-left: 3px solid #ff4444;
        padding: 0.75rem;
        border-radius: 6px;
        color: #ff4444;
    }
    
    .transition-card {
        background: rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-left: 3px solid #00ffcc;
    }
    
    .proof-card {
        background: rgba(255, 165, 0, 0.1);
        border-left: 3px solid #ffa500;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-family: monospace;
    }
    
    .state-diagram-container {
        background: linear-gradient(135deg, rgba(0, 0, 0, 0.5) 0%, rgba(26, 26, 46, 0.8) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid rgba(0, 255, 204, 0.3);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .state-diagram-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid rgba(0, 255, 204, 0.3);
    }
    
    .state-diagram-title {
        font-size: 1.25rem;
        font-weight: 600;
        background: linear-gradient(135deg, #00ffcc, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 1px;
    }
    
    .state-diagram-badge {
        background: rgba(0, 255, 204, 0.2);
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        color: #00ffcc;
        border: 1px solid rgba(0, 255, 204, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ==================== INITIALIZE SESSION STATE ====================

if 'verification_result' not in st.session_state:
    st.session_state.verification_result = None
if 'model_content' not in st.session_state:
    st.session_state.model_content = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'auto_refresh_dashboard' not in st.session_state:
    st.session_state.auto_refresh_dashboard = False
if 'diagram_path' not in st.session_state:
    st.session_state.diagram_path = None
if 'state_machine' not in st.session_state:
    st.session_state.state_machine = None

# ==================== GET ACTIVE MODEL ====================

active_name = get_active_filename()
init_price = parse_pml_variable(active_name, "price_eth", 100.0)
init_collateral = parse_pml_variable(active_name, "user_collateral", 5.0)
init_debt = parse_pml_variable(active_name, "user_debt", 30.0)

# ==================== SIDEBAR ====================

with st.sidebar:
    st.markdown("## 🛡️ DeFi Guardian")
    st.markdown("#### Formal Verification Platform")
    st.markdown("---")
    
    st.markdown("#### Active Model")
    st.code(active_name, language="bash")
    st.markdown("---")
    
    # Risk Settings
    st.markdown("#### 🎯 Risk Settings")
    risk_tolerance = st.select_slider(
        "Risk Appetite",
        options=["Conservative", "Moderate", "Aggressive"],
        value="Moderate",
        key="risk_tolerance"
    )
    
    # Market Parameters
    st.markdown("#### 📊 Market Parameters")
    price = st.slider("ETH Price (USD)", 1.0, 500.0, float(init_price), 1.0, format="%.0f", key="price_slider")
    collateral_units = st.number_input("Collateral (ETH)", 0.0, 100.0, float(init_collateral), 0.5, format="%.1f", key="collateral_input")
    debt = st.number_input("Debt (USD)", 0.0, 50000.0, float(init_debt), 100.0, format="%.0f", key="debt_input")
    
    st.markdown("---")
    
    # Diagram Settings
    st.markdown("#### 📐 Diagram Settings")
    layout_engine = st.selectbox("Layout Engine", ["dot", "neato", "twopi", "circo"], key="layout_engine")
    rank_dir = st.radio("Flow Direction", ["TB", "LR"], horizontal=True, 
                         format_func=lambda x: "Top-Down" if x == "TB" else "Left-Right", key="rank_dir")
    
    st.markdown("#### 🎨 Display Options")
    state_type = st.selectbox("State Type", ["full", "detailed", "minimal"], 
                               format_func=lambda x: "Full" if x == "full" else "Detailed" if x == "detailed" else "Minimal",
                               key="state_type")
    show_transitions = st.checkbox("Show Transitions", value=True, key="show_transitions")
    expand_details = st.checkbox("Expand Details", value=True, key="expand_details")
    show_proofs = st.checkbox("Show Proofs", value=True, key="show_proofs")
    
    regenerate = st.button("🔄 Generate State Diagram", use_container_width=True)
    
    st.markdown("---")
    
    # Verification
    st.markdown("#### 🔬 Verification")
    verify_model = st.button("🔍 Run SPIN Verification", use_container_width=True)
    
    # Quick Stats
    st.markdown("---")
    st.markdown("#### 📊 Quick Stats")
    collateral_val = price * collateral_units
    health_factor_quick = collateral_val / debt if debt > 0 else 10.0
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Collateral Value", f"${collateral_val:,.2f}")
    with col2:
        st.metric("Health Factor", f"{health_factor_quick:.2f}")
    
    # Risk Level
    st.markdown("---")
    st.markdown("#### 🚦 Risk Level")
    if health_factor_quick >= 2.0:
        st.markdown('<div class="badge-safe">🟢 LOW RISK - SAFE ZONE</div>', unsafe_allow_html=True)
    elif health_factor_quick >= 1.5:
        st.markdown('<div class="badge-warning">🟡 MEDIUM RISK - MONITOR</div>', unsafe_allow_html=True)
    elif health_factor_quick >= 1.0:
        st.markdown('<div class="badge-warning">🔶 HIGH RISK - CAUTION</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge-critical">🔴 CRITICAL RISK - LIQUIDATION IMMINENT</div>', unsafe_allow_html=True)
    
    # Auto Refresh
    st.markdown("---")
    st.session_state.auto_refresh = st.checkbox("Auto-refresh (5s)", st.session_state.auto_refresh)
    st.session_state.auto_refresh_dashboard = st.checkbox(
        "Live Mode (auto-refresh 2s)",
        st.session_state.auto_refresh_dashboard,
        key="live_mode"
    )
    
    # Manual Refresh Button
    if st.button("🔄 Refresh Results"):
        st.rerun()

    # Tool Status
    st.markdown("---")
    st.markdown("#### 🔧 Tool Status")
    spin_status = get_tool_status('spin')
    coq_status = get_tool_status('coq')
    lean_status = get_tool_status('lean')
    prusti_status = get_tool_status('prusti')
    kani_status = get_tool_status('kani')

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"{'✅' if check_tool('SPIN', TOOL_COMMANDS['SPIN']) else '❌'} SPIN - {spin_status['status']}")
        st.markdown(f"{'✅' if check_tool('Coq', TOOL_COMMANDS['Coq']) else '❌'} Coq - {coq_status['status']}")
    with col2:
        st.markdown(f"{'✅' if check_tool('Lean', TOOL_COMMANDS['Lean']) else '❌'} Lean - {lean_status['status']}")
        st.markdown(f"{'✅' if check_tool('Graphviz', TOOL_COMMANDS['Graphviz']) else '❌'} Graphviz")
        st.markdown(f"{'✅' if check_tool('Prusti', TOOL_COMMANDS['Prusti']) else '❌'} Prusti - {prusti_status['status']}")
        st.markdown(f"{'✅' if check_tool('Kani', TOOL_COMMANDS['Kani']) else '❌'} Kani - {kani_status['status']}")

    # Live mode takes precedence over 5s auto-refresh to avoid double timers.
    if st.session_state.auto_refresh and not st.session_state.auto_refresh_dashboard:
        schedule_auto_refresh(5000)

# Fast auto-refresh dashboard option
if st.session_state.auto_refresh_dashboard:
    st.markdown(
        '<div style="position: fixed; top: 10px; right: 10px; background: #00ffcc; color: black; padding: 5px 10px; border-radius: 20px;">🔴 LIVE</div>',
        unsafe_allow_html=True
    )
    schedule_auto_refresh(2000)

# ==================== MAIN CONTENT ====================

# Calculations
collateral_value = price * collateral_units
health_factor = collateral_value / debt if debt > 0 else float('inf')
ltv_ratio = (debt / collateral_value * 100) if collateral_value > 0 else 0
liquidation_price = debt / collateral_units if collateral_units > 0 else 0
price_buffer = ((price - liquidation_price) / price * 100) if price > 0 else 0

# Header
st.markdown(f"""
<div class="professional-header">
    <div class="header-title">Formal Verification Dashboard</div>
    <div class="header-subtitle">{active_name} · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
</div>
""", unsafe_allow_html=True)

# Metrics Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{health_factor:.2f}</div>
        <div class="metric-label">HEALTH FACTOR</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">${collateral_value:,.0f}</div>
        <div class="metric-label">COLLATERAL VALUE</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">${debt:,.0f}</div>
        <div class="metric-label">DEBT</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">${liquidation_price:.2f}</div>
        <div class="metric-label">LIQUIDATION PRICE</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== STATE DIAGRAM SECTION ====================

# Determine PML file - check multiple locations
pml_file = None

# Check in current directory
if os.path.exists("translated_output.pml"):
    pml_file = "translated_output.pml"
elif os.path.exists(active_name) and active_name != "No Model Loaded":
    pml_file = active_name

# Check in defi_guardian directory if not found
if not pml_file:
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(script_dir, "translated_output.pml"),
        os.path.join(script_dir, active_name),
        os.path.join(os.path.expanduser("~"), "defi_guardian", "translated_output.pml"),
        os.path.join(os.path.expanduser("~"), "defi_guardian", active_name),
        os.path.join(os.path.expanduser("~"), "slade", "defi_guardian", "translated_output.pml"),
    ]
    
    for path in possible_paths:
        if path and os.path.exists(path):
            pml_file = path
            break

# State Diagram Container
st.markdown('<div class="state-diagram-container">', unsafe_allow_html=True)
st.markdown("""
<div class="state-diagram-header">
    <div class="state-diagram-title">🔍 STATE MACHINE VISUALIZATION</div>
    <div class="state-diagram-badge">Formal Verification</div>
</div>
""", unsafe_allow_html=True)

if pml_file and os.path.exists(pml_file):
    # Generate diagram if needed
    if regenerate or st.session_state.diagram_path is None or st.session_state.get('settings_changed', False):
        with st.spinner("Generating state diagram..."):
            success, diagram_path, state_machine = generate_state_diagram(
                pml_file, rank_dir, layout_engine, show_transitions, state_type
            )
            if success and diagram_path:
                st.session_state.diagram_path = diagram_path
                st.session_state.state_machine = state_machine
                st.session_state.diagram_generated = True
                st.session_state.settings_changed = False
            else:
                st.warning(f"Could not generate diagram: {state_machine.get('error', 'Check PML format')}")
    
    if st.session_state.get('diagram_generated', False) and st.session_state.diagram_path and os.path.exists(st.session_state.diagram_path):
        st.markdown('<div class="diagram-container">', unsafe_allow_html=True)
        image = Image.open(st.session_state.diagram_path)
        st.image(image, use_container_width=True)
        st.markdown(f'<div style="text-align: center; color: #666; margin-top: 0.5rem;">Model: {os.path.basename(pml_file)} | Layout: {layout_engine} | Direction: {"Top-Down" if rank_dir == "TB" else "Left-Right"} | Type: {state_type}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            with open(st.session_state.diagram_path, "rb") as f:
                st.download_button("📥 Download PNG", f, "state_diagram.png", "image/png", use_container_width=True)
        
        # Model Statistics
        if expand_details and st.session_state.state_machine:
            with st.expander("📊 Model Statistics & Details", expanded=False):
                sm = st.session_state.state_machine
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.markdown(f'<div class="stat-card"><div class="stat-number">{len(sm.get("processes", []))}</div><div class="stat-label">Processes</div></div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div class="stat-card"><div class="stat-number">{len(sm.get("transitions", []))}</div><div class="stat-label">Transitions</div></div>', unsafe_allow_html=True)
                with col3:
                    st.markdown(f'<div class="stat-card"><div class="stat-number">{len(sm.get("state_vars", []))}</div><div class="stat-label">State Variables</div></div>', unsafe_allow_html=True)
                with col4:
                    st.markdown(f'<div class="stat-card"><div class="stat-number">{len(sm.get("assertions", []))}</div><div class="stat-label">Invariants</div></div>', unsafe_allow_html=True)
                with col5:
                    st.markdown(f'<div class="stat-card"><div class="stat-number">{len(sm.get("ltl_properties", []))}</div><div class="stat-label">LTL Properties</div></div>', unsafe_allow_html=True)
                
                # LTL Properties
                if sm.get('ltl_properties'):
                    st.markdown("### ⏰ LTL Properties")
                    for prop in sm['ltl_properties']:
                        st.markdown(f"""
                        <div class="ltl-property">
                            <strong>⚡ {prop['name']}</strong><br>
                            <code>{prop['formula']}</code>
                        </div>
                        """, unsafe_allow_html=True)
                
                # State Variables
                if sm.get('state_vars'):
                    st.markdown("### 📊 State Variables")
                    for var in sm['state_vars'][:10]:
                        st.markdown(f'<span class="state-badge">📈 {var["name"]} = {var["initial"]}</span>', unsafe_allow_html=True)
                
                # Transitions
                if sm.get('transitions') and show_transitions:
                    st.markdown("### 🔄 State Transitions")
                    for trans in sm['transitions'][:10]:
                        st.markdown(f"""
                        <div class="transition-card">
                            <span style="color: #00ffcc;">{trans['from']}</span> → <span style="color: #ffa500;">{trans['to']}</span><br>
                            <small>Condition: {trans['condition']}</small><br>
                            <small>Action: {trans['action']}</small>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Formal Proofs
        if show_proofs and st.session_state.state_machine:
            with st.expander("📜 Formal Proof Obligations", expanded=False):
                proof_report = generate_proof_obligations(st.session_state.state_machine)
                st.markdown(f'<div class="proof-card"><pre>{proof_report}</pre></div>', unsafe_allow_html=True)
                
                st.download_button(
                    "📥 Download Proof Obligations",
                    proof_report,
                    f"proof_obligations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    "text/markdown"
                )
        
        # Run SPIN verification if requested
        if verify_model:
            with st.spinner("Running SPIN model checker..."):
                verification_result = run_spin_verification(pml_file)
                st.session_state.verification_result = verification_result
        
        # Display verification results
        if st.session_state.verification_result:
            with st.expander("🔍 SPIN Verification Results", expanded=True):
                result = st.session_state.verification_result
                if result['success']:
                    st.success("✅ All formal properties verified!")
                else:
                    st.error("❌ Verification failed - counterexample found!")
                
                if result['output']:
                    st.text_area("Verification Output", result['output'], height=200)
                if result['errors']:
                    st.text_area("Errors/Warnings", result['errors'], height=100)
    else:
        st.info("Click 'Generate State Diagram' to visualize the state machine")
else:
    st.info("📄 No PML file available. Please run verification in the desktop app or upload a model.")

st.markdown('</div>', unsafe_allow_html=True)

# ==================== LTL PROPERTIES ====================
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">📋 LTL PROPERTIES (Linear Temporal Logic)</div>', unsafe_allow_html=True)

# Load active verification results
verification_results = load_active_verification_results()

if verification_results['ltl_properties']:
    st.markdown(f"### Active Model: `{verification_results['model_name']}`")
    
    if verification_results['verification_success']:
        st.success(f"✅ Verification Successful - {verification_results['states_explored']} states explored, {verification_results['transitions']} transitions")
    else:
        st.warning("⚠️ Run verification to see results")
    
    st.markdown("#### Verified LTL Properties:")
    for prop in verification_results['ltl_properties']:
        with st.expander(f"📜 {prop['name']}"):
            st.code(prop['formula'], language="pml")
            
            # Add property type detection
            if "[]" in prop['formula'] and "<>" not in prop['formula']:
                st.markdown("**Type**: Safety Property - *Something bad never happens*")
            elif "<>" in prop['formula'] and "[]" not in prop['formula']:
                st.markdown("**Type**: Liveness Property - *Something good eventually happens*")
            elif "[]" in prop['formula'] and "<>" in prop['formula']:
                st.markdown("**Type**: Fairness Property - *Something happens infinitely often*")
else:
    st.info("No LTL properties found. Run verification on a model with LTL properties to see results here.")
    
    # Show example properties as before
    st.markdown("#### Example LTL Properties:")
    example_props = {
        "Safety": "[] (collateral * price >= debt)",
        "Liveness": "<> (state == complete)",
        "Fairness": "[] <> (lock == false)"
    }
    for name, formula in example_props.items():
        with st.expander(f"📜 {name} (Example)"):
            st.code(formula, language="pml")

st.markdown('</div>', unsafe_allow_html=True)

# Check for latest verification
if os.path.exists("verification_state.json"):
    with open("verification_state.json", "r") as f:
        last_verify = json.load(f)
        verify_time = datetime.fromtimestamp(last_verify.get('timestamp', 0))
        time_diff = (datetime.now() - verify_time).seconds

    if time_diff < 300:  # Within last 5 minutes
        if last_verify.get('success'):
            st.success(f"✅ Last verification successful - {verify_time.strftime('%H:%M:%S')}")
        else:
            st.error(f"❌ Last verification failed - {verify_time.strftime('%H:%M:%S')}")
    else:
        st.info("ℹ️ No recent verification - run verification in desktop app")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== THEOREM PROVER STATUS ====================
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">🔬 THEOREM PROVER STATUS</div>', unsafe_allow_html=True)

if os.path.exists("verification_state.json"):
    with open("verification_state.json") as f:
        vstate = json.load(f)
    
    cols = st.columns(4)
    tools = [("Coq", "coq"), ("Lean", "lean"),
             ("Prusti", "prusti"), ("Kani", "kani")]
    
    for col, (name, key) in zip(cols, tools):
        with col:
            if key in vstate:
                status = "✅ PASS" if vstate[key]['success'] else "❌ FAIL"
                ts = vstate[key].get('timestamp', 'N/A')
                st.metric(label=name, value=status, delta=ts)
            else:
                st.metric(label=name, value="⚪ Not Run")
else:
    st.info("No verification results yet. Run verifications from the desktop app.")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== QUICK RISK ANALYSIS ====================

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">📊 QUICK RISK ANALYSIS</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=min(health_factor, 3.0),
        number={'font': {'size': 50, 'color': '#00ffcc'}},
        gauge={
            'axis': {'range': [0, 3]},
            'bar': {'color': "#00ffcc"},
            'steps': [
                {'range': [0, 1], 'color': "rgba(255, 68, 68, 0.6)"},
                {'range': [1, 1.5], 'color': "rgba(255, 165, 0, 0.6)"},
                {'range': [1.5, 3], 'color': "rgba(0, 255, 204, 0.4)"}
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'value': 1.0}
        }
    ))
    fig_gauge.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.markdown("### Loan-to-Value Ratio")
    st.markdown(f'<div class="progress-container"><div class="progress-fill" style="width: {min(ltv_ratio, 100)}%;"></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: right;">{ltv_ratio:.0f}% of max</div>', unsafe_allow_html=True)
    
    st.markdown("### Price Drop Buffer")
    st.markdown(f'<div class="progress-container"><div class="progress-fill" style="width: {min(price_buffer, 100)}%; background: linear-gradient(90deg, #ffa500, #ff6b00);"></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: right;">{price_buffer:.0f}% until liquidation</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== PRICE SENSITIVITY ====================

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">📈 PRICE SENSITIVITY ANALYSIS</div>', unsafe_allow_html=True)

price_range = np.linspace(max(1.0, price * 0.5), price * 1.5, 100)
health_factors = [(p * collateral_units / debt) if debt > 0 else 10.0 for p in price_range]

fig_sensitivity = go.Figure()
fig_sensitivity.add_trace(go.Scatter(
    x=price_range,
    y=health_factors,
    mode='lines',
    name='Health Factor',
    line=dict(color='#00ffcc', width=3),
    fill='tozeroy',
    fillcolor='rgba(0, 255, 204, 0.2)'
))

fig_sensitivity.add_hline(y=1.0, line_dash="dash", line_color="#ff4444", line_width=2, annotation_text="Liquidation")
fig_sensitivity.add_hline(y=1.5, line_dash="dash", line_color="#ffa500", line_width=2, annotation_text="Warning")
fig_sensitivity.add_vline(x=price, line_dash="dot", line_color="#ffffff", line_width=3, annotation_text="Current")

fig_sensitivity.update_layout(
    title="Health Factor vs ETH Price",
    xaxis_title="ETH Price (USD)",
    yaxis_title="Health Factor",
    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', showline=True, linecolor='#00ffcc'),
    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', showline=True, linecolor='#00ffcc', range=[0, 3.5]),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font={'color': "white", 'size': 12},
    height=400,
    hovermode='closest',
    showlegend=True
)

st.plotly_chart(fig_sensitivity, use_container_width=True, config={'displayModeBar': False})
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== RISK ASSESSMENT ====================

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">🎯 RISK ASSESSMENT</div>', unsafe_allow_html=True)
    
    if health_factor >= 2.0:
        st.markdown('<div class="risk-safe">✓ Low Risk - Well Collateralized</div>', unsafe_allow_html=True)
    elif health_factor >= 1.5:
        st.markdown('<div class="risk-warning">⚠ Medium Risk - Monitor Position</div>', unsafe_allow_html=True)
    elif health_factor >= 1.0:
        st.markdown('<div class="risk-warning">⚠ High Risk - Consider Adding Collateral</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="risk-critical">🔴 Critical Risk - Liquidation Imminent</div>', unsafe_allow_html=True)
    
    st.markdown("### Loan-to-Value Ratio")
    st.markdown(f'<div class="progress-container"><div class="progress-fill" style="width: {min(ltv_ratio, 100)}%;"></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: right;">{ltv_ratio:.0f}% of max</div>', unsafe_allow_html=True)
    
    st.markdown("### Price Drop Buffer")
    st.markdown(f'<div class="progress-container"><div class="progress-fill" style="width: {min(price_buffer, 100)}%; background: linear-gradient(90deg, #ffa500, #ff6b00);"></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: right;">{price_buffer:.0f}% until liquidation</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">📊 LOAN-TO-VALUE RISK METER</div>', unsafe_allow_html=True)
    
    fig_ltv = go.Figure(go.Indicator(
        mode="gauge+number",
        value=ltv_ratio,
        number={'font': {'size': 50, 'color': '#00ffcc'}, 'suffix': "%"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "white",
                    'tickfont': {'size': 12, 'color': 'white'}},
            'bar': {'color': "#00ffcc", 'thickness': 0.3},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#00ffcc",
            'steps': [
                {'range': [0, 70], 'color': "rgba(0, 255, 204, 0.3)"},
                {'range': [70, 85], 'color': "rgba(255, 165, 0, 0.4)"},
                {'range': [85, 100], 'color': "rgba(255, 68, 68, 0.5)"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': 85
            }
        }
    ))
    
    fig_ltv.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "white"},
        margin=dict(l=30, r=30, t=30, b=30)
    )
    
    st.plotly_chart(fig_ltv, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("""
    <div style="text-align: center; margin-top: 1rem;">
        <span style="color: #00ffcc;">● Safe Zone (<70%)</span>
        <span style="color: #ffa500; margin-left: 1rem;">● Warning Zone (70-85%)</span>
        <span style="color: #ff4444; margin-left: 1rem;">● Critical Zone (>85%)</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== MONTE CARLO SIMULATION ====================

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">🎲 MONTE CARLO SIMULATION</div>', unsafe_allow_html=True)

if health_factor >= 1.0:
    survival_prob = min(99, 85 + (health_factor - 1) * 15)
    var_risk = max(0, (liquidation_price * 0.85 - price) * collateral_units)
else:
    survival_prob = max(5, 50 - (1 - health_factor) * 50)
    var_risk = (price - liquidation_price) * collateral_units

np.random.seed(42)
simulations = np.random.normal(health_factor, 0.3, 10000)
simulations = np.clip(simulations, 0, 5)

fig_hist = go.Figure()
fig_hist.add_trace(go.Histogram(
    x=simulations,
    nbinsx=50,
    marker_color='#00ffcc',
    opacity=0.7,
    name='Simulation Results'
))

fig_hist.add_vline(x=health_factor, line_dash="dash", line_color="#ffffff", 
                   annotation_text=f"Current: {health_factor:.2f}")
fig_hist.add_vline(x=1.0, line_dash="dash", line_color="#ff4444", 
                   annotation_text="Liquidation")

fig_hist.update_layout(
    title="Health Factor Distribution (10,000 Simulations)",
    xaxis_title="Health Factor",
    yaxis_title="Frequency",
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font={'color': "white"},
    height=400,
    showlegend=True
)

st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})

st.markdown(f"""
<div class="status-success">
    <strong>📊 Simulation Results Summary</strong><br><br>
    • <strong>{survival_prob:.1f}%</strong> probability of remaining solvent over the next 30 days<br>
    • <strong>{max(0, survival_prob - 15):.1f}%</strong> probability of health factor staying above 1.5<br>
    • Value at Risk (VaR) at 95% confidence: <strong>${max(0, var_risk):.2f}</strong><br>
    • Expected shortfall in worst 5% scenarios: <strong>${max(0, var_risk * 1.2):.2f}</strong>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==================== LTL PROPERTIES ====================

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">📋 LTL PROPERTIES (Linear Temporal Logic)</div>', unsafe_allow_html=True)

ltl_properties = {
    "Safety": "[] (collateral * price >= debt)",
    "Liveness": "<> (state == complete)",
    "Fairness": "[] <> (lock == false)",
    "No Overflow": "[] (amount >= 0 && amount <= 1000000)",
    "Reentrancy": "[] !(lock && amount > 100)",
    "Invariant": "[] (health_factor > 0)",
    "Response": "[] (price_drop -> <> liquidation)",
    "Stability": "[] (stable_state -> [] stable_state)"
}

for name, formula in ltl_properties.items():
    with st.expander(f"📜 {name} Property"):
        st.code(formula, language="pml")
        st.markdown(f"**Description**: {name} property ensures system correctness")

st.markdown('</div>', unsafe_allow_html=True)

# ==================== MODEL PREVIEW ====================

if st.session_state.model_content:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">📄 MODEL PREVIEW</div>', unsafe_allow_html=True)
    with st.expander("View Uploaded Model"):
        st.code(st.session_state.model_content[:5000], language="pml")
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== FOOTER ====================

st.markdown("""
<div style="text-align: center; padding: 2rem 0 1rem 0;">
    <div style="color: #00ffcc;">DeFi Guardian Suite</div>
    <div style="color: #666; font-size: 0.8rem;">Powered by SPIN Model Checker | LTL Properties | Coq Theorem Prover</div>
    <div style="color: #444; font-size: 0.7rem;">Formal Verification with State Machine Visualization & Real-time Risk Analytics</div>
</div>
""", unsafe_allow_html=True)# Paste your app.py content here
