# IntelliCode-SL Repo Context

This file is the canonical high-signal handoff for the repository. If any markdown doc disagrees with the Python code, trust the code first.

## What This Repo Is

IntelliCode-SL is a Streamlit-based coding assistant with a VS Code-like editor on the left and a chat assistant on the right. It accepts a natural-language prompt plus optional editor code, routes the request through a LangGraph workflow, and returns one of these outcomes:

- explain existing code
- debug or modify code
- generate new code from scratch
- generate documentation text
- handle uncategorized prompts through an interrupt/approval path

The repo is a mix of runtime code, local model artifacts, fine-tuning notebooks, benchmark JSON outputs, and dataset JSON files. The executable source surface is small; most of the tree is supporting model or experiment data.

## Authoritative Sources

- `main.py` is the app entry point.
- `workflow.py` is the actual control plane for classification, routing, summaries, unknown handling, and final response synthesis.
- `model_loader.py` is only the model-loading/inference layer.
- `styles/components.py` and `styles/chat_styles.css` define the UI rendering and styling.

The README files are useful orientation, but they are partially stale. The active code uses Groq plus local SLMs, not the older OpenRouter-only story described in some docs.

## Top-Level Layout

Root files:

- `main.py` - Streamlit app and UI orchestration.
- `workflow.py` - LangGraph state machine and prompt logic.
- `model_loader.py` - local model loading, inference, and unloading.
- `requirements.txt` - Python dependencies.
- `README.md` - broad project documentation, but slightly stale.
- `README_STREAMLIT.md` - older Streamlit documentation, not current.
- `todo.md` - current open work items.
- `LICENSE` - MIT license.

Important folders:

- `styles/` - UI helpers and CSS.
- `scripts/` - utility scripts, mainly Hugging Face artifact restoration.
- `testing_files/` - lightweight test harnesses.
- `adapters/` - local PEFT adapter exports and tokenizer/chat-template files.
- `base_models/` - local base model snapshots.
- `merged_models/` - locally merged checkpoints.
- `fine_tuning_notebooks /` - training/comparison notebooks. The trailing space is part of the real folder name.
- `fine_tunning_datasets/` - JSON datasets for training. The typo `tunning` is real.
- `fine_tuning_notebooks /compair_results/` - benchmark/result JSON outputs. The typo `compair` is real.
- `fine_tuning_notebooks /model_merge /` - merge notebooks. The trailing space is real.

The folder names with spaces and spelling mistakes are part of the repository state. Preserve them exactly when referencing paths.

## Runtime Flow

1. `main.py` loads the CSS, renders the title, initializes `st.session_state`, and lays out a two-column editor/chat interface.
2. The editor is `streamlit-ace` with VS Code keybindings and a twilight theme.
3. The chat panel renders the full conversation history with custom HTML/CSS helpers.
4. When the user sends a prompt, the UI appends the user message, adds a placeholder assistant message (`🤔 Thinking...` or `🤔 Resuming...`), and reruns the app.
5. The next pass detects that placeholder and calls `workflow.invoke(...)`.
6. If the workflow returns `modified_code`, the editor content is replaced and the editor key is incremented so Streamlit refreshes the widget.
7. If the workflow emits an interrupt, the UI shows the interrupt text, sets `pending_hitl`, and the next user submission resumes with `Command(resume=...)`.

The UI does not call `run_workflow(...)`; it calls `workflow.invoke(...)` directly.

## `main.py` Details

`main.py` uses these session-state keys:

- `chat_history`
- `code_content`
- `selected_language`
- `input_counter`
- `editor_counter`
- `session_id`
- `pending_hitl`

The language dropdown supports:

- `python`
- `javascript`
- `java`
- `cpp`
- `c`
- `go`
- `rust`
- `typescript`

Other notable behavior:

- Entering text in the chat box is treated as a send event.
- The send button is a custom SVG-backed Streamlit button.
- Markdown/code fences returned by the workflow are stripped before editor update.
- The layout is intentionally wide and sidebar-collapsed.

## `workflow.py` Details

`workflow.py` is the actual behavior source for the assistant.

Environment and LLM setup:

- calls `load_dotenv()`
- reads `groq_api_key` or `GROQ_API_KEY`
- creates `ChatGroq(model='llama-3.1-8b-instant', groq_api_key=groq_api_key)`
- uses `MemorySaver()` as the LangGraph checkpointer

Workflow state is `intellicode_state` and contains these important fields:

- `session_id`
- `prompt`
- `input_code`
- `messeges` - intentionally misspelled and used consistently
- `message_summary`
- `latest_code_iteration`
- `task_type`
- `task_output`
- `change_summary`
- `final_answer`
- `modified_code`
- `unknown_route`

There are also two Pydantic schemas, `task_classifier_schema` and `unknown_node_schema`, but the runtime mostly relies on prompt formatting plus JSON parsing rather than a strict structured-output API.

### Shared Helpers

- `_append_message(...)` appends a chat message to the internal list.
- `summarize_messages(...)` condenses the most recent 12 messages into 4-6 bullet points.
- `_parse_json_response(...)` strips fences and extracts JSON from an LLM response.
- `run_workflow(...)` is a convenience wrapper that prepares `messeges` and returns interrupt messages as `final_answer`.

### Classification And Routing

`task_classifier(state)` first tries the local classifier SLM, then falls back to Groq if needed.

Local classifier label mapping:

- `debug` -> `debug`
- `generate` -> `write`
- `modify` -> `modify`
- `explain` -> `explain`
- `document` -> `docs`
- `unknown` -> `other`

The routing values used by the graph are:

- `explain`
- `debug`
- `modify`
- `write`
- `docs`
- `other`

The graph routes `modify` as an internal/legacy path even though some docs only mention five categories.

### Task Nodes

- `explain_slm(...)` - explain input code in point form.
- `debug_code(...)` - return corrected code only.
- `debug_summary(...)` - summarize the bug fixes.
- `modify_code(...)` - apply requested edits and return raw code.
- `modify_summary(...)` - summarize the edits.
- `write_code(...)` - generate new code from scratch.
- `write_summary(...)` - summarize the generated code.
- `docs_worker(...)` - generate documentation text from code.
- `docs_summary(...)` - summarize the document and infer a likely file format.
- `collator(...)` - turn raw task output into the final assistant response.
- `unknown(...)` - handle uncategorized prompts and the approval flow.

### Unknown / HITL Flow

`unknown(...)` uses `interrupt(...)` to ask whether the prompt should be sent to an external AI API. If the response is yes, it asks the Groq LLM for JSON with `summary` and optional `modified_code`, then routes to `collator`. If the response is no, it returns a polite refusal-style response and ends the graph.

The UI currently expects this path to use `pending_hitl` plus resume turns. There are also open TODO items around this flow.

### Collation

`collator(...)` does two things:

- it summarizes recent conversation messages for memory
- it passes the raw task output through the formatter model

If the formatter produces nothing useful, it falls back to `change_summary` directly.

### Graph Topology

The compiled graph is:

- `START -> task_classifier`
- `task_classifier ->` conditional branch to `explain_slm`, `debug_code`, `modify_code`, `write_code`, `docs_worker`, or `unknown`
- `explain_slm -> collator -> END`
- `debug_code -> debug_summary -> collator -> END`
- `modify_code -> modify_summary -> collator -> END`
- `write_code -> write_summary -> collator -> END`
- `docs_worker -> docs_summary -> collator -> END`
- `unknown ->` conditional branch to `collator` or `END`

The graph is compiled as `workflow = graph.compile(checkpointer=memory)`.

## `model_loader.py` Details

`model_loader.py` is intentionally narrow: it only loads models, runs inference, and unloads them. It does not build prompts and it does not contain business logic.

Path defaults come from environment variables, with local fallbacks:

- `CLASSIFIER_PATH` -> `merged_models/classifier_merged`
- `FORMATTER_PATH` -> `merged_models/formatter_merged`
- `CODING_BASE_PATH` -> `base_models/qwen2.5-coder-3b-instruct-bnb-4bit`
- `CODING_ADAPTER_PATH` -> `adapters/coding_adapter`
- `DOCS_BASE_PATH` -> `base_models/llama-3.2-1b-instruct`
- `DOCS_ADAPTER_PATH` -> `adapters/docs_explanation_adapter`
- `HF_TOKEN` -> Hugging Face token for local loads if needed

Device selection is `cuda` when available, otherwise `cpu`.

### Model Inventory

- Classifier - merged fp16 checkpoint.
- Formatter - merged fp16 checkpoint.
- Coding SLM - 4-bit base model plus fp16 adapter.
- Docs / explanation SLM - 4-bit base model plus fp16 adapter.

### Inference Behavior

- `_generate(...)` tokenizes with truncation and a 2048 token max length.
- Generation is deterministic (`do_sample=False`).
- It strips the prompt tokens and returns only the newly generated text.
- `run_classifier(...)` and `run_formatter(...)` load a merged model, infer once, unload, and return raw output.
- `run_coding_slm(...)` and `run_docs_slm(...)` lazy-load and keep the model resident for consecutive nodes.
- `unload_coding_slm()` and `unload_docs_slm()` free the module-level handles and clear CUDA cache.
- On failure, the public functions return an empty string so `workflow.py` can fall back to Groq.

## UI Helpers And Styling

`styles/components.py` contains reusable rendering helpers:

- `load_css(...)`
- `get_image_base64(...)`
- `render_welcome_message(...)`
- `render_user_message(...)`
- `render_assistant_message(...)`
- `render_chat_container_start(...)`
- `render_page_title(...)`
- `render_code_editor_wrapper_start(...)`
- `render_code_stats(...)`
- `render_send_button(...)`
- `render_chat_history(...)`

The chat rendering escapes HTML before display and uses `components.html(...)` to render a custom scrollable chat container.

`styles/chat_styles.css` defines the dark theme, chat bubble styles, scrollbar styling, input focus styling, and button styling.

## Scripts And Tests

- `scripts/restore_hf_artifacts.py` restores local model folders from Hugging Face snapshots.
- It supports `HF_TOKEN`, `HUGGINGFACE_HUB_TOKEN`, and `HUGGINGFACE_TOKEN`.
- It can list matching repos or download them into the local folder layout.

Artifact mapping used by the restore script:

- `Spartan1-1-7/intellicode-classifier-merged-qwen2.5-coder-0.5b` -> `merged_models/classifier_merged`
- `Spartan1-1-7/intellicode-coding-adapter-qwen2.5-coder-3b` -> `adapters/coding_adapter`
- `Spartan1-1-7/intellicode-docs-explain-adapter-llama3.2-1b` -> `adapters/docs_explanation_adapter`
- `Spartan1-1-7/intellicode-formatter-merged-llama3.2-1b` -> `merged_models/formatter_merged`

- `testing_files/test.py` is a simple script that invokes `workflow.invoke(...)` on a sample modify prompt and prints the response plus cleaned code.
- `testing_files/test_bed.ipynb` is a notebook test bed.

## Training, Data, And Benchmarks

The repo keeps training data and notebook-based experiment history alongside the runtime code.

### Datasets

`fine_tunning_datasets/` contains the JSON datasets used for training:

- `classifier_dataset.json`
- `debug_dataset.json`
- `documentation_dataset.json`
- `explanation_dataset.json`
- `formatter_dataset.json`
- `generation_dataset.json`
- `modification_dataset.json`

These files mirror the specialized tasks used by the workflow and notebooks.

### Fine-Tuning Notebooks

`fine_tuning_notebooks /fine_tuning/` contains the main training notebooks:

- `01_Classifier_Finetune.ipynb`
- `02_Coding_SLM_Finetune.ipynb`
- `03_Docs_Explanation_Finetune.ipynb`
- `04_Formatter_SLM_Finetune.ipynb`

### Model Comparison / Benchmark Notebooks

`fine_tuning_notebooks /model_compair/` contains comparison and benchmark notebooks, including:

- `05_Classifier_SLM_Comparison.ipynb`
- `06_Classifier_FP16_vs_8bit.ipynb`
- `07A_Coding_4bit.ipynb`
- `07B_Coding_8bit.ipynb`
- `08A_Docs_fp16.ipynb`
- `08B_Docs_4bit.ipynb`
- `08C_Docs_8bit.ipynb`
- `09A_Formatter_fp16.ipynb`
- `09B_Formatter_4bit.ipynb`
- `09C_Formatter_8bit.ipynb`
- `12_Coding_SLM_Full_Benchmark (1).ipynb`

The notebook series covers training, quantization comparison, and broader benchmark runs against both local SLMs and Groq API models.

### Comparison Outputs

`fine_tuning_notebooks /compair_results/` stores benchmark JSON outputs such as:

- `classifier_comparison.json`
- `classifier_fp16_vs_8bit.json`
- `coding_slm_4bit.json`
- `coding_slm_8bit.json`
- `coding_slm_full_benchmarkfull.json`
- `docs_eval_results.json`
- `docs_slm_fp16.json`
- `docs_slm_4bit.json`
- `docs_slm_8bit.json`
- `eval_results.json`
- `formatter_eval_results.json`
- `formatter_slm_fp16.json`
- `formatter_slm_4bit.json`
- `formatter_slm_8bit.json`
- `results_A_fp16.json`

These files are historical experiment outputs, not runtime dependencies.

## Documentation Caveats

Trust the code over the docs when they disagree.

- `README.md` still mentions OpenRouter / Grok-4.1-Fast in places, but `workflow.py` currently uses Groq with `llama-3.1-8b-instant` plus local SLMs.
- `README.md` also refers to `open_router_api`, while the live code reads `groq_api_key` or `GROQ_API_KEY`.
- `README_STREAMLIT.md` is older and refers to files/folders that do not exist in the current repo, such as `streamlit_app.py`, `controller.py`, `agents/`, and `slms/`.
- Several folder names are intentionally misspelled or have trailing spaces. Preserve them exactly.

## Current Known Work

`todo.md` currently tracks this open work:

- trace interrupt resume path
- replace interrupt with chat-safe pause
- return resumed response from unknown node
- route yes/no to end or LLM
- verify chat state updates

That list is the best snapshot of the current rough edge in the app flow.

## Practical Notes For Future Agents

- Use `main.py`, `workflow.py`, and `model_loader.py` as the source of truth for behavior.
- The code path is mostly single-file and small; the rest of the repo is model artifacts, datasets, or notebook history.
- If you need to reason about the unknown/approval flow, check both `workflow.py` and `main.py` together.
- If you need to restore weights locally, use `scripts/restore_hf_artifacts.py` rather than guessing folder contents.
- If you are trying to understand model provenance, start with `model_loader.py` and the fine-tuning notebooks.
