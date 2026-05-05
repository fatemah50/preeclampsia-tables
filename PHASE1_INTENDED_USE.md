c:/python314/python.exe -m streamlit run app.py# Phase 1: Intended Use Statement & Problem Definition

## Clinical Context
**Disease:** Preeclampsia (PE)  
**Severity:** Hypertensive emergency in pregnancy; leading cause of maternal and fetal mortality/morbidity  
**Prevalence:** 2-8% of pregnancies globally; Black women 1.5-3x higher risk (documented disparity)  

---

## Outcome Definition
**PRIMARY OUTCOME:** Preeclampsia (any severity) during pregnancy/immediate postpartum  
- Binary classification: **PE = Yes/No**
- Measurement: Clinical diagnosis (BP ≥140/90 on two occasions + proteinuria or end-organ dysfunction) per ACOG criteria

**SECONDARY OUTCOMES (for stratified analysis):**
- Severe PE (SBP ≥160 mmHg OR DBP ≥110 mmHg + symptoms)
- PE with severe features (eclampsia, HELLP, pulmonary edema, etc.)
- Maternal outcome: admission to ICU, delivery complications
- Fetal outcome: preterm delivery, FGR, stillbirth

---

## Target Population
**Inclusion:**
- Pregnant women (any age, any parity, any ethnicity)
- Second/third trimester assessment (≥14 weeks gestation ideal, but earlier screening acceptable)
- All risk profiles (nulliparous, multiparous, prior PE, chronic conditions)

**Exclusion:**
- Pre-existing diagnosis of hypertension disease (these are managed separately)
- Multiple major missing predictors (>30% of features)

**Stratification (for fairness audit):**
- Ethnicity: White, Black, Asian, Hispanic, Other
- Age bands: <20, 20-34, 35-39, ≥40 years
- Parity: Nulliparous vs multiparous
- BMI categories: <25, 25-29.9, 30-34.9, ≥35

---

## Candidate Predictors (from CSV evidence base)

### Demographic
- Maternal age (years)
- Race/ethnicity (encoded)
- Parity (nulliparous/multiparous)
- Gestational age at assessment (weeks)

### Anthropometric
- Pre-pregnancy BMI (kg/m²)
- Weight gain trajectory (optional)

### Obstetric History
- Prior preeclampsia (yes/no)
- Multiple gestation (yes/no)
- IVF/assisted reproduction (yes/no)

### Medical/Comorbidity
- Chronic hypertension (yes/no)
- Diabetes mellitus (type 1 or 2; yes/no)
- Chronic kidney disease (yes/no)
- Autoimmune disease (yes/no)
- Family history: PE, hypertension, diabetes (yes/no)

### Clinical Measurements (Second/Third Trimester)
- Systolic blood pressure (mmHg)
- Diastolic blood pressure (mmHg)
- Proteinuria (negative/+1/+2/+3/≥1)

### Biomarkers (if available; optional)
- PlGF (placental growth factor) pg/mL
- sFlt-1 (soluble fms-like tyrosine kinase-1) pg/mL
- sFlt-1/PlGF ratio
- Uric acid (mg/dL)

### Ultrasound (optional)
- Uterine artery pulsatility index (UtAPI)
- Notching / diastolic notch presence
- Estimated fetal weight percentile

---

## Intended Clinical Action

**For Clinicians:**
1. **Risk Stratification** → Triage patients into low/moderate/high-risk groups
2. **Decision Support** → Flag high-risk candidates for:
   - Intensified monitoring (BP checks, lab interval)
   - Prophylaxis consideration (low-dose aspirin <16 weeks if high risk)
   - Early referral to maternal-fetal medicine
   - Preterm delivery planning (if PE develops)
3. **Shared Decision-Making** → SHAP waterfall + confidence interval shows which features drove THIS patient's risk
4. **Bias Awareness** → Fairness report alerts if model performs unequally for subgroups (especially Black women)

**For Researchers:**
- Quantify per-predictor contributions to PE risk
- Identify potential proxy variables encoding racial/socioeconomic bias
- Establish benchmark model performance for future validation studies

---

## Model Requirements

### Classification Task
- **Type:** Binary logistic regression (primary) + XGBoost (sensitivity)
- **Output:** Predicted probability of PE (0–1), with 90% confidence interval
- **Threshold:** Risk stratification at ≥20% (moderate) and ≥50% (high) per ACOG context

### Explainability
- SHAP values for every patient → waterfall plot
- Global feature importance across cohort
- Per-subgroup explanation (age/ethnicity/parity)

### Fairness Constraints
- **Equalized odds:** False negative rate ≤5% within every ethnicity (no group is systematically under-screened)
- **Demographic parity:** Don't significantly differ in proportion flagged high-risk by ethnicity (adjust if justified by clinical outcome differences)
- **Calibration by group:** Predicted risk matches observed PE rate separately for each ethnicity
- **Proxy detection:** Check for variables like ZIP code, insurance type encoding protected attributes

### Risk Classification
| Score | Risk Level | Action |
|-------|-----------|--------|
| <20% | **Low** | Routine antenatal care |
| 20-49% | **Moderate** | Intensified monitoring; aspirin if <16 wks + additional risk |
| ≥50% | **High** | Specialist referral; aspirin; early delivery consideration |

---

## Data & Validation Plan

### Training Data
- **N target:** ≥500 cases with outcome data (≥50 PE cases for rare outcome)
- **Period:** Prospective or retrospective cohort with clear outcome ascertainment
- **Handling:** Stratified train/validation/test split (70/15/15)

### Validation
- **Internal:** Stratified 5-fold cross-validation on training set; final performance on held-out test set
- **External (ideal):** Second hospital/time period; different clinical setting

### Metrics Reported
- **Discrimination:** AUROC, sensitivity, specificity, PPV, NPV (overall + per subgroup)
- **Calibration:** Brier score, calibration slope, reliability diagram
- **Fairness:** AUC by ethnicity, false negative rate by ethnicity, demographic parity ratio
- **Uncertainty:** 90% CI on all estimates via bootstrap

---

## Regulatory & Ethical Framework

### Risk Classification (IEC 62304)
- **Class:** Class B (moderate risk)  
  - Supports diagnostic/monitoring decision, not primary treatment
  - Input from clinician interpretation + patient values required
  - Not sole arbiter of delivery timing

### Documentation (TRIPOD+AI Checklist)
- [ ] Study protocol + objective defined
- [ ] Data source, eligibility, outcome definition
- [ ] Participant flow, baseline characteristics by outcome
- [ ] Feature selection + missing data handling
- [ ] Model development, hyperparameter tuning
- [ ] Model performance (discrimination, calibration, fairness)
- [ ] Limitations + external validity
- [ ] Source code reproducibility

### Bias & Fairness
- **Known disparity:** Black women have 3-4x maternal mortality from PE; often diagnosed later
- **Hypothesis:** Model may inherit this disparity if trained on biased data
- **Mitigation:** 
  - Stratified fairness metrics from day 1
  - If false negative rate >5% for any subgroup → flag, re-weight data, or adjust threshold
  - Transparent reporting of fairness limitations in model card

### Consent & Privacy
- [ ] Confirm all patient data de-identified (no names, medical record #, DOB)
- [ ] GDPR/HIPAA compliance for any PHI handling
- [ ] Institutional IRB approval if clinical deployment intended

---

## Success Criteria (Prototype Phase)
✓ Logistic regression baseline with AUROC ≥0.75 on held-out test set  
✓ SHAP waterfall plot works for individual patient  
✓ Fairness audit shows no ethnic group has false negative rate >5% difference  
✓ Streamlit dashboard runs end-to-end (patient input → risk score → SHAP → fairness report)  
✓ Model card + code + CSV evidence documented and reproducible  

---

## Next Steps
1. **Phase 2:** Merge all 34 CSV tables into unified evidence dataset; identify missing clinical outcomes
2. **Phase 3:** Build baseline logistic regression; report cross-val performance
3. **Phase 4:** Add SHAP + Fairlearn; confirm fairness metrics
4. **Phase 5:** Test on held-out cohort; write TRIPOD report
5. **Phase 6:** Deploy Streamlit + React frontend; gather clinician feedback
ls
pwd
