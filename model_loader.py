"""
model_loader.py — Local SLM inference layer for IntelliCode-SL.

This file is a pure model management layer.
- It does NOT build prompts — prompts are built in workflow.py and passed in.
- It does NOT contain any business logic.
- It loads a model, runs the prompt passed to it, and returns the raw output string.
- Lazy loading: models are loaded on demand and unloaded after use.
- Groq fallback is handled in workflow.py — this file only returns empty string on failure.

Model inventory:
  Classifier  — merged fp16    — merged_models/classifier_merged/
  Coding SLM  — 4-bit + fp16 adapter — base_models/qwen2.5-coder-3b-instruct-bnb-4bit/ + adapters/coding_adapter/
  Docs SLM    — 4-bit + fp16 adapter — base_models/llama-3.2-1b-instruct/ + adapters/docs_explanation_adapter/
  Formatter   — merged fp16    — merged_models/formatter_merged/
"""

import os
import gc
import torch
from dotenv import load_dotenv

load_dotenv()

# ── Path constants ─────────────────────────────────────────────
# Read from .env — fall back to local relative paths matching the repo structure

CLASSIFIER_PATH      = os.getenv('CLASSIFIER_PATH',      'merged_models/classifier_merged')
FORMATTER_PATH       = os.getenv('FORMATTER_PATH',       'merged_models/formatter_merged')
CODING_BASE_PATH     = os.getenv('CODING_BASE_PATH',     'base_models/qwen2.5-coder-3b-instruct-bnb-4bit')
CODING_ADAPTER_PATH  = os.getenv('CODING_ADAPTER_PATH',  'adapters/coding_adapter')
DOCS_BASE_PATH       = os.getenv('DOCS_BASE_PATH',       'base_models/llama-3.2-1b-instruct')
DOCS_ADAPTER_PATH    = os.getenv('DOCS_ADAPTER_PATH',    'adapters/docs_explanation_adapter')
HF_TOKEN             = os.getenv('HF_TOKEN', None)

# ── Device helper ──────────────────────────────────────────────
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# ── Module-level model handles (None when unloaded) ───────────
_coding_model     = None
_coding_tokenizer = None
_docs_model       = None
_docs_tokenizer   = None


# ══════════════════════════════════════════════════════════════
#  INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════

def _free_vram():
    """Force garbage collection and clear CUDA cache."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _generate(model, tokenizer, prompt_text: str, max_new_tokens: int) -> str:
    """
    Run inference on any loaded model.
    Returns ONLY the newly generated text — the prompt is stripped out.
    """
    inputs = tokenizer(
        prompt_text,
        return_tensors='pt',
        truncation=True,
        max_length=2048,
    ).to(DEVICE)

    input_length = inputs['input_ids'].shape[1]

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    # Slice off the input tokens — decode only the new tokens
    new_tokens = outputs[0][input_length:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)


# ══════════════════════════════════════════════════════════════
#  CLASSIFIER  (merged fp16 — load → infer → unload per call)
# ══════════════════════════════════════════════════════════════

def run_classifier(prompt_text: str) -> str:
    """
    Load the classifier merged model, run the prompt, unload, return raw decoded string.

    The caller (task_classifier in workflow.py) is responsible for:
      - splitting the output on '### Category:' to extract the label
      - remapping the label to the workflow routing values

    Returns empty string on any failure — caller falls back to Groq.
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        print('[model_loader] Loading classifier...')
        model = AutoModelForCausalLM.from_pretrained(
            CLASSIFIER_PATH,
            torch_dtype=torch.float16,
            device_map='auto',
        )
        tokenizer = AutoTokenizer.from_pretrained(CLASSIFIER_PATH)
        model.eval()

        result = _generate(model, tokenizer, prompt_text, max_new_tokens=10)

        del model, tokenizer
        _free_vram()
        print('[model_loader] Classifier unloaded.')

        return result

    except Exception as e:
        print(f'[model_loader] Classifier ERROR: {e}')
        _free_vram()
        return ''


# ══════════════════════════════════════════════════════════════
#  CODING SLM  (4-bit base + fp16 adapter)
#  load/unload are separate so consecutive nodes share the model
# ══════════════════════════════════════════════════════════════

def _load_coding_slm():
    """
    Internal: load coding base model + adapter into module-level handles.
    No-op if already loaded.
    """
    global _coding_model, _coding_tokenizer

    if _coding_model is not None:
        return  # Already loaded

    try:
        from unsloth import FastLanguageModel
        from peft import PeftModel

        print('[model_loader] Loading coding SLM...')
        base_model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=CODING_BASE_PATH,
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
            token=HF_TOKEN,
        )
        model = PeftModel.from_pretrained(
            base_model,
            CODING_ADAPTER_PATH,
            torch_dtype=torch.float16,
        )
        FastLanguageModel.for_inference(model)
        model.eval()

        _coding_model     = model
        _coding_tokenizer = tokenizer
        print('[model_loader] Coding SLM loaded.')

    except Exception as e:
        print(f'[model_loader] Coding SLM load ERROR: {e}')
        _coding_model     = None
        _coding_tokenizer = None
        _free_vram()


def run_coding_slm(prompt_text: str, max_new_tokens: int = 512) -> str:
    """
    Run inference on the coding SLM using the prompt built in workflow.py.

    The prompt is already fully formed — this function just runs it.
    The caller extracts the relevant output section by splitting on
    '### Output:' (the separator used in the fine-tuning format).

    Does NOT unload after inference — call unload_coding_slm() when done
    (i.e. after the summary node that follows the main task node).

    Returns empty string on any failure — caller falls back to Groq.
    """
    _load_coding_slm()

    if _coding_model is None:
        return ''

    try:
        return _generate(_coding_model, _coding_tokenizer, prompt_text, max_new_tokens)
    except Exception as e:
        print(f'[model_loader] Coding SLM inference ERROR: {e}')
        return ''


def unload_coding_slm():
    """
    Unload the coding SLM from memory.
    Call this after the last consecutive node that uses the coding SLM
    (i.e. after debug_summary, write_summary, or modify_summary).
    """
    global _coding_model, _coding_tokenizer

    if _coding_model is None:
        return

    print('[model_loader] Unloading coding SLM...')
    del _coding_model, _coding_tokenizer
    _coding_model     = None
    _coding_tokenizer = None
    _free_vram()
    print('[model_loader] Coding SLM unloaded.')


# ══════════════════════════════════════════════════════════════
#  DOCS / EXPLAIN SLM  (4-bit base + fp16 adapter)
#  Same load/unload pattern as coding SLM
# ══════════════════════════════════════════════════════════════

def _load_docs_slm():
    """
    Internal: load docs/explain base model + adapter into module-level handles.
    No-op if already loaded.
    """
    global _docs_model, _docs_tokenizer

    if _docs_model is not None:
        return  # Already loaded

    try:
        from unsloth import FastLanguageModel
        from peft import PeftModel

        print('[model_loader] Loading docs/explain SLM...')
        base_model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=DOCS_BASE_PATH,
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
            token=HF_TOKEN,
        )
        model = PeftModel.from_pretrained(
            base_model,
            DOCS_ADAPTER_PATH,
            torch_dtype=torch.float16,
        )
        FastLanguageModel.for_inference(model)
        model.eval()

        _docs_model     = model
        _docs_tokenizer = tokenizer
        print('[model_loader] Docs/explain SLM loaded.')

    except Exception as e:
        print(f'[model_loader] Docs/explain SLM load ERROR: {e}')
        _docs_model     = None
        _docs_tokenizer = None
        _free_vram()


def run_docs_slm(prompt_text: str, max_new_tokens: int = 512) -> str:
    """
    Run inference on the docs/explain SLM using the prompt built in workflow.py.

    The prompt is already fully formed — this function just runs it.
    The caller extracts the relevant section by splitting on '### Response:'
    (the separator used in the fine-tuning format).

    Does NOT unload after inference — call unload_docs_slm() when done.

    Returns empty string on any failure — caller falls back to Groq.
    """
    _load_docs_slm()

    if _docs_model is None:
        return ''

    try:
        return _generate(_docs_model, _docs_tokenizer, prompt_text, max_new_tokens)
    except Exception as e:
        print(f'[model_loader] Docs/explain SLM inference ERROR: {e}')
        return ''


def unload_docs_slm():
    """
    Unload the docs/explain SLM from memory.
    Call this after the last consecutive node that uses the docs SLM
    (i.e. after explain_slm or docs_summary).
    """
    global _docs_model, _docs_tokenizer

    if _docs_model is None:
        return

    print('[model_loader] Unloading docs/explain SLM...')
    del _docs_model, _docs_tokenizer
    _docs_model     = None
    _docs_tokenizer = None
    _free_vram()
    print('[model_loader] Docs/explain SLM unloaded.')


# ══════════════════════════════════════════════════════════════
#  FORMATTER  (merged fp16 — load → infer → unload per call)
# ══════════════════════════════════════════════════════════════

def run_formatter(prompt_text: str, max_new_tokens: int = 400) -> str:
    """
    Load the formatter merged model, run the prompt, unload, return raw decoded string.

    The prompt is already fully formed — this function just runs it.
    The caller extracts the relevant section by splitting on '### Formatted Response:'
    (the separator used in the fine-tuning format).

    Returns empty string on any failure — caller falls back to Groq.
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        print('[model_loader] Loading formatter...')
        model = AutoModelForCausalLM.from_pretrained(
            FORMATTER_PATH,
            torch_dtype=torch.float16,
            device_map='auto',
        )
        tokenizer = AutoTokenizer.from_pretrained(FORMATTER_PATH)
        model.eval()

        result = _generate(model, tokenizer, prompt_text, max_new_tokens)

        del model, tokenizer
        _free_vram()
        print('[model_loader] Formatter unloaded.')

        return result

    except Exception as e:
        print(f'[model_loader] Formatter ERROR: {e}')
        _free_vram()
        return ''
