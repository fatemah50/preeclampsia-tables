from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import joblib

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# ============================================================================
# LOAD MODELS
# ============================================================================
def load_models():
    try:
        xgb_model = joblib.load('models/xgboost_preeclampsia.pkl')
        lr_model = joblib.load('models/lr_baseline.pkl')
        scaler = joblib.load('models/scaler.pkl')
        return xgb_model, lr_model, scaler
    except:
        return None, None, None

xgb_model, lr_model, scaler = load_models()

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    """Calculate risk based on patient parameters"""
    try:
        data = request.json
        
        # Extract parameters
        params = {
            'age': float(data.get('age', 28)),
            'ga_weeks': float(data.get('ga_weeks', 20)),
            'sbp': float(data.get('sbp', 120)),
            'dbp': float(data.get('dbp', 80)),
            'hr': float(data.get('hr', 75)),
            'platelet_count': float(data.get('platelet_count', 250)),
            'creatinine': float(data.get('creatinine', 0.8)),
            'ast': float(data.get('ast', 30)),
            'alt': float(data.get('alt', 25)),
            'protein_urine': float(data.get('protein_urine', 0.1)),
        }
        
        # Calculate MAP
        map_value = (params['sbp'] + 2 * params['dbp']) / 3
        
        # Prepare features for ML models
        features = np.array([
            params['age'],
            params['ga_weeks'],
            params['sbp'],
            params['dbp'],
            map_value,
            params['hr'],
            params['platelet_count'],
            params['creatinine'],
            params['ast'],
            params['alt'],
            params['protein_urine']
        ]).reshape(1, -1)
        
        # Get predictions if models exist
        ml_risk = 0
        if xgb_model and scaler:
            try:
                features_scaled = scaler.transform(features)
                ml_risk = float(xgb_model.predict_proba(features_scaled)[0, 1] * 100)
            except:
                ml_risk = 0
        
        # Calculate FMF-based risk (simplified algorithm)
        fmf_risk = calculate_fmf_risk(params)
        
        # Calculate NICE risk (simplified)
        nice_risk = calculate_nice_risk(params)
        
        # Calculate ACOG risk (simplified)
        acog_risk = calculate_acog_risk(params)
        
        # Composite risk
        composite_risk = (fmf_risk + nice_risk + acog_risk + ml_risk) / 4
        
        # Determine risk category
        if composite_risk >= 10:
            risk_category = "HIGH RISK"
            severity = "severe"
        elif composite_risk >= 5:
            risk_category = "MODERATE RISK"
            severity = "moderate"
        else:
            risk_category = "LOW RISK"
            severity = "low"
        
        return jsonify({
            'success': True,
            'risks': {
                'FMF': fmf_risk,
                'NICE': nice_risk,
                'ACOG': acog_risk,
                'ML': ml_risk,
                'Composite': composite_risk
            },
            'risk_category': risk_category,
            'severity': severity,
            'map': round(map_value, 1),
            'parameters': params
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/suggested-tests', methods=['POST'])
def suggested_tests():
    """Get suggested tests based on risk"""
    try:
        data = request.json
        risk_score = float(data.get('risk_score', 0))
        
        tests = []
        
        if risk_score >= 10:
            tests = [
                {'priority': 'URGENT', 'test': 'Full Blood Count', 'timeline': 'Within 24h'},
                {'priority': 'URGENT', 'test': 'Coagulation Profile', 'timeline': 'Within 24h'},
                {'priority': 'URGENT', 'test': 'Liver Function Tests', 'timeline': 'Within 24h'},
                {'priority': 'URGENT', 'test': 'Renal Function Panel', 'timeline': 'Within 24h'},
                {'priority': 'HIGH', 'test': 'Uric Acid Level', 'timeline': 'Within 48h'},
                {'priority': 'HIGH', 'test': 'sFlt-1/PlGF Ratio', 'timeline': 'Within 48h'},
            ]
        elif risk_score >= 5:
            tests = [
                {'priority': 'HIGH', 'test': 'Full Blood Count', 'timeline': 'Within 1 week'},
                {'priority': 'HIGH', 'test': 'Renal Function Tests', 'timeline': 'Within 1 week'},
                {'priority': 'MODERATE', 'test': 'Uric Acid Level', 'timeline': 'Within 2 weeks'},
                {'priority': 'MODERATE', 'test': 'sFlt-1/PlGF Ratio', 'timeline': 'Within 2 weeks'},
            ]
        else:
            tests = [
                {'priority': 'MODERATE', 'test': 'Routine Antenatal Screening', 'timeline': 'At next visit'},
                {'priority': 'MODERATE', 'test': 'Blood Pressure Monitoring', 'timeline': 'Ongoing'},
            ]
        
        return jsonify({'success': True, 'tests': tests})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/export-report', methods=['POST'])
def export_report():
    """Export risk assessment report"""
    try:
        data = request.json
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'patient_data': data.get('patient_data', {}),
            'risks': data.get('risks', {}),
            'recommendations': data.get('recommendations', [])
        }
        
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================================================
# RISK CALCULATION FUNCTIONS
# ============================================================================

def calculate_fmf_risk(params):
    """Fetal Medicine Foundation risk algorithm"""
    risk = 2.0  # Base risk
    
    # Age factor
    if params['age'] < 20:
        risk += 1.0
    elif params['age'] > 40:
        risk += 2.0
    
    # Blood pressure factor
    sbp = params['sbp']
    if sbp >= 140:
        risk += 3.0
    elif sbp >= 130:
        risk += 2.0
    elif sbp >= 120:
        risk += 1.0
    
    # Platelet count factor
    if params['platelet_count'] < 100:
        risk += 4.0
    elif params['platelet_count'] < 150:
        risk += 2.0
    
    # Creatinine factor
    if params['creatinine'] > 0.9:
        risk += 2.0
    
    return min(risk, 25.0)

def calculate_nice_risk(params):
    """NICE guideline risk assessment"""
    risk = 1.5  # Base risk
    
    # SBP/DBP factor
    sbp = params['sbp']
    dbp = params['dbp']
    
    if sbp >= 140 or dbp >= 90:
        risk += 4.0
    elif sbp >= 130 or dbp >= 80:
        risk += 2.0
    
    # Proteinuria factor
    if params['protein_urine'] > 0.5:
        risk += 3.0
    elif params['protein_urine'] > 0.3:
        risk += 1.5
    
    # Platelet factor
    if params['platelet_count'] < 100:
        risk += 3.0
    
    return min(risk, 25.0)

def calculate_acog_risk(params):
    """ACOG risk assessment"""
    risk = 1.0  # Base risk
    
    # BP elevation from baseline
    if params['sbp'] >= 160 or params['dbp'] >= 110:
        risk += 4.0
    elif params['sbp'] >= 140 or params['dbp'] >= 90:
        risk += 3.0
    
    # Severe features
    if params['platelet_count'] < 100:
        risk += 3.5
    if params['creatinine'] > 1.1:
        risk += 3.0
    if params['protein_urine'] > 2.0:
        risk += 2.0
    
    return min(risk, 25.0)

# ============================================================================
# SERVE STATIC FILES
# ============================================================================

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Run on all interfaces to allow external access
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
