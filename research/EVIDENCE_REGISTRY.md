# DEMETER Evidence Registry — EVIDENCE_REGISTRY.md
**Updated: 2026-09-19**  
**Zero-Fabrication Rule: Active**

---

## How to Read This File

| Column | Meaning |
|---|---|
| Claim | The specific claim being tracked |
| Status | FACT/MEASURED · CALCULATED · CONFIGURED · NOT YET MEASURED · PROPOSED |
| Evidence Source | The specific file, line, or measurement |
| Experiment | Which experiment produced the evidence |

---

## Registry

| # | Claim | Status | Evidence Source | Experiment |
|---|---|---|---|---|
| 1 | 52/52 automated tests pass | FACT/MEASURED | pytest stdout, 2026-09-19 | EXP-SYS-001 |
| 2 | Test duration 5.89s (Python 3.11.9, pytest 9.1.1) | FACT/MEASURED | pytest stdout | EXP-SYS-001 |
| 3 | 16 YOLO classification/detection .pt files present | FACT/MEASURED | `ultralytics.YOLO()` loop on `models/` | EXP-AI-001 |
| 4 | tomato.pt: 11 disease classes confirmed | FACT/MEASURED | `model.names` from YOLO load | Code audit |
| 5 | Classification model size: 19.9 MB each | FACT/MEASURED | `os.path.getsize()` | EXP-AI-001 |
| 6 | rice.pt size: 38.6 MB, task=detect | FACT/MEASURED | `os.path.getsize()` + `model.task` | EXP-AI-001 |
| 7 | YOLO CPU mean latency (classify): 56.7–59.8 ms | FACT/MEASURED | N=100, `time.perf_counter_ns()` | EXP-AI-001 |
| 8 | YOLO CUDA mean latency (classify): 10.4–10.7 ms | FACT/MEASURED | N=100, `cuda.synchronize()` | EXP-AI-001 |
| 9 | YOLO CUDA FPS (classify): 93–97 FPS | CALCULATED | 1000 / mean_ms | EXP-AI-001 |
| 10 | rice.pt CPU mean latency: 595.3 ms | FACT/MEASURED | N=100, `time.perf_counter_ns()` | EXP-AI-001 |
| 11 | rice.pt CUDA mean latency: 27.1 ms | FACT/MEASURED | N=100, `cuda.synchronize()` | EXP-AI-001 |
| 12 | YOLO CUDA VRAM (classify): 72.5 MB | FACT/MEASURED | `torch.cuda.memory_allocated()` | EXP-AI-001 |
| 13 | rice.pt CUDA VRAM: 109.8 MB | FACT/MEASURED | `torch.cuda.memory_allocated()` | EXP-AI-001 |
| 14 | PaliGemma 3B model present and loadable | FACT/MEASURED | 3× safetensors = 10.89 GB; load succeeded | EXP-AI-003 |
| 15 | PaliGemma 3B load time: 7.55 s | FACT/MEASURED | `time.perf_counter()`, float16, CUDA | EXP-AI-003 |
| 16 | PaliGemma 3B VRAM: 5.45 GB | FACT/MEASURED | `torch.cuda.memory_allocated()` | EXP-AI-003 |
| 17 | PaliGemma 3B mean inference latency: 216.6 ms | FACT/MEASURED | N=20, `time.perf_counter_ns()` + cuda.synchronize() | EXP-AI-003 |
| 18 | PaliGemma 3B P95 latency: 228.5 ms | FACT/MEASURED | N=20 timed distribution | EXP-AI-003 |
| 19 | No labelled test dataset in repository | FACT/MEASURED | Filesystem scan | EXP-AI-002 |
| 20 | Disease classification accuracy | NOT YET MEASURED | No test dataset — BLOCKER | EXP-AI-002 |
| 21 | Disease Precision / Recall / F1 | NOT YET MEASURED | No test dataset | EXP-AI-002 |
| 22 | Weather observations: 14,957 records | FACT/MEASURED | SQLite COUNT(*) | EXP-DATA-001 |
| 23 | Weather forecasts: 104,685 records | FACT/MEASURED | SQLite COUNT(*) | EXP-DATA-001 |
| 24 | Weather collection span: 21.96 days | CALCULATED | MAX(ts) - MIN(ts) in seconds / 86400 | EXP-DATA-001 |
| 25 | Zero null values in all 9 weather fields | FACT/MEASURED | SQLite NULL COUNT per field | EXP-DATA-001 |
| 26 | 732 duplicate weather records | FACT/MEASURED | SQLite GROUP BY timestamp+lat+lon | EXP-DATA-001 |
| 27 | 271 sub-900 hPa pressure outliers | FACT/MEASURED | SQLite WHERE pressure < 900 | EXP-DATA-001 |
| 28 | Mean sampling interval: 54.98 s | CALCULATED | Successive timestamp differences | EXP-DATA-001 |
| 29 | Sampling interval std dev: 1224.89 s | CALCULATED | std(intervals) | EXP-DATA-001 |
| 30 | 381 unique geographic locations | FACT/MEASURED | SQLite DISTINCT ROUND(lat,4)||lon | EXP-DATA-001 |
| 31 | GPU: NVIDIA RTX 3050 6GB | FACT/MEASURED | `torch.cuda.get_device_name(0)` | EXP-AI-001 |
| 32 | GPU VRAM total: 6.0 GB | FACT/MEASURED | `torch.cuda.get_device_properties(0).total_memory` | EXP-AI-001 |
| 33 | CPU: Intel i5-13420H | FACT/MEASURED | `platform.processor()` | EXP-AI-001 |
| 34 | PyTorch 2.11.0+cu128, CUDA 12.8 | FACT/MEASURED | `torch.__version__`, `torch.version.cuda` | EXP-AI-001 |
| 35 | AI router failover latency (EXP-NET-001) | NOT YET MEASURED | Script ready | EXP-NET-001 |
| 36 | ESP32 actual telemetry rate | NOT YET MEASURED | Hardware required | EXP-IOT-001 |
| 37 | Motor ground speed (m/s) | NOT YET MEASURED | Hardware required | EXP-ROB-001 |
| 38 | Power consumption (W) | NOT YET MEASURED | Hardware required | EXP-ROB-002 |
| 39 | Battery runtime (h) | NOT YET MEASURED | Hardware required | EXP-ROB-003 |
| 40 | GPS accuracy (CEP95) | NOT YET MEASURED | Hardware + outdoors required | EXP-GPS-001 |
| 41 | Field navigation accuracy | NOT YET MEASURED | Hardware + field required | EXP-FLD-001 |
| 42 | Spray deposition accuracy | NOT YET MEASURED | Hardware + spray system required | EXP-SPRAY-001 |
| 43 | DAVE-2 trained driving weights | NOT YET MEASURED | Only 1 sample in DB; random weights | — |
| 44 | Depth estimation metric accuracy | NOT YET MEASURED | No ground truth depth data | — |
| 45 | ESP32-S3 PWM 1 kHz configured | CONFIGURED | `#define PWM_FREQ_HZ 1000` in firmware | Code audit |
| 46 | ESP32-S3 telemetry target 50 Hz | CONFIGURED | `#define TELEMETRY_STREAM_HZ 50` | Code audit |
| 47 | BME280 @ 0x76, BH1750 @ 0x23 | CONFIGURED | `#define BME280_ADDR 0x76` in firmware | Code audit |
| 48 | 4-channel active-LOW relay system | CONFIGURED | Lines 49–54, `esp32_master.ino` | Code audit |
| 49 | AI router: 5-provider priority chain | CONFIGURED | `ai_router.py` `build_providers()` | Code audit |
| 50 | Multi-provider failover logic implemented | CONFIGURED | `mark_rate_limited()` + priority loop | Code audit |
| 51 | PaliGemma architecture: SigLIP + Gemma | CONFIGURED | `models/paligemma/config.json` | Code audit |
| 52 | TinyML weights: Xavier-random (not trained) | FACT | `_init_pretrained_weights()` uses random seed | Code audit |
| 53 | DAVE-2 weights: Random (not trained) | FACT | No pre-loaded weights; 1 training sample | Code audit |
| 54 | VLA engine: keyword-rule-based (not learned) | FACT | `vla_engine.py` uses `prompt_lower` keyword match | Code audit |
