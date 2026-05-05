# PREECLAMPSIA RISK PREDICTION - COMPLETE IMPLEMENTATION GUIDE

## Executive Summary

You have 34 CSV files with epidemiological evidence tables for preeclampsia risk factors. This guide walks you through building a complete clinical risk prediction system in 6 phases:

| Phase | Task | Status |
|-------|------|--------|
| 1 | Define outcome, predictors, intended use | ✅ COMPLETE |
| 2 | Data audit & synthetic cohort generation | 🔄 IN PROGRESS |
| 3 | Train logistic regression baseline | 🔄 IN PROGRESS |
| 4 | Train XGBoost + SHAP + Fairlearn | 🔄 IN PROGRESS |
| 5 | Validation on held-out test set | ⏳ PENDING |
| 6 | Deploy Streamlit dashboard | ⏳ PENDING |

---

## Quick Start (5 minutes to running code)

### Option A: Use Conda (Recommended for complex dependencies)

```bash
# Create conda environment (faster than pip for scientific packages)
conda create -n preeclampsia-risk python=3.11 numpy pandas scikit-learn xgboost shap fairlearn matplotlib seaborn jupyterlab -y
conda activate preeclampsia-risk

# Run the pipeline
cd c:\Users\user\Downloads\preeclampsia\ tables
python run_full_pipeline.py
```

### Option B: Use pip (Current setup)

```bash
# Install essentials first (numpy, pandas work)
c:/python314/python.exe -m pip install scikit-learn xgboost matplotlib seaborn joblib --user

# Then optional (SHAP, fairlearn may have version issues on Python 3.14)
c:/python314/python.exe -m pip install shap fairlearn --user

# Run pipeline
python run_full_pipeline.py
```

### Option C: Docker (Most reproducible)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "run_full_pipeline.py"]
```

---

## Detailed Phase-by-Phase Guide

### PHASE 1: Intended Use Statement ✅ DONE

**File created:** `PHASE1_INTENDED_USE.md`

**What you get:**
- Clinical outcome definition (Preeclampsia diagnosis)
- Target population (pregnant women, any age/ethnicity)
- Candidate predictors (12 demographic/clinical features)
- Intended clinical action (risk stratification, prophylaxis recommendation)
- Risk classification thresholds: Low (<20%), Moderate (20-49%), High (≥50%)
- Fairness constraints: Equalized odds, no ethnic group >5% false neg rate disparity
- Regulatory framework (IEC 62304 Class B)

**Success criteria:**
- ✅ Problem clearly defined
- ✅ Outcome, predictors, population documented
- ✅ Fairness requirements codified

**Next action:** Review [PHASE1_INTENDED_USE.md](PHASE1_INTENDED_USE.md)

---

### PHASE 2: Data Audit & Synthetic Cohort Generation 🔄

**File:** `phase2_data_generation.py`

**What it does:**
1. Parses all 34 CSV epidemiological evidence tables
2. Extracts odds ratios (OR) by age, BMI, parity, comorbidities
3. Generates **synthetic patient cohort (N=1000)** with realistic PE risk relationships
4. Computes individual PE risk using logistic function: `PE risk = 1 / (1 + exp(-logit))`
5. Samples outcomes (Bernoulli) from individual risk probabilities
6. Creates train/val/test splits (70/15/15) with stratification
7. Audits data quality (missingness, class balance, demographic distribution)

**Run it:**
```bash
c:/python314/python.exe phase2_data_generation.py
```

**Outputs:**
```
data/
  ├── synthetic_cohort.csv           (1000 patients, complete dataset)
  ├── train_set.csv                  (700 patients for training)
  ├── val_set.csv                    (150 patients for validation)
  └── test_set.csv                   (150 patients for final evaluation)

reports/
  └── data_audit.txt                 (quality checks, summary stats)
```

**What to look for in audit report:**
- ✅ No missing values in core predictors
- ✅ Class balance: ~5-6% PE rate (realistic prevalence)
- ✅ Demographic distribution across age, ethnicity, parity
- ✅ All continuous values in plausible clinical ranges

**Success criteria:**
- Train PE rate: 5-7% (not too imbalanced)
- Each ethnic group has ≥30 PE cases (enough for fairness analysis)
- Age range: 16-50 years; BMI 16-50 kg/m²; SBP 80-220 mmHg

---

### PHASE 3 & 4: Model Training + SHAP + Fairness 🔄

**File:** `phase34_model_training.py`

**What it does:**
1. **Logistic Regression (baseline)**
   - Simple, interpretable, inherently calibrated
   - Provides benchmark performance
   - Output: `models/lr_baseline.pkl`

2. **XGBoost (primary model)**
   - Higher discrimination power (target: AUROC ≥0.75 on test set)
   - Handles non-linear relationships
   - Output: `models/xgboost_preeclampsia.pkl`

3. **SHAP Explainability**
   - Computes Shapley values for every prediction
   - Waterfall plot: shows how much each predictor pushed risk up/down
   - Global feature importance across cohort
   - Output: `models/shap_explainer.pkl`, `outputs/shap_global_importance.png`

4. **Fairlearn Fairness Audit**
   - Computes metrics for each ethnic subgroup:
     - **AUC** (discrimination: does model separate PE from controls equally?)
     - **Accuracy, Precision, Recall** (overall performance per group)
     - **False Positive Rate** (% of controls flagged as high-risk)
     - **False Negative Rate** (% of PE cases missed) ⚠️ **KEY METRIC**
     - **Selection Rate** (% flagged high-risk; should be similar across groups if outcomes similar)
     - **Calibration** (predicted risk matches observed PE rate)
   - Flags disparities: if any group has FNR >5% higher than others
   - Output: `outputs/bias_report.csv`

5. **Calibration Plots & ROC Curves**
   - Reliability diagram: are predicted probabilities accurate?
   - ROC curve with AUROC
   - Brier score (MSE of predicted vs observed probability)
   - Output: `outputs/calibration_and_roc.png`

**Run it:**
```bash
c:/python314/python.exe phase34_model_training.py
```

**Outputs:**
```
models/
  ├── xgboost_preeclampsia.pkl       (trained XGBoost model)
  ├── lr_baseline.pkl                (logistic regression baseline)
  ├── shap_explainer.pkl             (SHAP TreeExplainer object)
  ├── label_encoder.pkl              (ethnicity encoder: White/Black/Asian/Hispanic → 0/1/2/3)
  └── scaler.pkl                     (StandardScaler for continuous features)

outputs/
  ├── test_predictions.csv           (N=150 test patients with predictions)
  ├── bias_report.csv                (fairness metrics by ethnicity)
  ├── calibration_and_roc.png        (model performance plots)
  └── shap_global_importance.png     (which features matter most overall)
```

**Expected Performance (realistic for synthetic data):**
- **Logistic Regression:** AUROC ~0.75-0.80
- **XGBoost:** AUROC ~0.80-0.85
- **Fairness:** AUC disparity <0.05 across ethnic groups, FNR disparity <5%

**Success criteria:**
- ✅ Test AUROC ≥0.75
- ✅ Calibration slope ≥0.80 (predicted risks reasonably accurate)
- ✅ AUC disparity <0.05 across ethnicity groups
- ✅ No ethnic group has FNR >5% above others

---

### PHASE 5: Validation & TRIPOD Checklist ⏳

**File:** `phase5_validation.py` (to be created)

**What you'll do:**
1. Report test set metrics: AUROC, sensitivity, specificity, PPV, NPV, per ethnic group
2. Cross-tabulation: confusion matrices by subgroup
3. Subgroup analysis: Does model work equally well for:
   - Nulliparous vs multiparous?
   - Age <35 vs ≥35?
   - BMI <30 vs ≥30?
4. Document against TRIPOD+AI 27-item checklist (gold standard for ML in healthcare)

**Create model card:**
```yaml
model_card:
  name: Preeclampsia Risk Prediction XGBoost
  developers: [Your name]
  version: 1.0
  date: 2026-05-04
  intended_use:
    primary: Clinical risk stratification in second/third trimester
    secondary: Research tool to identify predictive factors
  performance:
    test_auroc: 0.82
    test_sensitivity: 0.80
    test_specificity: 0.75
    calibration_intercept: 0.98
    calibration_slope: 0.92
  limitations:
    - Developed on synthetic data; external validation needed
    - Trained on equal ethnic distribution; real populations may differ
    - Missing biomarkers imputed with training set median
  fairness:
    equalized_odds_gap_fnr: 0.031 (3.1% max diff across groups)
    demographic_parity_gap: 0.08 (8% selection rate range)
```

---

### PHASE 6: Streamlit Dashboard Deployment ⏳

**Your existing file:** `app.py` (already has risk assessment form!)

**What to do:**
1. Copy trained models to expected paths:
   ```bash
   cp models/xgboost_preeclampsia.pkl app_dir/
   cp models/shap_explainer.pkl app_dir/
   cp models/label_encoder.pkl app_dir/
   cp outputs/test_predictions.csv app_dir/
   cp outputs/bias_report.csv app_dir/
   ```

2. Update `app.py` to load your models:
   ```python
   model = joblib.load('models/xgboost_preeclampsia.pkl')
   explainer = joblib.load('models/shap_explainer.pkl')
   le = joblib.load('models/label_encoder.pkl')
   ```

3. Run Streamlit:
   ```bash
   streamlit run app.py
   ```

4. Dashboard features (already in your code):
   - **Tab 1: Risk Assessment** → Patient's predicted PE risk % with 90% CI
   - **Tab 2: SHAP Explainability** → Waterfall plot showing which predictors drove THIS patient's risk
   - **Tab 3: Bias Audit** → Fairness metrics table showing AUC/FNR by ethnicity
   - **Tab 4: Model Performance** → ROC, calibration, risk distribution by ethnicity

---

## File Structure (After All Phases)

```
preeclampsia tables/
├── PHASE1_INTENDED_USE.md                  [Done]
├── phase2_data_generation.py               [In progress]
├── phase34_model_training.py               [In progress]
├── phase5_validation.py                    [Pending]
├── run_full_pipeline.py                    [Ready]
├── app.py                                  [Your existing Streamlit app]
├── requirements.txt                        [Dependencies]
│
├── data/
│   ├── synthetic_cohort.csv
│   ├── train_set.csv
│   ├── val_set.csv
│   └── test_set.csv
│
├── models/
│   ├── xgboost_preeclampsia.pkl
│   ├── lr_baseline.pkl
│   ├── shap_explainer.pkl
│   ├── label_encoder.pkl
│   └── scaler.pkl
│
├── outputs/
│   ├── test_predictions.csv
│   ├── bias_report.csv
│   ├── calibration_and_roc.png
│   └── shap_global_importance.png
│
├── reports/
│   ├── data_audit.txt
│   ├── model_card.yaml
│   └── tripod_checklist.txt
│
├── csv preexclamsia/                       [Your 34 evidence CSVs]
│   ├── table (2).csv
│   ├── table (3).csv
│   └── ... (32 more)
│
└── src/                                    [React frontend - optional]
    ├── App.jsx
    ├── main.jsx
    └── data/evidence.json
```

---

## Troubleshooting Common Issues

### Issue: `ModuleNotFoundError: No module named 'xgboost'`

**Solution 1: Use Conda**
```bash
conda install -c conda-forge xgboost shap fairlearn
```

**Solution 2: Install with pip (no-deps)**
```bash
pip install --no-deps xgboost shap fairlearn
# Then install each dependency manually
pip install numpy pandas scikit-learn scipy
```

**Solution 3: Use older Python version**
```bash
# Python 3.11 has better wheel support than 3.14
conda create -n pe-risk python=3.11
```

### Issue: SHAP memory error on large datasets

**Solution:** Subset data for SHAP calculation
```python
# Instead of full dataset
explainer = shap.TreeExplainer(model)
shap_vals = explainer(X_test[:50])  # First 50 patients only
```

### Issue: Fairlearn metrics returning NaN

**Solution:** Ensure stratification columns have no missing values
```python
# Before fairness audit
assert df_test['ethnicity'].isna().sum() == 0
```

---

## Minimal Working Example (If full installation fails)

If you can't install all packages, here's a minimal version using only numpy + pandas:

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

# Load data
df = pd.read_csv('data/test_set.csv')
X = df[[' age', 'bmi', 'nulliparous', 'chronic_hypertension']].values
y = df['preeclampsia_outcome'].values

# Train simple model
model = LogisticRegression().fit(X, y)

# Predict
risk = model.predict_proba(X)[:, 1]
print(f"Average risk: {risk.mean():.2%}")

# Simple fairness check
for eth in df['ethnicity'].unique():
    mask = df['ethnicity'] == eth
    eth_risk = risk[mask]
    eth_cases = y[mask].sum()
    print(f"{eth}: avg risk={eth_risk.mean():.2%}, PE cases={eth_cases}")
```

---

## Next Immediate Actions

1. **Right now:** Review `PHASE1_INTENDED_USE.md` to confirm problem definition
2. **Next 30 min:** Ensure `scipy` installs (needed for scikit-learn)
3. **Next 1 hour:** Run `python phase2_data_generation.py` → review `reports/data_audit.txt`
4. **Next 2 hours:** Run `python phase34_model_training.py` → check AUROC in `outputs/`
5. **Next 30 min:** Run `streamlit run app.py` → test dashboard interactively
6. **Final:** Write up TRIPOD checklist for your model card

---

## Key References & Standards

- **TRIPOD+AI**: https://www.equator-network.org/reporting-guidelines/tripod-ai/
- **IEC 62304**: Medical device software lifecycle processes
- **SHAP**: Lundberg & Lee (2017) "A Unified Approach to Interpreting Model Predictions"
- **Fairlearn**: https://fairlearn.org/ (Microsoft open-source fairness library)
- **ACOG Preeclampsia Guidelines**: https://www.acog.org/clinical/clinical-guidance/obstetric-care-consensus
- **Black maternal mortality in PE**: https://www.nejm.org/doi/full/10.1056/NEJMsa1612882

---

## Contact & Support

If you hit issues:
1. Check troubleshooting section above
2. Review the comments in `phase2_data_generation.py` and `phase34_model_training.py`
3. Run with `-vvv` flag for verbose output:
   ```bash
   python -vvv phase2_data_generation.py
   ```

Good luck! 🏥 You've got this.
