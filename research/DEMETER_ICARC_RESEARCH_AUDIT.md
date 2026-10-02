# DEMETER ICARC 2027 — Complete Research-Readiness Audit Report
**Audit Date:** 2026-09-19  
**Auditor Role:** DEMETER ICARC 2027 Research Validation Engineer  
**Zero-Fabrication Rule:** Active — every metric in this document is sourced from actual measurements, source code, database queries, or automated benchmark logs.  
**Target Conference:** ICARC 2027 (IEEE Format, 6 pages max)

---

## 1. Executive Summary

DEMETER is an autonomous agricultural robotic system comprising a dual-tier edge architecture (ESP32-S3 microcontroller + host laptop), a suite of 16 fine-tuned YOLO plant disease classification models, a PaliGemma 3B zero-shot vision-language model, custom neural networks for depth estimation and autonomous driving, a TinyML sensor classifier, a multi-provider resilient AI router, and an integrated weather intelligence database.

**Audit verdict:** The project has a substantial implemented software base with 52/52 automated tests passing. Five experiments were successfully executed this session, yielding real measured performance data for the first time. However, **the single most critical missing evidence item that prevents any accuracy claim is the absence of a labelled holdout test dataset** for the 16 YOLO disease classification models.

| Domain | Implemented | Tested | Measured | Paper-Ready |
| :--- | :---: | :---: | :---: | :---: |
| Core software architecture | YES | YES (52/52) | YES | **PARTIAL** |
| YOLO inference latency | YES | YES | **YES (new)** | **YES** |
| PaliGemma inference latency | YES | YES | **YES (new)** | **YES** |
| Disease classification accuracy | YES (code) | NO (no dataset) | **NO** | **NO** |
| Weather data collection | YES | YES | **YES (new)** | **YES (descriptive)** |
| AI router failover | YES | Partial | NOT YET | PARTIAL |
| Hardware telemetry | YES (configured) | NO (hardware) | **NO** | **NO** |
| Physical field performance | YES (design) | NO | **NO** | **NO** |

---

## 2. Current System Capabilities

### 2.1 Hardware Architecture (`esp32/esp32_master/esp32_master.ino`)

| Specification | Value | Classification |
| :--- | :--- | :--- |
| Microcontroller | ESP32-S3 N16R8 | `[CONFIGURED]` — from `#define CPU_STABLE_FREQ_MHZ 160` |
| Core architecture | Dual Tensilica Xtensa LX7, FreeRTOS | `[CONFIGURED]` — Core 0: Net/Cam, Core 1: Sensors/Motors |
| Motor drivers | BTS7960 43A Dual H-Bridge | `[CONFIGURED]` — from firmware |
| PWM Frequency | 1000 Hz, 8-bit | `[CONFIGURED]` — `#define PWM_FREQ_HZ 1000` |
| Relay system | 4-channel active-LOW, 0ms boot clamp | `[CONFIGURED]` — GPIO 4,5,6,7 |
| Sensor bus | I2C @ 100 kHz (SDA:21, SCL:47) | `[CONFIGURED]` — from firmware |
| BME280 sensor | Temp/Humidity/Pressure @ 0x76 | `[CONFIGURED]` |
| BH1750 sensor | Ambient light @ 0x23 | `[CONFIGURED]` |
| GPS | TinyGPS++, HardwareSerial (GPIO 41/42) | `[CONFIGURED]` |
| Telemetry rate target | 50 Hz | `[CONFIGURED]` — `#define TELEMETRY_STREAM_HZ 50` |
| WiFi | IEEE 802.11 b/g/n (Station mode) | `[CONFIGURED]` |
| TCP telemetry port | 5000 | `[CONFIGURED]` |
| Motor RPM / ground speed | NOT YET MEASURED | `[NOT YET MEASURED]` |
| Power consumption (W) | NOT YET MEASURED | `[NOT YET MEASURED]` |
| Battery runtime (hours) | NOT YET MEASURED | `[NOT YET MEASURED]` |
| GPS accuracy (CEP95) | NOT YET MEASURED | `[NOT YET MEASURED]` |
| Actual telemetry rate (Hz) | NOT YET MEASURED | `[NOT YET MEASURED]` |

> [!CAUTION]
> The firmware configures 50 Hz telemetry. This is a **target**, not a measured achievement. Actual UART jitter, OS scheduling, and WiFi stack overhead have **not been measured**.

### 2.2 Host / Edge Compute Layer

| Component | Specification | Classification |
| :--- | :--- | :--- |
| CPU | Intel Core i5-13420H (Intel64 Family 6, Model 186) | `[FACT / MEASURED]` — from Python `platform.processor()` |
| GPU | NVIDIA GeForce RTX 3050 6GB Laptop GPU | `[FACT / MEASURED]` — from `torch.cuda.get_device_name(0)` |
| GPU VRAM | 6.0 GB total | `[FACT / MEASURED]` — from `torch.cuda.get_device_properties(0).total_memory` |
| OS | Windows 10 (build 26100) | `[FACT / MEASURED]` — from `platform.platform()` |
| Python | 3.11.9 | `[FACT / MEASURED]` |
| PyTorch | 2.11.0+cu128 | `[FACT / MEASURED]` |
| CUDA toolkit | 12.8 | `[FACT / MEASURED]` |
| Ultralytics | 8.4.118 | `[FACT / MEASURED]` |
| OpenCV | 4.13.0 | `[FACT / MEASURED]` |
| NumPy | 2.4.6 | `[FACT / MEASURED]` |
| Transformers | 5.5.4 | `[FACT / MEASURED]` |

---

## 3. Verified Evidence (What Can Enter a Paper)

| Claim | Value | Evidence Source | Experiment |
| :--- | :--- | :--- | :--- |
| Software regression stability | 52/52 tests pass in 5.89s | pytest 9.1.1 stdout | EXP-SYS-001 |
| Weather observations collected | 14,957 records | SQLite query (`weather_history.db`) | EXP-DATA-001 |
| Weather forecasts stored | 104,685 records | SQLite query (`weather_history.db`) | EXP-DATA-001 |
| Weather collection span | 21.96 days (2026-08-28 to 2026-09-19) | SQLite timestamp range | EXP-DATA-001 |
| Zero null values in weather observations | 0 nulls across all 9 numeric fields | SQLite NULL count queries | EXP-DATA-001 |
| Unique geographic locations logged | 381 distinct lat/lon pairs (4dp) | SQLite distinct count | EXP-DATA-001 |
| Duplicate weather records present | 732 duplicate rows | SQLite GROUP BY query | EXP-DATA-001 |
| Pressure value outliers present | 271 records below 900 hPa | SQLite range check | EXP-DATA-001 |
| 16 YOLO classification models loaded | 16 `.pt` files confirmed | `ultralytics.YOLO()` + `model.names` | EXP-AI-001 |
| YOLO CPU mean latency (classification models) | 56.7–59.8 ms (varies by model) | N=100 timed iterations | EXP-AI-001 |
| YOLO CPU FPS (classification models) | 16.7–17.6 FPS | Calculated: 1000 / mean_ms | EXP-AI-001 |
| YOLO CUDA mean latency (classification models) | 10.4–10.7 ms (varies by model) | N=100 GPU-synced iterations | EXP-AI-001 |
| YOLO CUDA FPS (classification models) | 93.0–96.6 FPS | Calculated: 1000 / mean_ms | EXP-AI-001 |
| rice.pt CPU mean latency (detection model) | 595.3 ms | N=100 timed iterations | EXP-AI-001 |
| rice.pt CUDA mean latency (detection model) | 27.1 ms | N=100 GPU-synced iterations | EXP-AI-001 |
| YOLO CUDA VRAM usage (classification) | 72.5 MB per model (allocated) | `torch.cuda.memory_allocated()` | EXP-AI-001 |
| YOLO CUDA VRAM usage (rice detection) | 109.8 MB | `torch.cuda.memory_allocated()` | EXP-AI-001 |
| PaliGemma 3B model load time | 7.55 s (float16, CUDA) | `time.perf_counter()` | EXP-AI-003 |
| PaliGemma 3B VRAM usage | 5.45 GB (float16, CUDA) | `torch.cuda.memory_allocated()` | EXP-AI-003 |
| PaliGemma 3B mean inference latency | 216.6 ms (N=20, image prompt) | `time.perf_counter_ns()` + `cuda.synchronize()` | EXP-AI-003 |
| PaliGemma 3B P95 latency | 228.5 ms | Measured from 20-trial distribution | EXP-AI-003 |
| No labelled test dataset exists | 0 dataset directories, 26 unrelated images | Filesystem scan | EXP-AI-002 |
| Multi-provider AI failover logic | Code verified functional (Groq→Gemini→…) | `ai_router.py` code audit + `prove_system.py` | Code audit |
| ESP32-S3 MCU specifications | Dual LX7 @ 160 MHz, PWM 1 kHz, 4-relay | `esp32_master.ino` source | Code audit |

---

## 4. Unverified Claims (Cannot Enter a Paper)

| Claim | Why Unverified | What is Required |
| :--- | :--- | :--- |
| Disease classification accuracy (any model) | No labelled test dataset exists | Reconstruct/provide holdout splits from training sources |
| Disease classification Precision/Recall/F1 | No labelled test dataset exists | Same as above |
| PaliGemma disease-detection accuracy | No labelled anomaly test protocol | Design zero-shot evaluation with ground-truth labels |
| ESP32 telemetry actual rate | No hardware connected | Physical serial monitor + timestamp logging |
| Motor speed / ground speed | Not physically measured | Encoder or ground-truth ruler test |
| Battery runtime | Not measured | Full discharge log under continuous load |
| Power consumption | Not measured | USB power meter or current probe |
| GPS accuracy | Not measured | Static/dynamic NMEA log vs. known reference |
| Navigation accuracy | Not measured | Physical field trial with ground truth |
| Spray precision | Not measured | Deposition audit on test bench |
| AI router latency (EXP-NET-001) | Script created; awaiting execution | Run `research/exp_net_001_router_failover.py` |
| Depth estimation accuracy | No ground truth depth data | Stereo/lidar ground truth required |
| Steering/driving accuracy | No annotated driving data | Physical driving trial with recorded GPS track |

---

## 5. AI System Evidence

### 5.1 EXP-AI-001 — YOLO Inference Latency Benchmark
**Status: COMPLETED — 2026-09-19**  
**Command:** `python research/exp_ai_001_benchmark.py`  
**Protocol:** 10 warm-up + N=100 steady-state iterations, batch=1, 224×224 synthetic input  
**Evidence files:** `research/data/raw/EXP_AI_001_raw_2026-09-19T134719.csv` | `research/data/EXP_AI_001_summary_2026-09-19T134719.json`

**CPU Results (Intel i5-13420H):**
| Model | Classes | Mean (ms) | Median (ms) | Std (ms) | P95 (ms) | FPS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Anthurium_best | 10 | 58.08 | — | — | 64.24 | 17.22 |
| brinjai | 14 | 57.29 | — | — | 60.47 | 17.46 |
| cabbage_best | 8 | 57.70 | — | — | 62.56 | 17.33 |
| capsium | 2 | 59.12 | — | — | 63.42 | 16.91 |
| carrot_best | 2 | 57.76 | — | — | 61.33 | 17.31 |
| cauliflower_best | 5 | 57.60 | — | — | 61.93 | 17.36 |
| chilli | 8 | 57.65 | — | — | 61.84 | 17.35 |
| corn | 4 | 59.76 | — | — | 63.12 | 16.73 |
| lettuce_best | 8 | 56.73 | — | — | 60.51 | 17.63 |
| mushroom_best | 2 | 57.93 | — | — | 61.76 | 17.26 |
| potato | 3 | 57.22 | — | — | 61.40 | 17.48 |
| radish_best | 5 | 57.45 | — | — | 60.57 | 17.41 |
| rice (**detect**) | 3 | **595.30** | — | — | **605.02** | **1.68** |
| rose_best | 3 | 56.99 | — | — | 61.05 | 17.55 |
| tea_best | 6 | 57.29 | — | — | 61.73 | 17.46 |
| tomato | 11 | 57.80 | — | — | 61.21 | 17.30 |

**CUDA Results (NVIDIA RTX 3050 6GB):**
| Model | Classes | Mean (ms) | P95 (ms) | FPS | VRAM (MB) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Anthurium_best | 10 | 10.36 | 10.60 | 96.57 | 72.5 |
| brinjai | 14 | 10.54 | 10.82 | 94.87 | 72.5 |
| cabbage_best | 8 | 10.50 | 10.78 | 95.26 | 72.5 |
| capsium | 2 | 10.49 | 10.88 | 95.35 | 72.5 |
| carrot_best | 2 | 10.75 | 11.08 | 93.03 | 72.5 |
| cauliflower_best | 5 | 10.51 | 10.81 | 95.18 | 72.5 |
| chilli | 8 | 10.45 | 10.73 | 95.73 | 72.5 |
| corn | 4 | 10.44 | 10.72 | 95.76 | 72.5 |
| lettuce_best | 8 | 10.39 | 10.66 | 96.22 | 72.5 |
| mushroom_best | 2 | 10.37 | 10.65 | 96.46 | 72.5 |
| potato | 3 | 10.70 | 10.93 | 93.48 | 72.5 |
| radish_best | 5 | 10.61 | 10.78 | 94.26 | 72.5 |
| rice (**detect**) | 3 | **27.14** | **27.40** | **36.85** | **109.8** |
| rose_best | 3 | 10.42 | 10.68 | 95.95 | 72.5 |
| tea_best | 6 | 10.37 | 10.62 | 96.40 | 72.5 |
| tomato | 11 | 10.54 | 11.81 | 94.84 | 72.5 |

> [!IMPORTANT]
> `rice.pt` is a **detection** model (not classification). Its CPU latency (595 ms) is ~10× higher than classification models. This is architecturally expected but must be disclosed in any paper claiming a uniform latency figure.

> [!WARNING]
> These latency figures are measured on **random synthetic 224×224 images** — not on real crop disease images. Real-world latency may differ marginally due to image content variation and preprocessing pipelines.

### 5.2 EXP-AI-002 — Model Accuracy Evaluation
**Status: BLOCKED — NO TEST DATASET**  
**Finding:** Zero labelled test/validation image directories exist in the repository. Only 26 image files are present project-wide (none structured as a classification test set). The 16 YOLO models cannot be evaluated for accuracy until labelled holdout splits are provided.  
**Classification:** `[NOT YET MEASURED]`

### 5.3 EXP-AI-003 — PaliGemma 3B Inference Benchmark
**Status: COMPLETED — 2026-09-19**  
**Evidence file:** `research/data/EXP_AI_003_paligemma.json`

| Metric | Value | Classification |
| :--- | :--- | :--- |
| Model | PaliGemma 3B (`paligemma-3b-pt-224`) | `[FACT / MEASURED]` |
| Model size (FP32) | 10.89 GB | `[FACT / MEASURED]` |
| Model size (FP16, loaded) | 5.45 GB VRAM | `[FACT / MEASURED]` |
| Load time to GPU | 7.55 s | `[FACT / MEASURED]` |
| Input resolution | 224 × 224 | `[CONFIGURED]` |
| Prompt | "Is this plant healthy?" | `[CONFIGURED]` |
| Warm-up | 3 passes | `[CONFIGURED]` |
| Measurement iterations | N = 20 | `[CONFIGURED]` |
| Mean inference latency | **216.64 ms** | `[FACT / MEASURED]` |
| Median inference latency | **216.29 ms** | `[FACT / MEASURED]` |
| Std deviation | **4.24 ms** | `[FACT / MEASURED]` |
| Min latency | 211.50 ms | `[FACT / MEASURED]` |
| Max latency | 228.54 ms | `[FACT / MEASURED]` |
| P95 latency | 228.54 ms | `[FACT / MEASURED]` |
| Disease detection accuracy | NOT YET MEASURED | `[NOT YET MEASURED]` |

> [!NOTE]
> PaliGemma was loaded at float16 on the RTX 3050. The model occupies 5.45 GB of the 6.0 GB available VRAM — leaving only 0.55 GB free, which may cause OOM under batch or longer context workloads. These latencies are measured on a synthetic random image, not on real plant disease images. Disease-detection accuracy is a separate experiment requiring labelled test images.

---

## 6. IoT Evidence

### 6.1 Telemetry Architecture (`esp32_master.ino`)
- **Target rate:** 50 Hz — `[CONFIGURED]`
- **Actual measured rate:** `NOT YET MEASURED` — `[NOT YET MEASURED]`
- **UART baud rate:** 115200 — `[CONFIGURED]`
- **Packet structure:** JSON with temperature, humidity, pressure, lux, UV, soil × 2, GPS, motor speeds, relay states, uptime, packet_seq — `[CONFIGURED]`
- **Telemetry data quality in practice:** `NOT YET MEASURED` (jitter, packet loss unknown)

### 6.2 Weather Intelligence Database (EXP-DATA-001)
**Status: COMPLETED — 2026-09-19**

| Metric | Value | Classification |
| :--- | :--- | :--- |
| Total weather observations | 14,957 records | `[FACT / MEASURED]` |
| Total forecast records | 104,685 records | `[FACT / MEASURED]` |
| Data collection span | 21.96 days | `[CALCULATED]` |
| Date range | 2026-08-28 to 2026-09-19 | `[FACT / MEASURED]` |
| Unique robot ID | DEMETER-01 only | `[FACT / MEASURED]` |
| Unique geographic locations | 381 distinct lat/lon pairs | `[FACT / MEASURED]` |
| Null values in all numeric fields | 0 (0.0%) | `[FACT / MEASURED]` |
| Duplicate records (timestamp+lat+lon) | 732 rows | `[FACT / MEASURED]` |
| Mean sampling interval | 54.98 s | `[CALCULATED]` |
| Median sampling interval | 0.15 s | `[CALCULATED]` — **high std dev (1224.89s) indicates highly irregular sampling** |
| Pressure outliers (< 900 hPa) | 271 records | `[FACT / MEASURED]` — requires investigation |

> [!WARNING]
> The median sampling interval (0.15 s) versus mean (54.98 s) and std dev (1224.89 s) indicate **highly irregular sampling** — not a clean time-series. This must be disclosed in any paper. The 732 duplicate records and 271 sub-900 hPa pressure readings also require cleaning before the dataset can be described as a validated scientific dataset.

---

## 7. Robotics Evidence

| Capability | Implementation Status | Test Status | Physical Measurement | Classification |
| :--- | :---: | :---: | :---: | :--- |
| BTS7960 motor control | IMPLEMENTED | Unit tested (simulation) | NOT MEASURED | `[CONFIGURED]` |
| Pure pursuit navigation | IMPLEMENTED | Unit tested (simulation) | NOT MEASURED | `[PROPOSED]` |
| Extended Kalman Filter pose estimation | IMPLEMENTED | Unit tested (simulation) | NOT MEASURED | `[PROPOSED]` |
| Coverage path planning | IMPLEMENTED | Unit tested (simulation) | NOT MEASURED | `[PROPOSED]` |
| VLA embodied action generation | IMPLEMENTED | Unit tested (keyword-based rules only) | NOT MEASURED | `[PROPOSED]` |
| Precision spray control | IMPLEMENTED | Unit tested (rule-based) | NOT MEASURED | `[PROPOSED]` |
| Optical flow obstacle detection | IMPLEMENTED | Unit tested (synthetic images) | NOT MEASURED | `[PROPOSED]` |
| DAVE-2 neural driving network | IMPLEMENTED | Unit tested (random weights, 1 sample in DB) | NOT MEASURED | `[PROPOSED]` |
| Digital twin synchronization | IMPLEMENTED | Unit tested (mocked) | NOT MEASURED | `[PROPOSED]` |

> [!CAUTION]
> The DAVE-2 network is initialized with **random Xavier-initialized weights**. The driving dataset contains only **1 sample**. No imitation learning or behavioral cloning training has been performed. Claims of autonomous neural driving are `[PROPOSED]` only.

---

## 8. Software Verification

**EXP-SYS-001 — Automated Regression Suite**  
**Status: COMPLETED — Executed twice (2026-09-19)**

```
Platform:  win32 — Python 3.11.9 — pytest-9.1.1
rootdir:   C:\Users\Pasindu\.gemini\antigravity\scratch\CropGuard
Collected: 52 items
Passed:    52
Failed:    0
Skipped:   0
Duration:  5.89 s (second run, after import caching)
```
`[FACT / MEASURED]`

**Critical Note on Test Quality:**  
All 52 tests operate on:
- Synthetic random images (not real disease images)
- Rule-based/hardcoded logic (VLA keyword matching, not learned VLA)
- Mocked/simulated hardware connections (no physical ESP32 required)
- Xavier-initialized random weights (no trained model weights)

The tests verify **software contract satisfaction** (correct output types, range bounds, API surface consistency). They do **not** verify prediction quality, accuracy, or real-world efficacy. This distinction is essential for ICARC.

---

## 9. Hardware Verification

| Hardware Claim | Can Be Cited | Claim Type | Source |
| :--- | :---: | :--- | :--- |
| ESP32-S3 N16R8 selected | YES | `[CONFIGURED]` | `esp32_master.ino` header |
| PWM 1000 Hz, 8-bit set | YES | `[CONFIGURED]` | `#define PWM_FREQ_HZ 1000` |
| BTS7960 H-bridge selected | YES | `[CONFIGURED]` | Firmware comments & pin wiring |
| BME280 @ 0x76 configured | YES | `[CONFIGURED]` | `#define BME280_ADDR 0x76` |
| Active-LOW relay 0ms clamp | YES | `[CONFIGURED]` | Lines 49-54 in `.ino` |
| Motor RPM actual | NO | `[NOT YET MEASURED]` | Requires encoder or strobe test |
| Current draw (motors) | NO | `[NOT YET MEASURED]` | Requires DC clamp ammeter |
| Battery runtime | NO | `[NOT YET MEASURED]` | Requires discharge log |
| GPS fix time / accuracy | NO | `[NOT YET MEASURED]` | Requires NMEA logging outdoors |
| Telemetry actual Hz | NO | `[NOT YET MEASURED]` | Requires serial timestamp logging |

---

## 10. Missing Experiments (Blocker Level)

### BLOCKER — Cannot Write Paper Results Without These:
1. **EXP-AI-002**: Labelled test dataset for all 16 YOLO models — accuracy, Precision, Recall, F1, Confusion Matrix. **This is the #1 blocker.**
2. **EXP-NET-001**: AI router failover latency (N=50 trials, synthetic faults) — script is ready at `research/exp_net_001_router_failover.py`.
3. **EXP-IOT-001**: Actual ESP32 telemetry rate measurement (requires physical hardware connected).

### IMPORTANT — Needed to Support Robotics Claims:
4. **EXP-ROB-001**: Motor/robot speed measurement
5. **EXP-ROB-002**: Power consumption measurement
6. **EXP-GPS-001**: GPS positioning accuracy
7. **EXP-FLD-001**: Field navigation accuracy

---

## 11. Proposed Experiment Specifications

### EXP-NET-001 — AI Router Failover Latency
*(Script ready: `research/exp_net_001_router_failover.py`)*
- **Research question:** What is the empirical failover latency of the multi-provider AI router under HTTP 429 and timeout conditions?
- **Hypothesis:** Failover completes within 3 seconds in 95% of trials.
- **Independent variables:** Fault type (synthetic 429, timeout), provider pair
- **Dependent variables:** Total transaction latency (ms), success rate (%)
- **Controlled variables:** Fixed prompt, temperature=0, masked API keys
- **N:** 50 trials per fault type per provider pair
- **Data format:** CSV (trial_id, test_type, provider, fallback, elapsed_ms, success)
- **Statistical analysis:** Mean, median, std, P95, ECDF
- **Status:** READY TO EXECUTE

### EXP-IOT-001 — ESP32 Telemetry Rate Measurement
- **Research question:** Does the ESP32-S3 achieve the configured 50 Hz telemetry target under operational load?
- **Hypothesis:** Actual rate is between 40–50 Hz under WiFi + FreeRTOS scheduling overhead.
- **Independent variables:** CPU load state (idle vs. active motor control)
- **Dependent variables:** Packets/second, inter-packet interval (ms), jitter (std dev), packet loss rate
- **Controlled variables:** Fixed WiFi environment, fixed SSID, no camera streaming active
- **Required hardware:** ESP32-S3 board flashed with `esp32_master.ino`, USB serial connection to host
- **Measurement method:** PC-side serial timestamp logger (microsecond resolution) recording packet receipt times over 300 seconds
- **N:** Minimum 15,000 packets (5 minutes at target 50 Hz)
- **Data format:** CSV (seq_num, recv_timestamp_us, payload_size_bytes)
- **Statistical analysis:** Mean interval, std dev, jitter, packet loss count
- **Status:** HARDWARE REQUIRED

### EXP-ROB-001 — Motor and Ground Speed
- **Research question:** What is the actual ground speed (m/s) of DEMETER at different PWM duty cycles?
- **Hypothesis:** Speed increases approximately linearly with PWM duty cycle.
- **Independent variables:** PWM duty cycle (0, 64, 128, 192, 255 = 0%, 25%, 50%, 75%, 100%)
- **Dependent variables:** Measured ground speed (m/s), current draw (A)
- **Controlled variables:** Flat smooth surface, fully charged battery, ambient temperature 25°C
- **Required hardware:** Ruler or tape measure over 2m, stopwatch or high-speed camera, multimeter or DC clamp
- **N:** 5 runs per duty cycle level, bidirectional
- **Data format:** CSV (pwm_duty, run_id, distance_m, time_s, speed_ms, current_A)
- **Calculations:** `speed = distance / time`; mean and std dev per duty cycle
- **Status:** HARDWARE REQUIRED

### EXP-ROB-002 — Power Consumption
- **Research question:** What is the power draw of DEMETER in idle, driving, and peak actuation states?
- **Independent variables:** Operational state (idle WiFi, motors running, motors + pump + camera)
- **Dependent variables:** Voltage (V), Current (A), Power (W)
- **Required hardware:** USB power meter or DC inline power monitor (e.g., UM34C), fully charged battery
- **N:** 60-second average per state, 3 repetitions each
- **Calculations:** P (W) = V × I
- **Status:** HARDWARE REQUIRED

### EXP-ROB-003 — Battery Runtime
- **Research question:** What is the operational runtime of DEMETER under continuous mission load?
- **Independent variables:** Operational load (continuous navigation, periodic spraying)
- **Dependent variables:** Runtime until battery cutoff voltage (hours, minutes)
- **Required hardware:** Fully charged battery, running robot or resistive load, voltage monitor
- **N:** 3 full discharge cycles
- **Status:** HARDWARE REQUIRED

### EXP-GPS-001 — GPS Positioning Accuracy
- **Research question:** What is the actual GPS positioning accuracy (CEP95) of the GPS module configured in `esp32_master.ino`?
- **Hypothesis:** Accuracy is within 3–5 m CEP95 typical for consumer GNSS without DGPS.
- **Independent variables:** Static vs. dynamic mode, sky visibility (open vs. partial)
- **Dependent variables:** Latitude/longitude error vs. known reference point (m), HDOP value, fix time (s)
- **Required hardware:** ESP32 GPS module outdoors, known reference coordinate (surveyed or Google Maps), laptop serial logger
- **N:** 200 static readings at 3 known positions; 2 dynamic trajectory runs
- **Calculations:** Euclidean error in metres via haversine; CEP50, CEP95
- **Status:** HARDWARE REQUIRED

### EXP-FLD-001 — Field Navigation Accuracy
- **Research question:** How accurately does DEMETER follow a pre-planned waypoint trajectory in an actual agricultural field?
- **Dependent variables:** Cross-track error (m), waypoint arrival tolerance (m), completion rate (%)
- **Required hardware:** All hardware assembled, outdoor field or test area, GPS or manual measuring tape
- **N:** 5 full waypoint missions per trajectory type (straight, L-shape, coverage pattern)
- **Status:** HARDWARE + FULL INTEGRATION REQUIRED

### EXP-SPRAY-001 — Spray Deposition Accuracy
- **Research question:** What is the spray deposition accuracy of the precision spray subsystem on a target plant canopy?
- **Dependent variables:** Target coverage area (cm²), off-target deposition (%), nozzle pattern width
- **Required hardware:** Working spray subsystem, water-sensitive paper, calipers, balance scale
- **N:** 10 trials per distance (5, 10, 15, 20 cm nozzle-to-target)
- **Status:** HARDWARE + SPRAY SYSTEM REQUIRED

---

## 12. Research Contribution Candidates

### Candidate A — Multi-Crop Edge AI Disease Diagnosis
- **Available evidence:** 16 YOLO models loaded and latency-benchmarked; PaliGemma 3B inference measured. Architecture documented.
- **Missing evidence:** Test dataset (classification accuracy, F1) — **BLOCKER**. Without accuracy, this is an architecture description paper, not an AI results paper.
- **Research question:** Can edge-deployable YOLO classification models achieve diagnostic accuracy suitable for autonomous field use across 16 crop species under resource-constrained hardware?
- **Risk:** Cannot submit without EXP-AI-002.
- **Feasibility:** HIGH if test datasets can be reconstructed from Roboflow/Kaggle sources within 2 weeks.

### Candidate B — Edge AI Inference Benchmarking for Agricultural Robotics
- **Available evidence:** Complete latency benchmark across 16 models, CPU vs. CUDA comparison, PaliGemma 3B latency. All [FACT / MEASURED].
- **Missing evidence:** Comparison baseline (other methods on same hardware). Cannot claim "better" without it.
- **Research question:** What are the measured inference latency characteristics of YOLO classification and PaliGemma 3B VLM on an RTX 3050 6GB edge GPU for agricultural disease diagnosis?
- **Risk:** LOW on evidence side. Contribution may be limited if not combined with accuracy or field results.
- **Feasibility:** **HIGHEST** — data is already collected today.

### Candidate C — AI + IoT Agricultural Robotic Architecture
- **Available evidence:** Full system architecture implemented and software-verified; weather database with 14,957 observations; latency benchmarks; 52/52 tests passing.
- **Missing evidence:** Hardware performance measurements; AI accuracy; field demonstration.
- **Research question:** Can a zero-cost, resilient hybrid edge-cloud AI architecture support autonomous agricultural disease monitoring at low cost?
- **Risk:** MEDIUM — system description alone needs at least some measured field results to be compelling.
- **Feasibility:** MEDIUM.

### Candidate D — Resilient Multi-Provider AI Failover Architecture
- **Available evidence:** Architecture implemented in `ai_router.py`; logical failover verified via `prove_system.py`.
- **Missing evidence:** EXP-NET-001 latency measurements (script ready).
- **Research question:** Does a priority-tiered zero-cost multi-provider AI router provide statistically reliable service continuity for agricultural robotics under simulated upstream failures?
- **Risk:** LOW — EXP-NET-001 can be executed immediately.
- **Feasibility:** HIGH if run before paper submission.

### Candidate E — Autonomous Agricultural Perception and Navigation
- **Available evidence:** Architecture designed; unit tests for EKF, coverage planner, obstacle detector.
- **Missing evidence:** Physical field test results — `[NOT YET MEASURED]`. DAVE-2 has random weights.
- **Risk:** HIGH — no physical evidence available yet.
- **Feasibility:** LOW before ICARC 2027 without hardware investment.

### Candidate F — Multi-Modal Agricultural Decision Support
- **Available evidence:** Architecture for VLA, TinyML classifier, voice assistant, weather intelligence — all implemented and unit-tested.
- **Missing evidence:** End-to-end system evaluation with real data; accuracy of VLA and TinyML on real sensor readings.
- **Risk:** MEDIUM-HIGH — requires real deployment testing.
- **Feasibility:** MEDIUM.

---

## 13. ICARC Paper Readiness Assessment

### READY NOW (sufficient evidence exists)
- System architecture description with verified software component inventory
- YOLO inference latency table (CPU and CUDA) for 16 models — `[FACT / MEASURED]`
- PaliGemma 3B VLM inference latency on RTX 3050 — `[FACT / MEASURED]`
- Weather data collection volume and quality audit — `[FACT / MEASURED]`
- Software regression verification (52/52 tests) — `[FACT / MEASURED]`
- Hardware configuration table (firmware-sourced) — `[CONFIGURED]`

### NEEDS EXPERIMENTS (can be gathered before submission)
- AI router failover latency — EXP-NET-001 script ready
- YOLO model accuracy (accuracy/F1) — requires test dataset reconstruction
- ESP32 telemetry actual rate — requires hardware
- Comparison to baseline (needed for competitive claims)

### NOT YET SUPPORTED (physical hardware needed)
- Motor speed / ground speed
- Power consumption
- Battery runtime
- GPS accuracy
- Navigation/trajectory accuracy
- Spray deposition accuracy

### NOT SUITABLE AS A RESEARCH CLAIM (requires redesign of experiments)
- "DEMETER achieves X% accuracy" — no accuracy measurement exists
- "DEMETER is faster/better than existing systems" — no controlled comparison exists
- "50 Hz real-time telemetry" — only configured, not measured
- "The system is capable of autonomous navigation" — DAVE-2 has random weights and 1 training sample

---

## 14. Recommended Experimental Sequence

```
Priority 1 (This Week — Software Only):
  [1] EXP-NET-001: Run exp_net_001_router_failover.py (already written, ~1hr)
  [2] EXP-AI-002: Reconstruct test splits from Roboflow/Kaggle sources
                   for at least tomato, rice, potato, corn (most common)
                   Then run YOLO .val() on each test split

Priority 2 (This Month — Hardware Required):
  [3] EXP-IOT-001: Connect ESP32, run serial timestamp logger 5 min
  [4] EXP-ROB-001: Motor speed measurement at 5 PWM levels
  [5] EXP-GPS-001: Outdoor GPS accuracy at 3 known points

Priority 3 (Pre-Submission — Field):
  [6] EXP-FLD-001: Field navigation trial (5 missions)
  [7] EXP-SPRAY-001: Spray deposition test
```

---

## 15. Reproducibility Checklist

| Item | Status |
| :--- | :--- |
| All experiment scripts committed to `research/` | YES |
| Raw data saved to `research/data/raw/` | YES |
| Benchmark CSV with N=100 per model per device | YES |
| Random seed documented (seed=42 in benchmark) | YES |
| Library versions recorded | YES |
| Hardware identity recorded (GPU name, VRAM) | YES |
| All API keys masked in all logs | YES |
| Test dataset for accuracy evaluation | NO — REQUIRED |
| Physical experiment raw logs | NO — Hardware required |
| Trained DAVE-2 driving model weights | NO — Dataset too small |

---

## 16. Limitations

1. **TinyML classification rule override**: The `TinyMLSensorClassifier` hardcodes domain heuristics that override neural network outputs. Confidence scores reported by the classifier partially reflect these hard rules, not learned probabilities. This must be disclosed.
2. **Neural depth estimation (custom architecture)**: The `DepthEncoderDecoder` uses randomly initialized weights. Depth estimates are uncalibrated and have no ground-truth validation. This model is `[PROPOSED]` for research purposes.
3. **DAVE-2 driving network**: Randomly initialized, 1 training sample. Not a trained model.
4. **PaliGemma VRAM margin**: Only 0.55 GB VRAM free during inference. Long-context or batch scenarios will OOM.
5. **Weather data sampling irregularity**: Highly variable sampling intervals (median 0.15s, std 1224s) suggest polling bursts rather than a uniform time-series. Not suitable for time-series analyses without resampling and cleaning.
6. **Duplicate weather records**: 732 duplicates require deduplication before any published statistics.
7. **VLA action generation**: Uses keyword-matching rules, not a trained VLA model. Calling this "Vision-Language-Action" in a paper without a proper VLM-to-action model would be misleading.

---

## 17. Final Evidence Matrix

| # | Claim | Status | Experiment | Notes |
| :--- | :--- | :---: | :--- | :--- |
| 1 | 52/52 software tests passing | `FACT/MEASURED` | EXP-SYS-001 | 5.89s, Python 3.11.9 |
| 2 | 14,957 weather observations | `FACT/MEASURED` | EXP-DATA-001 | 21.96-day span |
| 3 | 104,685 forecast records | `FACT/MEASURED` | EXP-DATA-001 | 7-day lookahead |
| 4 | 0% missing in all 9 weather fields | `FACT/MEASURED` | EXP-DATA-001 | Good completeness |
| 5 | 732 duplicate weather records | `FACT/MEASURED` | EXP-DATA-001 | Data quality issue |
| 6 | 271 sub-900 hPa pressure outliers | `FACT/MEASURED` | EXP-DATA-001 | Requires investigation |
| 7 | YOLO CPU mean latency ~57 ms (classification) | `FACT/MEASURED` | EXP-AI-001 | N=100 per model |
| 8 | YOLO CUDA mean latency ~10.5 ms (classification) | `FACT/MEASURED` | EXP-AI-001 | N=100 per model |
| 9 | YOLO CUDA FPS ~95 (classification models) | `CALCULATED` | EXP-AI-001 | 1000/mean_ms |
| 10 | rice.pt detection CPU 595 ms | `FACT/MEASURED` | EXP-AI-001 | Different model type |
| 11 | rice.pt CUDA 27 ms | `FACT/MEASURED` | EXP-AI-001 | |
| 12 | PaliGemma 3B load time 7.55 s | `FACT/MEASURED` | EXP-AI-003 | float16, CUDA |
| 13 | PaliGemma 3B 5.45 GB VRAM | `FACT/MEASURED` | EXP-AI-003 | 0.55 GB headroom |
| 14 | PaliGemma 3B mean latency 216.6 ms | `FACT/MEASURED` | EXP-AI-003 | N=20, synthetic image |
| 15 | No labelled test dataset | `FACT/MEASURED` | EXP-AI-002 | BLOCKER |
| 16 | Disease accuracy (any model) | `NOT YET MEASURED` | EXP-AI-002 | Needs dataset |
| 17 | AI router failover latency | `NOT YET MEASURED` | EXP-NET-001 | Script ready |
| 18 | ESP32 actual telemetry Hz | `NOT YET MEASURED` | EXP-IOT-001 | Hardware required |
| 19 | Motor speed / torque | `NOT YET MEASURED` | EXP-ROB-001 | Hardware required |
| 20 | Battery runtime | `NOT YET MEASURED` | EXP-ROB-003 | Hardware required |
| 21 | GPS accuracy | `NOT YET MEASURED` | EXP-GPS-001 | Hardware required |
| 22 | Navigation field accuracy | `NOT YET MEASURED` | EXP-FLD-001 | Hardware required |
| 23 | Spray deposition accuracy | `NOT YET MEASURED` | EXP-SPRAY-001 | Hardware required |
| 24 | DAVE-2 driving model accuracy | `NOT YET MEASURED` | — | 1 training sample |
| 25 | DAVE-2 driving model trained | `NOT YET MEASURED` | — | Random weights |
| 26 | Depth estimation accuracy | `NOT YET MEASURED` | — | No ground truth |
| 27 | TinyML classification on real sensors | `NOT YET MEASURED` | — | Tested on simulated inputs only |

---

## Appendix A: Files Created This Session

| File | Purpose | Experiment |
| :--- | :--- | :--- |
| `research/RESEARCH_LOG.md` | Master experimental ledger | — |
| `research/EVIDENCE_REGISTRY.md` | Claim-to-evidence traceability matrix | — |
| `research/exp_ai_001_benchmark.py` | YOLO latency benchmark harness | EXP-AI-001 |
| `research/exp_ai_002_dataset_audit.py` | Test dataset availability audit | EXP-AI-002 |
| `research/exp_net_001_router_failover.py` | AI router failover benchmark | EXP-NET-001 |
| `research/exp_data_001_weather_audit.py` | Weather database audit | EXP-DATA-001 |
| `research/data/raw/EXP_AI_001_raw_*.csv` | N=100 raw latency records per model | EXP-AI-001 |
| `research/data/EXP_AI_001_summary_*.json` | Summary statistics | EXP-AI-001 |
| `research/data/EXP_AI_002_dataset_audit.json` | Dataset audit result | EXP-AI-002 |
| `research/data/EXP_AI_003_paligemma.json` | PaliGemma benchmark result | EXP-AI-003 |
| `research/data/EXP_DATA_001_weather_audit_*.json` | Weather database audit | EXP-DATA-001 |
