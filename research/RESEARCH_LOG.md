# DEMETER Master Experiment Ledger — RESEARCH_LOG.md
**Updated: 2026-09-19**

---

## Section 1: Baseline Audit Summary

| Item | Status | Date | Notes |
|---|---|---|---|
| Complete codebase audit | DONE | 2026-09-19 | All modules read |
| Firmware full audit | DONE | 2026-09-19 | `esp32_master.ino` 586 lines reviewed |
| Test suite execution | DONE | 2026-09-19 | 52/52 pass, 5.89s |
| Model inventory | DONE | 2026-09-19 | 16 YOLO .pt + PaliGemma 3B confirmed |
| Database audit | DONE | 2026-09-19 | 14,957 obs, 104,685 forecasts |
| Evidence registry | DONE | 2026-09-19 | See EVIDENCE_REGISTRY.md |
| DEMETER_ICARC_RESEARCH_AUDIT.md | DONE | 2026-09-19 | Full 17-section audit in research/ |

---

## Section 2: Claim Taxonomy

### FACT / MEASURED
A value from an actual measurement or database query. Can enter a research paper.

### CONFIGURED
A value specified in firmware, config files, or code constants. Describes design intent, not verified behaviour. Must be labelled as "configured" or "nominal", not presented as measured performance.

### CALCULATED
A value derived from measured data via a reproducible formula (e.g., FPS = 1000 / mean_ms). Can be cited if the source measurements are cited.

### NOT YET MEASURED
The experiment has not been executed. This value CANNOT appear in a paper without this label.

### PROPOSED
Architecture or feature exists in code but has not been demonstrated with empirical evidence.

---

## Section 3: Experiment Ledger

| ID | Title | Status | Date | Evidence File | N |
|---|---|---|---|---|---|
| EXP-SYS-001 | Automated Regression Suite | COMPLETE | 2026-09-19 | pytest stdout | 52 tests |
| EXP-AI-001 | YOLO Inference Latency Benchmark | COMPLETE | 2026-09-19 | `research/data/raw/EXP_AI_001_raw_*.csv` | N=100 per model |
| EXP-AI-002 | Model Accuracy Evaluation | BLOCKED | 2026-09-19 | `research/data/EXP_AI_002_dataset_audit.json` | No test dataset |
| EXP-AI-003 | PaliGemma 3B Inference Benchmark | COMPLETE | 2026-09-19 | `research/data/EXP_AI_003_paligemma.json` | N=20 |
| EXP-DATA-001 | Weather Database Audit | COMPLETE | 2026-09-19 | `research/data/EXP_DATA_001_weather_audit_*.json` | Full DB |
| EXP-NET-001 | AI Router Failover Latency | PENDING | — | Script ready at `research/exp_net_001_router_failover.py` | N=50 planned |
| EXP-IOT-001 | ESP32 Telemetry Rate Measurement | PENDING | — | Requires hardware | N=15,000+ planned |
| EXP-ROB-001 | Motor Speed Measurement | PENDING | — | Requires hardware | N=5 per PWM level |
| EXP-ROB-002 | Power Consumption | PENDING | — | Requires hardware | 3 repetitions |
| EXP-ROB-003 | Battery Runtime | PENDING | — | Requires hardware | 3 cycles |
| EXP-GPS-001 | GPS Accuracy | PENDING | — | Requires hardware outdoors | N=200 static |
| EXP-FLD-001 | Field Navigation Accuracy | PENDING | — | Requires full hardware + field | N=5 missions |
| EXP-SPRAY-001 | Spray Deposition Accuracy | PENDING | — | Requires spray subsystem | N=10 per distance |

---

## Section 4: Key Experimental Results

### EXP-AI-001 — YOLO Latency Key Findings
- Classification models (19.9 MB): **~57 ms CPU / ~10.5 ms CUDA** (mean, N=100)
- Detection model rice.pt (38.6 MB): **595 ms CPU / 27 ms CUDA** (mean, N=100)
- GPU speedup ratio: ~5.5× for classification; ~22× for detection
- CUDA VRAM: 72.5 MB per classification model; 109.8 MB for detection
- Hardware: Intel i5-13420H (CPU) / NVIDIA RTX 3050 6GB (CUDA)

### EXP-AI-003 — PaliGemma 3B Key Findings
- Model: `paligemma-3b-pt-224` (float16 on GPU)
- Load time: **7.55 s**
- VRAM: **5.45 GB** (leaves 0.55 GB free on RTX 3050 6GB)
- Mean inference latency: **216.6 ms** (N=20, synthetic image, max_new_tokens=20)
- P95 latency: 228.5 ms

### EXP-DATA-001 — Weather Database Key Findings
- 14,957 observations, 104,685 forecasts
- 21.96-day collection span
- 0% missing values in all numeric fields
- 732 duplicate records (timestamp+lat+lon)
- 271 sub-900 hPa pressure outliers (data quality issue)
- Highly irregular sampling: median 0.15s, std dev 1224s — not uniform time-series

---

## Section 5: Specification Standards

All physical experiments must include:
- Research question
- Hypothesis
- Independent / Dependent / Controlled variables
- Required instruments
- Sample sizes (N)
- Exact procedure
- Raw data format
- Statistical calculations
- Acceptance / rejection criteria
- Limitations
