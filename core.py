import os
import json
import re
from io import BytesIO
from datetime import datetime

import numpy as np
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

# Globals for ML models (can be assigned by web_app after loading)
xgb_model = None
lr_model = None
scaler = None

# ------------------------
# OCR / Image extraction
# ------------------------
def extract_values_from_image(image_file):
    """
    Simulate OCR/image analysis from uploaded medical report.
    In production, integrate with a proper OCR (Tesseract) or an LLM + vision API.
    Returns a dict of extracted numeric values.
    """
    try:
        # image_file can be a FileStorage or bytes-like
        if hasattr(image_file, 'read'):
            img = Image.open(image_file)
        else:
            img = Image.open(BytesIO(image_file))

        # Simulated extraction (randomized for demo)
        extracted = {
            'sbp': int(np.random.randint(110, 160)),
            'dbp': int(np.random.randint(70, 110)),
            'platelet_count': int(np.random.randint(100, 350)),
            'creatinine': float(np.round(np.random.uniform(0.5, 1.5), 2)),
            'ast': int(np.random.randint(20, 80)),
            'alt': int(np.random.randint(15, 70)),
            'protein_urine': float(np.round(np.random.uniform(0.0, 1.0), 2)),
            'hemoglobin': float(np.round(np.random.uniform(10.0, 15.0), 1)),
        }
        return extracted
    except Exception as e:
        # Return empty dict on failure
        return {}

# ------------------------
# Notes parsing
# ------------------------
def parse_clinical_notes(text):
    """
    Parse free-text clinical notes and extract structured parameters.
    Returns (extracted_dict, uncaptured_symptoms_list).
    """
    extracted = {}
    uncaptured_symptoms = []

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

    text_lower = text.lower()

    for param, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, text_lower)
            if matches:
                if isinstance(matches[0], tuple):
                    if param == 'sbp':
                        extracted['sbp'] = int(matches[0][0])
                        extracted['dbp'] = int(matches[0][1])
                else:
                    try:
                        if param in ['platelet_count', 'ast', 'alt', 'ldh', 'glucose', 'age', 'weight_kg', 'height_cm', 'gestational_age', 'wbc', 'rbc']:
                            extracted[param] = int(float(matches[0]))
                        else:
                            extracted[param] = float(matches[0])
                        break
                    except (ValueError, IndexError):
                        continue

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

# ------------------------
# Patient visits persistence
# ------------------------
VISITS_FILE = 'patient_visits.json'

def load_patient_visits():
    if os.path.exists(VISITS_FILE):
        with open(VISITS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_patient_visits(visits):
    with open(VISITS_FILE, 'w') as f:
        json.dump(visits, f, indent=2, default=str)

# ------------------------
# Suggested tests & ratios
# ------------------------
def get_suggested_tests(params, risk_score):
    tests = []
    if risk_score >= 50:
        tests.append(("URGENT", "Repeat BP monitoring", "Within 1 week", "Confirm hypertension diagnosis"))
        tests.append(("URGENT", "24-hour urine protein", "Within 3 days", "Assess proteinuria severity"))
        tests.append(("URGENT", "Platelet count + LFTs", "Within 3 days", "Screen for HELLP syndrome"))
        if not params.get('sflt1'):
            tests.append(("HIGH", "sFlt-1/PlGF ratio", "Within 1 week", "Angiogenic biomarker assessment"))
    if 20 <= risk_score < 50:
        tests.append(("MODERATE", "BP monitoring", "Weekly", "Trend assessment"))
        tests.append(("MODERATE", "Urine protein check", "Every 2 weeks", "Rule out proteinuria"))
        if params.get('ga_weeks', 0) >= 16 and not params.get('uterine_pi'):
            tests.append(("MODERATE", "Uterine artery Doppler", "Within 2 weeks", "Early PE detection"))
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
    if risk_score < 20 and not params.get('papp_a'):
        tests.append(("ROUTINE", "PAPP-A (if <13+6 weeks)", "Standard first-trimester screening", "Baseline risk assessment"))
    return tests

def analyze_parameter_ratios(params):
    analysis = []
    # reuse logic from app.py (simplified for web)
    if params.get('sbp', 0) > 0 and params.get('dbp', 0) > 0:
        ratio = params['sbp'] / params['dbp']
        if ratio > 2.0:
            analysis.append(("SBP/DBP Ratio", f"{ratio:.2f}", "Normal", "normal", f"Ratio {ratio:.2f} indicates balanced pressure (normal ~1.5)"))
        elif 1.3 <= ratio <= 2.0:
            analysis.append(("SBP/DBP Ratio", f"{ratio:.2f}", "Normal", "normal", "Physiologic blood pressure pattern"))
        else:
            analysis.append(("SBP/DBP Ratio", f"{ratio:.2f}", "Concern", "concern", "Unusual pattern - verify measurement"))
    # additional ratios can be computed similarly
    return analysis

# ------------------------
# Risk calculators (simplified versions ported from app.py)
# ------------------------

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
    if params.get('protein_urine', 0) > 0.3: score += 8
    if params.get('platelet_count') and params.get('platelet_count') < 150: score += 5
    return min(100, score)


def calculate_ml_ensemble(params):
    global xgb_model, scaler
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
        return float(risk_prob * 100)
    except Exception:
        return 50.0


def calculate_genetic_risk_modifier(params):
    genetic_markers = [
        'eNOS_G894T', 'ACE_ID', 'AGT_M235T', 'MTHFR_C677T',
        'CYP11B2', 'TNF_alpha', 'FOXP3_rs3761548', 'HLA_G_14bp',
        'Prothrombin_G20210A'
    ]
    genetic_load = sum([1 for marker in genetic_markers if params.get(marker, False)])
    polygenic_htn = params.get('polygenic_htn_risk', False)
    modifier = 1.0 + (genetic_load * 0.02)
    if polygenic_htn:
        modifier += 0.05
    return modifier


def calculate_composite_risk(params):
    fmf = calculate_fmf_score(params)
    nice = calculate_nice_score(params)
    acog = calculate_acog_score(params)
    ml = calculate_ml_ensemble(params)
    genetic_modifier = calculate_genetic_risk_modifier(params)
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

# ------------------------
# Clinical alerts
# ------------------------

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

# ------------------------
# PDF generation
# ------------------------

def generate_pdf_report(patient_id, visit_date, params, risks, tests, ratios):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#10b981'), spaceAfter=6, spaceBefore=12, fontName='Helvetica-Bold')
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, textColor=colors.black, spaceAfter=6)

    story.append(Paragraph("🏥 PrediCare Clinical Report", title_style))
    story.append(Paragraph("Preeclampsia Risk Stratification", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    patient_data = [
        ['Patient ID:', patient_id],
        ['Visit Date:', visit_date],
        ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M')],
    ]
    patient_table = Table(patient_data, colWidths=[2*inch, 2.5*inch])
    patient_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4fd')), ('TEXTCOLOR', (0, 0), (-1, -1), colors.black), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 8), ('GRID', (0, 0), (-1, -1), 1, colors.grey)]))
    story.append(patient_table)
    story.append(Spacer(1, 0.2*inch))

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
    risk_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, 0), 10), ('GRID', (0, 0), (-1, -1), 1, colors.grey)]))
    story.append(risk_table)
    story.append(Spacer(1, 0.15*inch))

    # Add clinical parameters (limited set)
    story.append(Paragraph("CLINICAL PARAMETERS", heading_style))
    param_data = [['Parameter', 'Value', 'Normal Range', 'Status']]
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
    param_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)]))
    story.append(param_table)
    story.append(Spacer(1, 0.15*inch))

    # Recommended tests
    if tests:
        story.append(Paragraph("RECOMMENDED FURTHER TESTING", heading_style))
        test_data = [['Priority', 'Test Name', 'Timeline']]
        for priority, test_name, timeline, rationale in tests[:10]:
            test_data.append([priority, test_name, timeline])
        test_table = Table(test_data, colWidths=[1.2*inch, 2.5*inch, 1.5*inch])
        test_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff4757')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)]))
        story.append(test_table)
        story.append(Spacer(1, 0.15*inch))

    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer
