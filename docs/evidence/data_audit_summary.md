# CIC-IDS2017 Dataset Audit & Integrity Report

Generated automatically via `src/sentinel/data_validation.py`.

## 1. Primary Archive: `MachineLearningCSV/MachineLearningCVE`

| File Name | Rows | Cols | Blank Labels | Top Labels | Validation Status |
|---|---|---|---|---|---|
| Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv | 225,745 | 79 | 0 | DDoS: 128027, BENIGN: 97718 | VALID |
| Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv | 286,467 | 79 | 0 | BENIGN: 127537, PortScan: 158930 | VALID |
| Friday-WorkingHours-Morning.pcap_ISCX.csv | 191,033 | 79 | 0 | BENIGN: 189067, Bot: 1966 | VALID |
| Monday-WorkingHours.pcap_ISCX.csv | 529,918 | 79 | 0 | BENIGN: 529918 | VALID |
| Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv | 288,602 | 79 | 0 | BENIGN: 288566, Infiltration: 36 | VALID |
| Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv | 170,366 | 79 | 0 | BENIGN: 168186, Web Attack ï¿½ Brute Force: 1507, Web Attack ï¿½ XSS: 652 | VALID |
| Tuesday-WorkingHours.pcap_ISCX.csv | 445,909 | 79 | 0 | BENIGN: 432074, FTP-Patator: 7938, SSH-Patator: 5897 | VALID |
| Wednesday-workingHours.pcap_ISCX.csv | 692,703 | 79 | 0 | BENIGN: 440031, DoS Hulk: 231073, DoS slowloris: 5796 | VALID |

## 2. Thursday WebAttacks & Infiltration Analysis
- **Primary Thursday WebAttacks**: Audited independently with explicit label support.
- **Secondary GeneratedLabelledFlows Check**: Secondary file size: 92,030,223 bytes, rows: 458,968, blank labels: 288,602.

> [!IMPORTANT]
> The primary `MachineLearningCSV` dataset is verified intact. Under no circumstances are unknown/missing labels silently mapped to BENIGN.
