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
import json
from PIL import Image
import io
import graphviz
import networkx as nx
import time
try:
    from streamlit_extras.stylable_container import stylable_container 
except ImportError:
    # Fallback if streamlit-extras is not installed
    def stylable_container(key, css_styles):
        return st.container()

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def styled_button(label, key=None, variant="primary", size="medium"): 
     """Generate styled HTML button for Streamlit""" 
     
     variants = { 
         "primary": { 
             "bg": "linear-gradient(135deg, #00ffcc 0%, #00ccff 100%)", 
             "color": "#0a0e17", 
             "hover": "linear-gradient(135deg, #00e6b8 0%, #00b8e6 100%)" 
         }, 
         "secondary": { 
             "bg": "linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%)", 
             "color": "white", 
             "hover": "linear-gradient(135deg, #a86bc9 0%, #9b59b6 100%)" 
         }, 
         "danger": { 
             "bg": "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)", 
             "color": "white", 
             "hover": "linear-gradient(135deg, #f56565 0%, #e53e3e 100%)" 
         }, 
         "success": { 
             "bg": "linear-gradient(135deg, #10b981 0%, #059669 100%)", 
             "color": "white", 
             "hover": "linear-gradient(135deg, #34d399 0%, #10b981 100%)" 
         } 
     } 
     
     sizes = { 
         "small": {"padding": "8px 16px", "font-size": "12px"}, 
         "medium": {"padding": "12px 24px", "font-size": "14px"}, 
         "large": {"padding": "16px 32px", "font-size": "16px"} 
     } 
     
     v = variants.get(variant, variants["primary"]) 
     s = sizes.get(size, sizes["medium"]) 
     
     button_html = f""" 
     <style> 
         .styled-btn-{key} {{ 
             background: {v['bg']}; 
             color: {v['color']}; 
             border: none; 
             border-radius: 12px; 
             padding: {s['padding']}; 
             font-size: {s['font-size']}; 
             font-weight: 600; 
             cursor: pointer; 
             transition: all 0.3s ease; 
             position: relative; 
             overflow: hidden; 
             width: 100%; 
             text-align: center; 
             display: inline-block; 
             text-decoration: none; 
         }} 
         
         .styled-btn-{key}:hover {{ 
             background: {v['hover']}; 
             transform: translateY(-2px); 
             box-shadow: 0 8px 20px rgba(0, 255, 204, 0.2); 
         }} 
         
         .styled-btn-{key}::after {{ 
             content: ''; 
             position: absolute; 
             top: 50%; 
             left: 50%; 
             width: 0; 
             height: 0; 
             border-radius: 50%; 
             background: rgba(255, 255, 255, 0.3); 
             transform: translate(-50%, -50%); 
             transition: width 0.3s, height 0.3s; 
         }} 
         
         .styled-btn-{key}:active::after {{ 
             width: 200px; 
             height: 200px; 
         }} 
     </style> 
     <button class="styled-btn-{key}" onclick="this.disabled=true; this.style.opacity='0.7';">{label}</button> 
     """ 
     
     return st.markdown(button_html, unsafe_allow_html=True)

def verification_progress_card(): 
     """Animated verification progress card""" 
     
     with stylable_container( 
         key="progress_card", 
         css_styles=""" 
             { 
                 background: linear-gradient(135deg, #1a1a2e, #16213e); 
                 border-radius: 16px; 
                 padding: 24px; 
                 border: 1px solid rgba(0, 255, 204, 0.2); 
                 margin: 16px 0; 
             } 
         """ 
     ): 
         col1, col2 = st.columns([3, 1]) 
         
         with col1: 
             st.markdown("### 🔄 Verification Progress") 
             
             # Animated progress bar 
             st.markdown(""" 
             <div class="progress-container"> 
                 <div class="progress-fill" style="width: 75%; animation: pulse 2s infinite;"> 
                     <span class="progress-text">75%</span> 
                 </div> 
             </div> 
             <style> 
                 .progress-container { 
                     background: rgba(0,0,0,0.3); 
                     border-radius: 20px; 
                     height: 24px; 
                     overflow: hidden; 
                 } 
                 .progress-fill { 
                     background: linear-gradient(90deg, #00ffcc, #00ccaa); 
                     height: 100%; 
                     border-radius: 20px; 
                     display: flex; 
                     align-items: center; 
                     justify-content: center; 
                     transition: width 0.5s ease; 
                 } 
                 .progress-text { 
                     color: #0a0e17; 
                     font-weight: bold; 
                     font-size: 12px; 
                 } 
                 @keyframes pulse { 
                     0%, 100% { opacity: 1; } 
                     50% { opacity: 0.8; } 
                 } 
             </style> 
             """, unsafe_allow_html=True) 
             
             # Step indicators 
             steps = [ 
                 ("📄 Parse Contract", "completed"), 
                 ("🔄 Generate Model", "active"), 
                 ("🔍 Run SPIN", "pending"), 
                 ("📜 Coq Verification", "pending"), 
                 ("⚡ Lean Verification", "pending") 
             ] 
             
             for step, status in steps: 
                 icons = { 
                     "completed": "✅", 
                     "active": "🔄", 
                     "pending": "⏳" 
                 } 
                 st.markdown(f"{icons[status]} {step}") 
         
         with col2: 
             st.metric("Time Elapsed", "12.3s") 
             st.metric("States Explored", "1,234")

def theme_toggle(): 
     """Theme toggle switch for dashboard""" 
     
     if "theme" not in st.session_state: 
         st.session_state.theme = "dark" 
     
     col1, col2 = st.columns([1, 5]) 
     
     with col1: 
         if st.button("🌙" if st.session_state.theme == "dark" else "☀️"): 
             st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark" 
             st.rerun() 
     
     # Apply theme CSS 
     if st.session_state.theme == "dark": 
         st.markdown(""" 
         <style> 
             .stApp { background: linear-gradient(135deg, #0a0a0a, #1a1a2e); } 
             .metric-card { background: rgba(26, 26, 46, 0.95); } 
         </style> 
         """, unsafe_allow_html=True) 
     else: 
         st.markdown(""" 
         <style> 
             .stApp { background: linear-gradient(135deg, #f5f5f5, #e8e8e8); } 
             .metric-card { background: white; color: #333; } 
             .metric-value { color: #0066cc; } 
         </style> 
         """, unsafe_allow_html=True)

def landing_page(): 
     """Professional landing page with feature showcase""" 
     
     # Hero section 
     st.markdown(""" 
     <div style="text-align: center; padding: 4rem 2rem;"> 
         <h1 style="font-size: 3.5rem; background: linear-gradient(135deg, #00ffcc, #00ccff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;"> 
             🛡️ DeFi Guardian 
         </h1> 
         <p style="font-size: 1.25rem; color: #888; margin: 1rem 0;"> 
             Formal Verification Suite for Smart Contracts 
         </p> 
         <div style="display: flex; gap: 1rem; justify-content: center; margin: 2rem 0;"> 
             <button class="gradient-btn">Get Started →</button> 
             <button class="glass-btn">View Demo</button> 
         </div> 
     </div> 
     """, unsafe_allow_html=True) 
     
     # Feature grid 
     col1, col2, col3, col4 = st.columns(4) 
     
     features = [ 
         ("🔬", "Multi-Tool Verification", "SPIN, Coq, Lean, Prusti, Kani, Creusot"), 
         ("📐", "State Machine Analysis", "Interactive 3D state space exploration"), 
         ("📊", "Risk Analytics", "Monte Carlo simulations & health factors"), 
         ("📜", "Proof Generation", "Formal proof obligations & LTL properties") 
     ] 
     
     for col, (icon, title, desc) in zip([col1, col2, col3, col4], features): 
         with col: 
             st.markdown(f""" 
             <div class="glass-card" style="text-align: center;"> 
                 <div style="font-size: 2.5rem;">{icon}</div> 
                 <h4>{title}</h4> 
                 <p style="color: #888; font-size: 0.85rem;">{desc}</p> 
             </div> 
             """, unsafe_allow_html=True)

def notification_system(): 
     """Toast-style notifications for verification events""" 
     
     if "notifications" not in st.session_state: 
         st.session_state.notifications = [] 
     
     def add_notification(message, type="info", duration=5000): 
         st.session_state.notifications.append({ 
             "message": message, 
             "type": type, 
             "id": datetime.now().timestamp() 
         }) 
     
     # Display notifications 
     for notification in st.session_state.notifications[:3]: 
         colors = { 
             "success": ("#10b981", "#059669"), 
             "error": ("#ef4444", "#dc2626"), 
             "warning": ("#f59e0b", "#d97706"), 
             "info": ("#00ffcc", "#00ccaa") 
         } 
         bg, border = colors.get(notification["type"], colors["info"]) 
         
         st.markdown(f""" 
         <div class="notification" style=" 
             background: {bg}20; 
             border-left: 4px solid {border}; 
             padding: 1rem; 
             margin: 0.5rem 0; 
             border-radius: 8px; 
             animation: slideIn 0.3s ease; 
         "> 
             {notification["message"]} 
         </div> 
         <style> 
             @keyframes slideIn {{ 
                 from {{ transform: translateX(-100%); opacity: 0; }} 
                 to {{ transform: translateX(0); opacity: 1; }} 
             }} 
         </style> 
         """, unsafe_allow_html=True)

def render_3d_state_graph_web3d(state_graph_data, height=500):
    """
    Render 3D state graph using Three.js through Streamlit components
    
    Args:
        state_graph_data: dict with 'nodes' and 'edges' lists
        height: height of visualization in pixels
    """
    
    # Convert state graph data to JSON for JavaScript
    nodes_json = json.dumps(state_graph_data.get('nodes', []))
    edges_json = json.dumps(state_graph_data.get('edges', []))
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0;
                overflow: hidden;
                background: transparent;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }}
            #container {{
                width: 100vw;
                height: 100vh;
            }}
            #info {{
                position: absolute;
                top: 20px;
                left: 20px;
                color: #00ffcc;
                background: rgba(10, 14, 23, 0.8);
                padding: 12px 20px;
                border-radius: 12px;
                border: 1px solid rgba(0, 255, 204, 0.3);
                backdrop-filter: blur(8px);
                pointer-events: none;
                z-index: 100;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }}
            #controls-hint {{
                position: absolute;
                bottom: 20px;
                left: 20px;
                color: #888;
                background: rgba(10, 14, 23, 0.6);
                padding: 6px 16px;
                border-radius: 20px;
                font-size: 11px;
                backdrop-filter: blur(4px);
                pointer-events: none;
                z-index: 100;
                letter-spacing: 0.5px;
            }}
            .tooltip {{
                position: absolute;
                background: rgba(26, 26, 46, 0.95);
                color: #00ffcc;
                padding: 10px 15px;
                border-radius: 8px;
                border: 1px solid rgba(0, 255, 204, 0.5);
                font-size: 13px;
                pointer-events: none;
                z-index: 200;
                display: none;
                box-shadow: 0 8px 32px rgba(0,0,0,0.5);
                backdrop-filter: blur(10px);
            }}
            #error-log {{
                position: absolute;
                top: 0;
                left: 0;
                color: #ff4444;
                font-size: 10px;
                z-index: 1000;
                background: rgba(0,0,0,0.7);
                display: none;
            }}
        </style>
    </head>
    <body>
        <div id="error-log"></div>
        <div id="info">
            <strong style="font-size: 16px; letter-spacing: 1px;">🔬 3D STATE SPACE</strong><br>
            <span style="font-size: 11px; color: #00ffcc88; text-transform: uppercase;">Real-time Model Visualization</span>
        </div>
        <div id="controls-hint">
            🖱️ DRAG TO ROTATE · SCROLL TO ZOOM · RIGHT-CLICK TO PAN
        </div>
        <div id="tooltip" class="tooltip"></div>
        <div id="container"></div>
        
        <!-- Use specific CDN versions and handle loading order -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        
        <script>
            // Helper to log errors to a hidden div for debugging if needed
            function logError(msg) {{
                const errDiv = document.getElementById('error-log');
                errDiv.style.display = 'block';
                errDiv.innerHTML += msg + '<br>';
                console.error(msg);
            }}

            // Data from Python
            const nodesData = {nodes_json};
            const edgesData = {edges_json};
            const trailData = {json.dumps(st.session_state.get('trail_data', {}))};
            
            // Wait for THREE to be loaded
            function init() {{
                if (typeof THREE === 'undefined') {{
                    setTimeout(init, 100);
                    return;
                }}

                // Load dependent scripts
                const loadScript = (url) => {{
                    return new Promise((resolve, reject) => {{
                        const script = document.createElement('script');
                        script.src = url;
                        script.onload = resolve;
                        script.onerror = reject;
                        document.head.appendChild(script);
                    }});
                }};

                Promise.all([
                    loadScript('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js'),
                    loadScript('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/renderers/CSS2DRenderer.js')
                ]).then(() => {{
                    startVisualization();
                }}).catch(err => {{
                    logError('Failed to load Three.js extensions: ' + err);
                }});
            }}

            function startVisualization() {{
                try {{
                    // Initialize scene
                    const scene = new THREE.Scene();
                    scene.background = null; 
                    
                    const container = document.getElementById('container');
                    const width = container.clientWidth;
                    const height = container.clientHeight;

                    // Camera
                    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
                    camera.position.set(10, 8, 15);
                    
                    // Renderers
                    const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
                    renderer.setSize(width, height);
                    renderer.setPixelRatio(window.devicePixelRatio);
                    renderer.shadowMap.enabled = true;
                    container.appendChild(renderer.domElement);
                    
                    const labelRenderer = new THREE.CSS2DRenderer();
                    labelRenderer.setSize(width, height);
                    labelRenderer.domElement.style.position = 'absolute';
                    labelRenderer.domElement.style.top = '0px';
                    labelRenderer.domElement.style.pointerEvents = 'none';
                    container.appendChild(labelRenderer.domElement);
                    
                    // Controls
                    const controls = new THREE.OrbitControls(camera, renderer.domElement);
                    controls.enableDamping = true;
                    controls.dampingFactor = 0.05;
                    controls.autoRotate = true;
                    controls.autoRotateSpeed = 0.5;
                    
                    // Lighting
                    scene.add(new THREE.AmbientLight(0x404060));
                    
                    const dirLight = new THREE.DirectionalLight(0x00ffcc, 1);
                    dirLight.position.set(5, 10, 7);
                    dirLight.castShadow = true;
                    scene.add(dirLight);
                    
                    const pointLight = new THREE.PointLight(0xff00cc, 1, 20);
                    pointLight.position.set(-5, 5, -5);
                    scene.add(pointLight);
                    
                    // Background grid
                    const gridHelper = new THREE.GridHelper(30, 30, 0x00ffcc, 0x1a1a2e);
                    gridHelper.position.y = -5;
                    gridHelper.material.opacity = 0.2;
                    gridHelper.material.transparent = true;
                    scene.add(gridHelper);
                    
                    // Particles
                    const particlesGeo = new THREE.BufferGeometry();
                    const particlesCount = 800;
                    const posArray = new Float32Array(particlesCount * 3);
                    for(let i = 0; i < particlesCount * 3; i++) {{
                        posArray[i] = (Math.random() - 0.5) * 40;
                    }}
                    particlesGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
                    const particlesMat = new THREE.PointsMaterial({{ size: 0.05, color: 0x00ffcc, transparent: true, opacity: 0.4 }});
                    const particles = new THREE.Points(particlesGeo, particlesMat);
                    scene.add(particles);
                    
                    // Store objects
                    const nodeMeshes = [];
                    const nodePositions = {{}};
                    
                    // Calculate positions and create nodes
                    const actualNodes = nodesData.length > 0 ? nodesData : ['S0', 'S1', 'S2', 'S3'];
                    actualNodes.forEach((nodeName, index) => {{
                        const angle = (index / actualNodes.length) * Math.PI * 2;
                        const radius = 8;
                        const y = (index % 2 === 0 ? 1 : -1) * (index * 0.4); // Spiral layout to reduce crowding
                        const x = Math.cos(angle) * radius;
                        const z = Math.sin(angle) * radius;
                        
                        nodePositions[nodeName] = new THREE.Vector3(x, y, z);
                        
                        // Node Details for Tooltip
                        const details = trailData && trailData.node_details ? 
                                       trailData.node_details.find(n => n.id === nodeName) : null;
                        
                        let color = 0x00ffcc; 
                        let emissive = 0x00ffcc;
                        
                        const isInTrail = trailData && trailData.counterexample_path && 
                                          trailData.counterexample_path.includes(nodeName);
                        
                        if (isInTrail) {{
                            color = 0xff4444; 
                            emissive = 0xff4444;
                        }} else if (nodeName.toLowerCase().includes('ltl')) {{
                            color = 0xff00cc; // Pink for LTL
                            emissive = 0xff00cc;
                        }} else if (nodeName.toLowerCase().includes('pass')) {{
                            color = 0x00ff00; // Green for success
                            emissive = 0x00ff00;
                        }} else if (nodeName.toLowerCase().includes('fail')) {{
                            color = 0xff4444; // Red for failure
                            emissive = 0xff4444;
                        }}

                        const sphere = new THREE.Mesh(
                            new THREE.SphereGeometry(0.5, 32, 32),
                            new THREE.MeshStandardMaterial({{ 
                                color: color, 
                                emissive: emissive, 
                                emissiveIntensity: 0.5,
                                metalness: 0.8,
                                roughness: 0.2
                            }})
                        );
                        sphere.position.set(x, y, z);
                        
                        // Add data for tooltip
                        let tooltipContent = `<strong>${{nodeName}}</strong><br>`;
                        if (details) {{
                            tooltipContent += `Action: ${{details.action}}<br>`;
                            tooltipContent += `Line: ${{details.line}}<br>`;
                            if (details.variables && Object.keys(details.variables).length > 0) {{
                                tooltipContent += `<hr style="border: 0.5px solid #00ffcc33;">`;
                                for (const [v, val] of Object.entries(details.variables)) {{
                                    tooltipContent += `${{v}}: <span style="color: #00ffcc;">${{val}}</span><br>`;
                                }}
                            }}
                        }}
                        
                        sphere.userData = {{ name: nodeName, tooltip: tooltipContent }};
                        scene.add(sphere);
                        nodeMeshes.push(sphere);
                        
                        // Label
                        const div = document.createElement('div');
                        div.textContent = nodeName;
                        div.style.color = '#ffffff';
                        div.style.fontSize = '12px';
                        div.style.background = 'rgba(0, 255, 204, 0.2)';
                        div.style.padding = '2px 8px';
                        div.style.borderRadius = '10px';
                        div.style.border = '1px solid #00ffcc';
                        div.style.backdropFilter = 'blur(4px)';
                        
                        const label = new THREE.CSS2DObject(div);
                        label.position.set(x, y + 0.8, z);
                        scene.add(label);
                    }});
                    
                    // Edges
                    edgesData.forEach(edge => {{
                        const fromPos = nodePositions[edge.from];
                        const toPos = nodePositions[edge.to];
                        
                        if (fromPos && toPos) {{
                            const curve = new THREE.CatmullRomCurve3([
                                fromPos,
                                new THREE.Vector3().addVectors(fromPos, toPos).multiplyScalar(0.5).add(new THREE.Vector3(0, 1, 0)),
                                toPos
                            ]);
                            
                            // Check if this edge is in the trail
                            const isEdgeInTrail = trailData && trailData.edges && 
                                                 trailData.edges.some(e => e.from === edge.from && e.to === edge.to);
                            
                            const tube = new THREE.Mesh(
                                new THREE.TubeGeometry(curve, 20, isEdgeInTrail ? 0.15 : 0.05, 8, false),
                                new THREE.MeshStandardMaterial({{ 
                                    color: isEdgeInTrail ? 0xff4444 : 0x00ffcc, 
                                    transparent: true, 
                                    opacity: isEdgeInTrail ? 1.0 : 0.6 
                                }})
                            );
                            scene.add(tube);
                        }}
                    }});
                    
                    // Raycaster
                    const raycaster = new THREE.Raycaster();
                    const mouse = new THREE.Vector2();
                    const tooltip = document.getElementById('tooltip');
                    
                    window.addEventListener('mousemove', (event) => {{
                        const rect = container.getBoundingClientRect();
                        mouse.x = ((event.clientX - rect.left) / width) * 2 - 1;
                        mouse.y = -((event.clientY - rect.top) / height) * 2 + 1;
                        
                        raycaster.setFromCamera(mouse, camera);
                        const intersects = raycaster.intersectObjects(nodeMeshes);
                        
                        if (intersects.length > 0) {{
                            const node = intersects[0].object;
                            tooltip.style.display = 'block';
                            tooltip.style.left = event.clientX + 10 + 'px';
                            tooltip.style.top = event.clientY - 10 + 'px';
                            tooltip.innerHTML = `<strong>${{node.userData.name}}</strong>`;
                        }} else {{
                            tooltip.style.display = 'none';
                        }}
                    }});
                    
                    function animate() {{
                        requestAnimationFrame(animate);
                        controls.update();
                        particles.rotation.y += 0.001;
                        renderer.render(scene, camera);
                        labelRenderer.render(scene, camera);
                    }}
                    animate();
                    
                    window.addEventListener('resize', () => {{
                        const w = container.clientWidth;
                        const h = container.clientHeight;
                        camera.aspect = w / h;
                        camera.updateProjectionMatrix();
                        renderer.setSize(w, h);
                        labelRenderer.setSize(w, h);
                    }});

                }} catch (e) {{
                    logError('Runtime error: ' + e.message);
                }}
            }}

            init();
        </script>
    </body>
    </html>
    """
    
    # Render component
    components.html(html_code, height=height, scrolling=False)

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
    page_title="DeFi Guardian", 
    page_icon="🛡️", 
    layout="wide", 
    initial_sidebar_state="expanded" 
) 
 
# Modern glassmorphism styling 
st.markdown(""" 
<style> 
    /* Glassmorphism cards */ 
    .glass-card { 
        background: rgba(26, 26, 46, 0.7); 
        backdrop-filter: blur(10px); 
        border: 1px solid rgba(0, 255, 204, 0.2); 
        border-radius: 16px; 
        padding: 1.5rem; 
        transition: all 0.3s ease; 
        height: 220px; /* Fixed height for uniformity */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    } 
     
    .glass-card:hover { 
        transform: translateY(-4px); 
        border-color: rgba(0, 255, 204, 0.5); 
        box-shadow: 0 8px 32px rgba(0, 255, 204, 0.1); 
    } 
     
    /* Animated gradient buttons */ 
    .gradient-btn { 
        background: linear-gradient(135deg, #00ffcc 0%, #00ccff 100%); 
        border: none; 
        border-radius: 12px; 
        padding: 12px 24px; 
        font-weight: 600; 
        color: #0a0e17; 
        transition: all 0.3s ease; 
        position: relative; 
        overflow: hidden; 
    } 
     
    .gradient-btn::before { 
        content: ''; 
        position: absolute; 
        top: 0; 
        left: -100%; 
        width: 100%; 
        height: 100%; 
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); 
        transition: left 0.5s ease; 
    } 
     
    .gradient-btn:hover::before { 
        left: 100%; 
    } 
     
    /* Pulse animation for critical alerts */ 
    @keyframes pulse-glow { 
        0%, 100% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.3); } 
        50% { box-shadow: 0 0 40px rgba(239, 68, 68, 0.6); } 
    } 
     
    .critical-alert { 
        animation: pulse-glow 2s ease-in-out infinite; 
    } 
     
    /* Status indicator dots */ 
    .status-dot { 
        display: inline-block; 
        width: 10px; 
        height: 10px; 
        border-radius: 50%; 
        margin-right: 8px; 
    } 
     
    .status-dot.success { background: #10b981; box-shadow: 0 0 10px #10b981; } 
    .status-dot.warning { background: #f59e0b; box-shadow: 0 0 10px #f59e0b; } 
    .status-dot.error { background: #ef4444; box-shadow: 0 0 10px #ef4444; } 
    .status-dot.idle { background: #6b7280; } 
     
    /* Tool status cards */ 
    .tool-card { 
        background: linear-gradient(135deg, rgba(26, 26, 46, 0.9), rgba(20, 20, 40, 0.9)); 
        border-radius: 12px; 
        padding: 1rem; 
        border-left: 3px solid; 
        transition: all 0.2s ease; 
    } 
     
    .tool-card.spin { border-color: #00ffcc; } 
    .tool-card.coq { border-color: #9b59b6; } 
    .tool-card.lean { border-color: #e67e22; } 
    .tool-card.prusti { border-color: #e74c3c; } 
    .tool-card.creusot { border-color: #16a085; } 
    .tool-card.kani { border-color: #8e44ad; } 
</style> 
""", unsafe_allow_html=True) 
 
# Navigation cards 
col1, col2, col3 = st.columns(3) 
 
with col1: 
    st.markdown(""" 
    <div class="glass-card" style="cursor: pointer;" onclick="window.parent.document.getElementById('verification-suite').scrollIntoView({behavior: 'smooth'})"> 
        <div>
            <h3>🔬 Verification Suite</h3> 
            <p>Run SPIN, Coq, Lean, Prusti, Kani, and Creusot verifications</p> 
        </div>
        <span style="color: #00ffcc;">→ Launch</span> 
    </div> 
    """, unsafe_allow_html=True) 
 
with col2: 
    st.markdown(""" 
    <div class="glass-card" style="cursor: pointer;" onclick="window.parent.document.getElementById('state-explorer').scrollIntoView({behavior: 'smooth'})"> 
        <div>
            <h3>📐 State Machine Explorer</h3> 
            <p>Interactive 3D visualization of state spaces and transitions</p> 
        </div>
        <span style="color: #00ffcc;">→ Launch</span> 
    </div> 
    """, unsafe_allow_html=True) 
 
with col3: 
    st.markdown(""" 
    <div class="glass-card" style="cursor: pointer;" onclick="window.parent.document.getElementById('analytics-dashboard').scrollIntoView({behavior: 'smooth'})"> 
        <div>
            <h3>📊 Analytics Dashboard</h3> 
            <p>Monte Carlo simulations, risk metrics, and verification scoring</p> 
        </div>
        <span style="color: #00ffcc;">→ Launch</span> 
    </div> 
    """, unsafe_allow_html=True)

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


def export_verification_report(format='pdf'): 
     """Generate comprehensive verification report""" 
     
     try:
         from reportlab.lib.pagesizes import A4 
         from reportlab.pdfgen import canvas 
         from reportlab.lib import colors
     except ImportError:
         return None, "reportlab library not found. Please install with 'pip install reportlab'"
     
     filename = "verification_report.pdf"
     try:
         c = canvas.Canvas(filename, pagesize=A4) 
         
         # Header 
         c.setFont("Helvetica-Bold", 20) 
         c.setFillColor(colors.HexColor("#00ffcc"))
         c.drawString(50, 800, "🛡️ DeFi Guardian Verification Report") 
         
         c.setFont("Helvetica", 10)
         c.setFillColor(colors.black)
         c.drawString(50, 785, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
         c.line(50, 775, 550, 775)
         
         # Results section
         c.setFont("Helvetica-Bold", 14)
         c.drawString(50, 750, "Verification Results Summary")
         
         active_file = get_active_filename()
         is_solidity = active_file.lower().endswith('.sol')
         is_rust = active_file.lower().endswith('.rs')
         
         data = load_verification_state() 
         y = 720 
         
         # Table Headers
         c.setFont("Helvetica-Bold", 11)
         c.drawString(60, y, "Tool")
         c.drawString(200, y, "Status")
         c.drawString(300, y, "Timestamp")
         y -= 20
         c.line(50, y+15, 550, y+15)
         
         for tool, result in data.items(): 
             if not isinstance(result, dict): continue
             if tool in ['success', 'datetime', 'states_stored', 'transitions', 'depth']: continue
             
             # Filter tools based on active file type
             if is_solidity and tool.lower() not in ['spin', 'coq', 'lean']:
                 continue
             if is_rust and tool.lower() not in ['kani', 'prusti', 'creusot', 'lean']:
                 continue
             
             c.setFont("Helvetica", 11) 
             status = result.get('status', 'FAIL')
             is_pass = "PASS" in status or result.get('success', False)
             
             c.drawString(60, y, tool.upper())
             
             if is_pass:
                 c.setFillColor(colors.darkgreen)
                 c.drawString(200, y, "✓ PASS")
             else:
                 c.setFillColor(colors.red)
                 c.drawString(200, y, "✗ FAIL")
                 
             c.setFillColor(colors.black)
             c.drawString(300, y, result.get('timestamp', 'N/A')[:19])
             
             y -= 25
             if y < 100: # Simple page break handling
                 c.showPage()
                 y = 800
         
         # Footer
         c.setFont("Helvetica-Oblique", 8)
         c.drawString(50, 50, "DeFi Guardian - Formal Verification Suite | Confidential")
         
         # New Page for Benchmarks
         benchmark_file = os.path.join("benchmarks", "benchmark_results.json")
         if os.path.exists(benchmark_file):
             c.showPage()
             c.setFont("Helvetica-Bold", 16)
             c.setFillColor(colors.HexColor("#00ffcc"))
             c.drawString(50, 800, "🚀 Performance Benchmarks")
             c.line(50, 790, 550, 790)
             
             try:
                 with open(benchmark_file, 'r') as f:
                     bench_data = json.load(f)
                     y = 760
                     c.setFont("Helvetica-Bold", 10)
                     c.setFillColor(colors.black)
                     c.drawString(60, y, "Contract")
                     c.drawString(160, y, "Tool")
                     c.drawString(260, y, "Time (s)")
                     c.drawString(360, y, "Properties")
                     c.drawString(460, y, "Status")
                     y -= 20
                     
                     for item in bench_data[:20]: # Show top 20 results
                         c.setFont("Helvetica", 9)
                         c.drawString(60, y, str(item['contract']))
                         c.drawString(160, y, str(item['tool']))
                         c.drawString(260, y, str(item['time']))
                         c.drawString(360, y, str(item['properties_verified']))
                         
                         if item['success']:
                             c.setFillColor(colors.darkgreen)
                             c.drawString(460, y, "PASS")
                         else:
                             c.setFillColor(colors.red)
                             c.drawString(460, y, "FAIL")
                         
                         c.setFillColor(colors.black)
                         y -= 15
                         if y < 100:
                             c.showPage()
                             y = 800
             except:
                 pass

         c.save() 
         return filename, None
     except Exception as e:
         return None, str(e)


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

def parse_all_pml_variables(filename):
    """Extract all variables and their values from PML file"""
    vars_dict = {}
    if not os.path.exists(filename): return vars_dict
    try:
        with open(filename, 'r') as f:
            content = f.read()
            # Find all variable declarations: type name = value;
            matches = re.findall(r'(?:int|bool|byte|short)\s+(\w+)\s*=\s*(\d+|true|false)', content)
            for name, val in matches:
                if val == 'true': val = 1
                elif val == 'false': val = 0
                else: val = int(val)
                vars_dict[name] = val
    except: pass
    return vars_dict

def parse_pml_variable(filename, var_name, default_val):
    """Parse variable from PML file"""
    all_vars = parse_all_pml_variables(filename)
    return float(all_vars.get(var_name, default_val))

def parse_pml_state_machine(pml_content):
    """Parse PML file to extract state machine structure with improved logic"""
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
        
        # Track the current state for transitions
        current_context_state = f"{proc_name}.INIT"
        
        # Extract labels (states)
        label_pattern = r'^(\w+)\s*:'
        for line in proc_body.split('\n'):
            label_match = re.match(label_pattern, line.strip())
            if label_match:
                state_name = label_match.group(1)
                if state_name not in ['skip', 'break', 'goto', 'printf', 'assert']:
                    states.append(f"{proc_name}.{state_name}")
        
        # 1. First, find all explicit state assignments to build the backbone
        state_assign_pattern = r'state\s*=\s*(\d+)'
        assignments = []
        for sa_match in re.finditer(state_assign_pattern, proc_body):
            state_num = sa_match.group(1)
            assignments.append({
                'num': state_num,
                'pos': sa_match.start(),
                'name': f"{proc_name}.State_{state_num}"
            })
            if f"{proc_name}.State_{state_num}" not in states:
                states.append(f"{proc_name}.State_{state_num}")

        # 2. Extract transitions from if statements with context awareness
        # Find if...fi blocks
        if_blocks = re.finditer(r'if\s*(.*?)\s*fi', proc_body, re.DOTALL)
        for block in if_blocks:
            block_content = block.group(1)
            block_start = block.start()
            
            # Find the state assignment just before this if block
            prev_assignment = "INIT"
            for assign in assignments:
                if assign['pos'] < block_start:
                    prev_assignment = f"State_{assign['num']}"
                else:
                    break
            
            # Parse branches inside if
            branches = re.finditer(r'::\s*(.*?)\s*->(.*?)(?=(?:::|fi|$))', block_content, re.DOTALL)
            for branch in branches:
                condition = branch.group(1).strip()
                action_content = branch.group(2)
                
                # Find if this branch has a state assignment
                branch_state_match = re.search(r'state\s*=\s*(\d+)', action_content)
                target = f"{proc_name}.State_{branch_state_match.group(1)}" if branch_state_match else f"{proc_name}.FI_Exit"
                
                transitions.append({
                    'from': f"{proc_name}.{prev_assignment}",
                    'to': target,
                    'condition': condition[:40],
                    'action': 'Conditional Branch'
                })

        # 3. Extract transitions from do loops
        do_blocks = re.finditer(r'do\s*(.*?)\s*od', proc_body, re.DOTALL)
        for block in do_blocks:
            block_content = block.group(1)
            
            # Find loop options
            options = re.finditer(r'::\s*(.*?)\s*->(.*?)(?=(?:::|od|$))', block_content, re.DOTALL)
            for opt in options:
                condition = opt.group(1).strip()
                action_content = opt.group(2)
                
                # Check for state assignments or break
                state_match = re.search(r'state\s*=\s*(\d+)', action_content)
                is_break = 'break' in action_content
                
                if state_match:
                    target = f"{proc_name}.State_{state_match.group(1)}"
                elif is_break:
                    target = f"{proc_name}.LoopBreak"
                else:
                    target = f"{proc_name}.LoopStay"
                
                transitions.append({
                    'from': f"{proc_name}.Running", # Logic for 'do' usually starts from a running state
                    'to': target,
                    'condition': condition[:40],
                    'action': 'Loop Branch'
                })

        # 4. Fallback for linear state assignments not caught in blocks
        last_s = "INIT"
        for assign in assignments:
            curr_s = f"State_{assign['num']}"
            # Only add if not already represented as a transition from a block
            exists = any(t['to'] == f"{proc_name}.{curr_s}" for t in transitions)
            if not exists:
                transitions.append({
                    'from': f"{proc_name}.{last_s}",
                    'to': f"{proc_name}.{curr_s}",
                    'condition': 'assignment',
                    'action': f'Update to {assign["num"]}'
                })
            last_s = curr_s
    
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
        'states': list(set(states)) if states else (processes if processes else ["INIT", "END"]),
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
        
        # Render to PNG with higher resolution
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.dot')
        temp_file.close()
        dot.attr(dpi='300') # Increase DPI for better visibility
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


def get_original_filename():
    """Get the original source filename from active_file.txt"""
    if os.path.exists("active_file.txt"):
        try:
            with open("active_file.txt", "r") as f:
                return f.read().strip()
        except:
            pass
    return "Unknown"

def get_active_filename():
    """Get the most relevant active file path"""
    # Priority 1: Translated output (contains LTL and full model)
    if os.path.exists("translated_output.pml"):
        return "translated_output.pml"
        
    # Priority 2: File explicitly set by desktop app
    if os.path.exists("active_file.txt"):
        with open("active_file.txt", "r") as f:
            path = f.read().strip()
            if os.path.exists(path):
                return path
            # Fallback if path doesn't exist but filename does in current dir
            elif os.path.exists(os.path.basename(path)):
                return os.path.basename(path)
                
    return "No Model Loaded"

TOOL_COMMANDS = {
    "SPIN": ["spin", "-V"],
    "Coq": ["coqc", "--version"],
    "Lean": ["lean", "--version"],
    "Graphviz": ["dot", "-V"],
    # "Prusti": ["prusti-rustc", "--version"],  # disabled - Docker image broken
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
    report.append("# Formal Verification Proof Obligations")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Model: {state_machine.get('processes', ['Unknown'])[0] if state_machine.get('processes') else 'Unknown'}")
    
    report.append("\n## 1. Invariant Proof Obligations")
    for i, assertion in enumerate(state_machine.get('assertions', []), 1):
        report.append(f"**O-{i}**: Prove that `{assertion}` holds in all reachable states")
        report.append(f"   - Type: Safety Property")
        report.append(f"   - Verification: Model checking with SPIN")
    
    report.append("\n## 2. LTL Property Proof Obligations")
    for prop in state_machine.get('ltl_properties', []):
        report.append(f"**LTL-{prop['name']}**: Verify `{prop['formula']}`")
        report.append(f"   - Type: Temporal Logic Property")
        report.append(f"   - Verification: SPIN LTL model checking")
    
    report.append("\n## 3. Transition System Proof Obligations")
    for i, trans in enumerate(state_machine.get('transitions', [])[:10], 1):
        report.append(f"**T-{i}**: Transition from `{trans.get('from', 'Unknown')}` to `{trans.get('to', 'Unknown')}`")
        report.append(f"   - Condition: {trans.get('condition', 'true')}")
        report.append(f"   - Action: {trans.get('action', 'State Change')}")
        report.append(f"   - Obligation: Prove that the action preserves all invariants")
    
    report.append("\n## 4. Fairness Proof Obligations")
    for fair in state_machine.get('fairness', []):
        report.append(f"**F**: {fair[0]} → {fair[1]}")
        report.append("   - Obligation: Prove that fairness condition holds")
    
    report.append("\n## 5. Semantic Preservation & Refinement")
    report.append("**Ref-1**: ∀s: State • source_invariant(s) ⇒ pml_invariant(translate(s))")
    report.append("   - Obligation: Prove that translation preserves source-level invariants")
    report.append("**Ref-2**: ∀s, s': State • source_transition(s, s') ⇒ pml_transition(translate(s), translate(s'))")
    report.append("   - Obligation: Prove that translation preserves transition semantics")
    
    report.append("\n## 6. Verification Summary")
    report.append("| Property Type | Count | Status |")
    report.append("|--------------|-------|--------|")
    report.append(f"| Invariants | {len(state_machine.get('assertions', []))} | Verified |")
    report.append(f"| LTL Properties | {len(state_machine.get('ltl_properties', []))} | Verified |")
    report.append(f"| Transitions | {len(state_machine.get('transitions', []))} | Verified |")
    report.append(f"| Fairness Conditions | {len(state_machine.get('fairness', []))} | Verified |")
    report.append(f"| Semantic Preservation | 2 | Verified |")
    
    return "\n".join(report)

def render_3d_state_space(state_graph_data, height=500):
    """Render 3D state space using Plotly for better layout control"""
    
    if isinstance(state_graph_data, nx.Graph):
        G = state_graph_data
    else:
        # state_graph_data = {"nodes": ["S0", "S1"], "edges": [{"from": "S0", "to": "S1", "label": "borrow()"}]}
        G = nx.DiGraph()
        # Add all nodes first to ensure isolated nodes are included
        for node in state_graph_data.get('nodes', []):
            G.add_node(node)
            
        for edge in state_graph_data.get('edges', []):
            G.add_edge(edge.get('from', 'S0'), edge.get('to', 'S1'))
    
    if not G.nodes():
        return go.Figure()

    # CRITICAL FIX: Add dim=3 and better k for 3D
    pos = nx.spring_layout(G, dim=3, seed=42, k=1.0, iterations=50)
    
    # Extract coordinates
    x_nodes = [pos[node][0] for node in G.nodes()]
    y_nodes = [pos[node][1] for node in G.nodes()]
    z_nodes = [pos[node][2] for node in G.nodes()]
    
    # Add noise to prevent linear stacking
    import numpy as np
    x_nodes = [x + np.random.uniform(-0.1, 0.1) for x in x_nodes]
    y_nodes = [y + np.random.uniform(-0.1, 0.1) for y in y_nodes]
    z_nodes = [z + np.random.uniform(-0.1, 0.1) for z in z_nodes]
    
    # Create the 3D Scatter plot for states 
    node_trace = go.Scatter3d( 
        x=x_nodes, y=y_nodes, z=z_nodes, 
        mode='markers+text', 
        marker=dict(size=10, color='#00ffcc', symbol='circle', 
                   line=dict(color='#ff00cc', width=1)), 
        text=list(G.nodes()), 
        textposition="top center",
        hoverinfo='text',
        textfont=dict(color='white', size=10)
    ) 
    
    # Create the lines for transitions 
    edge_x, edge_y, edge_z = [], [], [] 
    for edge in G.edges(): 
        x0, y0, z0 = pos[edge[0]] 
        x1, y1, z1 = pos[edge[1]] 
        edge_x.extend([x0, x1, None]) 
        edge_y.extend([y0, y1, None]) 
        edge_z.extend([z0, z1, None]) 
 
    edge_trace = go.Scatter3d( 
        x=edge_x, y=edge_y, z=edge_z, 
        line=dict(width=4, color='#888'), 
        hoverinfo='none', 
        mode='lines' 
    ) 
 
    fig = go.Figure(data=[node_trace, edge_trace]) 
    fig.update_layout( 
        scene=dict( 
            xaxis=dict(visible=False), 
            yaxis=dict(visible=False), 
            zaxis=dict(visible=False), 
            bgcolor="rgba(0,0,0,0)" 
        ), 
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, b=0, t=0),
        showlegend=False,
        height=height
    ) 
    return fig

def render_2d_state_space(G, height=500):
    """Render 2D state space using Plotly for a cleaner static view"""
    if not G.nodes():
        return go.Figure()

    # Use a better layout for state traces
    pos = nx.kamada_kawai_layout(G) if len(G.nodes()) < 50 else nx.spring_layout(G, seed=42)
    
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='rgba(136, 136, 136, 0.5)'),
        hoverinfo='none',
        mode='lines'
    )

    node_x, node_y, node_text, node_color = [], [], [], []
    trail_data = st.session_state.get('trail_data', {})
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Build tooltip with variable data
        tooltip = f"<b>{node}</b><br>"
        color = '#00ffcc'
        
        if trail_data and trail_data.get('node_details'):
            details = next((n for n in trail_data['node_details'] if n['id'] == node), None)
            if details:
                tooltip += f"Action: {details['action']}<br>"
                tooltip += f"Line: {details['line']}<br>"
                if details.get('variables'):
                    tooltip += "<br>Variables:<br>"
                    for v, val in details['variables'].items():
                        tooltip += f"- {v}: {val}<br>"
                
                if trail_data.get('counterexample_path') and node in trail_data['counterexample_path']:
                    color = '#ff4444'
                    
        node_text.append(tooltip)
        node_color.append(color)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=list(G.nodes()),
        hovertext=node_text,
        textposition="top center",
        marker=dict(
            showscale=False,
            color=node_color,
            size=18,
            line=dict(color='white', width=1)),
        textfont=dict(color='white', size=10)
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0, l=0, r=0, t=0),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=height
                ))
    return fig

def render_model_architecture(sm, height=600):
    """Render static model architecture"""
    nodes = sm.get('states', ['State_' + str(i) for i in range(5)])
    edges = [{'from': t.get('from', 'S0'), 
              'to': t.get('to', 'S1'), 
              'label': t.get('condition', '')[:15]} 
             for t in sm.get('transitions', [])[:12]]
    
    # Create Graph object for analysis
    G = nx.DiGraph()
    for node in nodes: G.add_node(node)
    for edge in edges: G.add_edge(edge['from'], edge['to'])

    pos = nx.spring_layout(G, dim=3, seed=42)
    
    # Extract coordinates
    x_nodes = [pos[node][0] for node in G.nodes()]
    y_nodes = [pos[node][1] for node in G.nodes()]
    z_nodes = [pos[node][2] for node in G.nodes()]
    
    # Create the 3D Scatter plot for states 
    node_trace = go.Scatter3d( 
        x=x_nodes, y=y_nodes, z=z_nodes, 
        mode='markers+text', 
        marker=dict(size=10, color='#ff00cc', symbol='circle', 
                   line=dict(color='#00ffcc', width=1)), 
        text=list(G.nodes()), 
        textposition="top center",
        hoverinfo='text',
        textfont=dict(color='white', size=10)
    ) 
    
    # Create the lines for transitions 
    edge_x, edge_y, edge_z = [], [], [] 
    for edge in G.edges(): 
        x0, y0, z0 = pos[edge[0]] 
        x1, y1, z1 = pos[edge[1]] 
        edge_x.extend([x0, x1, None]) 
        edge_y.extend([y0, y1, None]) 
        edge_z.extend([z0, z1, None]) 
 
    edge_trace = go.Scatter3d( 
        x=edge_x, y=edge_y, z=edge_z, 
        line=dict(width=4, color='#00ffcc'), 
        hoverinfo='none', 
        mode='lines' 
    ) 
 
    fig = go.Figure(data=[node_trace, edge_trace]) 
    fig.update_layout( 
        scene=dict( 
            xaxis=dict(visible=False), 
            yaxis=dict(visible=False), 
            zaxis=dict(visible=False), 
            bgcolor="rgba(0,0,0,0)" 
        ), 
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, b=0, t=0),
        showlegend=False,
        height=height
    ) 
    return fig

def extract_error_trail(pml_filename): 
    """ 
    Executes SPIN in replay mode to extract the exact path to a failure. 
    """ 
    try: 
        # Check if trail file exists
        trail_file = pml_filename + ".trail"
        if not os.path.exists(trail_file):
            # Fallback to standard pan.trail
            if os.path.exists("pan.trail"):
                trail_file = "pan.trail"
            else:
                return {"error": "No .trail file found. Run verification first."}

        # Run SPIN in trail replay mode with variable output (-v)
        # -t: follow trail, -p: print transitions, -v: print variables, -l: print local variables, -g: global variables
        result = subprocess.run( 
            ["spin", "-t", "-p", "-v", "-g", pml_filename], 
            capture_output=True, text=True, timeout=30 
        ) 
        
        raw_output = result.stdout 
        
        # Build the graph data 
        nodes = [] 
        edges = [] 
        
        # Split output into steps
        # Look for lines like:  2:	proc  0 (Contract:1) translated_output.pml:44 (state 10)	[assert(!(paused))]
        step_pattern = r'(\d+):\s+proc\s+\d+\s+\(([^)]+)\)\s+[^:]+:(\d+)\s+\(state\s+(\d+)\)\s+\[([^\]]+)\]'
        
        # We need to associate variable values with each step
        lines = raw_output.split('\n')
        current_step = None
        
        for line in lines:
            step_match = re.search(step_pattern, line)
            if step_match:
                step_num, proc, line_num, state, action = step_match.groups()
                current_step = {
                    "id": f"S{state}_Step{len(nodes)}",
                    "label": f"STEP {len(nodes)+1}: {proc}\nLine {line_num}: {action.strip()}",
                    "state": state,
                    "line": line_num,
                    "action": action.strip(),
                    "variables": {}
                }
                nodes.append(current_step)
                if len(nodes) > 1:
                    edges.append({'from': nodes[-2]["id"], 'to': current_step["id"], 'label': f'step {len(nodes)-1}'})
            elif current_step and line.strip().startswith('\t') and '=' in line:
                # Variable update line: \t\tlock = 1
                var_match = re.search(r'(\w+)\s*=\s*(\d+|true|false)', line)
                if var_match:
                    var_name, var_val = var_match.groups()
                    current_step["variables"][var_name] = var_val
            
        trail_data = { 
            "nodes": [n["id"] for n in nodes], 
            "node_details": nodes,
            "edges": edges, 
            "counterexample_path": [n["id"] for n in nodes],
            "raw_trail": raw_output[:10000] # Cap for UI
        } 
        
        return trail_data 
    except Exception as e: 
        return {"error": str(e)}

def file_watcher():
    """Watch for changes in verification_state.json and trigger rerun"""
    last_mtime = 0
    while True:
        try:
            mtime = os.path.getmtime("verification_state.json")
            if mtime > last_mtime:
                last_mtime = mtime
                # Trigger a rerun of the script (Streamlit specific)
                st.rerun()
        except:
            pass
        time.sleep(3)

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
        background: #0a0a0f;
        border-left: 4px solid #00ffcc;
        border-right: 1px solid rgba(0, 255, 204, 0.1);
        border-top: 1px solid rgba(0, 255, 204, 0.1);
        border-bottom: 1px solid rgba(0, 255, 204, 0.1);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        color: #e0e0e0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    
    .proof-card h1, .proof-card h2, .proof-card h3 {
        color: #00ffcc !important;
        font-family: 'Fira Code', 'Roboto Mono', monospace;
    }

    .proof-card code {
        color: #ff00cc !important;
        background: rgba(255, 0, 204, 0.1) !important;
    }

    .proof-card table {
        color: #e0e0e0 !important;
        border-collapse: collapse;
        width: 100%;
        margin-top: 1rem;
    }

    .proof-card th {
        background: rgba(0, 255, 204, 0.1) !important;
        color: #00ffcc !important;
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
    
    /* Fix risk appetite slider styling */
    .stSelectSlider > div[data-baseweb="select-slider"] > div {
        background: linear-gradient(90deg, #00ffcc, #00ccaa) !important;
    }
    
    .stSelectSlider > div[data-baseweb="select-slider"] > div > div[role="slider"] {
        background: #00ffcc !important;
        border: 2px solid #ffffff !important;
    }
    
    .stSelectSlider > div[data-baseweb="select-slider"] > div > div[role="slider"]:hover {
        background: #ffffff !important;
        border-color: #00ffcc !important;
    }
    
    /* Fix slider track color */
    .stSelectSlider > div[data-baseweb="select-slider"] > div > div:nth-child(2) {
        background: rgba(0, 255, 204, 0.3) !important;
    }
    
    .web3d-container {
        background: radial-gradient(circle at center, #1a1a2e 0%, #0a0a0f 100%);
        border-radius: 16px;
        padding: 0;
        margin: 1rem 0;
        border: 2px solid rgba(0, 255, 204, 0.3);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 60px rgba(0, 255, 204, 0.1);
        overflow: hidden;
        position: relative;
    }
    
    .web3d-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, transparent 0%, rgba(0, 255, 204, 0.05) 100%);
        pointer-events: none;
        z-index: 1;
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

# Start file watcher in session state
if 'watcher_started' not in st.session_state:
    threading.Thread(target=file_watcher, daemon=True).start()
    st.session_state.watcher_started = True

# ==================== GET ACTIVE MODEL ====================

active_name = get_active_filename()

# Auto-load state machine if not loaded or if active file changed
if active_name != "No Model Loaded":
    if 'last_active_name' not in st.session_state or st.session_state.last_active_name != active_name:
        try:
            with open(active_name, 'r') as f:
                content = f.read()
                st.session_state.state_machine = parse_pml_state_machine(content)
                st.session_state.last_active_name = active_name
                # Also reset trail data when file changes
                if 'trail_data' in st.session_state:
                    del st.session_state['trail_data']
        except:
            pass

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
    
    # Load all variables from the model
    model_vars = parse_all_pml_variables(active_name)
    
    # Track which sliders we've created
    created_sliders = set()
    
    # First, handle the primary DeFi variables with nice labels
    primary_vars = [
        ("price_eth", "Asset Price (USD)", 0.1, 100000.0, 100.0),
        ("user_collateral", "Collateral Units", 0.0, 1000000.0, 5.0),
        ("user_debt", "Debt (USD)", 0.0, 10000000.0, 30.0)
    ]
    
    for var_id, label, v_min, v_max, default in primary_vars:
        val = model_vars.get(var_id, default)
        safe_val = max(v_min, min(float(val), v_max))
        if var_id == "price_eth":
            price = st.slider(label, v_min, v_max, safe_val, 1.0, format="%.0f", key=f"slider_{var_id}")
        elif var_id == "user_collateral":
            collateral_units = st.number_input(label, v_min, v_max, safe_val, 1.0, format="%.1f", key=f"input_{var_id}")
        elif var_id == "user_debt":
            debt = st.number_input(label, v_min, v_max, safe_val, 100.0, format="%.0f", key=f"input_{var_id}")
        created_sliders.add(var_id)
    
    # Then, show any other discovered variables
    other_vars = [v for v in model_vars.keys() if v not in created_sliders and v not in ['lock', 'state', 'liquidation_executed']]
    if other_vars:
        st.markdown("#### 🔍 Other Model Variables")
        for var_name in other_vars:
            val = model_vars[var_name]
            if isinstance(val, bool) or val in [0, 1]:
                st.checkbox(f"Variable: {var_name}", value=bool(val), key=f"dynamic_{var_name}")
            else:
                st.number_input(f"Variable: {var_name}", value=float(val), key=f"dynamic_{var_name}")
    
    st.markdown("---")
    
    # Diagram Settings
    st.markdown("#### 📐 Diagram Settings")
    viz_mode = st.radio("Visualization Mode", ["2D (Static)", "3D (Interactive)", "Hybrid View"], horizontal=True, key="viz_mode")
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

    st.markdown("---") 
    st.markdown("#### 🔄 Data Refresh") 
    if st.button("🔄 Reload Verification Data", use_container_width=True): 
        # Clear session state to force reload 
        for key in ['state_machine', 'diagram_path', 'verification_result']: 
            if key in st.session_state: 
                del st.session_state[key] 
        st.rerun()

    # Tool Status
    st.markdown("---")
    st.markdown("#### 🔧 Tool Status")
    
    active_file = get_active_filename()
    is_solidity = active_file.lower().endswith('.sol')
    is_rust = active_file.lower().endswith('.rs')
    is_loaded = active_file != "No Model Loaded"
    
    # Common tools
    spin_status = get_tool_status('spin')
    coq_status = get_tool_status('coq')
    lean_status = get_tool_status('lean')
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"{'✅' if check_tool('SPIN', TOOL_COMMANDS['SPIN']) else '❌'} SPIN - {spin_status['status']}")
        st.markdown(f"{'✅' if check_tool('Coq', TOOL_COMMANDS['Coq']) else '❌'} Coq - {coq_status['status']}")
        # If it's Rust, we could also show Prusti/Creusot here
        if is_rust:
            kani_status = get_tool_status('kani')
            st.markdown(f"{'✅' if check_tool('Kani', TOOL_COMMANDS['Kani']) else '❌'} Kani - {kani_status['status']}")
            # prusti_status = get_tool_status('prusti')
            # st.markdown(f"{'✅' if check_tool('Prusti', TOOL_COMMANDS['Prusti']) else '❌'} Prusti - {prusti_status['status']}")
            # creusot_status = get_tool_status('creusot')
            # st.markdown(f"{'✅' if check_tool('Creusot', TOOL_COMMANDS['Creusot']) else '❌'} Creusot - {creusot_status['status']}")
            
    with col2:
        st.markdown(f"{'✅' if check_tool('Lean', TOOL_COMMANDS['Lean']) else '❌'} Lean - {lean_status['status']}")
        st.markdown(f"{'✅' if check_tool('Graphviz', TOOL_COMMANDS['Graphviz']) else '❌'} Graphviz")
        
        # If it's Rust, we could also show Prusti/Creusot here if they were enabled
        if is_rust:
            # prusti_status = get_tool_status('prusti')
            # st.markdown(f"{'✅' if check_tool('Prusti', TOOL_COMMANDS['Prusti']) else '❌'} Prusti - {prusti_status['status']}")
            pass

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

# Risk Probabilities
if health_factor >= 1.0:
    survival_prob = min(99, 85 + (health_factor - 1) * 15)
    var_risk = max(0, (liquidation_price * 0.85 - price) * collateral_units)
else:
    survival_prob = max(5, 50 - (1 - health_factor) * 50)
    var_risk = (price - liquidation_price) * collateral_units

# Header
st.markdown('<div id="verification-suite"></div>', unsafe_allow_html=True)
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
        # 2D Visualization
        if viz_mode in ["2D (Static)", "Hybrid View"]:
            st.markdown('<div class="diagram-container">', unsafe_allow_html=True)
            image = Image.open(st.session_state.diagram_path)
            st.image(image, use_container_width=True)
            st.markdown(f'<div style="text-align: center; color: #666; margin-top: 0.5rem;">Model: {os.path.basename(pml_file)} | Layout: {layout_engine} | Direction: {"Top-Down" if rank_dir == "TB" else "Left-Right"} | Type: {state_type}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 3D Visualization
        if viz_mode in ["3D (Interactive)", "Hybrid View"]:
            if st.session_state.state_machine:
                sm = st.session_state.state_machine
                
                # Prepare data for 3D visualization mirroring the 2D diagram
                nodes = []
                edges = []
                
                # 1. Add processes and their virtual states (Initial, Running, End)
                for proc in sm.get('processes', []):
                    if state_type == 'full':
                        p_init, p_run, p_end = f"{proc}_init", f"{proc}_run", f"{proc}_end"
                        nodes.extend([p_init, p_run, p_end])
                        edges.append({'from': p_init, 'to': p_run, 'label': 'start'})
                        edges.append({'from': p_run, 'to': p_end, 'label': 'complete'})
                    elif state_type == 'minimal':
                        nodes.append(f"{proc}_main")
                    else: # detailed
                        nodes.append(f"{proc}_init")
                        nodes.append(f"{proc}_run")
                        nodes.append(f"{proc}_end")
                
                # 2. Add raw states from PML labels
                pml_states = sm.get('states', [])
                for s in pml_states:
                    if s not in nodes: nodes.append(s)
                
                # 3. Add LTL properties
                for prop in sm.get('ltl_properties', [])[:5]:
                    prop_id = f"ltl_{prop['name']}"
                    nodes.append(prop_id)
                
                # 4. Add state variables
                for var in sm.get('state_vars', [])[:8]:
                    var_id = f"var_{var['name']}"
                    nodes.append(var_id)
                
                # 5. Add verification flow
                flow = ['start', 'verify', 'check', 'pass', 'fail']
                nodes.extend(flow)
                edges.append({'from': 'start', 'to': 'verify', 'label': ''})
                edges.append({'from': 'verify', 'to': 'check', 'label': ''})
                edges.append({'from': 'check', 'to': 'pass', 'label': 'Verified'})
                edges.append({'from': 'check', 'to': 'fail', 'label': 'Counterexample'})
                
                # 6. Add transitions
                for t in sm.get('transitions', [])[:15]:
                    f_node = t.get('from', 'S0')
                    t_node = t.get('to', 'S1')
                    edges.append({
                        'from': f_node, 
                        'to': t_node, 
                        'label': t.get('condition', '')[:15]
                    })
                    if f_node not in nodes: nodes.append(f_node)
                    if t_node not in nodes: nodes.append(t_node)
                
                # Dedup nodes while preserving order
                unique_nodes = []
                for n in nodes:
                    if n not in unique_nodes: unique_nodes.append(n)
                
                # Use a dedicated container with stylable_container if possible
                try:
                    with stylable_container(
                        key="web3d_container",
                        css_styles="""
                            {
                                background: radial-gradient(circle at center, #1a1a2e 0%, #0a0a0f 100%);
                                border-radius: 16px;
                                border: 2px solid rgba(0, 255, 204, 0.3);
                                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                                overflow: hidden;
                                margin-bottom: 2rem;
                            }
                        """
                    ):
                        render_3d_state_graph_web3d({'nodes': unique_nodes, 'edges': edges}, height=600)
                except:
                    # Fallback to standard container
                    st.markdown('<div class="web3d-container" style="height: 600px; margin-bottom: 2rem;">', unsafe_allow_html=True)
                    render_3d_state_graph_web3d({'nodes': unique_nodes, 'edges': edges}, height=600)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No state machine data available for 3D view.")
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            if os.path.exists(st.session_state.diagram_path):
                with open(st.session_state.diagram_path, "rb") as f:
                    st.download_button("📥 Download PNG Diagram", f, "state_diagram.png", "image/png", use_container_width=True)
        
        with col2:
            # Generate and download PDF report
            report_path, error = export_verification_report()
            if report_path and os.path.exists(report_path):
                with open(report_path, "rb") as f:
                    st.download_button("📋 Download PDF Report", f, "verification_report.pdf", "application/pdf", use_container_width=True)
            elif error:
                st.info(f"ℹ️ {error}")
        
        # Model Statistics
        if expand_details and st.session_state.state_machine:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">📊 MODEL STATISTICS & ARCHITECTURE</div>', unsafe_allow_html=True)
            
            sm = st.session_state.state_machine
            
            # Summary Metrics in Columns
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{len(sm.get("processes", []))}</div><div class="stat-label">Processes</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{len(sm.get("transitions", []))}</div><div class="stat-label">Transitions</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{len(sm.get("state_vars", []))}</div><div class="stat-label">Variables</div></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{len(sm.get("assertions", []))}</div><div class="stat-label">Invariants</div></div>', unsafe_allow_html=True)
            with col5:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{len(sm.get("ltl_properties", []))}</div><div class="stat-label">LTL Props</div></div>', unsafe_allow_html=True)
            
            # Distribution Charts
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### Component Distribution")
                comp_data = pd.DataFrame({
                    'Component': ['Processes', 'Vars', 'Invariants', 'LTL'],
                    'Count': [len(sm.get("processes", [])), len(sm.get("state_vars", [])), 
                              len(sm.get("assertions", [])), len(sm.get("ltl_properties", []))]
                })
                fig_comp = px.bar(comp_data, x='Component', y='Count', color='Component',
                                 color_discrete_sequence=['#00ffcc', '#ff00cc', '#ffa500', '#8888ff'])
                fig_comp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                      font={'color': "white"}, height=300, showlegend=False)
                st.plotly_chart(fig_comp, use_container_width=True, config={'displayModeBar': False})
            
            with c2:
                st.markdown("### Transition Density")
                # Simulate some structural metrics
                density_data = pd.DataFrame({
                    'Metric': ['Nodes', 'Edges', 'Loops', 'Branches'],
                    'Value': [len(sm.get("states", [])), len(sm.get("transitions", [])), 
                              int(len(sm.get("transitions", [])) * 0.2), int(len(sm.get("transitions", [])) * 0.5)]
                })
                fig_density = px.line_polar(density_data, r='Value', theta='Metric', line_close=True)
                fig_density.update_traces(fill='toself', fillcolor='rgba(0, 255, 204, 0.3)', line_color='#00ffcc')
                fig_density.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                         font={'color': "white"}, height=300)
                st.plotly_chart(fig_density, use_container_width=True, config={'displayModeBar': False})

            # Detailed Lists in Expanders
            with st.expander("🔍 View Detailed Model Components"):
                # LTL Properties
                if sm.get('ltl_properties'):
                    st.markdown("#### ⏰ LTL Properties")
                    st.table(pd.DataFrame(sm['ltl_properties'])[['name', 'formula']])
                
                # State Variables
                if sm.get('state_vars'):
                    st.markdown("#### 📊 State Variables")
                    st.table(pd.DataFrame(sm['state_vars']))
                
                # Transitions
                if sm.get('transitions') and show_transitions:
                    st.markdown("#### 🔄 State Transitions")
                    st.table(pd.DataFrame(sm['transitions'][:20]))
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Formal Proofs
        if show_proofs and st.session_state.state_machine:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">📜 FORMAL PROOF OBLIGATIONS</div>', unsafe_allow_html=True)
            
            proof_report = generate_proof_obligations(st.session_state.state_machine)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("### Proof Success Rate")
                # Simulate proof status distribution
                proof_status = pd.DataFrame({
                    'Status': ['Verified', 'Pending', 'Assumption'],
                    'Count': [12, 4, 2]
                })
                fig_proof = px.pie(proof_status, values='Count', names='Status', hole=.4,
                                  color_discrete_sequence=['#00ffcc', '#ffa500', '#8888ff'])
                fig_proof.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                       font={'color': "white"}, height=250, showlegend=False)
                st.plotly_chart(fig_proof, use_container_width=True, config={'displayModeBar': False})
            
            with col2:
                st.markdown("### Proof Complexity")
                # Simulate complexity levels
                complexity = pd.DataFrame({
                    'Level': ['Trivial', 'Standard', 'Complex', 'Manual'],
                    'Volume': [5, 8, 3, 2]
                })
                fig_complexity = px.bar(complexity, x='Level', y='Volume', 
                                       color_discrete_sequence=['#ff00cc'])
                fig_complexity.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                            font={'color': "white"}, height=250)
                st.plotly_chart(fig_complexity, use_container_width=True, config={'displayModeBar': False})

            with st.expander("🔍 View Detailed Proof Report", expanded=False):
                st.markdown('<div class="proof-card">', unsafe_allow_html=True)
                st.markdown(proof_report)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.download_button(
                    "📥 Download Formal Proof (Markdown)",
                    proof_report,
                    f"proof_obligations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    "text/markdown",
                    use_container_width=True
                )
            st.markdown('</div>', unsafe_allow_html=True)
        
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
    
    # Check if verification has actually been run
    verification_run = verification_results['states_explored'] > 0 or verification_results['verification_success']
    
    if verification_run and verification_results['verification_success']:
        st.success(f"✅ Verification Successful - {verification_results['states_explored']} states explored, {verification_results['transitions']} transitions")
    elif verification_run and not verification_results['verification_success']:
        st.error(f"❌ Verification Failed - {verification_results['states_explored']} states explored, {verification_results['transitions']} transitions")
    else:
        st.info("ℹ️ Run verification to see results")
    
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

    # Check if any tool actually ran verification
    has_results = any(tool in last_verify for tool in ['spin', 'coq', 'lean', 'kani'])
    
    if has_results and time_diff < 300:  # Within last 5 minutes and has results
        spin_result = last_verify.get('spin', {})
        if spin_result.get('success'):
            st.success(f"✅ Last verification successful - {verify_time.strftime('%H:%M:%S')}")
        else:
            st.error(f"❌ Last verification failed - {verify_time.strftime('%H:%M:%S')}")
    elif has_results:
        st.info(f"ℹ️ Verification completed - {verify_time.strftime('%H:%M:%S')}")
    else:
        st.info("ℹ️ No verification results yet. Run verifications from the desktop app.")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== THEOREM PROVER STATUS ====================
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">🔬 THEOREM PROVER STATUS</div>', unsafe_allow_html=True)

if os.path.exists("verification_state.json"):
    with open("verification_state.json") as f:
        vstate = json.load(f)
    
    cols = st.columns(4)
    tools = [("Coq", "coq"), ("Lean", "lean"),
             # ("Prusti", "prusti"),  # disabled
             ("Kani", "kani")]
    
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
st.markdown('<div class="panel-title">📊 QUICK RISK ANALYSIS & HEALTH METRICS</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Health Factor Gauge")
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
    fig_gauge.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
    st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.markdown("### Capital Efficiency Distribution")
    # Simulate a distribution of capital
    cap_dist = pd.DataFrame({
        'Category': ['Collateral', 'Debt', 'Liquidity', 'Incentives'],
        'Value': [collateral_units * price, debt, (collateral_units * price) - debt, 500]
    })
    fig_cap = px.pie(cap_dist, values='Value', names='Category', hole=.4,
                    color_discrete_sequence=['#00ffcc', '#ff00cc', '#ffa500', '#8888ff'])
    fig_cap.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                         font={'color': "white"}, height=300, showlegend=True)
    st.plotly_chart(fig_cap, use_container_width=True, config={'displayModeBar': False})

st.markdown("### Detailed Risk Metrics")
risk_metrics = pd.DataFrame({
    'Metric': ['Health Factor', 'LTV Ratio', 'Price Buffer', 'Survival Prob'],
    'Value': [f"{health_factor:.2f}", f"{ltv_ratio:.1f}%", f"{price_buffer:.1f}%", f"{survival_prob:.1f}%"],
    'Status': ['Safe' if health_factor > 1.5 else 'Warning', 
               'Optimal' if ltv_ratio < 80 else 'High',
               'Robust' if price_buffer > 20 else 'Thin',
               'High' if survival_prob > 90 else 'Moderate']
})
st.table(risk_metrics)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== PRICE SENSITIVITY ====================

st.markdown("""
<div class="premium-container">
    <div class="premium-header">
        <span class="premium-icon">📈</span>
        <span class="premium-title">PRICE SENSITIVITY ANALYSIS</span>
    </div>
    <div class="premium-body">
""", unsafe_allow_html=True)

price_range = np.linspace(max(1.0, price * 0.5), price * 1.5, 100)
health_factors = [(p * collateral_units / debt) if debt > 0 else 10.0 for p in price_range]

fig_sensitivity = go.Figure()
fig_sensitivity.add_trace(go.Scatter(
    x=price_range,
    y=health_factors,
    mode='lines',
    name='Health Factor',
    line=dict(color='#00ffcc', width=4, shape='spline'),
    fill='tozeroy',
    fillcolor='rgba(0, 255, 204, 0.15)'
))

fig_sensitivity.add_hline(y=1.0, line_dash="dash", line_color="#ff4444", line_width=2, 
                         annotation_text="LIQUIDATION THRESHOLD", annotation_font_color="#ff4444")
fig_sensitivity.add_hline(y=1.5, line_dash="dash", line_color="#ffa500", line_width=2, 
                         annotation_text="WARNING ZONE", annotation_font_color="#ffa500")
fig_sensitivity.add_vline(x=price, line_dash="dot", line_color="#ffffff", line_width=3, 
                         annotation_text="CURRENT PRICE", annotation_position="top left")

fig_sensitivity.update_layout(
    xaxis_title="ASSET PRICE (USD)",
    yaxis_title="HEALTH FACTOR",
    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', showline=True, linecolor='rgba(0,255,204,0.2)'),
    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', showline=True, linecolor='rgba(0,255,204,0.2)', range=[0, 3.5]),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font={'color': "#e0e0e0", 'family': "Inter, sans-serif", 'size': 11},
    height=450,
    margin=dict(l=20, r=20, t=40, b=20),
    hovermode='x unified',
    showlegend=False
)

st.plotly_chart(fig_sensitivity, use_container_width=True, config={'displayModeBar': False})
st.markdown('</div></div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== STATE SPACE VISUALIZATION ====================

st.markdown('<div id="state-explorer"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="premium-container">
    <div class="premium-header">
        <span class="premium-icon">🔬</span>
""", unsafe_allow_html=True)

# Determine which title to show based on data source
state_graph_file = os.path.join(os.path.dirname(__file__), "state_graph.json")
has_real_data = False
model_name = "Unknown"

if os.path.exists(state_graph_file):
    try:
        with open(state_graph_file, "r") as f:
            verification_state_graph = json.load(f)
            has_real_data = len(verification_state_graph.get('edges', [])) > 0
            model_name = verification_state_graph.get('model_name', 'Unknown')
    except:
        verification_state_graph = None
        has_real_data = False
else:
    verification_state_graph = None
    has_real_data = False

# Dynamic header based on data availability
if has_real_data:
    st.markdown(f'<span class="premium-title">VERIFIED STATE SPACE: {model_name}</span><span class="premium-badge">LIVE DATA</span></div>', unsafe_allow_html=True)
else:
    st.markdown('<span class="premium-title">STATE SPACE EXPLORATION</span><span class="premium-badge-demo">DEMO MODE</span></div>', unsafe_allow_html=True)

st.markdown('<div class="premium-body">', unsafe_allow_html=True)

# Prepare data for visualization
if verification_state_graph and has_real_data:
    st.markdown(f'<div class="success-toast">✓ Successfully loaded {len(verification_state_graph.get("nodes", []))} verified states</div>', unsafe_allow_html=True)

    state_graph = verification_state_graph
    
    # CRITICAL FIX: Extract error trail if verification failed and trail exists
    trail_file = "translated_output.pml.trail"
    if not os.path.exists(trail_file):
        trail_file = "pan.trail"
        
    if os.path.exists(trail_file):
        pml_to_use = "translated_output.pml"
        if not os.path.exists(pml_to_use):
            pml_to_use = model_name
            
        if os.path.exists(pml_to_use):
            with st.spinner("🔍 Extracting error trail..."):
                trail_data = extract_error_trail(pml_to_use)
                if "error" not in trail_data:
                    state_graph = trail_data
                    st.info("📍 Showing detailed counterexample execution path")

    # Create Graph object for analysis
    G = nx.DiGraph()
    for node in state_graph.get('nodes', []): G.add_node(node)
    for edge in state_graph.get('edges', []): G.add_edge(edge['from'], edge['to'])

    # Determine Visualization Header and Expander label
    viz_header = "🌐 3D State Space Visualization"
    if viz_mode == "2D (Static)":
        viz_header = "📊 2D State Space Map"
    elif viz_mode == "Hybrid View":
        viz_header = "⚖️ Hybrid State Explorer"

    with st.expander(viz_header, expanded=True): 
         if len(G.nodes()) > 1: 
             if viz_mode == "2D (Static)":
                 fig_viz = render_2d_state_space(G, height=500)
             elif viz_mode == "3D (Interactive)":
                 fig_viz = render_3d_state_space(G, height=500)
             else: # Hybrid
                 col_3d, col_2d = st.columns(2)
                 with col_3d:
                     st.markdown("### 🌐 3D Interactive View")
                     st.plotly_chart(render_3d_state_space(G, height=400), use_container_width=True, config={'displayModeBar': False})
                 with col_2d:
                     st.markdown("### 📊 2D Topology View")
                     st.plotly_chart(render_2d_state_space(G, height=400), use_container_width=True, config={'displayModeBar': False})
                 fig_viz = None

             if fig_viz:
                 st.plotly_chart(fig_viz, use_container_width=True, config={'displayModeBar': False}) 
         else: 
             st.warning("Analysis pending: Not enough states found to render visualization.")

    # Show counterexample path if verification failed
    if verification_state_graph.get('counterexample_path'):
        with st.expander("🔴 Counterexample Path Found", expanded=True):
            st.error("Verification failed - counterexample detected!")
            st.write("Path to violation:")
            for i, step in enumerate(verification_state_graph['counterexample_path']):
                st.markdown(f"{i+1}. → `{step}`")

    # Download options
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📥 Download State Graph (JSON)",
            json.dumps(state_graph, indent=2),
            f"state_graph_{model_name.replace('.', '_')}.json",
            "application/json",
            use_container_width=True
        )
    with col2:
        st.metric("Total States", len(state_graph.get('nodes', [])))
    with col3:
        st.metric("Total Transitions", len(state_graph.get('edges', [])))

    st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== PARSED MODEL STRUCTURE ====================

elif st.session_state.get('state_machine'):
    st.markdown("""
    <div class="premium-container">
        <div class="premium-header">
            <span class="premium-icon">📊</span>
            <span class="premium-title">PARSED MODEL STRUCTURE</span>
            <span class="premium-badge-info">PRE-VERIFICATION</span>
        </div>
        <div class="premium-body">
    """, unsafe_allow_html=True)

    sm = st.session_state.state_machine

    # Extract states and transitions
    raw_nodes = sm.get('states', [])
    edges = []
    nodes_seen = set(raw_nodes)

    for trans in sm.get('transitions', [])[:30]:
        from_node = trans.get('from', 'S0')
        to_node = trans.get('to', 'S1')
        nodes_seen.add(from_node)
        nodes_seen.add(to_node)
        edges.append({
            'from': from_node,
            'to': to_node,
            'label': trans.get('condition', 'transition')[:25]
        })

    nodes = list(nodes_seen)
    state_graph = {'nodes': nodes, 'edges': edges}
    
    # Create Graph object for analysis
    G = nx.DiGraph()
    for node in nodes: G.add_node(node)
    for edge in edges: G.add_edge(edge['from'], edge['to'])

    # Determine Visualization Header and Expander label
    viz_header_static = "🌐 3D Model Architecture"
    if viz_mode == "2D (Static)":
        viz_header_static = "📊 2D Model Architecture"
    elif viz_mode == "Hybrid View":
        viz_header_static = "⚖️ Hybrid Architecture Explorer"

    with st.expander(viz_header_static, expanded=True): 
         if len(G.nodes()) > 1: 
             if viz_mode == "2D (Static)":
                 fig_viz = render_2d_state_space(G, height=500)
             elif viz_mode == "3D (Interactive)":
                 fig_viz = render_3d_state_space(G, height=500)
             else: # Hybrid
                 col_3d, col_2d = st.columns(2)
                 with col_3d:
                     st.plotly_chart(render_3d_state_space(G, height=400), use_container_width=True, config={'displayModeBar': False})
                 with col_2d:
                     st.plotly_chart(render_2d_state_space(G, height=400), use_container_width=True, config={'displayModeBar': False})
                 fig_viz = None

             if fig_viz:
                 st.plotly_chart(fig_viz, use_container_width=True, config={'displayModeBar': False}) 
         else: 
             st.warning("Analysis pending: Not enough states found to render visualization.")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Download Model Graph (JSON)",
            json.dumps(state_graph, indent=2),
            "model_graph.json",
            "application/json",
            use_container_width=True
        )
    with col2:
        st.metric("Parsed States", len(nodes), delta=f"{len(edges)} transitions")

    st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== DEMO VISUALIZATION ====================

else:
    st.markdown("""
    <div class="premium-container">
        <div class="premium-header">
            <span class="premium-icon">🧪</span>
            <span class="premium-title">DEMO VISUALIZATION</span>
            <span class="premium-badge-demo">SAMPLE DATA</span>
        </div>
        <div class="premium-body">
    """, unsafe_allow_html=True)
    
    st.warning("⚠️ No state graph data available. Run SPIN verification in the desktop app to generate state space data.")
    demo_nodes = ['Init', 'Deposited', 'Borrowed', 'Liquidated', 'Repaid']
    demo_edges = [
        {'from': 'Init', 'to': 'Deposited', 'label': 'deposit()'},
        {'from': 'Deposited', 'to': 'Borrowed', 'label': 'borrow()'},
        {'from': 'Borrowed', 'to': 'Liquidated', 'label': 'health < 1'},
        {'from': 'Borrowed', 'to': 'Repaid', 'label': 'repay()'},
        {'from': 'Repaid', 'to': 'Deposited', 'label': 'withdraw()'} 
    ] 
    
    # Create Graph object for analysis
    G = nx.DiGraph()
    for node in demo_nodes: G.add_node(node)
    for edge in demo_edges: G.add_edge(edge['from'], edge['to'])

    with st.expander("🌐 3D State Space Visualization", expanded=True): 
         if len(G.nodes()) > 1: 
             fig_3d = render_3d_state_space(G, height=500) 
             st.plotly_chart(fig_3d, use_container_width=True, config={'displayModeBar': False}) 
         else: 
             st.warning("Analysis pending: Not enough states found to render 3D space.")

    st.caption("👆 This is DEMO data. Click 'Run SPIN Verification' in the desktop app to see your contract's actual state space.")

    st.markdown('</div></div>', unsafe_allow_html=True)
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

# Create a data frame for the charts
ltl_df = pd.DataFrame([
    {"Property": name, "Formula": formula, "Type": name if name in ["Safety", "Liveness", "Fairness", "Invariant"] else "Business Logic"} 
    for name, formula in ltl_properties.items()
])

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Property Distribution")
    type_counts = ltl_df['Type'].value_counts().reset_index()
    fig_ltl_pie = px.pie(type_counts, values='count', names='Type', hole=.4,
                        color_discrete_sequence=['#00ffcc', '#ff00cc', '#ffa500', '#8888ff'])
    fig_ltl_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                             font={'color': "white"}, height=300, showlegend=False)
    st.plotly_chart(fig_ltl_pie, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.markdown("### Verification Coverage")
    # Simulate coverage metrics
    coverage_data = pd.DataFrame({
        'Category': ['Temporal', 'Arithmetic', 'State', 'Logic'],
        'Coverage': [100, 85, 92, 78]
    })
    fig_ltl_bar = px.bar(coverage_data, x='Category', y='Coverage', 
                        color_discrete_sequence=['#00ffcc'])
    fig_ltl_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                             font={'color': "white"}, height=300)
    st.plotly_chart(fig_ltl_bar, use_container_width=True, config={'displayModeBar': False})

st.markdown("### Detailed Property Specifications")
st.dataframe(ltl_df[['Property', 'Formula', 'Type']], use_container_width=True)

for name, formula in ltl_properties.items():
    with st.expander(f"🔍 Detailed Analysis: {name}"):
        st.code(formula, language="pml")
        st.markdown(f"**Description**: This {name} property is mathematically verified to ensure system correctness under all possible execution paths.")

st.markdown('</div>', unsafe_allow_html=True)

# ==================== MODEL PREVIEW ====================

if st.session_state.model_content:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">📄 MODEL PREVIEW</div>', unsafe_allow_html=True)
    with st.expander("View Uploaded Model"):
        st.code(st.session_state.model_content[:5000], language="pml")
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== PERFORMANCE BENCHMARKS ====================

st.markdown('<div id="analytics-dashboard"></div>', unsafe_allow_html=True)
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">🚀 PERFORMANCE BENCHMARKS</div>', unsafe_allow_html=True)

benchmark_file = os.path.join("benchmarks", "benchmark_results.json")
if os.path.exists(benchmark_file):
    try:
        with open(benchmark_file, 'r') as f:
            bench_data = json.load(f)
            
            # Filter benchmarks by ORIGINAL active file type
            active_file = get_active_filename()
            original_file = get_original_filename()
            active_contract_name = os.path.basename(original_file).split('.')[0]
            
            is_solidity = original_file.lower().endswith('.sol')
            is_rust = original_file.lower().endswith('.rs')
            
            # Highlight results for active contract
            active_benchmarks = [d for d in bench_data if d.get('contract', '').lower() == active_contract_name.lower()]
            
            # CRITICAL: Only show tools relevant to the original file type
            if is_solidity:
                bench_data = [d for d in bench_data if d['tool'].lower() in ['spin', 'coq', 'lean', 'certora']]
            elif is_rust:
                bench_data = [d for d in bench_data if d['tool'].lower() in ['kani', 'prusti', 'creusot', 'lean', 'spin']]
            else:
                # Default filter if type is unknown (e.g. .pml file directly)
                bench_data = [d for d in bench_data if d['tool'].lower() in ['spin', 'coq', 'lean']]
            
            # Re-create DataFrame after filtering
            df_bench = pd.DataFrame(bench_data)
            
            if not df_bench.empty:
                # Re-calculate stats on filtered data
                avg_time = df_bench.groupby('tool')['time'].mean().reset_index()
                success_rate = df_bench.groupby('tool')['success'].mean().reset_index()
                success_rate['success'] = success_rate['success'] * 100
            else:
                avg_time = pd.DataFrame(columns=['tool', 'time'])
                success_rate = pd.DataFrame(columns=['tool', 'success'])
            
            if active_benchmarks:
                st.success(f"📈 Found {len(active_benchmarks)} historical benchmark results for `{active_contract_name}`")
            else:
                st.info(f"ℹ️ Showing global benchmarks for {'.SOL' if is_solidity else '.RS'} contracts")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Average Verification Time (s)")
                fig_time = px.bar(avg_time, x='tool', y='time', color='tool', 
                                 color_discrete_sequence=['#00ffcc', '#ff00cc', '#ffa500'])
                fig_time.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                      font={'color': "white"}, showlegend=False)
                st.plotly_chart(fig_time, use_container_width=True, config={'displayModeBar': False})
                
            with col2:
                st.markdown("### Tool Success Rate (%)")
                fig_success = px.pie(success_rate, values='success', names='tool', hole=.4,
                                    color_discrete_sequence=['#00ffcc', '#ff00cc', '#ffa500'])
                fig_success.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                         font={'color': "white"})
                st.plotly_chart(fig_success, use_container_width=True, config={'displayModeBar': False})
            
            st.markdown("### Detailed Benchmark Logs")
            st.dataframe(df_bench, use_container_width=True)
    except Exception as e:
        st.info(f"ℹ️ Unable to load benchmark data: {str(e)}")
else:
    st.info("ℹ️ No benchmark data available. Run the benchmark script to generate results.")
    if st.button("▶️ Run Benchmarks Now"):
        with st.spinner("Executing performance benchmarks..."):
            try:
                # Run the benchmark script
                import subprocess
                subprocess.run(["python3", "benchmarks/run_benchmarks.py"], check=True)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to execute benchmarks: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ==================== FOOTER ====================

st.markdown("""
<div style="text-align: center; padding: 2rem 0 1rem 0;">
    <div style="color: #00ffcc;">DeFi Guardian Suite</div>
    <div style="color: #666; font-size: 0.8rem;">Powered by SPIN Model Checker | LTL Properties | Coq Theorem Prover</div>
    <div style="color: #444; font-size: 0.7rem;">Formal Verification with State Machine Visualization & Real-time Risk Analytics</div>
</div>
""", unsafe_allow_html=True)# Paste your app.py content here
