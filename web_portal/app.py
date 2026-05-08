"""
DeFi Guardian - Web Portal
Wraps existing functionality in a web interface
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
import sys
import json
import threading
import subprocess
from pathlib import Path

# Add parent directory to path to import existing modules
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
except NameError:
    # Fallback if __file__ is not defined
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath('.'))))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'defi_guardian.db')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
EXTERNAL_AUDIT_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated', 'reports', 'audit_log.json')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==================== DATABASE SETUP ====================

def init_db():
    """Initialize database tables"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            organization TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Audit history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            file_type TEXT,
            tool_used TEXT,
            status TEXT,
            states_explored INTEGER,
            transitions INTEGER,
            depth_reached INTEGER,
            vulnerabilities_found TEXT,
            ltl_properties TEXT,
            verification_output TEXT,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            report_path TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Contact messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0
        )
    ''')
    
    # Service subscriptions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup — sync_external_audit_history is called
# after it is defined (further below) to avoid a NameError at import time.
init_db()

# ==================== USER MODEL ====================

class User(UserMixin):
    def __init__(self, id, username, email, role):
        self.id = id
        self.username = username
        self.email = email
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return User(user[0], user[1], user[2], user[3])
    return None

# ==================== AUDIT DATABASE HELPER ====================

def sync_external_audit_history():
    """Import desktop audit log entries into portal audit history."""
    if not os.path.exists(EXTERNAL_AUDIT_LOG_FILE):
        return

    try:
        with open(EXTERNAL_AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
    except Exception:
        return

    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()

        for job in jobs:
            filename = job.get('file', 'unknown')
            tool = job.get('tool', 'unknown')
            timestamp = job.get('timestamp', '')
            status = job.get('status', '').upper()
            if status in ('SUCCESS', 'PASSED'):
                status = 'PASS'
            elif status not in ('PASS', 'FAIL'):
                status = 'FAIL'

            cursor.execute('''
                SELECT 1 FROM audit_history
                WHERE filename = ? AND tool_used = ? AND audit_date = ?
            ''', (filename, tool, timestamp))
            if cursor.fetchone():
                continue

            log_path   = job.get('log_path', '')
            trace_path = job.get('trace_path', '')
            # verification_output stores the log file path so the API can read it
            # report_path stores the trace/trail path for trace viewer
            cursor.execute('''
                INSERT INTO audit_history (
                    user_id, filename, file_type, tool_used, status,
                    states_explored, transitions, depth_reached,
                    vulnerabilities_found, ltl_properties,
                    verification_output, audit_date, report_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                None,
                filename,
                os.path.splitext(filename)[1] or '',
                tool,
                status,
                job.get('details', {}).get('states', 0),
                job.get('details', {}).get('transitions', 0),
                job.get('details', {}).get('depth', 0),
                job.get('details', {}).get('error_msg', ''),
                json.dumps(job.get('specs', [])),
                log_path,
                timestamp,
                trace_path or log_path,
            ))

        conn.commit()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except:
            pass

# Now that sync_external_audit_history is defined, run the initial sync
sync_external_audit_history()

class AuditDatabase:
    """Handle audit history operations"""
    
    @staticmethod
    def save_audit(user_id, filename, file_type, tool, status, stats, ltl_results, output, report_path):
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_history 
            (user_id, filename, file_type, tool_used, status, states_explored, 
             transitions, depth_reached, ltl_properties, verification_output, report_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, filename, file_type, tool, status,
            stats.get('states', 0), stats.get('transitions', 0),
            stats.get('depth', 0), json.dumps(ltl_results),
            output, report_path
        ))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_user_audits(user_id, limit=50):
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM audit_history 
            WHERE user_id = ? OR user_id IS NULL
            ORDER BY audit_date DESC 
            LIMIT ?
        ''', (user_id, limit))
        audits = cursor.fetchall()
        conn.close()
        return audits
    
    @staticmethod
    def get_public_audits(limit=20):
        """Get recent audits for public display (anonymized)"""
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''
            SELECT filename, file_type, tool_used, status, 
                   states_explored, depth_reached, audit_date
            FROM audit_history 
            ORDER BY audit_date DESC 
            LIMIT ?
        ''', (limit,))
        audits = cursor.fetchall()
        conn.close()
        return audits

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Homepage or redirect authenticated users to their dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    recent_audits = AuditDatabase.get_public_audits(5)
    return render_template('index.html', recent_audits=recent_audits)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/services')
def services():
    """Services page"""
    plans = [
        {
            'name': 'Community',
            'price': 'Free',
            'features': [
                'Basic SPIN Verification',
                'Up to 3 contracts/month',
                'Community support',
                'Public audit history'
            ]
        },
        {
            'name': 'Professional',
            'price': '$49/month',
            'features': [
                'Full Verification Suite (SPIN, Coq, Lean)',
                'Unlimited contracts',
                'Rust verification (Prusti, Kani, Creusot)',
                '3D State Visualization',
                'Priority email support',
                'Private audit history'
            ]
        },
        {
            'name': 'Enterprise',
            'price': 'Custom',
            'features': [
                'Everything in Professional',
                'Dedicated support team',
                'Custom rule development',
                'API access',
                'SLA guarantees',
                'On-premise deployment option'
            ]
        }
    ]
    return render_template('services.html', plans=plans)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contact_messages (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        ''', (name, email, subject, message))
        conn.commit()
        conn.close()
        
        flash('Message sent successfully! We\'ll get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        organization = request.form.get('organization', '')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('register.html')
        
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # Check existing user
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            flash('Username or email already exists.', 'danger')
            conn.close()
            return render_template('register.html')
        
        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, organization)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, organization))
        
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, password_hash, role FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data[3], password):
            user = User(user_data[0], user_data[1], user_data[2], user_data[4])
            login_user(user, remember=request.form.get('remember'))
            
            # Update last login
            conn = sqlite3.connect(app.config['DATABASE'])
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user.id,))
            conn.commit()
            conn.close()
            
            flash(f'Welcome back, {username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with audit history"""
    audits = AuditDatabase.get_user_audits(current_user.id)
    return render_template('dashboard.html', audits=audits)

@app.route('/counterexample/<int:audit_id>')
@login_required
def counterexample_analysis(audit_id):
    """Counterexample analysis page"""
    return render_template('counterexample.html', audit_id=audit_id)

@app.route('/trace/<int:audit_id>')
@login_required
def trace_viewer(audit_id):
    """Trace viewer page"""
    return render_template('trace.html', audit_id=audit_id)

@app.route('/visualization')
@login_required
def visualization():
    """3D visualization and state graphs"""
    return render_template('visualization.html')

@app.route('/specifications')
@login_required
def specifications():
    """Specification writing interface"""
    return render_template('specifications.html')

@app.route('/benchmarks')
@login_required
def benchmarks():
    """Benchmarks and performance metrics"""
    return render_template('benchmarks.html')

@app.route('/streamlit', endpoint='streamlit')
@login_required
def streamlit_dashboard():
    """Embedded Streamlit dashboard"""
    return render_template('streamlit.html')

@app.route('/logs')
@login_required
def logs():
    """Logs and reports section"""
    return render_template('logs.html')

@app.route('/api/logs/<log_type>')
@login_required
def get_logs(log_type):
    """Get logs of specific type, enriched with the contract file they were generated for"""
    try:
        import glob, re
        base_dir = os.path.dirname(os.path.dirname(__file__))

        if log_type == 'console':
            patterns = [
                os.path.join(base_dir, '*.log'),
                os.path.join(base_dir, 'console_exports', '*.txt'),
                os.path.join(base_dir, 'console_exports', '*.log'),
            ]
        elif log_type == 'tool':
            patterns = [
                os.path.join(base_dir, 'logs', '**', '*.log'),
            ]
        elif log_type == 'report':
            patterns = [
                os.path.join(base_dir, 'generated', 'reports', '*.json'),
                os.path.join(base_dir, 'generated', 'reports', '*.pdf'),
                os.path.join(base_dir, 'generated', 'reports', '*.txt'),
                os.path.join(base_dir, 'generated', 'reports', 'traces', '*'),
            ]
        else:
            return jsonify({'error': 'Invalid log type'}), 400

        log_files = []
        for pattern in patterns:
            log_files.extend(glob.glob(pattern, recursive=True))

        # Also cross-reference audit_log.json for richer file→log mapping
        audit_map = {}  # log_path -> contract filename
        if os.path.exists(EXTERNAL_AUDIT_LOG_FILE):
            try:
                with open(EXTERNAL_AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
                    runs = json.load(f)
                for r in runs:
                    lp = r.get('log_path', '')
                    if lp:
                        audit_map[os.path.normpath(lp)] = {
                            'contract': os.path.basename(r.get('file', '')),
                            'tool': r.get('tool', ''),
                            'status': r.get('status', ''),
                            'timestamp': r.get('timestamp', ''),
                        }
            except Exception:
                pass

        logs = []
        for file_path in log_files:
            if not os.path.isfile(file_path):
                continue
            try:
                stat = os.stat(file_path)
                rel = os.path.relpath(file_path, base_dir)
                subdir = os.path.basename(os.path.dirname(file_path))

                # Try audit_map first (most reliable)
                norm = os.path.normpath(file_path)
                audit_info = audit_map.get(norm, {})
                contract = audit_info.get('contract', '')
                tool = audit_info.get('tool', subdir)
                status = audit_info.get('status', '')

                # Fall back: read first 6 lines of the log file
                if not contract:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            head = [f.readline() for _ in range(6)]
                        for line in head:
                            m = re.search(r'file:\s*(.+)', line, re.IGNORECASE)
                            if m:
                                contract = os.path.basename(m.group(1).strip())
                                break
                    except Exception:
                        pass

                # Infer tool from subdir name or filename
                if not tool or tool == '.':
                    name_lower = os.path.basename(file_path).lower()
                    for t in ('spin', 'certora', 'coq', 'lean', 'prusti', 'kani', 'creusot', 'verus'):
                        if t in name_lower or t in subdir.lower():
                            tool = t.upper()
                            break

                logs.append({
                    'name':     os.path.basename(file_path),
                    'path':     file_path,
                    'rel_path': rel,
                    'size':     stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'type':     'file',
                    'subdir':   subdir,
                    'contract': contract or 'Unknown',
                    'tool':     tool or subdir,
                    'status':   status,
                })
            except Exception:
                continue

        logs.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'logs': logs})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs/view/<path:filename>')
@login_required
def view_log_file(filename):
    """View content of a specific log file"""
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))

        # Security: prevent directory traversal
        if '..' in filename:
            return jsonify({'error': 'Invalid file path'}), 400

        # filename may be a relative path like logs/spin/foo.log
        file_path = os.path.normpath(os.path.join(base_dir, filename))

        # Ensure it stays within base_dir
        if not file_path.startswith(os.path.normpath(base_dir)):
            return jsonify({'error': 'Access denied'}), 403

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({'error': f'File not found: {filename}'}), 404

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs/download/<path:filename>')
@login_required
def download_log_file(filename):
    """Download a specific log file"""
    try:
        from flask import send_file as flask_send_file
        base_dir = os.path.dirname(os.path.dirname(__file__))
        if '..' in filename:
            return jsonify({'error': 'Invalid file path'}), 400
        file_path = os.path.normpath(os.path.join(base_dir, filename))
        if not file_path.startswith(os.path.normpath(base_dir)):
            return jsonify({'error': 'Access denied'}), 403
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        return flask_send_file(file_path, as_attachment=True,
                               download_name=os.path.basename(file_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

_streamlit_process = None

@app.route('/api/streamlit/start')
@login_required
def start_streamlit():
    """Start Streamlit dashboard"""
    global _streamlit_process
    import socket, time

    # Check if already running
    def is_up(port):
        try:
            with socket.create_connection(('localhost', port), timeout=1.0):
                return True
        except OSError:
            return False

    if is_up(8501):
        return jsonify({'message': 'Already running', 'port': 8501, 'url': 'http://localhost:8501'})

    try:
        app_py = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.py')
        log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'streamlit_server.log')
        with open(log_path, 'w') as log_f:
            _streamlit_process = subprocess.Popen(
                [sys.executable, '-m', 'streamlit', 'run', app_py,
                 '--server.port', '8501',
                 '--server.headless', 'true',
                 '--server.enableCORS', 'false',
                 '--server.enableXsrfProtection', 'false'],
                stdout=log_f, stderr=log_f,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )
        return jsonify({'message': 'Streamlit starting…', 'port': 8501, 'url': 'http://localhost:8501'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/streamlit/stop')
@login_required
def stop_streamlit():
    """Stop Streamlit dashboard"""
    global _streamlit_process
    try:
        if _streamlit_process and _streamlit_process.poll() is None:
            _streamlit_process.terminate()
            _streamlit_process.wait(timeout=5)
        _streamlit_process = None
        # Also kill any orphaned streamlit processes
        subprocess.run(['pkill', '-f', 'streamlit'], stderr=subprocess.DEVNULL)
        return jsonify({'message': 'Stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/streamlit/status')
@login_required
def streamlit_status():
    """Check if Streamlit is running"""
    import socket
    try:
        with socket.create_connection(('localhost', 8501), timeout=1.0):
            return jsonify({'running': True, 'url': 'http://localhost:8501'})
    except OSError:
        return jsonify({'running': False})

@app.route('/terms')
def terms():
    """Terms and Conditions"""
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    """Privacy Policy"""
    return render_template('privacy.html')

# ==================== API ENDPOINTS FOR EXISTING TOOLS ====================

@app.route('/api/run-verification', methods=['POST'])
@login_required
def run_verification():
    """API endpoint to trigger verification from web interface"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save uploaded file
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Determine file type
    ext = os.path.splitext(filename)[1].lower()
    
    # Run verification in background thread
    def run_verification_task():
        try:
            # Import existing verification modules
            from translator import DeFiTranslator
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            if ext == '.sol':
                translated = DeFiTranslator.translate_solidity(content)
            elif ext == '.rs':
                translated = DeFiTranslator.translate_rust(content)
            else:
                translated = content
            
            # Save translated model
            pml_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_model.pml')
            with open(pml_path, 'w') as f:
                f.write(translated)
            
            # Run SPIN verification
            result = subprocess.run(
                ['spin', '-a', pml_path],
                capture_output=True, text=True, timeout=60
            )
            
            # Save audit record
            AuditDatabase.save_audit(
                current_user.id,
                filename,
                ext,
                'SPIN Model Checker',
                'PASS' if result.returncode == 0 else 'FAIL',
                {'states': 0, 'transitions': 0, 'depth': 0},
                [],
                result.stdout,
                pml_path
            )
            
        except Exception as e:
            print(f"Verification error: {e}")
    
    thread = threading.Thread(target=run_verification_task)
    thread.start()
    
    return jsonify({'message': 'Verification started', 'filename': filename}), 202

@app.route('/api/state/current')
@login_required
def get_current_state():
    """Get current verification state from desktop app"""
    try:
        import os
        import json
        
        state_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'verification_state.json')
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/status')
@login_required
def get_tools_status():
    """Get status of all verification tools by probing the system live."""
    import subprocess, shutil

    def probe(cmd):
        """Return True if the command exits 0 within 5 s."""
        try:
            r = subprocess.run(cmd.split(), capture_output=True, timeout=5)
            return r.returncode == 0
        except Exception:
            return False

    # Try the project-root check_tools module first (most accurate)
    try:
        import sys as _sys
        _root = os.path.dirname(os.path.dirname(__file__))
        if _root not in _sys.path:
            _sys.path.insert(0, _root)
        from check_tools import check_all_tools
        return jsonify(check_all_tools())
    except Exception:
        pass

    # Fallback: probe each binary directly
    tools_status = {
        'SPIN':    {'installed': probe('spin -V'),          'status': 'available' if probe('spin -V')          else 'not_found'},
        'Coq':     {'installed': probe('coqc --version'),   'status': 'available' if probe('coqc --version')   else 'not_found'},
        'Lean':    {'installed': probe('lean --version'),   'status': 'available' if probe('lean --version')   else 'not_found'},
        'Prusti':  {'installed': probe('prusti-rustc --version'), 'status': 'available' if probe('prusti-rustc --version') else 'not_found'},
        'Kani':    {'installed': probe('cargo kani --version'),   'status': 'available' if probe('cargo kani --version')   else 'not_found'},
        'Certora': {'installed': probe('certoraRun --version'),   'status': 'available' if probe('certoraRun --version')   else 'not_found'},
        'GCC':     {'installed': probe('gcc --version'),    'status': 'available' if probe('gcc --version')    else 'not_found'},
    }
    return jsonify(tools_status)

@app.route('/api/counterexample/<int:audit_id>')
@login_required
def get_counterexample(audit_id):
    """Get counterexample analysis for specific audit"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''
            SELECT verification_output, report_path, tool_used, filename, status, ltl_properties
            FROM audit_history
            WHERE id = ? AND (user_id = ? OR user_id IS NULL)
        ''', (audit_id, current_user.id))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return jsonify({'error': 'Audit not found'}), 404

        log_path, report_path, tool, filename, status, ltl_props_raw = result

        ltl_properties = []
        if ltl_props_raw:
            try:
                ltl_properties = json.loads(ltl_props_raw)
            except Exception:
                pass
        tool_upper = (tool or '').upper()

        # Read the actual log file content
        output_text = ''
        if log_path and os.path.exists(log_path):
            try:
                with open(log_path, 'r', errors='replace') as f:
                    output_text = f.read()
            except Exception:
                pass

        # ── Non-SPIN tools: parse their own error format ──────────────
        if tool_upper in ('COQ', 'LEAN', 'CERTORA', 'KANI', 'PRUSTI', 'CREUSOT', 'VERUS'):
            # Extract meaningful error lines from the log
            error_lines = []
            for line in output_text.splitlines():
                low = line.lower()
                if any(k in low for k in ('error', 'fail', 'violation', 'warning', 'assert',
                                           'admitted', 'no such goal', 'cannot', 'undefined')):
                    stripped = line.strip()
                    if stripped:
                        error_lines.append(stripped)

            # Build a synthetic counterexample list from errors
            if not error_lines and output_text.strip():
                # Show the full log as the "trace" if no specific errors found
                error_lines = [l.strip() for l in output_text.splitlines() if l.strip()][:40]

            # Tool-specific recommendations
            recommendations = {
                'COQ': [
                    'Check that all Prop definitions are well-typed',
                    'Replace admit/Admitted with concrete proof tactics (lia, omega, auto)',
                    'Ensure bool fields use = true / = false comparisons, not >= 0',
                    'Use native_decide for decidable propositions',
                ],
                'LEAN': [
                    'Check theorem statement types match (Nat vs Int)',
                    'Use decide or native_decide for decidable goals',
                    'Ensure all imports are available (no Mathlib needed for basic proofs)',
                ],
                'CERTORA': [
                    'Check solc version matches contract pragma (solc8.17 vs pragma solidity)',
                    'Ensure envfree functions truly do not read msg.sender',
                    'Verify method signatures in the methods block match the contract ABI',
                    'Check CERTORAKEY environment variable is set',
                ],
            }.get(tool_upper, [
                'Review the verification log for specific error messages',
                'Check tool installation and version compatibility',
            ])

            return jsonify({
                'output':          output_text,
                'report_path':     log_path,
                'trail_path':      '',
                'trail_content':   '',
                'counterexample':  error_lines,
                'ltl_properties':  ltl_properties,
                'state_graph':     _load_state_graph(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'tool':            tool,
                'filename':        filename,
                'tool_type':       tool_upper,
                'is_non_spin':     True,
                'recommendations': recommendations,
            })

        # ── SPIN: parse trail file ────────────────────────────────────
        counterexample = parse_counterexample(output_text)

        trail_file = ''
        candidates = []
        if report_path:
            candidates.append(report_path)
            candidates.append(report_path.replace('.pml', '.trail'))
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates += [
            os.path.join(project_dir, 'translated_output.pml.trail'),
            os.path.join(project_dir, 'outputs', 'translated_output.pml.trail'),
            os.path.join(project_dir, 'logs', 'spin', 'translated_output.pml.trail'),
        ]
        for c in candidates:
            if c and os.path.exists(c):
                trail_file = c
                break

        trail_content = ''
        if trail_file:
            try:
                with open(trail_file, 'r', errors='replace') as f:
                    trail_content = f.read()
            except Exception:
                pass

        state_graph = _load_state_graph(project_dir)

        return jsonify({
            'output':          output_text,
            'report_path':     log_path,
            'trail_path':      trail_file,
            'trail_content':   trail_content,
            'counterexample':  counterexample,
            'ltl_properties':  ltl_properties,
            'state_graph':     state_graph,
            'tool':            tool,
            'filename':        filename,
            'tool_type':       'SPIN',
            'is_non_spin':     False,
            'recommendations': [
                'Review the LTL property that was violated',
                'Check the counterexample trace for the exact failing state',
                'Verify that the Promela model accurately represents the contract',
                'Consider adding constraints to rule out spurious counterexamples',
            ],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trace/<int:audit_id>')
@login_required
def get_trace(audit_id):
    """Get execution trace for specific audit"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute('''
            SELECT report_path, verification_output, tool_used
            FROM audit_history
            WHERE id = ? AND (user_id = ? OR user_id IS NULL)
        ''', (audit_id, current_user.id))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return jsonify({'error': 'Audit not found'}), 404

        report_path, log_path, tool = result
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Read log file for output text
        output_text = ''
        if log_path and os.path.exists(log_path):
            try:
                with open(log_path, 'r', errors='replace') as f:
                    output_text = f.read()
            except Exception:
                pass

        # Find trail file
        trail_file = ''
        candidates = []
        if report_path:
            candidates.append(report_path)
            candidates.append(report_path.replace('.pml', '.trail'))
        candidates += [
            os.path.join(project_dir, 'translated_output.pml.trail'),
            os.path.join(project_dir, 'outputs', 'translated_output.pml.trail'),
            os.path.join(project_dir, 'logs', 'spin', 'translated_output.pml.trail'),
        ]
        for c in candidates:
            if c and os.path.exists(c):
                trail_file = c
                break

        if not trail_file:
            # Try the saved trace JSON first (has full structured data)
            trace_json_path = report_path if report_path and report_path.endswith('.json') else ''
            if trace_json_path and os.path.exists(trace_json_path):
                try:
                    with open(trace_json_path, 'r', errors='replace') as f:
                        trace_json = json.load(f)
                    # Convert node_details format to trace step format
                    raw_steps = trace_json.get('node_details') or trace_json.get('steps') or []
                    steps = []
                    for s in raw_steps:
                        steps.append({
                            'step':       str(s.get('step', s.get('id', len(steps)+1))),
                            'proc':       s.get('proc', s.get('proc_name', 'Contract')),
                            'line':       str(s.get('line', 0)),
                            'state':      str(s.get('state', '')),
                            'file':       s.get('file', ''),
                            'action':     s.get('action', s.get('raw', '')),
                            'updates':    s.get('updates', {}),
                            'variables':  s.get('variables', {}),
                            'is_error':   s.get('type') == 'violation',
                            'transition': s.get('action', s.get('raw', '')),
                        })
                    return jsonify({'trace': steps, 'source': 'json', 'log_path': log_path})
                except Exception:
                    pass

            # Return log output as trace lines if no trail file
            if output_text:
                steps = parse_trace(output_text)
                if steps:
                    return jsonify({'trace': steps, 'source': 'log', 'log_path': log_path})
                # Last resort: raw lines
                lines = [{'step': str(i+1), 'state': line.strip(), 'proc': '', 'line': '0',
                          'action': line.strip(), 'updates': {}, 'variables': {},
                          'is_error': 'error' in line.lower() or 'violation' in line.lower(),
                          'transition': ''}
                         for i, line in enumerate(output_text.splitlines()) if line.strip()]
                return jsonify({'trace': lines, 'source': 'log', 'log_path': log_path})
            return jsonify({'error': 'Trace not found'}), 404

        with open(trail_file, 'r', errors='replace') as f:
            trail_content = f.read()

        trace = parse_trace(trail_content)
        return jsonify({
            'trace': trace,
            'trail_path': trail_file,
            'source': 'trail',
            'output': output_text,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/state-graph/<int:audit_id>')
@login_required
def get_state_graph(audit_id):
    """Return state graph JSON for a given audit"""
    try:
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        state_graph = _load_state_graph(project_dir)
        if state_graph:
            return jsonify(state_graph)
        return jsonify({'error': 'State graph not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _load_state_graph(project_dir):
    """Load the most recent state graph JSON from the project directory"""
    candidates = [
        os.path.join(project_dir, 'generated', 'reports', 'state_graph.json'),
        os.path.join(project_dir, 'generated', 'verification_state.json'),
        os.path.join(project_dir, 'verification_state.json'),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                continue
    return None

def parse_counterexample(output):
    """
    Parse SPIN verification output into a list of meaningful step strings.
    Captures the full execution trace, not just lines after the word 'error'.
    """
    if not output:
        return []

    steps = []
    import re

    # Pattern A: SPIN 6.x  "N:  proc P (Name) file:line (state S)  [action]"
    pat_a = re.compile(
        r'^\s*(\d+):\s*proc\s+\d+\s*\(([^)]+)\)\s+\S+:(\d+)\s+\(state\s+(\d+)\)\s*(?:\[(.*)\])?'
    )
    # Pattern B: older SPIN  "N:  proc P (Name) line L "file" (state S)  [action]"
    pat_b = re.compile(
        r'^\s*(\d+):\s*proc\s+\d+\s*\(([^)]+)\)\s+line\s+(\d+)\s+"[^"]+"\s+\(state\s+(\d+)\)\s*(?:\[(.*)\])?'
    )

    for line in output.splitlines():
        m = pat_a.match(line) or pat_b.match(line)
        if m:
            groups = m.groups()
            step_num  = groups[0]
            proc_name = groups[1].strip()
            line_num  = groups[2]
            state_id  = groups[3]
            action    = (groups[4] or "").strip()
            is_error  = (
                "assert" in action.lower() or
                "violation" in line.lower() or
                "error" in line.lower() or
                "acceptance" in line.lower()
            )
            label = f"[{step_num}] {proc_name}  line {line_num}  state {state_id}"
            if action:
                label += f"  →  {action}"
            if is_error:
                label = "❌ " + label
            steps.append(label)
            continue

        # Capture LTL violation / assertion lines even outside step blocks
        low = line.lower()
        if any(k in low for k in ("ltl", "assertion violated", "acceptance cycle", "error:")):
            stripped = line.strip()
            if stripped:
                steps.append("⚠️  " + stripped)

    # If SPIN replay produced no parseable steps, fall back to the raw log
    # but filter out blank lines and pure separator lines
    if not steps:
        for line in output.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith('=') and not stripped.startswith('-'):
                steps.append(stripped)

    return steps


def parse_trace(trail_content):
    """
    Parse SPIN trail/log content into structured step dicts for the trace viewer.
    Handles both SPIN replay output and raw log files.
    """
    if not trail_content:
        return []

    import re
    steps = []

    pat_a = re.compile(
        r'^\s*(\d+):\s*proc\s+(\d+)\s*\(([^)]+)\)\s+(\S+):(\d+)\s+\(state\s+(\d+)\)\s*(?:\[(.*)\])?'
    )
    pat_b = re.compile(
        r'^\s*(\d+):\s*proc\s+(\d+)\s*\(([^)]+)\)\s+line\s+(\d+)\s+"([^"]+)"\s+\(state\s+(\d+)\)\s*(?:\[(.*)\])?'
    )
    var_pat = re.compile(r'^\s+(\w+)\s*=\s*(.+)$')

    current = None
    current_vars = {}

    for line in trail_content.splitlines():
        m = pat_a.match(line)
        if m:
            sn, pid, pname, fname, lnum, sid, action = m.groups()
            updates = {}
            if action:
                for part in action.split(','):
                    if '=' in part:
                        k, v = part.split('=', 1)
                        updates[k.strip()] = v.strip()
                        current_vars[k.strip()] = v.strip()
            is_err = bool(action and ("assert" in action.lower() or "violation" in action.lower()))
            current = {
                'step':       sn,
                'proc':       pname.strip(),
                'line':       lnum,
                'state':      sid,
                'file':       fname,
                'action':     (action or "").strip(),
                'updates':    updates,
                'variables':  current_vars.copy(),
                'is_error':   is_err,
                'transition': (action or "").strip(),
            }
            steps.append(current)
            continue

        m = pat_b.match(line)
        if m:
            sn, pid, pname, lnum, fname, sid, action = m.groups()
            updates = {}
            if action:
                for part in action.split(','):
                    if '=' in part:
                        k, v = part.split('=', 1)
                        updates[k.strip()] = v.strip()
                        current_vars[k.strip()] = v.strip()
            is_err = bool(action and ("assert" in action.lower() or "violation" in action.lower()))
            current = {
                'step':       sn,
                'proc':       pname.strip(),
                'line':       lnum,
                'state':      sid,
                'file':       fname,
                'action':     (action or "").strip(),
                'updates':    updates,
                'variables':  current_vars.copy(),
                'is_error':   is_err,
                'transition': (action or "").strip(),
            }
            steps.append(current)
            continue

        # Variable assignment line
        if current:
            m = var_pat.match(line)
            if m:
                k, v = m.group(1).strip(), m.group(2).strip()
                current['variables'][k] = v
                current['updates'][k]   = v
                current_vars[k]         = v
                continue

        # LTL / assertion violation lines
        low = line.lower()
        if any(k in low for k in ("ltl", "assertion violated", "acceptance cycle", "error:")):
            stripped = line.strip()
            if stripped:
                steps.append({
                    'step':       str(len(steps) + 1),
                    'proc':       'verifier',
                    'line':       '0',
                    'state':      'violation',
                    'file':       '',
                    'action':     stripped,
                    'updates':    {},
                    'variables':  current_vars.copy(),
                    'is_error':   True,
                    'transition': stripped,
                })

    return steps

@app.route('/api/desktop-runs')
@login_required
def get_desktop_runs():
    """Return recent desktop audit runs from audit_log.json"""
    try:
        if not os.path.exists(EXTERNAL_AUDIT_LOG_FILE):
            return jsonify([])
        with open(EXTERNAL_AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
            runs = json.load(f)
        # Return only the fields needed by the dashboard
        result = [
            {
                'id': r.get('id', ''),
                'timestamp': r.get('timestamp', ''),
                'tool': r.get('tool', ''),
                'file': r.get('file', ''),
                'status': r.get('status', ''),
                'states': r.get('details', {}).get('states', 0),
                'depth': r.get('details', {}).get('depth', 0),
                'error_msg': r.get('details', {}).get('error_msg', ''),
            }
            for r in runs[:50]
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_globals():
    """Inject common variables into all templates"""
    return {
        'current_year': datetime.now().year,
        'app_name': 'DeFi Guardian',
        'app_version': '1.0.0'
    }

if __name__ == '__main__':
    app.run(debug=False, port=5000, threaded=True, use_reloader=False)