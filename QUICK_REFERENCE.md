# PrediCare Quick Start - Day/Light Mode & Network Sharing

## ⚡ Quick Commands

### Run Locally (Dark Mode)
```bash
streamlit run app.py
```
Then open: **http://localhost:8501**

### Run with Network Tunnel (Share URL)
```bash
python start_network_tunnel.py
```
Then share the **https://xxx-xxx-xxx.ngrok.io** URL

---

## 🎨 How to Switch Themes

1. Open http://localhost:8501 (or your network URL)
2. Look at the **LEFT SIDEBAR**
3. At the bottom, click:
   - **🌙 Dark Mode** (professional dark theme)
   - **☀️ Light Mode** (bright accessible theme)

✓ Theme updates instantly!  
✓ Your choice is saved for this session

---

## 🌐 Share with Team

### Step 1: Start Tunnel
```bash
python start_network_tunnel.py
```

### Step 2: Copy Network URL
You'll see something like:
```
NETWORK URL: https://abc-12345-xyz.ngrok.io
```

### Step 3: Share with Team
Send them the URL. They can access from:
- Same Wi-Fi
- Different network
- Different country
- Anywhere with internet

---

## 🔐 Persistent URL (Keep Same URL)

### Get Auth Token
1. Go to: https://dashboard.ngrok.com/auth
2. Copy your token

### Set & Run
**Windows (Command Prompt):**
```cmd
set NGROK_AUTHTOKEN=your_token_here
python start_network_tunnel.py
```

**Windows (PowerShell):**
```powershell
$env:NGROK_AUTHTOKEN = "your_token_here"
python start_network_tunnel.py
```

**Linux/Mac:**
```bash
export NGROK_AUTHTOKEN="your_token_here"
python start_network_tunnel.py
```

Result: Same URL every time! ✓

---

## 📊 Files Modified/Created

| File | Purpose |
|------|---------|
| `app.py` | Added theme switcher & dual-color CSS |
| `start_network_tunnel.py` | Python script to launch with tunnel |
| `start_with_tunnel.bat` | Batch file for Windows |
| `requirements.txt` | Added pyngrok dependency |
| `THEME_AND_NETWORK_GUIDE.md` | Full documentation |
| `QUICK_REFERENCE.md` | This file |

---

## 🚀 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or manually
pip install streamlit pyngrok
```

---

## ❓ Common Issues

**Q: URL changes each time?**  
A: Normal! Add ngrok auth token for persistent URL (see above)

**Q: Can't access from network?**  
A: Check firewall or use ngrok dashboard to debug

**Q: Port 8501 busy?**  
A: Edit `start_network_tunnel.py` line with `streamlit_port=8502`

**Q: Dark mode on light mode text is hard to read?**  
A: Switch themes in sidebar! Light mode colors are optimized for readability

---

## 📞 Support

- **Local issues:** Run `streamlit run app.py`
- **Network issues:** Check https://status.ngrok.com
- **Theme issues:** Clear browser cache or open in incognito

---

**Ready?** Run `python start_network_tunnel.py` and share the URL! 🎉
