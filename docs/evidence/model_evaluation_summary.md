# Model Evaluation & Comparison Summary

Evaluation conducted on the genuine untouched test holdout set (21,231 flows) across all 8 CIC-IDS2017 files.

## 1. Candidate Comparison Table

| Model | Accuracy | Precision | Recall | F1-Score | Macro-F1 | Status |
|---|---|---|---|---|---|---|
| Dummy Baseline | 80.26% | 0.00% | 0.00% | 0.00% | 44.52% | Baseline |
| Logistic Regression | 94.18% | 79.33% | 95.35% | 86.61% | 91.44% | Candidate |
| **HistGradientBoosting** | **99.87%** | **99.48%** | **99.86%** | **99.67%** | **99.79%** | **CHAMPION (Selected)** |

## 2. Test Holdout Confusion Matrix

- True Negatives (Benign as Benign): 17,018
- False Positives (Benign as Malicious): 22
- False Negatives (Malicious as Benign): 6
- True Positives (Malicious as Malicious): 4,185

## 3. Operational Risk Analysis
- **False Alarm Rate**: 0.129%
- **Missed Intrusion Rate (FN)**: 0.143%
Both rates are rigorously tracked to ensure network operational stability and security containment.
