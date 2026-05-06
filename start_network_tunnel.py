"""
PrediCare Network Tunnel Setup
Launches Streamlit app with ngrok tunnel for secure network sharing
"""

import subprocess
import sys
import time
import os
from pathlib import Path

try:
    from pyngrok import ngrok, conf
except ImportError:
    print("Installing pyngrok for network tunneling...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok", "-q"])
    from pyngrok import ngrok, conf

def setup_ngrok_tunnel(streamlit_port=8501):
    """
    Setup ngrok tunnel for Streamlit app
    """
    try:
        print("\n" + "="*60)
        print("  PrediCare Network Tunnel Setup")
        print("="*60 + "\n")
        
        # Optional: Set authtoken for persistent URLs
        # Get token from https://dashboard.ngrok.com/auth
        ngrok_token = os.getenv("NGROK_AUTHTOKEN")
        if ngrok_token:
            ngrok.set_auth_token(ngrok_token)
            print(f"✓ ngrok authenticated for persistent URLs")
        else:
            print("ℹ For persistent URLs, set NGROK_AUTHTOKEN environment variable")
        
        # Create ngrok tunnel
        print(f"\nCreating tunnel to localhost:{streamlit_port}...")
        public_url = ngrok.connect(streamlit_port, "http")
        
        print(f"\n✓ Tunnel created successfully!\n")
        print("="*60)
        print(f"  NETWORK URL: {public_url}")
        print("="*60)
        print(f"\n  Local URL:   http://localhost:{streamlit_port}")
        print(f"  Network URL: {public_url}")
        print(f"\n  Share the NETWORK URL with team members to access PrediCare")
        print(f"  (works on same network or internet)")
        print("\n" + "="*60 + "\n")
        
        return public_url
    
    except Exception as e:
        print(f"✗ Error setting up tunnel: {e}")
        print("Continuing with local-only access on http://localhost:8501")
        return None

def main():
    """
    Start Streamlit and create network tunnel
    """
    # Verify app.py exists
    if not Path("app.py").exists():
        print("✗ Error: app.py not found in current directory")
        print(f"  Current directory: {os.getcwd()}")
        sys.exit(1)
    
    print("Starting PrediCare Streamlit Application...\n")
    
    # Setup tunnel (non-blocking)
    tunnel_url = setup_ngrok_tunnel()
    
    # Start Streamlit
    try:
        print("Starting Streamlit server...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.headless=false"
        ])
    except KeyboardInterrupt:
        print("\n\n✓ Shutting down gracefully...")
        ngrok.kill()
        print("✓ Tunnel closed")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        ngrok.kill()
        sys.exit(1)

if __name__ == "__main__":
    main()
