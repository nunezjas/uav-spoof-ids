# E1 Baseline Results — Complete
Weeks 1–3 deliverable

## Tabular Baselines (UAVIDS-2025)
| Model    | Macro F1 | ±std   | Mean FPR |
|----------|----------|--------|----------|
| XGBoost  | 1.0000   | 0.0000 | 0.000008 |
| LightGBM | 0.9999   | 0.0001 | 0.000017 |
| RealMLP  | 0.9979   | 0.0005 | 0.000519 |
| AD-GNN   | 0.9988   | 0.0003 | —        |
| GCN      | 0.4401   | 0.0401 | —        |

## Key Findings
1. Dataset saturated — XGBoost/LightGBM hit F1=1.0 due to NS-3 simulation artifacts
2. Three features have zero variance per class (SrcPort, DstPort, MeanPacketSize)
3. GCN F1=0.44 proves graph topology alone insufficient for stealthy attacks
4. AD-GNN TCN component adds +0.56 F1 over GCN — temporal features dominate
5. Unscaled AD-GNN: loss explosion (~1B) — normalization critical for reproduction
6. UAVIDS-2025 has 0 duplicates (AD-GNN reported 8,205 — different dataset version)
7. No GPS/GNSS features, no spoofing class — reproducibility gap confirmed

## TEXBAT Analysis
- Pseudorange shift: ds2=+112km, ds3=+65km, ds7=+38km
- Clock bias delta: <0.004s — matched-power spoofer evades clock-based detectors
- C/N0 delta: <2 dBHz — matched-power attack evades signal-strength detectors
- Implication: physics-informed IMU innovation monitoring required

## Datasets Ready
- UAVIDS-2025: 122,171 flows, cleaned, parquet saved
- Aissou GPS: 510,530 samples, 4 classes, parquet saved
- Whelan UAV: ULog files uploaded to Drive
- TEXBAT: 127,719 obs, 4 scenarios, parquet saved
