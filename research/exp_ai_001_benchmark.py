"""
EXP-AI-001: DEMETER YOLO Model Inference Latency & Resource Benchmark
======================================================================
Measures cold-start, warm-up, and steady-state inference latency for all 16
YOLO classification models on both CPU and CUDA (RTX 3050 6GB Laptop GPU).

Benchmark Protocol:
  - 10 mandatory warm-up passes (discarded from statistics)
  - N=100 timed inference iterations (steady-state)
  - All timings use time.perf_counter_ns() with torch.cuda.synchronize() for GPU
  - Input: synthetic 224x224 random uint8 image (consistent across all models)
  - batch_size = 1 (emulating real-time single-frame inference)
  - Results saved to: research/data/raw/EXP_AI_001_raw.csv
  - Summary saved to: research/data/EXP_AI_001_summary.json

Evidence classification: [FACT / MEASURED] upon completion.
"""

import os
import sys
import time
import json
import csv
import numpy as np
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]          # CropGuard/
MODELS_DIR = ROOT / "models"
RAW_DIR    = ROOT / "research" / "data" / "raw"
OUT_DIR    = ROOT / "research" / "data"
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

WARM_UP_N = 10
MEASURE_N = 100
INPUT_W, INPUT_H = 224, 224  # Standard crop-disease input resolution

# ── Environment info ─────────────────────────────────────────────────────────
import torch
import platform

RUN_TIMESTAMP = time.strftime("%Y-%m-%dT%H%M%S")
CUDA_AVAILABLE = torch.cuda.is_available()
GPU_NAME       = torch.cuda.get_device_name(0) if CUDA_AVAILABLE else "N/A"
GPU_VRAM_GB    = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if CUDA_AVAILABLE else 0

env_info = {
    "experiment_id": "EXP-AI-001",
    "date": time.strftime("%Y-%m-%d"),
    "run_timestamp": RUN_TIMESTAMP,
    "python_version": sys.version.split()[0],
    "pytorch_version": torch.__version__,
    "cuda_version": torch.version.cuda,
    "gpu_name": GPU_NAME,
    "gpu_vram_total_gb": GPU_VRAM_GB,
    "os": platform.platform(),
    "cpu": platform.processor(),
    "warm_up_iterations": WARM_UP_N,
    "measure_iterations": MEASURE_N,
    "input_resolution": f"{INPUT_W}x{INPUT_H}",
    "batch_size": 1
}

print("=" * 70)
print("EXP-AI-001: YOLO Inference Latency Benchmark")
print("=" * 70)
print(json.dumps(env_info, indent=2))
print()

# ── Load all .pt model files ─────────────────────────────────────────────────
from ultralytics import YOLO

model_files = sorted([f for f in os.listdir(MODELS_DIR) if f.endswith(".pt")])
print(f"Found {len(model_files)} model files: {model_files}\n")

# ── Benchmark function ────────────────────────────────────────────────────────
def benchmark_model(model_path: str, device: str, n_measure: int, n_warmup: int):
    """
    Loads a YOLO model onto `device`, runs n_warmup warm-up passes,
    then n_measure timed passes. Returns (latencies_ms_list, vram_allocated_mb).
    """
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Cold-start timing
    t_cold_start = time.perf_counter_ns()
    model = YOLO(model_path)
    t_cold_end = time.perf_counter_ns()
    cold_start_ms = (t_cold_end - t_cold_start) / 1e6

    # Move model to device (YOLO predict() uses device kwarg)
    # Create synthetic image
    rng = np.random.default_rng(seed=42)
    dummy_img = rng.integers(0, 256, (INPUT_H, INPUT_W, 3), dtype=np.uint8)

    # Warm-up passes (not timed, not recorded)
    for _ in range(n_warmup):
        _ = model.predict(dummy_img, device=device, verbose=False)

    # Synchronize GPU before starting measurements
    if device == "cuda" and torch.cuda.is_available():
        torch.cuda.synchronize()

    # Measure VRAM after warmup
    vram_mb = 0.0
    if device == "cuda" and torch.cuda.is_available():
        vram_mb = round(torch.cuda.memory_allocated() / (1024 * 1024), 2)

    # Steady-state timed iterations
    latencies_ms = []
    for i in range(n_measure):
        if device == "cuda" and torch.cuda.is_available():
            torch.cuda.synchronize()
        t0 = time.perf_counter_ns()
        _ = model.predict(dummy_img, device=device, verbose=False)
        if device == "cuda" and torch.cuda.is_available():
            torch.cuda.synchronize()
        t1 = time.perf_counter_ns()
        latencies_ms.append((t1 - t0) / 1e6)

    return cold_start_ms, latencies_ms, vram_mb


# ── Run benchmarks ────────────────────────────────────────────────────────────
devices = ["cpu"]
if CUDA_AVAILABLE:
    devices.append("cuda")

raw_records = []
summary_results = []

for device in devices:
    print(f"\n{'─'*60}")
    print(f"DEVICE: {device.upper()} {'(' + GPU_NAME + ')' if device == 'cuda' else ''}")
    print(f"{'─'*60}")

    for fname in model_files:
        model_path = str(MODELS_DIR / fname)
        model_name = fname.replace(".pt", "")
        size_mb    = round(os.path.getsize(model_path) / (1024 * 1024), 1)

        print(f"  Benchmarking: {fname} ({size_mb} MB) on {device} ...", end=" ", flush=True)

        try:
            cold_ms, latencies, vram_mb = benchmark_model(
                model_path, device, MEASURE_N, WARM_UP_N
            )

            lat_arr   = np.array(latencies)
            mean_ms   = round(float(np.mean(lat_arr)), 3)
            median_ms = round(float(np.median(lat_arr)), 3)
            std_ms    = round(float(np.std(lat_arr)), 3)
            min_ms    = round(float(np.min(lat_arr)), 3)
            max_ms    = round(float(np.max(lat_arr)), 3)
            p95_ms    = round(float(np.percentile(lat_arr, 95)), 3)
            fps       = round(1000.0 / mean_ms, 2) if mean_ms > 0 else 0.0

            print(f"mean={mean_ms}ms  p95={p95_ms}ms  FPS={fps}")

            # Raw records — one per iteration
            for i, lat in enumerate(latencies):
                raw_records.append({
                    "experiment_id": "EXP-AI-001",
                    "timestamp": RUN_TIMESTAMP,
                    "model": model_name,
                    "device": device,
                    "iteration": i + 1,
                    "latency_ms": round(lat, 4),
                    "vram_allocated_mb": vram_mb,
                    "file_size_mb": size_mb,
                })

            # Summary
            summary_results.append({
                "model": model_name,
                "file_size_mb": size_mb,
                "device": device,
                "cold_start_ms": round(cold_ms, 3),
                "warm_up_n": WARM_UP_N,
                "measure_n": MEASURE_N,
                "mean_ms": mean_ms,
                "median_ms": median_ms,
                "std_ms": std_ms,
                "min_ms": min_ms,
                "max_ms": max_ms,
                "p95_ms": p95_ms,
                "fps": fps,
                "vram_allocated_mb": vram_mb,
            })

        except Exception as ex:
            print(f"ERROR: {ex}")
            raw_records.append({
                "experiment_id": "EXP-AI-001",
                "timestamp": RUN_TIMESTAMP,
                "model": model_name,
                "device": device,
                "iteration": -1,
                "latency_ms": "ERROR",
                "vram_allocated_mb": "ERROR",
                "file_size_mb": size_mb,
                "error": str(ex)
            })
            summary_results.append({
                "model": model_name,
                "file_size_mb": size_mb,
                "device": device,
                "error": str(ex),
                "status": "FAILED"
            })

# ── Write raw CSV ─────────────────────────────────────────────────────────────
raw_csv_path = RAW_DIR / f"EXP_AI_001_raw_{RUN_TIMESTAMP}.csv"
if raw_records:
    fields = list(raw_records[0].keys())
    with open(raw_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(raw_records)
    print(f"\n[SAVED] Raw CSV: {raw_csv_path}")

# ── Write summary JSON ────────────────────────────────────────────────────────
summary_path = OUT_DIR / f"EXP_AI_001_summary_{RUN_TIMESTAMP}.json"
final_output = {
    "environment": env_info,
    "results": summary_results
}
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2)
print(f"[SAVED] Summary JSON: {summary_path}")

# ── Print final summary table ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("EXP-AI-001 BENCHMARK SUMMARY")
print("=" * 70)
print(f"{'Model':<32} {'Device':<6} {'Mean(ms)':<10} {'P95(ms)':<10} {'FPS':<8} {'VRAM(MB)'}")
print("─" * 70)
for r in summary_results:
    if "error" not in r:
        print(f"{r['model']:<32} {r['device']:<6} {r['mean_ms']:<10} {r['p95_ms']:<10} {r['fps']:<8} {r['vram_allocated_mb']}")
    else:
        print(f"{r['model']:<32} {r['device']:<6} ERROR: {r.get('error','')[:30]}")
print("=" * 70)
print(f"\nEXP-AI-001 COMPLETE")
print(f"Claim classification: [FACT / MEASURED]")
print(f"Evidence files: {raw_csv_path} | {summary_path}")
