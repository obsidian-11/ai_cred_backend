# services/ai_detector.py
import os
import subprocess
import json
import glob
import math
import tempfile
import traceback

DETECTGPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../detectGPT"))

BASE_MODEL = "gpt2"
MASK_MODEL = "t5-small"
DEVICE = "cpu"

def detect_ai(text: str) -> float:
    tmp_path = None
    try:
        # Write text to a temp file to avoid shell escaping issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write(text)
            tmp_path = tmp.name
        print(f"[DetectGPT] Wrote text to temp file: {tmp_path}")

        cmd = [
            "python3",
            os.path.join(DETECTGPT_PATH, "run.py"),
            "--base_model_name", BASE_MODEL,
            "--mask_filling_model_name", MASK_MODEL,
            "--DEVICE", DEVICE,
            "--custom_text_file", tmp_path,
            "--n_perturbation_list", "1",
            "--n_samples", "1",
            "--skip_baselines",
        ]

        print(f"[DetectGPT] Running command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=DETECTGPT_PATH
        )

        print(f"[DetectGPT] Return code: {result.returncode}")
        print(f"[DetectGPT] STDOUT:\n{result.stdout}")
        print(f"[DetectGPT] STDERR:\n{result.stderr}")

        if result.returncode != 0:
            return 0.5

        pattern = os.path.join(DETECTGPT_PATH, "results", "**", "perturbation_1_d_results.json")
        files = glob.glob(pattern, recursive=True)
        print(f"[DetectGPT] Results files found: {files}")

        if not files:
            return 0.5

        perturb_file = max(files, key=os.path.getmtime)
        print(f"[DetectGPT] Using: {perturb_file}")

        with open(perturb_file, "r") as f:
            data = json.load(f)

        print(f"[DetectGPT] JSON keys: {list(data.keys())}")

        raw = data.get("raw_results", [])
        if not raw:
            print("[DetectGPT] raw_results is empty")
            return 0.5

        print(f"[DetectGPT] raw_results[0]: {raw[0]}")

        discrepancies = [r["original_ll"] - r["perturbed_original_ll"] for r in raw]
        mean_discrepancy = sum(discrepancies) / len(discrepancies)
        ai_prob = 1 / (1 + math.exp(-mean_discrepancy))
        return float(ai_prob)

    except Exception as e:
        print(f"[AI Detector] Exception: {e}")
        print(traceback.format_exc())
        return 0.5

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)