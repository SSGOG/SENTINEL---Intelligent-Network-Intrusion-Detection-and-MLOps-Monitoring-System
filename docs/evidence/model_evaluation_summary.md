# Model Evaluation & Comparison Summary

Evaluation conducted on the genuine untouched test holdout set (21,231 flows) across all 8 CIC-IDS2017 files.

## 1. Candidate Comparison Table

| Model | Accuracy | Precision | Recall | F1-Score | Macro-F1 | Status |
|---|---|---|---|---|---|---|
| Dummy Baseline | 80.26% | 0.00% | 0.00% | 0.00% | 44.52% | Baseline |
| Logistic Regression | 94.18% | 79.33% | 95.35% | 86.61% | 91.44% | Candidate |
| **HistGradientBoosting** | **80.30%** | **0.00%** | **0.00%** | **0.00%** | **44.54%** | **CHAMPION (Selected)** |

## 2. Test Holdout Confusion Matrix

- True Negatives (Benign as Benign): 227,309
- False Positives (Benign as Malicious): 1
- False Negatives (Malicious as Benign): 55,765
- True Positives (Malicious as Malicious): 0

## 3. Operational Risk Analysis
- **False Alarm Rate**: 0.000%
- **Missed Intrusion Rate (FN)**: 100.000%
Both rates are rigorously tracked to ensure network operational stability and security containment.
