# PrediCare Website - Startup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Website
```bash
python web_app.py
```

The website will be available at:
- **Local**: http://localhost:5000
- **External Access**: http://<your-machine-ip>:5000

### 3. Access from External Browsers
To access the website from other computers on your network:

1. Find your machine's IP address:
   - **Windows**: Run `ipconfig` in Command Prompt, look for IPv4 Address
   - **Mac/Linux**: Run `ifconfig`, look for inet address

2. Access from another device:
   - Open browser and go to: `http://<your-ip>:5000`
   - Example: `http://192.168.1.100:5000`

## Features

✅ **AI-Powered Risk Assessment**
- Calculates preeclampsia risk using multiple clinical algorithms
- FMF, NICE, ACOG, and ML Ensemble models
- Real-time risk scoring

✅ **Professional Website Interface**
- Clean, modern design
- Responsive layout for mobile and desktop
- Easy-to-use form inputs
- Tabbed results view

✅ **Clinical Decision Support**
- Recommended testing based on risk level
- Vital signs summary
- Risk comparison across models
- Print and download capabilities

## Features Coming Soon
- PDF report generation
- Patient data persistence
- Multi-language support
- Mobile app version

## System Requirements
- Python 3.8+
- 4GB RAM minimum
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, edit `web_app.py` and change the port:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Models Not Found
Make sure you have the trained models in the `models/` directory:
- `models/xgboost_preeclampsia.pkl`
- `models/lr_baseline.pkl`
- `models/scaler.pkl`

### External Access Not Working
- Check firewall settings
- Ensure the port is not blocked
- Use your actual machine IP (not localhost)

## Architecture

```
web_app.py              - Flask backend server
├── /templates/
│   └── index.html      - Main website interface
└── /models/            - Machine learning models
```

## API Endpoints

### POST /api/predict
Calculate risk assessment
**Request:**
```json
{
  "age": 28,
  "ga_weeks": 20,
  "sbp": 120,
  "dbp": 80,
  "hr": 75,
  "platelet_count": 250,
  "creatinine": 0.8,
  "ast": 30,
  "alt": 25,
  "protein_urine": 0.1
}
```

**Response:**
```json
{
  "success": true,
  "risks": {
    "FMF": 2.5,
    "NICE": 3.2,
    "ACOG": 2.8,
    "ML": 4.1,
    "Composite": 3.15
  },
  "risk_category": "LOW RISK",
  "severity": "low",
  "map": 93.3
}
```

### POST /api/suggested-tests
Get recommended tests based on risk score
**Request:**
```json
{
  "risk_score": 5.5
}
```

## Development Notes

To modify the website:
1. Edit `templates/index.html` for UI changes
2. Edit `web_app.py` for backend logic
3. The website will auto-reload in debug mode (just refresh the browser)

## Deployment

For production deployment:
1. Set `debug=False` in `web_app.py`
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
   ```
3. Configure a reverse proxy (Nginx)
4. Set up SSL/TLS certificates
5. Configure firewall rules

## License & Support
For clinical questions or technical support, contact the development team.
