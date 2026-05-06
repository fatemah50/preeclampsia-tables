# PrediCare v3.0 - Theme & Network Sharing Guide

## New Features

### 1. Day/Light Mode Toggle 🌙☀️

The app now supports **Dark Mode** (default) and **Light Mode** themes.

**How to switch themes:**
- Open the app at `http://localhost:8501`
- Look at the **Sidebar** (left panel)
- Click either:
  - **🌙 Dark Mode** - For the original dark professional theme
  - **☀️ Light Mode** - For a bright, accessible light theme

The theme preference is **saved for your session** and applies instantly to:
- Background colors
- Text colors  
- Cards and panels
- Alerts and badges
- All UI elements

---

## 2. Network Sharing with Stable URL 🌐

Share PrediCare with your team via a **stable public URL** using ngrok tunneling.

### Quick Start

#### Option A: Using Python Script (Recommended)

```bash
# Install dependencies (one-time)
pip install pyngrok streamlit

# Start with network tunnel
python start_network_tunnel.py
```

**Output will show:**
```
============================================================
  PrediCare Network Tunnel Setup
============================================================

✓ Tunnel created successfully!

============================================================
  NETWORK URL: https://abc-123-xyz-789.ngrok.io
============================================================

  Local URL:   http://localhost:8501
  Network URL: https://abc-123-xyz-789.ngrok.io

  Share the NETWORK URL with team members to access PrediCare
  (works on same network or internet)

============================================================
```

#### Option B: Using Batch File (Windows)

```bash
start_with_tunnel.bat
```

---

### Sharing URLs with Your Team

**Share this URL:** `https://abc-123-xyz-789.ngrok.io` (replace with your actual URL)

#### Network Access Requirements:
- ✓ Same local network (Wi-Fi)
- ✓ Different network (internet access)
- ✓ Different country (global access)

#### Share via:
- Email
- Teams/Slack/Discord
- QR code (generate from URL)
- Patient portal
- Documentation

---

### Getting a Persistent URL (Optional)

By default, ngrok generates a new URL each time. For a **persistent URL** that doesn't change:

1. **Create ngrok account:** https://dashboard.ngrok.com
2. **Get your auth token:** Copy from dashboard
3. **Set environment variable:**
   
   **Windows (PowerShell):**
   ```powershell
   $env:NGROK_AUTHTOKEN = "your_token_here"
   python start_network_tunnel.py
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   set NGROK_AUTHTOKEN=your_token_here
   python start_network_tunnel.py
   ```
   
   **Linux/Mac:**
   ```bash
   export NGROK_AUTHTOKEN="your_token_here"
   python start_network_tunnel.py
   ```

4. **Result:** Your URL will stay the same across restarts!

---

## Architecture

### Local Access (No Tunnel)
```
User's Browser → localhost:8501 → Streamlit App
```

### Network Access (With Tunnel)
```
Team Member's Browser → ngrok URL → ngrok tunnel → localhost:8501 → Streamlit App
```

---

## Security & Best Practices

### Protection Features:
- ✓ HTTPS encryption (ngrok handles SSL)
- ✓ Automatic URL changes (without auth token)
- ✓ Traffic logs available in ngrok dashboard
- ✓ Session isolation

### Recommendations:
1. **Disable tunnel when not in use**
2. **Use strong passwords** if password-protecting the app
3. **Monitor access logs** in ngrok dashboard
4. **Share URLs only with authorized users**
5. **For production:** Consider Streamlit Cloud or private hosting

---

## Troubleshooting

### Problem: ngrok not found

**Solution:**
```bash
pip install pyngrok
```

### Problem: Port 8501 already in use

**Solution:** Change port in `start_network_tunnel.py`:
```python
tunnel_url = setup_ngrok_tunnel(streamlit_port=8502)  # Change port
```

### Problem: Can't access from external network

**Possible causes:**
- Firewall blocking outbound connections
- ngrok service down (check status.ngrok.com)
- Network policy restrictions

**Solution:**
1. Check firewall settings
2. Try connecting from another device on same Wi-Fi
3. Verify ngrok token is correct
4. Check ngrok dashboard for errors

### Problem: URL keeps changing every restart

**Solution:** Get persistent URL with auth token (see section above)

---

## Theme Technical Details

### Dark Mode Colors
- Background: `#060b14` (deep navy)
- Text: `#e8f4fd` (light cyan)
- Accent: `#ffa502` (amber)
- Success: `#2ed573` (green)
- Alert: `#ff4757` (red)

### Light Mode Colors
- Background: `#f8f9fa` (off-white)
- Text: `#1a1a1a` (dark gray)
- Accent: `#ff9800` (orange)
- Success: `#27ae60` (dark green)
- Alert: `#d63031` (dark red)

### Implementation
Theme switching uses **Streamlit session state** to persist the user's preference during their session and applies **dynamic CSS variables** for instant visual updates.

---

## Advanced Usage

### Embedding in Documentation
```html
<iframe src="https://your-ngrok-url.ngrok.io" width="100%" height="800"></iframe>
```

### API Access (if integrated)
```bash
curl https://your-ngrok-url.ngrok.io/api/predict \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"age": 35, "sbp": 150}'
```

### Custom Domain Forwarding
With ngrok Pro subscription, map to custom domain:
```bash
# This allows URL like: https://predicare.yourdomain.com
```

---

## Support

For issues:
1. Check PrediCare logs: `EXECUTION_COMPLETE.md`
2. Review ngrok dashboard: https://dashboard.ngrok.com
3. Verify Streamlit is running: `http://localhost:8501`

---

**Last Updated:** 2026-05-06  
**PrediCare Version:** 3.0
