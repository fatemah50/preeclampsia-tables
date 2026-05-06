#!/usr/bin/env python3
"""
PrediCare v3.0.1 - Quick Start Script
Automatically tests and launches the app with helpful output
"""

import subprocess
import sys
import os
from pathlib import Path

def print_header():
    """Print welcome header"""
    print("\n" + "="*70)
    print("🏥 PrediCare v3.0.1 - Theme & Network Sharing Ready!")
    print("="*70)
    print()

def print_features():
    """Print new features"""
    print("✨ NEW FEATURES:")
    print("  🎨 Day/Light Mode Theme Switcher")
    print("  🌐 Network Sharing with Stable URLs")
    print()

def print_options():
    """Print usage options"""
    print("📋 QUICK OPTIONS:")
    print()
    print("  1️⃣  Run Locally (Dark Mode)")
    print("     $ streamlit run app.py")
    print("     → Opens: http://localhost:8501")
    print()
    print("  2️⃣  Switch to Light Mode")
    print("     (Once running) Click ☀️ button in sidebar")
    print()
    print("  3️⃣  Share with Team")
    print("     $ python start_network_tunnel.py")
    print("     → Get URL: https://abc-123-xyz.ngrok.io")
    print()
    print("  4️⃣  Persistent URL (Same each time)")
    print("     $ set NGROK_AUTHTOKEN=your_token")
    print("     $ python start_network_tunnel.py")
    print()
    print("  5️⃣  One-Click Windows")
    print("     → Double-click: START_NETWORK_SHARING.bat")
    print()

def print_documentation():
    """Print documentation guide"""
    print("📚 DOCUMENTATION:")
    print()
    print("  Quick (5 min):     QUICK_REFERENCE.md")
    print("  Complete (15 min): COMPLETE_FEATURE_GUIDE.md")
    print("  Technical (10 min): ARCHITECTURE_DIAGRAMS.md")
    print("  Master Index:      START_HERE_NEW.md")
    print()

def print_themes():
    """Print theme info"""
    print("🎨 THEME OPTIONS:")
    print()
    print("  🌙 Dark Mode (Professional)")
    print("     • Reduces eye strain")
    print("     • Medical settings")
    print("     • Professional look")
    print()
    print("  ☀️ Light Mode (Accessible)")
    print("     • High contrast")
    print("     • Presentations")
    print("     • Day-time use")
    print()

def print_security():
    """Print security info"""
    print("🔐 SECURITY:")
    print()
    print("  ✓ HTTPS Encryption (ngrok handles SSL/TLS)")
    print("  ✓ Auto URL Rotation (without auth token)")
    print("  ✓ Traffic Logging (ngrok dashboard)")
    print("  ✓ Session Isolation (each user separate)")
    print("  ✓ Firewall Compatible (standard HTTPS)")
    print()

def check_dependencies():
    """Check if dependencies are installed"""
    print("🔍 CHECKING DEPENDENCIES...")
    print()
    
    checks = {
        "Python 3.8+": lambda: sys.version_info >= (3, 8),
        "Streamlit": lambda: check_module("streamlit"),
        "pyngrok": lambda: check_module("pyngrok"),
        "pandas": lambda: check_module("pandas"),
        "numpy": lambda: check_module("numpy"),
    }
    
    all_ok = True
    for name, check in checks.items():
        try:
            result = check()
            status = "✓" if result else "✗"
            print(f"  {status} {name}")
            if not result:
                all_ok = False
        except:
            print(f"  ✗ {name}")
            all_ok = False
    
    print()
    
    if not all_ok:
        print("⚠️  Some dependencies missing!")
        print("   Run: pip install -r requirements.txt")
        print()
        return False
    else:
        print("✅ All dependencies OK!")
        print()
        return True

def check_module(module_name):
    """Check if a module is installed"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def print_next_steps():
    """Print next steps"""
    print("🚀 NEXT STEPS:")
    print()
    print("  1. Try locally:        streamlit run app.py")
    print("  2. Test themes:        Click 🌙 and ☀️ in sidebar")
    print("  3. Share with team:    python start_network_tunnel.py")
    print("  4. Read docs:          Start with QUICK_REFERENCE.md")
    print()

def print_footer():
    """Print footer"""
    print("="*70)
    print("For complete guide: see START_HERE_NEW.md")
    print("Questions? Check THEME_AND_NETWORK_GUIDE.md #troubleshooting")
    print("="*70)
    print()

def main():
    """Main function"""
    print_header()
    print_features()
    print_options()
    print_documentation()
    print_themes()
    print_security()
    
    deps_ok = check_dependencies()
    
    print_next_steps()
    print_footer()
    
    if not deps_ok:
        print("⚠️  Please install dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ Everything looks good! Ready to start?")
    print()
    print("   Command: streamlit run app.py")
    print()

if __name__ == "__main__":
    main()
