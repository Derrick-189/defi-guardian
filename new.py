cat > ~/Desktop/DeFi-Guardian.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=DeFi Guardian
Name[en]=DeFi Guardian
GenericName=Formal Verification Suite
Comment=Formal verification platform for DeFi protocols
Comment[en]=Formal verification platform for DeFi protocols
Exec=python3 /home/slade/defi_guardian/defi_guardian_shortcut.py
Icon=/home/slade/defi_guardian/defi_guardian.png
Terminal=false
StartupNotify=true
Categories=Development;Security;Utility;
Keywords=formal verification;SPIN;LTL;security;audit;defi;
StartupWMClass=defi-guardian
Actions=Desktop;Dashboard;Both;

[Desktop Action Desktop]
Name=Launch Desktop App
Exec=python3 /home/slade/defi_guardian/desktop_app.py
Icon=/home/slade/defi_guardian/defi_guardian.png

[Desktop Action Dashboard]
Name=Launch Dashboard
Exec=streamlit run /home/slade/defi_guardian/app.py
Icon=/home/slade/defi_guardian/defi_guardian.png
Terminal=true

[Desktop Action Both]
Name=Launch Both
Exec=python3 /home/slade/defi_guardian/launch_both.py
Icon=/home/slade/defi_guardian/defi_guardian.png
EOF

chmod +x ~/Desktop/DeFi-Guardian.desktop