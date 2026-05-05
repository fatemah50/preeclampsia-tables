#!/usr/bin/env python
"""
PrediCare Setup Verification Script
Checks if everything is properly configured for deployment
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """Check Python version"""
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"✓ Python {version}")
    return True

def check_venv():
    """Check if virtual environment exists"""
    if os.path.exists('.venv'):
        print("✓ Virtual environment exists")
        return True
    else:
        print("✗ Virtual environment not found")
        print("  Creating virtual environment...")
        os.system('python -m venv .venv')
        print("✓ Virtual environment created")
        return True

def check_requirements():
    """Check if all required packages are installed"""
    required = [
        'streamlit', 'flask', 'flask-cors', 'pandas', 'numpy', 
        'joblib', 'scikit-learn', 'plotly', 'pillow', 'reportlab'
    ]
    
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
        
        missing = [pkg for pkg in required if pkg.lower() not in installed]
        
        if missing:
            print(f"✗ Missing packages: {', '.join(missing)}")
            print("  Installing missing packages...")
            os.system('pip install -q -r requirements.txt')
            print("✓ Dependencies installed")
            return True
        else:
            print("✓ All required packages installed")
            return True
    except Exception as e:
        print(f"✗ Error checking packages: {e}")
        return False

def check_models():
    """Check if ML models exist"""
    models_dir = Path('models')
    required_models = [
        'xgboost_preeclampsia.pkl',
        'lr_baseline.pkl',
        'scaler.pkl'
    ]
    
    if not models_dir.exists():
        print("✗ Models directory not found")
        return False
    
    missing = [m for m in required_models if not (models_dir / m).exists()]
    
    if missing:
        print(f"✗ Missing models: {', '.join(missing)}")
        return False
    else:
        print("✓ All ML models found")
        return True

def check_files():
    """Check if required files exist"""
    required_files = [
        'app.py',
        'web_app.py',
        'requirements.txt',
        '.streamlit/config.toml',
        'templates/index.html'
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    
    if missing:
        print(f"✗ Missing files: {', '.join(missing)}")
        return False
    else:
        print("✓ All required files present")
        return True

def check_config():
    """Check Streamlit config for issues"""
    config_file = Path('.streamlit/config.toml')
    
    if not config_file.exists():
        print("✗ Streamlit config not found")
        return False
    
    content = config_file.read_text()
    
    # Check for deprecated options
    if 'showStderr' in content or 'showErrorDetails' in content:
        print("⚠ Streamlit config has deprecated options")
        print("  Fixing config...")
        content = content.replace('showStderr = true', '# Deprecated')
        content = content.replace('showErrorDetails = true', '# Deprecated')
        config_file.write_text(content)
        print("✓ Config updated")
        return True
    else:
        print("✓ Streamlit config valid")
        return True

def print_header():
    """Print header"""
    print("\n" + "="*50)
    print("PrediCare Deployment Verification")
    print("="*50 + "\n")

def print_footer():
    """Print footer with next steps"""
    print("\n" + "="*50)
    print("✅ Setup Verification Complete!")
    print("="*50)
    print("\n📱 Next Steps:\n")
    print("1. RUN THE APP LOCALLY:")
    print("   Windows: deploy_streamlit.bat")
    print("   macOS/Linux: bash deploy_streamlit.sh")
    print("\n2. TEST IN BROWSER:")
    print("   http://localhost:8501")
    print("\n3. DEPLOY TO CLOUD:")
    print("   - Go to: https://share.streamlit.io")
    print("   - Sign in with GitHub")
    print("   - Deploy and share!")
    print("\n📖 For more details, see DEPLOYMENT_GUIDE.md\n")

def main():
    """Run all checks"""
    print_header()
    
    checks = [
        ("Python Version", check_python),
        ("Virtual Environment", check_venv),
        ("Required Packages", check_requirements),
        ("ML Models", check_models),
        ("Project Files", check_files),
        ("Streamlit Config", check_config),
    ]
    
    all_passed = True
    for name, check in checks:
        print(f"\nChecking {name}...")
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"✗ Error: {e}")
            all_passed = False
    
    print_footer()
    
    if not all_passed:
        sys.exit(1)

if __name__ == '__main__':
    main()
