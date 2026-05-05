# PrediCare Deployment Guide

## Overview
PrediCare is a Preeclampsia Risk Prediction application available in two versions:
- **Streamlit Version**: Modern, interactive web interface (Recommended)
- **Flask Version**: Traditional web app with REST API

---

## ✅ Quick Start (Local Deployment)

### Option 1: Streamlit (RECOMMENDED)

#### Windows:
1. Double-click **`deploy_streamlit.bat`**
2. Wait for the message: `You can now view your Streamlit app in your browser`
3. Open your browser to: **`http://localhost:8501`**

#### macOS/Linux:
```bash
chmod +x deploy_streamlit.sh
./deploy_streamlit.sh
```

### Option 2: Flask

#### Windows:
1. Double-click **`deploy_flask.bat`**
2. Open your browser to: **`http://127.0.0.1:5000`**

#### macOS/Linux:
```bash
python web_app.py
```

---

## 🌐 Cloud Deployment Options

### Option 1: Streamlit Cloud (FREE & EASY) ⭐ RECOMMENDED

**Best for**: Sharing with collaborators, quick deployment, free hosting

#### Steps:
1. **Create Streamlit Cloud account**:
   - Go to: https://streamlit.io/cloud
   - Sign up with GitHub
   
2. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push
   ```

3. **Deploy from Streamlit Cloud**:
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your GitHub repo, branch, and `app.py`
   - Click "Deploy"

4. **Share your app URL** with anyone!

**Advantages**:
- ✓ Free tier available
- ✓ Auto-deploys on git push
- ✓ No server management
- ✓ SSL certificate included
- ✓ Custom domain support (paid)

---

### Option 2: Heroku (Simple Cloud Deployment)

**Best for**: More control, traditional web hosting

#### Prerequisites:
- Heroku account (https://www.heroku.com)
- Heroku CLI installed

#### Steps:

1. **Create a `Procfile`** in your project root:
   ```
   web: python -m streamlit.cli run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Create a `runtime.txt`** in your project root:
   ```
   python-3.11.4
   ```

3. **Deploy**:
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   heroku open
   ```

---

### Option 3: PythonAnywhere (Easy Python Hosting)

**Best for**: Long-term hosting, always-on server

#### Steps:
1. Sign up at: https://www.pythonanywhere.com
2. Upload your project files
3. Create a web app with Flask backend
4. Configure the WSGI file to point to `web_app.py`
5. Set domain and SSL

---

### Option 4: AWS/Google Cloud/Azure (Advanced)

For production deployments with full control:
- AWS: EC2 instance with Streamlit/Flask
- Google Cloud: Cloud Run (serverless)
- Azure: App Service

Requires more configuration but offers maximum flexibility.

---

## 🔧 Environment Configuration

### Local Development

Create a `.env` file (for Flask):
```
FLASK_ENV=development
DEBUG=True
PORT=5000
```

### Production

Update `.streamlit/config.toml`:
```toml
[server]
headless = true
port = 8501
address = "0.0.0.0"

[client]
# Remove deprecated options

[theme]
primaryColor = "#2563eb"
```

---

## ✨ Recommended Workflow

### For Development:
1. Run locally using `deploy_streamlit.bat` or `deploy_flask.bat`
2. Test all features
3. Fix any bugs

### For Sharing/Demo:
1. Deploy to **Streamlit Cloud** (takes 2 minutes)
2. Share the public URL with team/stakeholders

### For Production:
1. Set up **Heroku** or **AWS**
2. Configure custom domain
3. Set up monitoring and logging
4. Add authentication if needed

---

## 🐛 Troubleshooting

### "Command not found" errors:
- Activate virtual environment: `.venv\Scripts\activate`
- Install requirements: `pip install -r requirements.txt`

### Port already in use:
- **Streamlit**: `python -m streamlit run app.py --server.port=8502`
- **Flask**: Set `PORT` in `.env` file

### Models not found:
- Ensure `models/` folder exists with:
  - `xgboost_preeclampsia.pkl`
  - `lr_baseline.pkl`
  - `scaler.pkl`

### Connection issues:
- Make sure firewall allows port 5000/8501
- Use `0.0.0.0` address for network access

---

## 📊 Comparison: Streamlit vs Flask

| Feature | Streamlit | Flask |
|---------|-----------|-------|
| Setup Time | 5 minutes | 10 minutes |
| Learning Curve | Easy | Medium |
| UI/UX | Built-in, modern | Requires frontend |
| Deployment | Super easy (Cloud) | Moderate |
| Performance | Good for ML apps | Better for APIs |
| Best Use | Data science, MLapps | Traditional web apps |

---

## ✅ Success Checklist

- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Models folder exists with all 3 `.pkl` files
- [ ] Local deployment works (http://localhost:8501 or :5000)
- [ ] App accepts user input and generates predictions
- [ ] Results are displayed correctly
- [ ] Cloud deployment account created
- [ ] Code pushed to GitHub
- [ ] Cloud deployment successful
- [ ] URL shared with team

---

## 🆘 Need Help?

1. Check the error message carefully
2. Review the relevant section above
3. Check GitHub Issues
4. Contact support

---

## Next Steps

1. ✅ Test locally using the deployment scripts
2. 🚀 Deploy to Streamlit Cloud in 2 minutes
3. 🔗 Share the URL with your team
4. 📈 Gather feedback and iterate

**Your app is ready to be shared! Choose Streamlit Cloud for the quickest deployment.**
