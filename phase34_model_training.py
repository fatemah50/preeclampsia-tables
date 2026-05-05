#!/usr/bin/env python3
"""
=============================================================================
PHASE 3 & 4: Model Training + SHAP Explainability + Fairlearn Bias Audit
=============================================================================

This script:
1. Trains logistic regression baseline (interpretable, calibrated)
2. Trains XGBoost (higher performance)
3. Computes SHAP values for per-patient feature importance
4. Runs Fairlearn fairness metrics across ethnic subgroups
5. Generates calibration plots + bias audit report
6. Saves trained models for Streamlit deployment

Outputs:
  - models/xgboost_preeclampsia.pkl (trained model)
  - models/lr_baseline.pkl (logistic regression)
  - models/shap_explainer.pkl (SHAP explainer object)
  - models/label_encoder.pkl (ethnicity encoder)
  - outputs/test_predictions.csv (predictions + explanations)
  - outputs/bias_report.csv (fairness metrics by ethnicity)
  - outputs/calibration_plot.png, roc_curve.png, etc.
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    roc_auc_score, roc_curve, auc, brier_score_loss,
    confusion_matrix, accuracy_score, precision_score, recall_score
)
from sklearn.calibration import calibration_curve
import xgboost as xgb
import shap
import joblib

# Fairness library
from fairlearn.metrics import MetricFrame
from fairlearn.postprocessing import ThresholdOptimizer
import fairlearn.metrics as flmetrics

# ═══════════════════════════════════════════════════════════════════════════
# 1. DATA LOADING & PREPROCESSING
# ═══════════════════════════════════════════════════════════════════════════

def load_and_preprocess_data():
    """Load train/val/test sets and prepare for modeling."""
    
    # Load datasets
    df_train = pd.read_csv('data/train_set.csv')
    df_val = pd.read_csv('data/val_set.csv')
    df_test = pd.read_csv('data/test_set.csv')
    
    print(f"[DATA LOADED]")
    print(f"  Train: {len(df_train)}, Val: {len(df_val)}, Test: {len(df_test)}")
    
    # Define feature columns
    feature_cols = [
        'age', 'bmi', 'nulliparous', 'prior_preeclampsia',
        'chronic_hypertension', 'diabetes', 'chronic_kidney_disease',
        'autoimmune_disease', 'multiple_gestation', 'gestational_age_weeks',
        'systolic_bp', 'diastolic_bp'
    ]
    
    # Encode categorical variables
    le = LabelEncoder()
    
    # Encode proteinuria
    proteinuria_map = {'Negative': 0, '+1': 1, '+2': 2, '+3': 3}
    df_train['proteinuria_numeric'] = df_train['proteinuria'].map(proteinuria_map)
    df_val['proteinuria_numeric'] = df_val['proteinuria'].map(proteinuria_map)
    df_test['proteinuria_numeric'] = df_test['proteinuria'].map(proteinuria_map)
    
    feature_cols.append('proteinuria_numeric')
    
    # Encode ethnicity for modeling but keep original for fairness analysis
    df_train['ethnicity_encoded'] = le.fit_transform(df_train['ethnicity'])
    df_val['ethnicity_encoded'] = le.transform(df_val['ethnicity'])
    df_test['ethnicity_encoded'] = le.transform(df_test['ethnicity'])
    
    # Store encoder for later
    joblib.dump(le, 'models/label_encoder.pkl')
    
    # Handle missing values in biomarkers (fill with median from training set)
    for col in ['plgf_pg_ml', 'sflt1_plgf_ratio']:
        if col in df_train.columns:
            median_val = df_train[col].median()
            df_train[col].fillna(median_val, inplace=True)
            df_val[col].fillna(median_val, inplace=True)
            df_test[col].fillna(median_val, inplace=True)
            feature_cols.append(col)
    
    # Standardize continuous features
    scaler = StandardScaler()
    continuous_features = ['age', 'bmi', 'gestational_age_weeks', 
                          'systolic_bp', 'diastolic_bp', 'proteinuria_numeric']
    
    X_train = df_train[feature_cols].copy()
    X_val = df_val[feature_cols].copy()
    X_test = df_test[feature_cols].copy()
    
    y_train = df_train['preeclampsia_outcome'].values
    y_val = df_val['preeclampsia_outcome'].values
    y_test = df_test['preeclampsia_outcome'].values
    
    # Fit scaler on training data
    X_train[continuous_features] = scaler.fit_transform(X_train[continuous_features])
    X_val[continuous_features] = scaler.transform(X_val[continuous_features])
    X_test[continuous_features] = scaler.transform(X_test[continuous_features])
    
    joblib.dump(scaler, 'models/scaler.pkl')
    
    return {
        'X_train': X_train, 'y_train': y_train, 'df_train': df_train,
        'X_val': X_val, 'y_val': y_val, 'df_val': df_val,
        'X_test': X_test, 'y_test': y_test, 'df_test': df_test,
        'feature_cols': feature_cols, 'le': le, 'scaler': scaler
    }

# ═══════════════════════════════════════════════════════════════════════════
# 2. TRAIN LOGISTIC REGRESSION BASELINE
# ═══════════════════════════════════════════════════════════════════════════

def train_logistic_regression(data_dict):
    """Train logistic regression for interpretability + calibration."""
    
    print("\n[LOGISTIC REGRESSION BASELINE]")
    
    X_train = data_dict['X_train']
    y_train = data_dict['y_train']
    X_val = data_dict['X_val']
    y_val = data_dict['y_val']
    
    # Train with class weighting for imbalance
    lr = LogisticRegression(
        max_iter=1000,
        class_weight='balanced',
        solver='lbfgs',
        random_state=42
    )
    
    lr.fit(X_train, y_train)
    
    # Cross-validation on training set
    cv_scores = cross_val_score(
        lr, X_train, y_train,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        scoring='roc_auc'
    )
    print(f"  5-fold CV AUROC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    # Validation performance
    y_pred_proba_val = lr.predict_proba(X_val)[:, 1]
    val_auc = roc_auc_score(y_val, y_pred_proba_val)
    print(f"  Validation AUROC: {val_auc:.4f}")
    
    joblib.dump(lr, 'models/lr_baseline.pkl')
    
    return lr

# ═══════════════════════════════════════════════════════════════════════════
# 3. TRAIN XGBOOST (PRIMARY MODEL)
# ═══════════════════════════════════════════════════════════════════════════

def train_xgboost(data_dict):
    """Train XGBoost as primary model (better discrimination)."""
    
    print("\n[XGBOOST TRAINING]")
    
    X_train = data_dict['X_train']
    y_train = data_dict['y_train']
    X_val = data_dict['X_val']
    y_val = data_dict['y_val']
    X_test = data_dict['X_test']
    y_test = data_dict['y_test']
    
    # Calculate scale_pos_weight for class imbalance
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    # Train XGBoost
    xgb_model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='logloss'
    )
    
    xgb_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    # Validation performance
    y_pred_proba_val = xgb_model.predict_proba(X_val)[:, 1]
    val_auc = roc_auc_score(y_val, y_pred_proba_val)
    print(f"  Validation AUROC: {val_auc:.4f}")
    
    # Test performance
    y_pred_proba_test = xgb_model.predict_proba(X_test)[:, 1]
    test_auc = roc_auc_score(y_test, y_pred_proba_test)
    print(f"  Test AUROC: {test_auc:.4f}")
    
    joblib.dump(xgb_model, 'models/xgboost_preeclampsia.pkl')
    
    return xgb_model, y_pred_proba_test

# ═══════════════════════════════════════════════════════════════════════════
# 4. SHAP EXPLAINABILITY
# ═══════════════════════════════════════════════════════════════════════════

def compute_shap_values(xgb_model, X_train, X_test):
    """Compute SHAP values for model explainability."""
    
    print("\n[SHAP EXPLAINABILITY]")
    
    # Create explainer
    explainer = shap.TreeExplainer(xgb_model)
    shap_values_test = explainer(X_test)
    
    print(f"  ✓ SHAP values computed for {len(X_test)} test patients")
    
    # Save explainer for Streamlit app
    joblib.dump(explainer, 'models/shap_explainer.pkl')
    
    # Global feature importance plot
    fig = plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values_test, X_test, plot_type="bar", show=False)
    plt.title("SHAP Global Feature Importance", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('outputs/shap_global_importance.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ Global importance plot saved")
    
    return explainer, shap_values_test

# ═══════════════════════════════════════════════════════════════════════════
# 5. FAIRNESS AUDIT (FAIRLEARN)
# ═══════════════════════════════════════════════════════════════════════════

def fairness_audit(xgb_model, X_test, y_test, df_test, y_pred_proba_test):
    """
    Comprehensive fairness analysis across ethnic groups.
    Metrics: AUC, accuracy, selection_rate, false positive/negative rates, calibration
    """
    
    print("\n[FAIRNESS AUDIT - BY ETHNICITY]")
    
    # Create sensitive attribute (ethnicity)
    sensitive_attr = df_test['ethnicity'].values
    
    # Make binary predictions for calibration/parity metrics
    threshold = 0.5
    y_pred = (y_pred_proba_test >= threshold).astype(int)
    
    # Compute metrics by group
    metrics = {
        'AUC': flmetrics.roc_auc_score,
        'accuracy': flmetrics.accuracy_score,
        'precision': flmetrics.precision_score,
        'recall': flmetrics.recall_score,
        'false_pos_rate': lambda y_true, y_pred: 
            ((1 - y_true) * y_pred).sum() / max(1, (1 - y_true).sum()),
        'false_neg_rate': lambda y_true, y_pred: 
            (y_true * (1 - y_pred)).sum() / max(1, y_true.sum()),
        'selection_rate': lambda y_true, y_pred: y_pred.mean()
    }
    
    bias_report_dict = {}
    
    for eth_group in df_test['ethnicity'].unique():
        mask = df_test['ethnicity'] == eth_group
        group_test = y_test[mask]
        group_pred = y_pred[mask]
        group_pred_proba = y_pred_proba_test[mask]
        
        bias_report_dict[eth_group] = {
            'N': mask.sum(),
            'PE_rate': group_test.mean(),
            'AUC': roc_auc_score(group_test, group_pred_proba) if len(np.unique(group_test)) > 1 else np.nan,
            'accuracy': accuracy_score(group_test, group_pred),
            'precision': precision_score(group_test, group_pred, zero_division=0),
            'recall': recall_score(group_test, group_pred, zero_division=0),
            'selection_rate': group_pred.mean(),
            'false_pos_rate': ((1 - group_test) * group_pred).sum() / max(1, (1 - group_test).sum()),
            'false_neg_rate': (group_test * (1 - group_pred)).sum() / max(1, group_test.sum()),
        }
    
    bias_df = pd.DataFrame(bias_report_dict).T
    bias_df.to_csv('outputs/bias_report.csv')
    
    print("\n  Performance by Ethnicity:")
    print(bias_df.to_string())
    
    # Flag disparities
    auc_by_group = bias_df['AUC'].dropna()
    fnr_by_group = bias_df['false_neg_rate']
    
    if len(auc_by_group) > 1:
        auc_diff = auc_by_group.max() - auc_by_group.min()
        if auc_diff > 0.05:
            print(f"\n  ⚠️ WARNING: AUC disparity of {auc_diff:.3f} detected across groups")
            print(f"     Highest: {auc_by_group.idxmax()} ({auc_by_group.max():.3f})")
            print(f"     Lowest:  {auc_by_group.idxmin()} ({auc_by_group.min():.3f})")
    
    if (fnr_by_group.max() - fnr_by_group.min()) > 0.05:
        print(f"\n  ⚠️ WARNING: False negative rate disparity detected")
        print(f"     Highest: {fnr_by_group.idxmax()} ({fnr_by_group.max():.3f})")
        print(f"     Lowest:  {fnr_by_group.idxmin()} ({fnr_by_group.min():.3f})")
    
    return bias_df

# ═══════════════════════════════════════════════════════════════════════════
# 6. CALIBRATION & PERFORMANCE PLOTS
# ═══════════════════════════════════════════════════════════════════════════

def plot_calibration_and_roc(xgb_model, X_test, y_test, y_pred_proba_test):
    """Generate calibration plot and ROC curve."""
    
    print("\n[CALIBRATION & PERFORMANCE PLOTS]")
    
    # Calibration plot
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
    
    print("  ✓ Calibration + ROC plots saved")
    
    # Brier score
    brier = brier_score_loss(y_test, y_pred_proba_test)
    print(f"  Brier Score: {brier:.4f}")

# ═══════════════════════════════════════════════════════════════════════════
# 7. SAVE TEST PREDICTIONS FOR STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════

def save_test_predictions(xgb_model, X_test, y_test, df_test, y_pred_proba_test):
    """Save test set predictions for downstream analysis."""
    
    print("\n[SAVING TEST PREDICTIONS]")
    
    test_results = df_test[['patient_id', 'ethnicity', 'age', 'bmi']].copy()
    test_results['y_true'] = y_test
    test_results['y_pred_proba'] = y_pred_proba_test
    test_results['y_pred'] = (y_pred_proba_test >= 0.5).astype(int)
    
    test_results.to_csv('outputs/test_predictions.csv', index=False)
    print(f"  ✓ Saved predictions for {len(test_results)} test patients")
    
    return test_results

# ═══════════════════════════════════════════════════════════════════════════
# 8. MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    os.makedirs('models', exist_ok=True)
    os.makedirs('outputs', exist_ok=True)
    
    print("="*70)
    print("PHASE 3 & 4: MODEL TRAINING + EXPLAINABILITY + FAIRNESS")
    print("="*70)
    
    # Load and preprocess
    data_dict = load_and_preprocess_data()
    
    # Train models
    lr_model = train_logistic_regression(data_dict)
    xgb_model, y_pred_proba_test = train_xgboost(data_dict)
    
    # SHAP explainability
    explainer, shap_values_test = compute_shap_values(
        xgb_model, 
        data_dict['X_train'], 
        data_dict['X_test']
    )
    
    # Fairness audit
    bias_df = fairness_audit(
        xgb_model,
        data_dict['X_test'],
        data_dict['y_test'],
        data_dict['df_test'],
        y_pred_proba_test
    )
    
    # Plots
    plot_calibration_and_roc(
        xgb_model,
        data_dict['X_test'],
        data_dict['y_test'],
        y_pred_proba_test
    )
    
    # Save predictions
    test_results = save_test_predictions(
        xgb_model,
        data_dict['X_test'],
        data_dict['y_test'],
        data_dict['df_test'],
        y_pred_proba_test
    )
    
    print("\n" + "="*70)
    print("✓ PHASE 3 & 4 COMPLETE")
    print("="*70)
    print("\nArtifacts ready for Streamlit deployment:")
    print("  - models/xgboost_preeclampsia.pkl")
    print("  - models/shap_explainer.pkl")
    print("  - models/label_encoder.pkl")
    print("  - outputs/test_predictions.csv")
    print("  - outputs/bias_report.csv")
    print("  - outputs/calibration_and_roc.png")
    print("  - outputs/shap_global_importance.png")
