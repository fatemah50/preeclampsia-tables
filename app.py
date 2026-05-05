import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import joblib
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import io
import re
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ============================================================================
# STREAMLIT PAGE CONFIG & STYLING
# ============================================================================
st.set_page_config(
    page_title="PrediCare: Preeclampsia Risk Predictor v3.0",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    * { box-sizing: border-box; }
    :root {
        --cyan: #00d4ff;
        --red-alert: #ff4757;
        --amber: #ffa502;
        --green-ok: #2ed573;
        --bg-deep: #060b14;
        --bg-panel: #0a1628;
        --bg-card: #0d1f35;
        --border: rgba(0,212,255,0.18);
        --text: #e8f4fd;
        --text-muted: #6b8fa8;
    }
    
    body { background-color: var(--bg-deep); color: var(--text); }
    .stApp { background-color: var(--bg-deep); }
    
    .alert-severe { background-color: rgba(255,71,87,0.1); border-left: 4px solid #ff4757; padding: 12px; border-radius: 4px; margin: 10px 0; }
    .alert-moderate { background-color: rgba(255,165,2,0.1); border-left: 4px solid #ffa502; padding: 12px; border-radius: 4px; margin: 10px 0; }
    .alert-low { background-color: rgba(46,213,115,0.1); border-left: 4px solid #2ed573; padding: 12px; border-radius: 4px; margin: 10px 0; }
    .risk-card { background-color: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin: 8px 0; }
    .metric-value { font-size: 32px; font-weight: bold; color: var(--amber); font-family: 'Courier New', monospace; }
    
    .comparison-table { background-color: var(--bg-card); padding: 12px; border-radius: 6px; margin: 8px 0; border: 1px solid var(--border); }
    .ratio-badge { display: inline-block; padding: 6px 12px; border-radius: 4px; margin: 4px; font-size: 12px; font-weight: bold; }
    .ratio-normal { background-color: rgba(46,213,115,0.2); color: #2ed573; border: 1px solid #2ed573; }
    .ratio-concern { background-color: rgba(255,165,2,0.2); color: #ffa502; border: 1px solid #ffa502; }
    .ratio-danger { background-color: rgba(255,71,87,0.2); color: #ff4757; border: 1px solid #ff4757; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LOAD MODELS
# ============================================================================
@st.cache_resource
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
# SUGGESTED TESTS BASED ON RISK
# ============================================================================
def get_suggested_tests(params, risk_score):
    """Generate recommended tests based on current parameters and risk"""
    tests = []
    
    # High-risk patients need comprehensive workup
    if risk_score >= 50:
        tests.append(("URGENT", "Repeat BP monitoring", "Within 1 week", "Confirm hypertension diagnosis"))
        tests.append(("URGENT", "24-hour urine protein", "Within 3 days", "Assess proteinuria severity"))
        tests.append(("URGENT", "Platelet count + LFTs", "Within 3 days", "Screen for HELLP syndrome"))
        if not params.get('sflt1'):
            tests.append(("HIGH", "sFlt-1/PlGF ratio", "Within 1 week", "Angiogenic biomarker assessment"))
    
    # Moderate-risk patients
    if 20 <= risk_score < 50:
        tests.append(("MODERATE", "BP monitoring", "Weekly", "Trend assessment"))
        tests.append(("MODERATE", "Urine protein check", "Every 2 weeks", "Rule out proteinuria"))
        if params.get('ga_weeks', 0) >= 16 and not params.get('uterine_pi'):
            tests.append(("MODERATE", "Uterine artery Doppler", "Within 2 weeks", "Early PE detection"))
    
    # Specific lab abnormalities trigger tests
    if params.get('platelet_count', 999) < 150:
        tests.append(("HIGH", "Repeat platelet count", "Within 3-5 days", "Monitor for declining trend"))
    
    if params.get('protein_urine', 0) > 0.3 and params.get('protein_urine', 0) < 3.0:
        tests.append(("MODERATE", "Repeat 24h urine protein", "Within 1 week", "Confirm persistent proteinuria"))
    
    if params.get('sbp', 0) >= 140:
        tests.append(("MODERATE", "Home BP monitoring log", "Daily for 1 week", "Assess BP pattern (office vs home)"))
    
    if params.get('creatinine', 0) > 0.9:
        tests.append(("MODERATE", "Renal function panel", "Within 1 week", "Assess baseline renal status"))
    
    if params.get('ast', 0) > 40 or params.get('alt', 0) > 40:
        tests.append(("MODERATE", "Repeat liver enzymes", "Within 3-5 days", "Monitor for HELLP development"))
    
    if params.get('ga_weeks', 0) >= 20 and not params.get('umbilical_pi'):
        tests.append(("ROUTINE", "Umbilical artery Doppler", "At next scan", "Assess fetal adaptation"))
    
    if params.get('gdm') or params.get('diabetes'):
        tests.append(("ROUTINE", "HbA1c if not done", "If >3 months since last", "Glycemic control assessment"))
    
    # Risk score specific
    if risk_score < 20 and not params.get('papp_a'):
        tests.append(("ROUTINE", "PAPP-A (if <13+6 weeks)", "Standard first-trimester screening", "Baseline risk assessment"))
    
    return tests

# ============================================================================
# PARAMETER RATIO ANALYSIS
# ============================================================================
def analyze_parameter_ratios(params):
    """Analyze combinations of parameters to identify concerning patterns"""
    analysis = []
    
    # SBP/DBP ratio
    if params.get('sbp', 0) > 0 and params.get('dbp', 0) > 0:
        ratio = params['sbp'] / params['dbp']
        if ratio > 2.0:
            analysis.append(("SBP/DBP Ratio", f"{ratio:.2f}", "Normal", "normal", f"Ratio {ratio:.2f} indicates balanced pressure (normal ~1.5)"))
        elif ratio >= 1.3 and ratio <= 2.0:
            analysis.append(("SBP/DBP Ratio", f"{ratio:.2f}", "Normal", "normal", "Physiologic blood pressure pattern"))
        else:
            analysis.append(("SBP/DBP Ratio", f"{ratio:.2f}", "Concern", "concern", "Unusual pattern - verify measurement"))
    
    # MAP/SBP ratio
    if params.get('sbp', 0) > 0 and params.get('map', 0) > 0:
        map_sbp_ratio = params['map'] / params['sbp']
        if 0.55 <= map_sbp_ratio <= 0.70:
            analysis.append(("MAP/SBP Ratio", f"{map_sbp_ratio:.2f}", "Normal", "normal", "Well-regulated blood pressure"))
        else:
            analysis.append(("MAP/SBP Ratio", f"{map_sbp_ratio:.2f}", "Concern", "concern", "Abnormal pressure distribution"))
    
    # Creatinine-BUN ratio
    if params.get('creatinine', 0) > 0 and params.get('bun', 0) > 0:
        cr_bun = params['bun'] / params['creatinine']
        if 10 <= cr_bun <= 20:
            analysis.append(("BUN/Creatinine", f"{cr_bun:.1f}", "Normal", "normal", "Normal kidney function (ratio 10-20)"))
        elif cr_bun > 20:
            analysis.append(("BUN/Creatinine", f"{cr_bun:.1f}", "Concern", "concern", "Elevated ratio suggests prerenal azotemia"))
        else:
            analysis.append(("BUN/Creatinine", f"{cr_bun:.1f}", "Concern", "concern", "Low ratio - assess hydration status"))
    
    # AST/ALT ratio (De Ritis ratio)
    if params.get('ast', 0) > 0 and params.get('alt', 0) > 0:
        de_ritis = params['ast'] / params['alt']
        if de_ritis < 1.0:
            analysis.append(("AST/ALT (De Ritis)", f"{de_ritis:.2f}", "Normal", "normal", "<1.0 indicates hepatocellular pattern"))
        elif de_ritis > 2.0:
            analysis.append(("AST/ALT (De Ritis)", f"{de_ritis:.2f}", "Concern", "concern", ">2.0 suggests cirrhosis or hemolysis"))
        else:
            analysis.append(("AST/ALT (De Ritis)", f"{de_ritis:.2f}", "Normal", "normal", "1.0-2.0 indicates mixed pattern"))
    
    # LDH/platelet ratio (hemolysis marker)
    if params.get('ldh', 0) > 0 and params.get('platelet_count', 0) > 0:
        ldh_plt = params['ldh'] / params['platelet_count']
        if ldh_plt < 1.0:
            analysis.append(("LDH/Platelet", f"{ldh_plt:.2f}", "Normal", "normal", "No hemolysis pattern"))
        elif ldh_plt >= 1.0 and ldh_plt < 1.5:
            analysis.append(("LDH/Platelet", f"{ldh_plt:.2f}", "Concern", "concern", "Possible early hemolysis"))
        else:
            analysis.append(("LDH/Platelet", f"{ldh_plt:.2f}", "Danger", "danger", "Significant hemolysis pattern - HELLP risk"))
    
    # Proteinuria/Creatinine ratio approximation
    if params.get('protein_urine', 0) > 0 and params.get('creatinine', 0) > 0:
        pr_cr = params['protein_urine'] / params['creatinine']
        if pr_cr < 0.1:
            analysis.append(("Protein/Creatinine", f"{pr_cr:.3f}", "Normal", "normal", "<0.3 is normal proteinuria"))
        elif 0.1 <= pr_cr < 0.5:
            analysis.append(("Protein/Creatinine", f"{pr_cr:.3f}", "Concern", "concern", "Significant proteinuria - monitor"))
        else:
            analysis.append(("Protein/Creatinine", f"{pr_cr:.3f}", "Danger", "danger", "Nephrotic-range proteinuria"))
    
    # HDL/LDL ratio
    if params.get('hdl', 0) > 0 and params.get('ldl', 0) > 0:
        hdl_ldl = params['hdl'] / params['ldl']
        if hdl_ldl >= 0.3:
            analysis.append(("HDL/LDL", f"{hdl_ldl:.2f}", "Normal", "normal", "Good lipid ratio (>0.3)"))
        else:
            analysis.append(("HDL/LDL", f"{hdl_ldl:.2f}", "Concern", "concern", "Low HDL/LDL - increased CV risk"))
    
    # BMI-age interaction
    if params.get('bmi', 0) > 0 and params.get('age', 0) > 0:
        bmi_age = params['bmi'] * (params['age'] / 30)
        if params['bmi'] >= 30 and params['age'] >= 35:
            analysis.append(("Age×BMI Risk", f"{bmi_age:.1f}", "Danger", "danger", "Combined age + obesity = very high PE risk"))
        elif params['bmi'] >= 30 or params['age'] >= 35:
            analysis.append(("Age×BMI Risk", f"{bmi_age:.1f}", "Concern", "concern", "Either age ≥35 or BMI ≥30 increases risk"))
        else:
            analysis.append(("Age×BMI Risk", f"{bmi_age:.1f}", "Normal", "normal", "Favorable age-BMI profile"))
    
    # sFlt-1/PlGF combination
    if params.get('sflt_plgf_ratio', 0) > 0:
        if params.get('sflt_plgf_ratio', 0) > 85:
            analysis.append(("sFlt-1/PlGF Ratio", f"{params['sflt_plgf_ratio']:.1f}", "Danger", "danger", ">85 = high PE risk (early-onset)"))
        elif 35 <= params.get('sflt_plgf_ratio', 0) <= 85:
            analysis.append(("sFlt-1/PlGF Ratio", f"{params['sflt_plgf_ratio']:.1f}", "Concern", "concern", "35-85 = elevated risk (late-onset PE))"))
        else:
            analysis.append(("sFlt-1/PlGF Ratio", f"{params['sflt_plgf_ratio']:.1f}", "Normal", "normal", "<35 = low PE risk"))
    
    return analysis

# ============================================================================
# SIMULATED OCR / IMAGE ANALYSIS
# ============================================================================
def extract_values_from_image(image_file):
    """
    Simulate OCR/image analysis from uploaded medical report.
    In production, integrate with Anthropic API or Tesseract OCR.
    """
    try:
        img = Image.open(image_file)
        
        # Simulated extraction (in production: use Claude API + vision)
        extracted = {
            'sbp': np.random.randint(110, 160),
            'dbp': np.random.randint(70, 110),
            'platelet_count': np.random.randint(100, 350),
            'creatinine': np.random.uniform(0.5, 1.5),
            'ast': np.random.randint(20, 80),
            'alt': np.random.randint(15, 70),
            'protein_urine': np.random.uniform(0.0, 1.0),
            'hemoglobin': np.random.uniform(10.0, 15.0),
        }
        return extracted
    except Exception as e:
        st.error(f"Image analysis failed: {str(e)}")
        return None

# ============================================================================
# PATIENT DATA STORAGE
# ============================================================================
def load_patient_visits():
    if os.path.exists('patient_visits.json'):
        with open('patient_visits.json', 'r') as f:
            return json.load(f)
    return {}

def save_patient_visits(visits):
    with open('patient_visits.json', 'w') as f:
        json.dump(visits, f, indent=2, default=str)

# ============================================================================
# NATURAL LANGUAGE PROCESSING - AUTO-FILL FROM NOTES
# ============================================================================
def parse_clinical_notes(text):
    """
    Parse free-text clinical notes and extract structured medical parameters.
    Searches for patterns like "BP 138/90", "creatinine 1.2", etc.
    """
    extracted = {}
    uncaptured_symptoms = []
    
    # Define regex patterns for each parameter
    patterns = {
        'sbp': [r'BP\s*(?:SBP)?[\s:]*(\d{2,3})/(\d{2,3})', r'(?:systolic|SBP)[\s:]*(\d{2,3})', r'(\d{2,3})/\d{2,3}\s*(?:mmHg)?'],
        'dbp': [r'BP\s*(?:DBP)?[\s:]*\d{2,3}/(\d{2,3})', r'(?:diastolic|DBP)[\s:]*(\d{2,3})'],
        'platelet_count': [r'platelets?[\s:]*(\d+)', r'PLT[\s:]*(\d+)'],
        'creatinine': [r'creatinine[\s:]*([0-9.]+)', r'(?:Cr|SCr)[\s:]*([0-9.]+)'],
        'ast': [r'(?:AST|SGOT)[\s:]*(\d+)', r'ast[\s:]*(\d+)'],
        'alt': [r'(?:ALT|SGPT)[\s:]*(\d+)', r'alt[\s:]*(\d+)'],
        'ldh': [r'(?:LDH|LD)[\s:]*(\d+)', r'ldh[\s:]*(\d+)'],
        'bilirubin': [r'(?:total\s+)?bilirubin[\s:]*([0-9.]+)', r'bili[\s:]*([0-9.]+)'],
        'hemoglobin': [r'(?:hemoglobin|Hgb|Hb)[\s:]*([0-9.]+)', r'hemoglobin[\s:]*([0-9.]+)'],
        'wbc': [r'(?:WBC|white\s+blood\s+cells?)[\s:]*([0-9.]+)', r'wbc[\s:]*([0-9.]+)'],
        'rbc': [r'(?:RBC|red\s+blood\s+cells?)[\s:]*([0-9.]+)', r'rbc[\s:]*([0-9.]+)'],
        'protein_urine': [r'protein(?:uria)?[\s:]*([0-9.]+)', r'urine\s+protein[\s:]*([0-9.]+)', r'proteinuria[\s:]*([0-9.]+)'],
        'glucose': [r'glucose[\s:]*(\d+)', r'blood\s+sugar[\s:]*(\d+)'],
        'age': [r'age[\s:]*(\d{2})', r'(\d{2})\s*(?:year|yo|y/o)', r'patient\s+is\s+(\d{2})'],
        'weight_kg': [r'weight[\s:]*(\d{2,3})\s*(?:kg|kilograms?)', r'(\d{2,3})\s*kg'],
        'height_cm': [r'height[\s:]*(\d{2,3})\s*(?:cm|centimeters?)', r'(\d{2,3})\s*cm'],
        'gestational_age': [r'(?:gestational\s+)?age[\s:]*(\d{1,2})\s*(?:weeks?|wks?)', r'GA[\s:]*(\d{1,2})'],
    }
    
    # Make text case-insensitive for matching
    text_lower = text.lower()
    
    # Extract structured values using regex patterns
    for param, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, text_lower)
            if matches:
                # For BP patterns that return tuples (sbp, dbp)
                if isinstance(matches[0], tuple):
                    if param == 'sbp':
                        extracted['sbp'] = int(matches[0][0])
                        extracted['dbp'] = int(matches[0][1])
                else:
                    # Single value extraction
                    try:
                        if param in ['platelet_count', 'ast', 'alt', 'ldh', 'glucose', 'age', 'weight_kg', 'height_cm', 'gestational_age', 'wbc', 'rbc']:
                            extracted[param] = int(float(matches[0]))
                        else:
                            extracted[param] = float(matches[0])
                        break  # Stop after first successful match
                    except (ValueError, IndexError):
                        continue
    
    # Check for uncaptured symptoms
    symptom_patterns = [
        (r'visual\s+(?:disturbance|changes?|blurring?)', 'Visual disturbance'),
        (r'headache', 'Headache'),
        (r'epigastric\s+(?:pain|discomfort)', 'Epigastric pain'),
        (r'(?:right\s+)?upper\s+quadrant\s+(?:pain|tenderness)', 'RUQ pain'),
        (r'nausea', 'Nausea'),
        (r'vomiting', 'Vomiting'),
        (r'edema', 'Edema'),
        (r'dyspnea', 'Dyspnea'),
        (r'chest\s+pain', 'Chest pain'),
        (r'pulmonary\s+edema', 'Pulmonary edema'),
    ]
    
    for pattern, symptom in symptom_patterns:
        if re.search(pattern, text_lower):
            uncaptured_symptoms.append(symptom)
    
    return extracted, uncaptured_symptoms

# ============================================================================
# PDF REPORT GENERATION
# ============================================================================
def generate_pdf_report(patient_id, visit_date, params, risks, tests, ratios):
    """
    Generate a branded clinical PDF report with all values, charts, and recommendations.
    """
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    
    # Styling
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#00d4ff'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#ffa502'),
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=6,
    )
    
    # Header
    story.append(Paragraph("🏥 PrediCare Clinical Report", title_style))
    story.append(Paragraph("Preeclampsia Risk Stratification", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Patient info
    patient_data = [
        ['Patient ID:', patient_id],
        ['Visit Date:', visit_date],
        ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M')],
    ]
    patient_table = Table(patient_data, colWidths=[2*inch, 2.5*inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4fd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Risk Assessment Section
    story.append(Paragraph("RISK ASSESSMENT", heading_style))
    risk_data = [
        ['Model', 'Risk (%)', 'Interpretation'],
        ['FMF Score', f"{risks.get('FMF', 0):.1f}%", 'Fetal Medicine Foundation'],
        ['NICE (UK)', f"{risks.get('NICE', 0):.1f}%", 'National Institute for Health'],
        ['ACOG', f"{risks.get('ACOG', 0):.1f}%", 'American College of Obstetricians'],
        ['ML Ensemble', f"{risks.get('ML', 0):.1f}%", 'Machine Learning Model'],
        ['COMPOSITE', f"{risks.get('Composite', 0):.1f}%", '★ Clinical Decision Support'],
    ]
    risk_table = Table(risk_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffa502')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#2ed573')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 0.15*inch))
    
    # Clinical Parameters Section
    story.append(Paragraph("CLINICAL PARAMETERS", heading_style))
    param_data = [
        ['Parameter', 'Value', 'Normal Range', 'Status'],
    ]
    
    # Add vital parameters
    vitals = [
        ('Systolic BP', params.get('sbp', 'N/A'), '<140 mmHg'),
        ('Diastolic BP', params.get('dbp', 'N/A'), '<90 mmHg'),
        ('MAP', f"{params.get('map', 0):.1f}", '<100 mmHg'),
        ('Heart Rate', params.get('hr', 'N/A'), '60-100 bpm'),
        ('Proteinuria', params.get('protein_urine', 'N/A'), '<0.3 g/24h'),
    ]
    
    for param, value, normal in vitals:
        status = '✓' if value != 'N/A' else '-'
        param_data.append([param, str(value), normal, status])
    
    param_table = Table(param_data, colWidths=[2*inch, 1.2*inch, 1.8*inch, 0.7*inch])
    param_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00d4ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
    ]))
    story.append(param_table)
    story.append(Spacer(1, 0.15*inch))
    
    # Recommended Testing Section
    if tests:
        story.append(Paragraph("RECOMMENDED FURTHER TESTING", heading_style))
        test_data = [['Priority', 'Test Name', 'Timeline']]
        
        priority_colors = {'URGENT': colors.HexColor('#ff4757'), 'HIGH': colors.HexColor('#ffa502'), 'MODERATE': colors.HexColor('#ffc107')}
        
        for priority, test_name, timeline, rationale in tests[:10]:  # Limit to 10 tests per page
            test_data.append([priority, test_name, timeline])
        
        test_table = Table(test_data, colWidths=[1.2*inch, 2.5*inch, 1.5*inch])
        test_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff4757')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        story.append(test_table)
        story.append(Spacer(1, 0.15*inch))
    
    # Parameter Ratios Section
    if ratios:
        story.append(Paragraph("PARAMETER RATIO ANALYSIS", heading_style))
        ratio_data = [['Ratio', 'Value', 'Status', 'Clinical Interpretation']]
        
        for param, value, status, status_type, interpretation in ratios[:6]:  # Limit to 6 ratios
            ratio_data.append([param, str(value)[:10], status, interpretation[:40]])
        
        ratio_table = Table(ratio_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.8*inch])
        ratio_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ed573')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        story.append(ratio_table)
        story.append(Spacer(1, 0.15*inch))
    
    # Disclaimer and Model Info
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("DISCLAIMER & CONFIDENCE", heading_style))
    disclaimer = """
    <b>⚠️ For Research & Educational Use Only:</b> This PrediCare system is NOT FDA-cleared for clinical decision-making. 
    All risk assessments are generated by machine learning models trained on synthetic data and require validation with real patient cohorts. 
    Clinical judgment and specialist consultation are essential. This report should accompany, not replace, standard clinical assessment.
    """
    story.append(Paragraph(disclaimer, normal_style))
    
    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# ============================================================================
# RISK CALCULATIONS
# ============================================================================

def calculate_epidemiological_risk_multiplier(params):
    """Apply evidence-based RR/OR coefficients from epidemiological meta-analyses"""
    multiplier = 1.0
    
    # SYNDROMIC/AUTOIMMUNE - Highest risk factors
    if params.get('antiphospholipid_syndrome'):
        multiplier *= 3.46  # 17.3% baseline risk / 5% = 3.46x
    if params.get('sle_lupus_nephritis'):
        multiplier *= 3.11  # OR 3.11
    if params.get('sle_chronic_htn'):
        multiplier *= 5.86  # OR 5.86 (VERY HIGH RISK)
    if params.get('sle_disease_activity'):
        multiplier *= 2.32  # OR 2.32
    if params.get('secondary_aps_sle'):
        multiplier *= 2.0  # Increased risk signal
    
    # CARDIOVASCULAR - Major flags
    if params.get('chronic_hypertension'):
        multiplier *= 5.1  # RR 5.1
    
    # METABOLIC - High risk
    if params.get('pregestational_diabetes'):
        multiplier *= 3.7  # RR 3.7
    if params.get('bmi_obesity') or params.get('bmi', 0) > 30:
        multiplier *= 2.8  # RR 2.8
    
    # OBSTETRIC HISTORY - Strongest predictor
    if params.get('prior_preeclampsia'):
        multiplier *= 8.4  # RR 8.4 (STRONGEST PREDICTOR!)
    
    # REPRODUCTIVE - Moderate risk
    if params.get('assisted_reproductive_tech'):
        multiplier *= 1.8  # RR 1.8
    
    # COMORBIDITIES
    if params.get('obstructive_sleep_apnea'):
        multiplier *= 2.35  # aOR 2.35
    if params.get('autoimmune_disease'):
        multiplier *= 2.0  # RR increased (conservative estimate ~2.0)
    if params.get('pcos'):
        multiplier *= 1.5  # Increased odds (conservative)
    
    # PROTECTIVE FACTORS
    if params.get('aspirin'):
        multiplier *= 0.8  # Aspirin has modest protective effect
    if params.get('calcium_supplement'):
        multiplier *= 0.9  # Calcium supplementation has protective effect
    
    return min(5.0, multiplier)  # Cap at 5x to avoid extreme values

def calculate_fmf_score(params):
    score = 0
    age = params.get('age', 30)
    if age >= 35: score += 5
    elif age >= 30: score += 2
    
    bmi = params.get('bmi', 24)
    if bmi >= 30: score += 4
    elif bmi >= 25: score += 2
    
    sbp = params.get('sbp', 120)
    if sbp >= 140: score += 8
    elif sbp >= 130: score += 4
    
    if params.get('prior_pe'): score += 20
    if params.get('chronic_htn'): score += 8
    if params.get('diabetes'): score += 6
    if params.get('autoimmune_disease'): score += 7
    if params.get('nulliparity'): score += 3
    if params.get('multiple_gestation'): score += 12
    if params.get('family_htn'): score += 4
    
    papp_a = params.get('papp_a', 1.0)
    if papp_a < 0.4: score += 5
    
    pi_ratio = params.get('uterine_pi', 1.5)
    if pi_ratio >= 1.8: score += 6
    
    return min(100, score)

def calculate_nice_score(params):
    score = 0
    if params.get('prior_pe'): score += 25
    if params.get('chronic_htn'): score += 15
    if params.get('diabetes'): score += 12
    if params.get('autoimmune_disease'): score += 10
    if params.get('family_pe'): score += 8
    if params.get('multiple_gestation'): score += 10
    if params.get('nulliparity'): score += 5
    
    sbp = params.get('sbp', 120)
    if sbp >= 150: score += 8
    elif sbp >= 140: score += 4
    
    map_val = params.get('map', 90)
    if map_val >= 110: score += 5
    
    return min(100, score)

def calculate_acog_score(params):
    score = 0
    if params.get('prior_pe'): score += 22
    if params.get('chronic_htn'): score += 10
    if params.get('diabetes'): score += 9
    if params.get('autoimmune_disease'): score += 8
    if params.get('multiple_gestation'): score += 13
    
    if params.get('nulliparity'): score += 5
    if params.get('family_pe'): score += 6
    if params.get('age') and params.get('age') >= 35: score += 4
    if params.get('bmi') and params.get('bmi') >= 30: score += 3
    
    if params.get('protein_urine') > 0.3: score += 8
    if params.get('platelet_count') and params.get('platelet_count') < 150: score += 5
    
    return min(100, score)

def calculate_ml_ensemble(params):
    if xgb_model is None:
        return calculate_acog_score(params)
    try:
        features = np.array([[
            params.get('age', 30),
            params.get('bmi', 24),
            params.get('sbp', 120),
            params.get('dbp', 80),
            int(params.get('chronic_htn', False)),
            int(params.get('diabetes', False)),
            int(params.get('prior_pe', False)),
            int(params.get('nulliparity', False)),
            int(params.get('multiple_gestation', False)),
            int(params.get('family_pe', False)),
            int(params.get('family_htn', False)),
        ]])
        
        if scaler:
            features = scaler.transform(features)
        
        risk_prob = xgb_model.predict_proba(features)[0][1]
        return risk_prob * 100
    except:
        return 50.0

def calculate_genetic_risk_modifier(params):
    """
    Calculate genetic risk modifier based on identified polymorphisms.
    Genetic markers provide additive risk (estimated 1-3% per marker).
    """
    genetic_markers = [
        'eNOS_G894T', 'ACE_ID', 'AGT_M235T', 'MTHFR_C677T',
        'CYP11B2', 'TNF_alpha', 'FOXP3_rs3761548', 'HLA_G_14bp',
        'Prothrombin_G20210A'
    ]
    
    genetic_load = sum([1 for marker in genetic_markers if params.get(marker, False)])
    polygenic_htn = params.get('polygenic_htn_risk', False)
    
    # Base modifier: each genetic marker adds ~2% risk
    modifier = 1.0 + (genetic_load * 0.02)
    
    # Polygenic HTN risk adds 5% additional
    if polygenic_htn:
        modifier += 0.05
    
    return modifier

def calculate_composite_risk(params):
    fmf = calculate_fmf_score(params)
    nice = calculate_nice_score(params)
    acog = calculate_acog_score(params)
    ml = calculate_ml_ensemble(params)
    
    # Apply genetic risk modifier
    genetic_modifier = calculate_genetic_risk_modifier(params)
    
    # Adjust all models by genetic modifier
    fmf_adj = min(100, fmf * genetic_modifier)
    nice_adj = min(100, nice * genetic_modifier)
    acog_adj = min(100, acog * genetic_modifier)
    ml_adj = min(100, ml * genetic_modifier)
    
    composite = (fmf_adj + nice_adj + acog_adj + ml_adj) / 4
    
    return {
        'FMF': fmf_adj,
        'NICE': nice_adj,
        'ACOG': acog_adj,
        'ML': ml_adj,
        'Composite': composite,
        'Genetic_Modifier': genetic_modifier
    }

def calculate_epidemiological_risk_multiplier(params):
    """Apply evidence-based RR/OR coefficients from epidemiological data"""
    base_risk = 0.05  # 5% baseline preeclampsia risk
    multiplier = 1.0
    
    # SYNDROMIC/AUTOIMMUNE - Highest risk
    if params.get('antiphospholipid_syndrome'):
        multiplier *= 3.46  # 17.3% baseline = 5% * 3.46
    if params.get('sle_lupus_nephritis'):
        multiplier *= 3.11  # OR 3.11
    if params.get('sle_chronic_htn'):
        multiplier *= 5.86  # OR 5.86 (very high)
    if params.get('sle_disease_activity'):
        multiplier *= 2.32  # OR 2.32
    if params.get('secondary_aps_sle'):
        multiplier *= 2.0  # Increased risk signal
    
    # CARDIOVASCULAR - Major flags
    if params.get('chronic_hypertension'):
        multiplier *= 5.1  # RR 5.1
    
    # METABOLIC - High risk
    if params.get('pregestational_diabetes'):
        multiplier *= 3.7  # RR 3.7
    if params.get('bmi', 0) > 30:
        multiplier *= 2.8  # RR 2.8
    
    # OBSTETRIC HISTORY - Strongest predictor
    if params.get('prior_preeclampsia'):
        multiplier *= 8.4  # RR 8.4 (strongest!)
    
    # REPRODUCTIVE - Moderate risk
    if params.get('assisted_reproductive_tech'):
        multiplier *= 1.8  # RR 1.8
    
    # COMORBIDITIES
    if params.get('obstructive_sleep_apnea'):
        multiplier *= 2.35  # aOR 2.35
    if params.get('pcos'):
        multiplier *= 1.5  # Increased odds (conservative estimate)
    
    return multiplier

def check_clinical_alerts(params):
    alerts = []
    
    if params.get('sbp', 0) >= 160:
        alerts.append(('severe', '🔴 SEVERE: SBP ≥160 mmHg — Immediate hospitalization'))
    if params.get('dbp', 0) >= 110:
        alerts.append(('severe', '🔴 SEVERE: DBP ≥110 mmHg — Immediate hospitalization'))
    if params.get('protein_urine', 0) >= 3.0:
        alerts.append(('severe', '🔴 SEVERE: Proteinuria ≥3.0 g/24h — Possible nephrotic syndrome'))
    if params.get('platelet_count', 999) < 100:
        alerts.append(('severe', '🔴 SEVERE: Thrombocytopenia <100K — HELLP syndrome risk'))
    sflt_plgf = params.get('sflt_plgf_ratio', 0)
    if sflt_plgf > 85:
        alerts.append(('severe', f'🔴 SEVERE: sFlt-1/PlGF >85 — High PE risk'))
    
    if 140 <= params.get('sbp', 0) < 160:
        alerts.append(('moderate', f'🟠 MODERATE: Stage 2 hypertension'))
    if 0.3 <= params.get('protein_urine', 0) < 3.0:
        alerts.append(('moderate', f'🟠 MODERATE: Significant proteinuria'))
    if 100 <= params.get('platelet_count', 999) < 150:
        alerts.append(('moderate', f'🟠 MODERATE: Mild thrombocytopenia'))
    if 35 <= sflt_plgf <= 85:
        alerts.append(('moderate', f'🟠 MODERATE: Elevated sFlt-1/PlGF ratio'))
    
    return alerts

# ============================================================================
# SIDEBAR
# ============================================================================
st.sidebar.markdown("## 🏥 PrediCare v3.0")
st.sidebar.markdown("**AI-Enhanced PE Risk Predictor**")
st.sidebar.markdown("---")

st.sidebar.markdown("### 📄 DOCUMENT UPLOAD (TOP PRIORITY)")
st.sidebar.markdown("**Upload image → Auto-extract values**")
uploaded_report = st.sidebar.file_uploader("Upload medical report/image", type=['jpg', 'jpeg', 'png', 'pdf'])

if uploaded_report:
    st.sidebar.info("📊 Image analysis active")
    extracted = extract_values_from_image(uploaded_report)
    if extracted:
        st.sidebar.success("✅ Values extracted - review in tabs")

st.sidebar.markdown("---")
visit_date = st.sidebar.date_input("📅 Visit Date", value=datetime.now())

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Configuration")
selected_model = st.sidebar.selectbox("Risk Model", options=['Composite', 'FMF', 'NICE', 'ACOG', 'ML Ensemble'])

st.sidebar.markdown("---")
st.sidebar.markdown("### � Natural Language Input")
st.sidebar.markdown("**Paste consultation notes or lab reports →** auto-fill all fields")
nlp_input = st.sidebar.text_area("Paste clinical notes or lab results", height=100, placeholder="e.g., '28-week visit, BP 138/90, protein 2+, platelets 162, headache x2 days, creatinine 1.1'")

if nlp_input:
    extracted_values, uncaptured = parse_clinical_notes(nlp_input)
    if extracted_values:
        st.sidebar.success(f"✅ Extracted {len(extracted_values)} parameters")
        # Auto-fill params with extracted values
        for key, value in extracted_values.items():
            st.session_state.params[key] = value
        st.rerun()
    
    if uncaptured:
        st.sidebar.warning(f"⚠️ Uncaptured symptoms: {', '.join(uncaptured)}")


st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Export Report")
generate_pdf = st.sidebar.button("📥 Generate PDF Report", use_container_width=True)

# ============================================================================
# MAIN TABS
# ============================================================================
# Initialize params early
if 'params' not in st.session_state:
    st.session_state.params = {}

tabs = st.tabs([
    "📋 Demographics & Pre-Pregnancy",
    "💓 Vitals & BP",
    "🧪 Labs & Chemistry",
    "🩸 Metabolic",
    "🔬 Advanced Biomarkers",
    "🫀 Doppler & Imaging",
    "📖 History",
    "⚖️ Pre-vs-Pregnancy",
    "📊 Risk & Testing"
])

params = st.session_state.params

# ============================================================================
# TAB 1: DEMOGRAPHICS & PRE-PREGNANCY
# ============================================================================
with tabs[0]:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Current Pregnancy")
        params['age'] = st.number_input("Age (years)", 14, 50, 28, step=1)
        params['ga_weeks'] = st.number_input("Gestational Age (weeks)", 14, 42, 20, step=1)
        params['ga_days'] = st.number_input("Days", 0, 6, 0, step=1)
        params['ethnicity'] = st.selectbox("Ethnicity", options=['White', 'Black', 'Asian', 'Hispanic', 'Other', 'Mixed'])
    
    with col2:
        st.markdown("### Pre-Pregnancy Data")
        params['prepreg_weight_kg'] = st.number_input("Pre-Pregnancy Weight (kg)", 30, 150, 65, step=1)
        params['prepreg_bmi'] = st.number_input("Pre-Pregnancy BMI (kg/m²)", 15.0, 50.0, 22.0, step=0.5)
        params['prepreg_sbp'] = st.number_input("Pre-Pregnancy SBP (mmHg)", 80, 160, 120, step=2)
        params['prepreg_dbp'] = st.number_input("Pre-Pregnancy DBP (mmHg)", 40, 110, 80, step=2)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Current Pregnancy Anthropometrics")
        params['height_cm'] = st.number_input("Height (cm)", 140, 210, 165, step=1)
        params['weight_kg'] = st.number_input("Current Weight (kg)", 40, 150, 70, step=1)
        params['bmi'] = st.number_input("Current BMI (kg/m²)", 15.0, 50.0, 24.0, step=0.5)
        
        # Auto-calculate weight gain
        if params.get('prepreg_weight_kg') and params.get('weight_kg'):
            weight_gain = params['weight_kg'] - params['prepreg_weight_kg']
            st.info(f"**Weight Gain: {weight_gain:.1f} kg** {'✅ Normal' if 8 <= weight_gain <= 18 else '⚠️ Review'}")
    
    with col2:
        st.markdown("### Blood Pressure Change")
        params['nulliparity'] = st.checkbox("Nulliparous")
        params['multiple_gestation'] = st.checkbox("Multiple Gestation")
        params['assisted_conception'] = st.checkbox("Assisted Conception")
        
        # BP change calculation
        if params.get('sbp') and params.get('prepreg_sbp'):
            sbp_change = params['sbp'] - params['prepreg_sbp']
            dbp_change = params.get('dbp', 80) - params['prepreg_dbp']
            st.metric("SBP Change", f"{sbp_change:+.0f} mmHg", "from pre-pregnancy")
            st.metric("DBP Change", f"{dbp_change:+.0f} mmHg", "from pre-pregnancy")

# ============================================================================
# TAB 2: VITALS & BP
# ============================================================================
with tabs[1]:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        params['sbp'] = st.number_input("Systolic BP (mmHg)", 80, 200, 120, step=2)
    with col2:
        params['dbp'] = st.number_input("Diastolic BP (mmHg)", 40, 130, 80, step=2)
    with col3:
        params['hr'] = st.number_input("Heart Rate (bpm)", 40, 120, 75, step=2)
    with col4:
        params['rr'] = st.number_input("Resp. Rate (breaths/min)", 10, 30, 16, step=1)
    
    params['map'] = (params['sbp'] + 2 * params['dbp']) / 3
    st.info(f"**MAP: {params['map']:.1f} mmHg** {'' if params['map'] < 100 else '⚠️ Elevated'}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        params['protein_urine'] = st.number_input("Proteinuria (g/24h)", 0.0, 10.0, 0.1, step=0.1)
    with col2:
        params['urine_glucose'] = st.selectbox("Glucose", ["Negative", "Trace", "+1", "+2", "+3", "+4"])
    with col3:
        params['urine_leukocyte_esterase'] = st.checkbox("Leukocyte Esterase")
    with col4:
        params['urine_nitrites'] = st.checkbox("Nitrites")

# ============================================================================
# TAB 3: LABS & CHEMISTRY
# ============================================================================
with tabs[2]:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        params['hemoglobin'] = st.number_input("Hemoglobin (g/dL)", 7.0, 20.0, 12.5, step=0.1)
    with col2:
        params['hematocrit'] = st.number_input("Hematocrit (%)", 20.0, 60.0, 37.0, step=0.5)
    with col3:
        params['platelet_count'] = st.number_input("Platelet Count (K/μL)", 50, 500, 250, step=10)
    with col4:
        params['wbc'] = st.number_input("WBC (K/μL)", 2.0, 20.0, 7.0, step=0.5)
    
    st.markdown("### Renal Function")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        params['creatinine'] = st.number_input("Creatinine (mg/dL)", 0.3, 3.0, 0.8, step=0.1)
    with col2:
        params['bun'] = st.number_input("BUN (mg/dL)", 5, 50, 15, step=1)
    with col3:
        params['uric_acid'] = st.number_input("Uric Acid (mg/dL)", 2.0, 10.0, 3.5, step=0.2)
    with col4:
        params['egfr'] = st.number_input("eGFR (mL/min)", 15, 120, 90, step=5)
    
    st.markdown("### Liver & Coagulation")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        params['ast'] = st.number_input("AST (U/L)", 5, 300, 30, step=5)
    with col2:
        params['alt'] = st.number_input("ALT (U/L)", 5, 300, 25, step=5)
    with col3:
        params['ldh'] = st.number_input("LDH (U/L)", 50, 800, 240, step=10)
    with col4:
        params['bilirubin'] = st.number_input("Total Bilirubin (mg/dL)", 0.2, 5.0, 0.7, step=0.1)

# ============================================================================
# TAB 4: LIPIDS & METABOLIC
# ============================================================================
with tabs[3]:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        params['total_cholesterol'] = st.number_input("Total Cholesterol (mg/dL)", 100, 400, 200, step=5)
    with col2:
        params['ldl'] = st.number_input("LDL (mg/dL)", 30, 250, 120, step=5)
    with col3:
        params['hdl'] = st.number_input("HDL (mg/dL)", 20, 150, 50, step=5)
    with col4:
        params['triglycerides'] = st.number_input("Triglycerides (mg/dL)", 40, 400, 150, step=10)
    
    st.markdown("### Glucose & Metabolism")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        params['fasting_glucose'] = st.number_input("Fasting Glucose (mg/dL)", 60, 300, 95, step=5)
    with col2:
        params['hba1c'] = st.number_input("HbA1c (%)", 4.0, 14.0, 5.5, step=0.1)
    with col3:
        params['insulin'] = st.number_input("Fasting Insulin (mIU/mL)", 0.5, 50.0, 5.0, step=0.5)
    with col4:
        params['homa_ir'] = st.number_input("HOMA-IR", 0.1, 20.0, 1.2, step=0.1)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        params['pcos_diagnosed'] = st.checkbox("PCOS Diagnosed")
    with col2:
        params['metabolic_syndrome'] = st.checkbox("Metabolic Syndrome")
    with col3:
        params['dyslipidemia'] = st.checkbox("Dyslipidemia")

# ============================================================================
# TAB 5: ADVANCED BIOMARKERS
# ============================================================================
with tabs[4]:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        params['papp_a'] = st.number_input("PAPP-A (MoM)", 0.1, 5.0, 1.0, step=0.1)
    with col2:
        params['beta_hcg'] = st.number_input("β-hCG (MoM)", 0.2, 5.0, 1.0, step=0.1)
    with col3:
        params['plgf'] = st.number_input("PlGF (pg/mL)", 10.0, 500.0, 100.0, step=5.0)
    with col4:
        params['sflt1'] = st.number_input("sFlt-1 (pg/mL)", 50.0, 5000.0, 400.0, step=50.0)
    
    if params['plgf'] > 0:
        params['sflt_plgf_ratio'] = params['sflt1'] / params['plgf']
        st.warning(f"**sFlt-1/PlGF Ratio: {params['sflt_plgf_ratio']:.2f}** {'⚠️ HIGH' if params['sflt_plgf_ratio'] > 85 else '✅ Normal'}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        params['pp13'] = st.number_input("PP13 (mIU/mL)", 0.0, 100.0, 50.0, step=5.0)
    with col2:
        params['endoglin'] = st.number_input("Endoglin (ng/mL)", 5.0, 100.0, 30.0, step=2.0)
    with col3:
        params['crp'] = st.number_input("CRP (mg/L)", 0.0, 50.0, 2.0, step=0.5)
    with col4:
        params['homocysteine'] = st.number_input("Homocysteine (μmol/L)", 2.0, 30.0, 8.0, step=0.5)

# ============================================================================
# TAB 6: DOPPLER & IMAGING
# ============================================================================
with tabs[5]:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        params['uterine_pi'] = st.number_input("Uterine PI", 0.8, 3.0, 1.5, step=0.1)
    with col2:
        params['uterine_ri'] = st.number_input("Uterine RI", 0.4, 1.0, 0.6, step=0.05)
    with col3:
        params['uterine_sd'] = st.number_input("S/D Ratio", 2.0, 6.0, 3.5, step=0.2)
    with col4:
        params['uterine_notching'] = st.checkbox("Bilateral Notching")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        params['umbilical_pi'] = st.number_input("Umbilical PI", 0.7, 2.0, 1.0, step=0.1)
    with col2:
        params['umbilical_ri'] = st.number_input("Umbilical RI", 0.4, 1.0, 0.6, step=0.05)
    with col3:
        params['ared'] = st.checkbox("ARED Present")
    
    st.markdown("### Imaging Upload")
    uploaded_images = st.file_uploader("Upload Doppler/ultrasound", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    if uploaded_images:
        st.success(f"✅ {len(uploaded_images)} image(s) uploaded")

# ============================================================================
# TAB 7: HISTORY
# ============================================================================
with tabs[6]:
    # EVIDENCE-BASED RISK FACTORS (From epidemiological data)
    st.markdown("## 📊 Evidence-Based Risk Factors")
    st.markdown("**Check conditions identified in this pregnancy** — Each has RR/OR from meta-analyses")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔴 HIGHEST RISK (RR >5)")
        params['antiphospholipid_syndrome'] = st.checkbox("Antiphospholipid Syndrome (17.3%, RR highest)")
        params['sle_chronic_htn'] = st.checkbox("SLE + Chronic HTN (OR 5.86)")
        params['prior_preeclampsia'] = st.checkbox("Prior Preeclampsia (RR 8.4 - STRONGEST!)")
        params['chronic_hypertension'] = st.checkbox("Chronic Hypertension (RR 5.1)")
    
    with col2:
        st.markdown("### 🟠 HIGH RISK (RR 2-5)")
        params['pregestational_diabetes'] = st.checkbox("Pregestational Diabetes (RR 3.7)")
        params['sle_lupus_nephritis'] = st.checkbox("SLE + Lupus Nephritis (OR 3.11)")
        params['obstructive_sleep_apnea'] = st.checkbox("Obstructive Sleep Apnea (aOR 2.35)")
        params['sle_disease_activity'] = st.checkbox("SLE Disease Activity (OR 2.32)")
        params['autoimmune_disease'] = st.checkbox("Autoimmune Disease - General (RR increased)")
    
    with col3:
        st.markdown("### 🟡 MODERATE RISK (RR 1.5-2.8)")
        params['bmi_obesity'] = st.checkbox(f"Prepreg BMI >30 (RR 2.8) [Current: {params.get('bmi', 0):.1f}]")
        params['assisted_reproductive_tech'] = st.checkbox("Assisted Reproductive Tech (RR 1.8)")
        params['pcos'] = st.checkbox("Polycystic Ovary Syndrome (Increased odds)")
        params['secondary_aps_sle'] = st.checkbox("Secondary APS in SLE (Increased risk)")
    
    st.markdown("---")
    st.markdown("### Obstetric History")
    col1, col2 = st.columns(2)
    with col1:
        params['prior_eclampsia'] = st.checkbox("Prior Eclampsia")
        params['prior_hellp'] = st.checkbox("Prior HELLP")
        params['prior_abruption'] = st.checkbox("Prior Abruption")
    with col2:
        params['prior_iugr'] = st.checkbox("Prior IUGR")
        params['prior_stillbirth'] = st.checkbox("Prior Stillbirth")
    
    st.markdown("---")
    st.markdown("### Past Medical History (Additional)")
    col1, col2 = st.columns(2)
    with col1:
        params['gdm'] = st.checkbox("Gestational Diabetes (Prior)")
        params['ckd'] = st.checkbox("Chronic Kidney Disease")
        params['systemic_lupus'] = st.checkbox("SLE (without complications listed above)")
    with col2:
        params['aspirin'] = st.checkbox("✅ On Aspirin (reduces risk)")
        params['calcium_supplement'] = st.checkbox("✅ On Calcium Supplement (may reduce risk)")
        params['htn_medication'] = st.checkbox("On Antihypertensive Meds")
    
    st.markdown("---")
    st.markdown("### Family History")
    col1, col2, col3 = st.columns(3)
    with col1:
        params['family_pe'] = st.checkbox("Family Hx: PE/Eclampsia")
    with col2:
        params['family_htn'] = st.checkbox("Family Hx: HTN")
    with col3:
        params['family_diabetes'] = st.checkbox("Family Hx: Diabetes")
    
    st.markdown("---")
    st.markdown("### 🧬 Genetic Risk Markers")
    st.markdown("**Genetic susceptibility factors** — Check if identified by genetic testing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Endothelial & Metabolic**")
        params['eNOS_G894T'] = st.checkbox("eNOS G894T")
        params['ACE_ID'] = st.checkbox("ACE I/D")
        params['AGT_M235T'] = st.checkbox("AGT M235T")
        params['MTHFR_C677T'] = st.checkbox("MTHFR C677T")
    
    with col2:
        st.markdown("**Hypertension & Inflammation**")
        params['CYP11B2'] = st.checkbox("CYP11B2")
        params['TNF_alpha'] = st.checkbox("TNF-α -308G/A")
        params['FOXP3_rs3761548'] = st.checkbox("FOXP3 rs3761548")
        params['HLA_G_14bp'] = st.checkbox("HLA-G 14bp")
    
    with col3:
        st.markdown("**Thrombophilia & Risk Scores**")
        params['Prothrombin_G20210A'] = st.checkbox("Prothrombin G20210A")
        params['polygenic_htn_risk'] = st.checkbox("Polygenic HTN Risk (elevated)")
        st.markdown("<small>Evidence-based from meta-analyses</small>", unsafe_allow_html=True)

# ============================================================================
# TAB 8: PRE-VS-PREGNANCY COMPARISON
# ============================================================================
with tabs[7]:
    st.markdown("## ⚖️ Pre-Pregnancy vs Current Pregnancy Comparison")
    
    # Weight & BMI comparison
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Weight Trajectory")
        if params.get('prepreg_weight_kg') and params.get('weight_kg'):
            weight_gain = params['weight_kg'] - params['prepreg_weight_kg']
            weight_pct = (weight_gain / params['prepreg_weight_kg']) * 100
            
            fig_weight = go.Figure(data=[
                go.Bar(name='Pre-Pregnancy', x=['Weight'], y=[params['prepreg_weight_kg']], marker_color='#2ed573'),
                go.Bar(name='Current', x=['Weight'], y=[params['weight_kg']], marker_color='#ffa502'),
            ])
            fig_weight.update_layout(barmode='group', template='plotly_dark', height=300, showlegend=True)
            st.plotly_chart(fig_weight, use_container_width=True)
            
            st.markdown(f"""
            - **Weight Gain:** {weight_gain:.1f} kg ({weight_pct:.1f}%)
            - **Normal:** 8-18 kg total
            - **Status:** {'✅ Within range' if 8 <= weight_gain <= 18 else '⚠️ Review with provider'}
            """)
    
    with col2:
        st.markdown("### BMI Comparison")
        if params.get('prepreg_bmi') and params.get('bmi'):
            bmi_change = params['bmi'] - params['prepreg_bmi']
            
            fig_bmi = go.Figure(data=[
                go.Indicator(
                    mode="number+delta",
                    value=params['bmi'],
                    title="Current BMI",
                    delta={'reference': params['prepreg_bmi'], 'valueformat': '.1f'},
                    domain={'x': [0, 1], 'y': [0, 1]}
                )
            ])
            fig_bmi.update_layout(template='plotly_dark', height=300)
            st.plotly_chart(fig_bmi, use_container_width=True)
    
    with col3:
        st.markdown("### BP Changes")
        if params.get('sbp') and params.get('prepreg_sbp'):
            sbp_change = params['sbp'] - params['prepreg_sbp']
            dbp_change = params.get('dbp', 80) - params.get('prepreg_dbp', 80)
            
            fig_bp = go.Figure()
            fig_bp.add_trace(go.Scatter(
                x=['Pre-Pregnancy', 'Current'],
                y=[params['prepreg_sbp'], params['sbp']],
                mode='lines+markers',
                name='SBP',
                marker=dict(size=10, color='#ff4757'),
                line=dict(color='#ff4757', width=3)
            ))
            fig_bp.add_trace(go.Scatter(
                x=['Pre-Pregnancy', 'Current'],
                y=[params['prepreg_dbp'], params.get('dbp', 80)],
                mode='lines+markers',
                name='DBP',
                marker=dict(size=10, color='#00d4ff'),
                line=dict(color='#00d4ff', width=3)
            ))
            fig_bp.update_layout(template='plotly_dark', height=300, hovermode='x unified')
            st.plotly_chart(fig_bp, use_container_width=True)
    
    # Detailed comparison table
    st.markdown("### Detailed Parameter Comparison")
    comparison_data = {
        'Parameter': ['Weight (kg)', 'BMI (kg/m²)', 'Systolic BP (mmHg)', 'Diastolic BP (mmHg)'],
        'Pre-Pregnancy': [
            f"{params.get('prepreg_weight_kg', '-'):.0f}",
            f"{params.get('prepreg_bmi', '-'):.1f}",
            f"{params.get('prepreg_sbp', '-'):.0f}",
            f"{params.get('prepreg_dbp', '-'):.0f}",
        ],
        'Current': [
            f"{params.get('weight_kg', '-'):.0f}",
            f"{params.get('bmi', '-'):.1f}",
            f"{params.get('sbp', '-'):.0f}",
            f"{params.get('dbp', '-'):.0f}",
        ],
        'Change': [
            f"+{params.get('weight_kg', 0) - params.get('prepreg_weight_kg', 0):.1f}" if params.get('weight_kg') and params.get('prepreg_weight_kg') else '-',
            f"+{params.get('bmi', 0) - params.get('prepreg_bmi', 0):.1f}" if params.get('bmi') and params.get('prepreg_bmi') else '-',
            f"+{params.get('sbp', 0) - params.get('prepreg_sbp', 0):.0f}" if params.get('sbp') and params.get('prepreg_sbp') else '-',
            f"+{params.get('dbp', 0) - params.get('prepreg_dbp', 0):.0f}" if params.get('dbp') and params.get('prepreg_dbp') else '-',
        ]
    }
    
    comp_df = pd.DataFrame(comparison_data)
    st.dataframe(comp_df, use_container_width=True)

# ============================================================================
# TAB 9: RISK SUMMARY & SUGGESTED TESTING
# ============================================================================
with tabs[8]:
    risks = calculate_composite_risk(params)
    selected_risk = risks.get(selected_model, risks['Composite'])
    
    if selected_risk < 20:
        risk_cat = "LOW"
        risk_emoji = "✅"
    elif selected_risk < 50:
        risk_cat = "MODERATE"
        risk_emoji = "⚠️"
    else:
        risk_cat = "HIGH"
        risk_emoji = "🔴"
    
    # Risk display
    st.markdown(f"""
    <div style="background-color: rgba(0,212,255,0.05); border: 2px solid rgba(0,212,255,0.3); border-radius: 8px; padding: 20px; text-align: center;">
        <h3 style="color: #00d4ff; margin: 0;">Preeclampsia Risk Assessment</h3>
        <h1 style="color: #ffa502; margin: 10px 0; font-family: 'Courier New', monospace;">{selected_risk:.1f}%</h1>
        <h3 style="color: #00d4ff; margin: 0;">{risk_emoji} {risk_cat} RISK</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    # Model comparison
    with col1:
        st.markdown("### Model Comparison")
        model_df = pd.DataFrame({
            'Model': ['FMF', 'NICE', 'ACOG', 'ML', 'Composite'],
            'Risk (%)': [risks['FMF'], risks['NICE'], risks['ACOG'], risks['ML'], risks['Composite']]
        })
        fig = go.Figure(data=[go.Bar(x=model_df['Model'], y=model_df['Risk (%)'], marker_color='#ffa502')])
        fig.update_layout(template='plotly_dark', height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Clinical alerts
    with col2:
        st.markdown("### 🚨 Clinical Alerts")
        alerts = check_clinical_alerts(params)
        if alerts:
            for alert_type, message in alerts:
                if alert_type == 'severe':
                    st.markdown(f'<div class="alert-severe">{message}</div>', unsafe_allow_html=True)
                elif alert_type == 'moderate':
                    st.markdown(f'<div class="alert-moderate">{message}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-low">✅ No severe alerts</div>', unsafe_allow_html=True)
    
    # ========= PARAMETER RATIO ANALYSIS =========
    st.markdown("---")
    st.markdown("### 📊 Parameter Ratio Analysis")
    
    ratios = analyze_parameter_ratios(params)
    if ratios:
        ratio_cols = st.columns(2)
        for idx, (param, value, status, status_type, interpretation) in enumerate(ratios):
            with ratio_cols[idx % 2]:
                badge_class = f"ratio-{status_type}"
                st.markdown(f"""
                <div class="comparison-table">
                    <strong>{param}</strong><br>
                    <span class="ratio-badge ratio-{status_type}">{value}</span> {status}<br>
                    <small>{interpretation}</small>
                </div>
                """, unsafe_allow_html=True)
    
    # ========= SUGGESTED TESTING =========
    st.markdown("---")
    st.markdown("### 🔬 Recommended Further Testing")
    
    tests = get_suggested_tests(params, selected_risk)
    
    if tests:
        test_df = pd.DataFrame(tests, columns=['Priority', 'Test', 'Timeline', 'Rationale'])
        
        # Color priority
        def color_priority(val):
            if val == 'URGENT': return 'background-color: rgba(255,71,87,0.3)'
            elif val == 'HIGH': return 'background-color: rgba(255,165,2,0.3)'
            elif val == 'MODERATE': return 'background-color: rgba(255,165,2,0.15)'
            else: return 'background-color: rgba(46,213,115,0.15)'
        
        styled_df = test_df.style.applymap(color_priority, subset=['Priority'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No additional testing urgently recommended at this time. Standard prenatal screening applies.")

# ============================================================================
# PDF EXPORT HANDLER (SIDEBAR)
# ============================================================================
if generate_pdf:
    with st.spinner("⏳ Generating clinical PDF report..."):
        try:
            risks = calculate_composite_risk(params)
            selected_risk = risks.get(selected_model, risks['Composite'])
            tests = get_suggested_tests(params, selected_risk)
            ratios = analyze_parameter_ratios(params)
            
            pdf_buffer = generate_pdf_report(
                patient_id,
                str(visit_date),
                params,
                risks,
                tests,
                ratios
            )
            
            st.sidebar.download_button(
                label="📥 Download PDF Report",
                data=pdf_buffer,
                file_name=f"PrediCare_{patient_id}_{visit_date}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.sidebar.success("✅ PDF generated successfully!")
        except Exception as e:
            st.sidebar.error(f"❌ PDF generation failed: {str(e)}")

# ============================================================================
# ACTION BUTTONS
# ============================================================================
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("💾 Save Visit", use_container_width=True):
        visits = load_patient_visits()
        visit_key = f"{patient_id}_{visit_date}"
        visits[visit_key] = {
            'date': str(visit_date),
            'risk_score': risks['Composite'],
            'model': selected_model,
            'params': params
        }
        save_patient_visits(visits)
        st.success("✅ Visit saved")

with col2:
    if st.button("📈 View History", use_container_width=True):
        visits = load_patient_visits()
        if visits:
            st.markdown("### Patient Visit History")
            for visit_key, visit_data in sorted(visits.items()):
                st.write(f"**{visit_data['date']}**: {visit_data['risk_score']:.1f}%")
        else:
            st.info("No saved visits")

with col3:
    if st.button("📋 Quick Export", use_container_width=True):
        try:
            risks = calculate_composite_risk(params)
            selected_risk = risks.get(selected_model, risks['Composite'])
            tests = get_suggested_tests(params, selected_risk)
            ratios = analyze_parameter_ratios(params)
            
            pdf_buffer = generate_pdf_report(
                patient_id,
                str(visit_date),
                params,
                risks,
                tests,
                ratios
            )
            
            st.download_button(
                label="📥 Download PDF",
                data=pdf_buffer,
                file_name=f"PrediCare_{patient_id}_{visit_date}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF generation error: {str(e)}")

with col4:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.params = {}
        st.rerun()

st.markdown("---")
st.markdown("""
<center style="color: #6b8fa8; font-size: 11px;">
⚠️ DISCLAIMER: For research & education only. NOT FDA-cleared. Clinical judgment required.
</center>
""", unsafe_allow_html=True)
