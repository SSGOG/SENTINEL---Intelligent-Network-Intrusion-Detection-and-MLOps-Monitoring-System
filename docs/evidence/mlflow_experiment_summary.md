# MLflow Experiment Tracking Evidence & Lineage

The current training stage logs the packaged champion as an `XGBClassifier` under the `SENTINEL` experiment.

## Current Champion
- **Model artifact**: `models/champion_model.joblib`
- **Feature contract**: 78 ordered numeric features from `data/processed/feature_schema.json`
- **Training input**: Median-imputed, unscaled feature arrays
- **Validation provenance**: `reports/metrics/model_selection_manifest.json`
- **Holdout evaluation**: `reports/metrics/test_holdout_evaluation.json`
- **Holdout evidence**: `docs/evidence/model_evaluation_summary.md`

Previous experiment notes and older evaluation files refer to a HistGradientBoosting model and a different holdout size. They are historical records and do not describe the currently packaged champion.
