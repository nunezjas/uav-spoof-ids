# E1 Baseline Results — UAVIDS-2025
Weeks 1–3 deliverable

| Model    | Macro F1 | ± std  | Notes |
|----------|----------|--------|-------|
| XGBoost  | 1.0000   | 0.0000 | Saturated — simulation artifact |
| LightGBM | 0.9999   | 0.0001 | Saturated — simulation artifact |
| AD-GNN   | 0.9988   | 0.0003 | GAT+TCN re-implementation (scaled) |
| GCN      | 0.4401   | 0.0401 | Graph topology only — lower bound |

## Key Findings
- UAVIDS-2025 has 0 duplicates (AD-GNN paper reported 8,205 — different dataset version)
- No GPS/GNSS features, no spoofing class — reproducibility gap confirmed
- SrcPort, DstPort, MeanPacketSize have zero variance for Flooding and Sybil (NS-3 artifact)
- All tabular/temporal models saturate at F1≈1.0 — dataset not a meaningful benchmark
- GCN F1=0.44 proves graph topology alone insufficient for stealthy attacks
- AD-GNN TCN adds +0.56 F1 over GCN — temporal features carry the signal
- Unscaled AD-GNN causes loss explosion (~1B) — feature normalization critical
