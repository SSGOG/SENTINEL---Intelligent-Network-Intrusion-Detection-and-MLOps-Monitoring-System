# Champion Model Holdout Evaluation

Model: `XGBClassifier`. Evaluated on the held-out 10% test split (283,075 flows) using the raw imputed feature values consumed during training and serving.

| Accuracy | Precision | Recall | F1-Score | Macro-F1 | ROC-AUC |
|---:|---:|---:|---:|---:|---:|
| 99.921% | 99.623% | 99.977% | 99.800% | 99.875% | 99.997% |

## Test Holdout Confusion Matrix

- True Negatives (Benign as Benign): 227,099
- False Positives (Benign as Malicious): 211
- False Negatives (Malicious as Benign): 13
- True Positives (Malicious as Malicious): 55,752

## Operational Error Rates
- **False Alarm Rate**: 0.093%
- **Missed Intrusion Rate (FN)**: 0.023%
Review false positives and false negatives as part of operational monitoring.
