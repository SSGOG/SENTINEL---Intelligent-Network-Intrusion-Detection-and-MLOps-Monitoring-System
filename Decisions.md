# Architecture Decisions and Methodology

## 1. Storage & Cloud Constraints
- **Zero-Budget Guardrail**: The 52 GB PCAPs and 2+ GB flow CSVs remain on local disk (`E:\downloads_2\SENTINELOPS`).
- **Cloud Usage Strategy**: Cloud deployment is strictly optional and credit-constrained. Only compact artifacts (trained model pipeline, feature schema, metrics, and lightweight demo sample) are staged for AWS deployment testing.
- **Rollback & Teardown**: All cloud resources deployed during staging tests are immediately de-provisioned to guarantee zero credit leakage.

## 2. Preprocessing & Leakage Prevention
- **Split Before Fit**: Train/Validation/Test splits are computed before fitting any scaler, imputer, or encoder.
- **Schema Normalization**: Strips leading/trailing whitespaces in column names and resolves the known duplicate `Fwd Header Length` in CIC-IDS2017.
- **Target Integrity**: Blank, missing, or malformed label rows are quarantined with documented evidence—never silently imputed as BENIGN.
