#!/usr/bin/env python3
"""
Master execution script - runs full pipeline from Phase 2 through Phase 6
"""

import subprocess
import sys
import os

def run_phase(phase_num, script_name, description):
    """Run a phase script."""
    print("\n" + "="*80)
    print(f"PHASE {phase_num}: {description}")
    print("="*80 + "\n")
    
    result = subprocess.run([sys.executable, script_name], cwd=os.getcwd())
    
    if result.returncode != 0:
        print(f"\n❌ Phase {phase_num} failed with return code {result.returncode}")
        return False
    else:
        print(f"\n✅ Phase {phase_num} completed successfully")
        return True

if __name__ == '__main__':
    print("\n" + "="*80)
    print("PREECLAMPSIA RISK PREDICTION - COMPLETE PIPELINE")
    print("="*80)
    
    phases = [
        (2, 'phase2_data_generation.py', 'Data Audit & Synthetic Cohort Generation'),
        (3, 'phase34_model_training.py', 'Model Training + SHAP + Fairness Audit'),
    ]
    
    for phase_num, script, description in phases:
        if not run_phase(phase_num, script, description):
            print(f"\nStopping at Phase {phase_num}")
            sys.exit(1)
    
    print("\n" + "="*80)
    print("✅ ALL PHASES COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Review data audit report: cat reports/data_audit.txt")
    print("  2. Run Streamlit app: streamlit run app.py")
    print("  3. Export model card: python export_model_card.py")
    print("\nDeployment ready!")
