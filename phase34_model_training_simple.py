#!/usr/bin/env python3
"""
PHASE 3 & 4 SIMPLIFIED: Model Training without optional SHAP/Fairlearn
Falls back to sklearn only if SHAP/Fairlearn unavailable
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    roc_auc_score, roc_curve, auc, brier_score_loss,
    confusion_matrix, accuracy_score, precision_score, recall_score
)
from sklearn.calibration import calibration_curve
import xgboost as xgb
import joblib

print("="*70)
print("PHASE 3 & 4: MODEL TRAINING + BASIC FAIRNESS AUDIT")
print("="*70)

# ═════════════════════════════════════════════════════════════════
# 1. LOAD DATA
# ═════════════════════════════════════════════════════════════════

print("\n[DATA LOADED]")
df_train = pd.read_csv('data/train_set.csv')
df_test = pd.read_csv('data/test_set.csv')

print(f"  Train: {len(df_train)}, Test: {len(df_test)}")

# Features to use
feature_cols = [
    'age', 'bmi', 'nulliparous', 'prior_preeclampsia',
    'chronic_hypertension', 'diabetes', 'chronic_kidney_disease',
    'autoimmune_disease', 'multiple_gestation', 'gestational_age_weeks',
    'systolic_bp', 'diastolic_bp'
]

# Prepare data
X_train = df_train[feature_cols].values
y_train = df_train['preeclampsia_outcome'].values
X_test = df_test[feature_cols].values
y_test = df_test['preeclampsia_outcome'].values

# Standardize
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)
joblib.dump(scaler, 'models/scaler.pkl')

# ═════════════════════════════════════════════════════════════════
# 2. TRAIN LOGISTIC REGRESSION BASELINE
# ═════════════════════════════════════════════════════════════════

print("\n[LOGISTIC REGRESSION BASELINE]")
lr = LogisticRegression(max_iter=1000, class_weight='balanced', solver='lbfgs', random_state=42)
lr.fit(X_train, y_train)

cv_scores = cross_val_score(lr, X_train, y_train, cv=5, scoring='roc_auc')
print(f"  5-fold CV AUROC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

y_pred_proba_test_lr = lr.predict_proba(X_test)[:, 1]
test_auc_lr = roc_auc_score(y_test, y_pred_proba_test_lr)
print(f"  Test AUROC: {test_auc_lr:.4f}")

joblib.dump(lr, 'models/lr_baseline.pkl')

# ═════════════════════════════════════════════════════════════════
# 3. TRAIN XGBOOST
# ═════════════════════════════════════════════════════════════════

print("\n[XGBOOST TRAINING]")
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
xgb_model = xgb.XGBClassifier(
    n_estimators=100, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight, random_state=42, eval_metric='logloss'
)
xgb_model.fit(X_train, y_train, verbose=False)

y_pred_proba_test = xgb_model.predict_proba(X_test)[:, 1]
test_auc = roc_auc_score(y_test, y_pred_proba_test)
print(f"  Test AUROC: {test_auc:.4f}")

joblib.dump(xgb_model, 'models/xgboost_preeclampsia.pkl')

# ═════════════════════════════════════════════════════════════════
# 4. FAIRNESS AUDIT (WITHOUT FAIRLEARN)
# ═════════════════════════════════════════════════════════════════

print("\n[FAIRNESS AUDIT - BY ETHNICITY]")
bias_report = {}
threshold = 0.5
y_pred = (y_pred_proba_test >= threshold).astype(int)

for eth in df_test['ethnicity'].unique():
    mask = df_test['ethnicity'] == eth
    eth_y = y_test[mask]
    eth_pred = y_pred[mask]
    eth_proba = y_pred_proba_test[mask]
    
    if len(np.unique(eth_y)) > 1:
        eth_auc = roc_auc_score(eth_y, eth_proba)
    else:
        eth_auc = np.nan
    
    eth_fnr = (eth_y * (1 - eth_pred)).sum() / max(1, eth_y.sum()) if eth_y.sum() > 0 else np.nan
    eth_sensitivity = recall_score(eth_y, eth_pred, zero_division=0)
    
    bias_report[eth] = {
        'N': mask.sum(),
        'PE_rate': eth_y.mean(),
        'AUC': eth_auc,
        'accuracy': accuracy_score(eth_y, eth_pred),
        'sensitivity': eth_sensitivity,
        'false_neg_rate': eth_fnr,
    }

bias_df = pd.DataFrame(bias_report).T
bias_df.to_csv('outputs/bias_report.csv')

print("\n  Performance by Ethnicity:")
print(bias_df.to_string())

# ═════════════════════════════════════════════════════════════════
# 5. CALIBRATION & ROC PLOTS
# ═════════════════════════════════════════════════════════════════

print("\n[CALIBRATION & PERFORMANCE PLOTS]")
prob_true, prob_pred = calibration_curve(y_test, y_pred_proba_test, n_bins=10)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Calibration plot
ax1.plot(prob_pred, prob_true, 's-', label='XGBoost', linewidth=2)
ax1.plot([0, 1], [0, 1], 'k--', label='Perfectly calibrated')
ax1.set_xlabel('Mean Predicted Probability', fontsize=11)
ax1.set_ylabel('Fraction of Positives', fontsize=11)
ax1.set_title('Calibration Plot', fontsize=12, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# ROC curve
fpr, tpr, _ = roc_curve(y_test, y_pred_proba_test)
test_auc = roc_auc_score(y_test, y_pred_proba_test)
ax2.plot(fpr, tpr, 'b-', linewidth=2, label=f'XGBoost (AUC={test_auc:.3f})')
ax2.plot([0, 1], [0, 1], 'k--', label='Random')
ax2.set_xlabel('False Positive Rate', fontsize=11)
ax2.set_ylabel('True Positive Rate', fontsize=11)
ax2.set_title('ROC Curve', fontsize=12, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/calibration_and_roc.png', dpi=150, bbox_inches='tight')
plt.close()

brier = brier_score_loss(y_test, y_pred_proba_test)
print(f"  Brier Score: {brier:.4f}")
print(f"  OK Plots saved")

# ═════════════════════════════════════════════════════════════════
# 6. SAVE TEST PREDICTIONS
# ═════════════════════════════════════════════════════════════════

print("\n[SAVING TEST PREDICTIONS]")
test_results = df_test[['patient_id', 'ethnicity', 'age', 'bmi']].copy()
test_results['y_true'] = y_test
test_results['y_pred_proba'] = y_pred_proba_test
test_results['y_pred'] = (y_pred_proba_test >= threshold).astype(int)
test_results.to_csv('outputs/test_predictions.csv', index=False)
print(f"  OK Predictions saved for {len(test_results)} test patients")

# ═════════════════════════════════════════════════════════════════
# OPTIONAL: TRY TO IMPORT SHAP
# ═════════════════════════════════════════════════════════════════

try:
    import shap
    print("\n[SHAP EXPLAINABILITY]")
    explainer = shap.TreeExplainer(xgb_model)
    shap_values_test = explainer(X_test)
    joblib.dump(explainer, 'models/shap_explainer.pkl')
    
    # Global importance plot
    fig = plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values_test, X_test, plot_type="bar", show=False)
    plt.title("SHAP Global Feature Importance", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('outputs/shap_global_importance.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  OK SHAP values computed and saved")
except ImportError:
    print("\n[SHAP NOT AVAILABLE]")
    print("  Note: SHAP library not installed. Skipping explainability plots.")
    print("  Install with: pip install shap")

print("\n" + "="*70)
print("PHASE 3 & 4 COMPLETE")
print("="*70)
print("\nKey Results:")
print(f"  - Logistic Regression AUROC: {test_auc_lr:.4f}")
print(f"  - XGBoost AUROC: {test_auc:.4f}")
print(f"  - Fairness: See outputs/bias_report.csv")
print(f"  - Plots: outputs/calibration_and_roc.png")
