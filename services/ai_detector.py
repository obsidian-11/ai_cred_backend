# services/ai_detector.py
import os
import sys
import math
import argparse
import traceback

# Add detectGPT to path so we can import its utils directly
DETECTGPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../detectGPT"))
sys.path.insert(0, DETECTGPT_PATH)

from utils.load_models_tokenizers import (
    load_base_model_and_tokenizer,
    load_base_model,
    load_mask_filling_model,
)
from utils.baselines.detectGPT import get_perturbation_results

def _make_args():
    args = argparse.Namespace(
        base_model_name="gpt2",
        mask_filling_model_name="t5-small",
        DEVICE="cpu",
        dataset="xsum",
        pct_words_masked=0.3,
        span_length=2,
        n_samples=1,
        n_perturbation_list=[10],
        n_perturbation_rounds=1,
        buffer_size=1,
        mask_top_p=1.0,
        chunk_size=20,
        batch_size=50,
        int8=False,
        half=False,
        base_half=False,
        do_top_k=False,
        top_k=40,
        do_top_p=False,
        top_p=0.96,
        random_fills=False,
        random_fills_tokens=False,
        pre_perturb_pct=0.0,
        pre_perturb_span_length=5,
        openai_model=None,
        openai_key=None,
        baselines_only=False,
        skip_baselines=True,
        cache_dir=os.path.join(DETECTGPT_PATH, "cache"),
        scoring_model_name="",
        output_name="",
    )
    return args

print("[AI Detector] Loading models (one-time)...")
_args = _make_args()
_config = {
    "n_perturbation_list": _args.n_perturbation_list,
    "n_perturbation_rounds": _args.n_perturbation_rounds,
    "SAVE_FOLDER": os.path.join(DETECTGPT_PATH, "results"),
}
os.makedirs(_config["SAVE_FOLDER"], exist_ok=True)

try:
    load_base_model_and_tokenizer(_args, _config, None)
    load_mask_filling_model(_args, _config)
    load_base_model(_args, _config)
    print("[AI Detector] Models loaded successfully.")
except Exception as e:
    print(f"[AI Detector] ERROR loading models: {e}")
    print(traceback.format_exc())
    raise


def detect_ai(text: str) -> float:
    try:
        words = text.split()
        if len(words) > 300:
            text = " ".join(words[:300])

        from utils.baselines.likelihood import get_ll

        # Move base model to device first
        load_base_model(_args, _config)

        ll = get_ll(_args, _config, text)
        print(f"[AI Detector] log_likelihood={ll:.4f}")

        # GPT-2 log-likelihood interpretation:
        # AI text (GPT-style): typically -2.0 to -3.0  (high probability → likely AI)
        # Human text:          typically -4.0 to -7.0  (lower probability → likely human)
        # Sigmoid centered at -3.5 maps this to (0, 1)
        ai_prob = 1.0 / (1.0 + math.exp(ll + 3.5))
        print(f"[AI Detector] ai_prob={ai_prob:.4f}")
        return float(ai_prob)

    except Exception as e:
        print(f"[AI Detector] Exception in detect_ai: {e}")
        print(traceback.format_exc())
        return 0.5