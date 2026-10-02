"""EXP-AI-002: Validation Dataset Availability Audit"""
import sys, time, json, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path
ROOT = Path(r'C:\Users\Pasindu\.gemini\antigravity\scratch\CropGuard')

print("=== EXP-AI-002: Validation Dataset Availability Audit ===")
print()

data_search_paths = [
    ROOT / "data",
    ROOT / "dataset",
    ROOT / "datasets",
    ROOT / "val",
    ROOT / "test",
    ROOT / "validation",
    ROOT / "images",
]
print("Checking for labelled validation/test dataset directories:")
found_datasets = []
for p in data_search_paths:
    exists = p.exists()
    status = "EXISTS" if exists else "NOT FOUND"
    print(f"  {p.name}: {status}")
    if exists:
        found_datasets.append(str(p))

image_count = 0
image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '__pycache__', '.git')]
    for f in files:
        if Path(f).suffix.lower() in image_extensions:
            image_count += 1

print(f"\nTotal image files found in project (excl. node_modules): {image_count}")

result = {
    "experiment_id": "EXP-AI-002",
    "date": time.strftime("%Y-%m-%d"),
    "objective": "Determine if labelled validation/test dataset exists for model accuracy evaluation",
    "dataset_directories_found": found_datasets,
    "total_image_files_in_project": image_count,
    "conclusion": "NO INDEPENDENT TEST DATASET FOUND IN PROJECT REPOSITORY",
    "impact": "Top-1 accuracy, Precision, Recall, F1 cannot be computed without a labelled test set",
    "claim_classification": "NOT YET MEASURED",
    "action_required": "Provide or reconstruct labelled hold-out test splits from original training datasets to enable EXP-AI-002",
    "note": "Models are Ultralytics classification checkpoints; evaluation requires test split images organized by class in subdirectories"
}
print()
print(json.dumps(result, indent=2))

out = ROOT / "research" / "data" / "EXP_AI_002_dataset_audit.json"
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w") as f:
    json.dump(result, f, indent=2)
print(f"[SAVED] {out}")
