## IMPORTING THE NEEDED LIBRARIES

import json
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from typing import TypedDict, Literal, Optional
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import os

from model_loader import (
    run_classifier,
    run_coding_slm,
    unload_coding_slm,
    run_docs_slm,
    unload_docs_slm,
    run_formatter,
)


## LOADING THE REQUIRED API KEYS AND VALIDATION LOGIC

# API key
load_dotenv()
groq_api_key = os.getenv('groq_api_key') or os.getenv('GROQ_API_KEY')

# validation
llm = ChatGroq(
    model='llama-3.1-8b-instant',
    groq_api_key=groq_api_key,
)




## DEFINING SCHEMAS FOR VARIOUS LLM/SLM POMPTS

# defining the schema for the task classifier node
class task_classifier_schema(BaseModel):
    task_type: Literal['explain','modify','debug','write','docs','other']= Field(description='classify the prompt in various categories')

# defining the schema for the uknown node 
class unknown_node_schema(BaseModel):
    summary: str= Field(description='Point-wise brief response explaining the action taken for prompts that do not fit any predefined category.')
    modified_code : Optional[str] = Field(default=None, description='The final modified code produced by the node, containing only the corrected or generated code.')



## DEFINING THE STATE FOR THE WORKFLOW

# defining the literal for task_type
task_type= Literal['explain','modify','debug','write','docs','other']

# defining the state
class intellicode_state( TypedDict):

    # user inputs
    session_id: Optional[str]
    prompt:str
    input_code: Optional[str] 

    # context
    messeges: list[dict[str, str]]
    message_summary: Optional[str]
    latest_code_iteration: Optional[str]

    # Routing and task info
    task_type: task_type
    task_output: Optional[str]
    change_summary: Optional[str]

    # final response
    final_answer: Optional[str]
    modified_code: Optional[str]
    unknown_route: Optional[str]

    # metasdata (left empty for future additions)




# CHECKPOINTED SESSION MEMORY HELPERS

memory = MemorySaver()
SUMMARY_MAX_MESSAGES = 12


def _append_message(messages: list[dict[str, str]], role: str, content: str) -> list[dict[str, str]]:
    return [*messages, {'role': role, 'content': content}]


def summarize_messages(messages: list[dict[str, str]]) -> str:
    if not messages:
        return ''

    recent_messages = messages[-SUMMARY_MAX_MESSAGES:]
    history = '\n'.join(
        f"{message.get('role', 'unknown')}: {message.get('content', '').strip()}" for message in recent_messages
    )
    prompt = f"""You are a concise memory summarizer.
Summarize the conversation below in 4-6 short bullet points.
Keep it compact and focused on persistent context.

Conversation:
{history}

Summary:"""

    response = llm.invoke([
        {
            'role': 'user',
            'content': prompt,
        }
    ])

    return response.content.strip()


def _parse_json_response(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.endswith("```"):
            text = text[:-3].strip()

    start_index = text.find("{")
    end_index = text.rfind("}")
    if start_index != -1 and end_index != -1 and end_index > start_index:
        text = text[start_index:end_index + 1]

    return json.loads(text)


def run_workflow(initial_state: intellicode_state, session_id: Optional[str] = None):
    active_session_id = session_id or initial_state.get('session_id') or 'default'
    prepared_state = {
        **initial_state,
        'session_id': active_session_id,
        'messeges': list(initial_state.get('messeges', [])),
    }
    result = workflow.invoke(prepared_state, config={'configurable': {'thread_id': active_session_id}})

    if isinstance(result, dict) and result.get('__interrupt__'):
        interrupt_payload = result['__interrupt__'][0] if result['__interrupt__'] else None
        interrupt_message = getattr(interrupt_payload, 'value', '') if interrupt_payload is not None else ''
        return {
            **result,
            'final_answer': interrupt_message,
        }

    return result


## DEFINING THE FUNTIONS FOR ALL THE NODES OF THE WORKFLOW

# ── Label remapping: SLM output → workflow routing values ──────
# The classifier SLM was fine-tuned on these labels:
#   debug | generate | modify | explain | document | unknown
# The workflow routes on these labels:
#   debug | write    | modify | explain | docs      | other
# This map is the single place where the translation happens.
_CLASSIFIER_LABEL_MAP = {
    'debug':    'debug',
    'generate': 'write',
    'modify':   'modify',
    'explain':  'explain',
    'document': 'docs',
    'unknown':  'other',
}


# Defining the task_classifier function to classify the prompt into various catergories
def task_classifier(state: intellicode_state):

    # ── Build the prompt exactly as before ─────────────────────
    # The same prompt used by the original Groq-based classifier
    # is passed directly to the local SLM — no duplicate template.
    prompt = f"""You are a coding-assistant classifier.
Your job is to classify the user's request into one of the following five categories:

1. explain — The user wants an explanation of the given input code.
2. debug — The user wants to fix, analyze, or find errors/bugs in the input code.
3. write — The user wants new code written from scratch (not modifying or explaining existing code).
4. docs — The user wants documentation, comments, or descriptive text about the input code.
5. other —
   - The request is coding-related but does not fit any category above, OR
   - The request is not related to coding.

Use the prompt below and the provided input code as context.

User prompt:
\"\"\"{state['prompt']}\"\"\"

Input code:
\"\"\"{state['input_code']}\"\"\"

Return a single JSON object with the field task_type set to exactly one of: explain, debug, write, docs, other.
Do not include any extra text, markdown, or keys.
"""

    # ── Try local classifier SLM first ─────────────────────────
    # run_classifier returns the full decoded string.
    # The SLM was fine-tuned to output the label after '### Category:'.
    # We extract it and remap to the workflow routing values.
    slm_classifier_prompt = f"""### Instruction:
Classify the following user request into exactly one category:
debug, generate, modify, explain, document, unknown

### User Request:
{state['prompt']}

### Category:
"""
    task_type = None
    raw_output = run_classifier(slm_classifier_prompt)

    if raw_output.strip():
        # Extract label — split on the fine-tuning separator
        if '### Category:' in raw_output:
            raw_label = raw_output.split('### Category:')[-1].strip().split()[0].lower()
        else:
            # If separator not present, take the last word of the output
            raw_label = raw_output.strip().split()[-1].lower()

        # Strip any punctuation that may have been appended
        raw_label = raw_label.strip('.,;:!?')

        # Remap to workflow routing label
        task_type = _CLASSIFIER_LABEL_MAP.get(raw_label)

        if task_type is None:
            print(f'[task_classifier] Unrecognised SLM label: "{raw_label}" — falling back to Groq')

    # ── Fallback to Groq if SLM failed or returned unknown label ─
    if not task_type:
        print('[task_classifier] Using Groq fallback.')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        parsed_response = _parse_json_response(response.content)
        task_type = parsed_response.get('task_type', 'other')
        if task_type not in ('explain', 'modify', 'debug', 'write', 'docs', 'other'):
            task_type = 'other'

    updated_messages = _append_message(state.get('messeges', []), 'user', state['prompt'])
    return {'task_type': task_type, 'messeges': updated_messages}


# defining the function which handles the explaination node of the workflow
def explain_slm(state: intellicode_state):

    # ── Build the prompt exactly as before ─────────────────────
    prompt = f"""You are a coding assistant. 
Your task is to **explain the given input code** in a clear, concise, and point-wise format.
Do NOT rewrite the code. Do NOT add unnecessary details.
Produce a brief, easy-to-understand list of points describing what the code does.

User prompt:
\"\"\"{state['prompt']}\"\"\"

Input code:
\"\"\"{state['input_code']}\"\"\"

Now explain the code in a numbered point-wise format.
"""

    # ── Try local docs/explain SLM ─────────────────────────────
    # The SLM was fine-tuned with '### Response:' as output separator.
    raw_output = run_docs_slm(prompt)
    explain = None

    if raw_output.strip():
        if '### Response:' in raw_output:
            explain = raw_output.split('### Response:')[-1].strip()
        else:
            explain = raw_output.strip()

    # Unload docs SLM — no further docs/explain node follows explain_slm
    unload_docs_slm()

    # ── Fallback to Groq if SLM failed ─────────────────────────
    if not explain:
        print('[explain_slm] Using Groq fallback.')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        explain = response.content

    return {'change_summary': explain}


def modify_code(state: intellicode_state):

    # ── Build the prompt exactly as before ─────────────────────
    prompt = f"""You are an expert software engineer. Your sole task is to modify the given code based on the user's request.

    ---
    USER REQUEST:
    {state['prompt']}

    ---
    ORIGINAL CODE:
    {state['input_code']}

    ---
    INSTRUCTIONS:
    1. Read the user's request carefully and understand exactly what change is needed.
    2. Apply only the modifications requested — nothing more, nothing less.
    3. Preserve all existing logic, structure, and style that is unrelated to the request.
    4. Do not fix unrelated bugs, refactor, rename variables, or add unrequested features.

    OUTPUT RULES (critical):
    - Output raw code only.
    - No markdown, no triple backticks, no code fences.
    - No explanations, comments, or preamble.
    - No "Here is the modified code:" or similar phrases.
    - Return the complete modified file, not just the changed section.
    """

    # ── Try local coding SLM ───────────────────────────────────
    # The SLM was fine-tuned with '### Output:' as output separator.
    # Do NOT unload — modify_summary runs next and reuses this model.
    raw_output = run_coding_slm(prompt)
    code = None

    if raw_output.strip():
        if '### Output:' in raw_output:
            code = raw_output.split('### Output:')[-1].strip()
        else:
            code = raw_output.strip()

    # ── Fallback to Groq if SLM failed ─────────────────────────
    if not code:
        print('[modify_code] Using Groq fallback.')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        code = response.content

    return {'modified_code': code, 'latest_code_iteration': code}


def modify_summary(state: intellicode_state):

    # ── Build the prompt exactly as before ─────────────────────
    prompt = f"""You are a coding assistant.
    Your task is to generate a brief, point-wise summary of the modifications made to the code.

    User request:
    \"\"\"{state['prompt']}\"\"\"

    Original code:
    \"\"\"{state['input_code']}\"\"\"

    Modified code:
    \"\"\"{state['modified_code']}\"\"\"

    Write a short, clear, point-wise summary describing exactly what was changed based on the user's request.
    Focus only on intentional modifications:
    - features added or removed
    - logic changes
    - structural changes
    - behavior changes

    Do NOT rewrite the code.
    Do NOT include extra explanations.
    Output only concise bullet points.
    """

    # ── Try local coding SLM (still loaded from modify_code) ───
    raw_output = run_coding_slm(prompt)
    summary = None

    if raw_output.strip():
        if '### Output:' in raw_output:
            summary = raw_output.split('### Output:')[-1].strip()
        else:
            summary = raw_output.strip()

    # Unload coding SLM — modify path is done after this node
    unload_coding_slm()

    # ── Fallback to Groq if SLM failed ─────────────────────────
    if not summary:
        print('[modify_summary] Using Groq fallback.')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        summary = response.content

    return {'change_summary': summary}


# defining the function which handles the debuggin of the code
def debug_code(state: intellicode_state):

    # ── Build the prompt exactly as before ─────────────────────
    prompt = f"""You are a coding assistant.
Your task is to debug the given input code.

- Read the user's prompt:
\"\"\"{state['prompt']}\"\"\"

- Read the input code:
\"\"\"{state['input_code']}\"\"\"

Fix all bugs, errors, and issues in the code.
Improve correctness ONLY—do not change logic unless required to fix an error.

IMPORTANT:
Output **only** the fully corrected code.
Do NOT include explanations, comments, or markdown formatting.
Return raw code only.
"""

    # ── Try local coding SLM ───────────────────────────────────
    # Do NOT unload — debug_summary runs next and reuses this model.
    raw_output = run_coding_slm(prompt)
    code = None

    if raw_output.strip():
        if '### Output:' in raw_output:
            code = raw_output.split('### Output:')[-1].strip()
        else:
            code = raw_output.strip()

    # ── Fallback to Groq if SLM failed ─────────────────────────
    if not code:
        print('[debug_code] Using Groq fallback.')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        code = response.content

    return {'modified_code': code, 'latest_code_iteration': code}


# defining the fuction for the node which handles the response of debugging the code
def debug_summary(state: intellicode_state):

    # ── Build the prompt exactly as before ─────────────────────
    prompt = f"""You are a coding assistant.
Your task is to generate a brief, point-wise summary of the changes made during debugging.

User prompt:
\"\"\"{state['prompt']}\"\"\"

Original input code:
\"\"\"{state['input_code']}\"\"\"

Debugged code (final corrected version):
\"\"\"{state['modified_code']}\"\"\"

Write a short, clear, point-wise summary describing exactly what was fixed, changed, or improved.
Focus only on meaningful modifications:
- bug fixes
- syntax corrections
- logic corrections
- improvements required for the code to run

Do NOT rewrite the code.
Do NOT include extra explanations.
Output only concise bullet points.
"""

    # ── Try local coding SLM (still loaded from debug_code) ────
    raw_output = run_coding_slm(prompt)
    summary = None

    if raw_output.strip():
        if '### Output:' in raw_output:
            summary = raw_output.split('### Output:')[-1].strip()
        else:
            summary = raw_output.strip()

    # Unload coding SLM — debug path is done after this node
    unload_coding_slm()

    # ── Fallback to Groq if SLM failed ─────────────────────────
    if not summary:
        print('[debug_summary] Using Groq fallback.')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        summary = response.content

    return {'change_summary': summary}


# defining the function for the node which handles writing the code from scratch
def write_code(state: intellicode_state):

    # ── Build the prompt exactly as before ─────────────────────
    prompt = f"""You are a coding assistant.
Your task is to write the required code from scratch based on the user's prompt.

User prompt:
\"\"\"{state['prompt']}\"\"\"

Generate only the code that satisfies the request.
Do NOT include explanations, comments, markdown, or any extra text.
Output raw executable code only.
"""

    # ── Try local coding SLM ───────────────────────────────────
    # Do NOT unload — write_summary runs next and reuses this model.
    raw_output = run_coding_slm(prompt)
    code = None

    if raw_output.strip():
        if '### Output:' in raw_output:
            code = raw_output.split('### Output:')[-1].strip()
        else:
            code = raw_output.strip()

    # ── Fallback to Groq if SLM failed ─────────────────────────
    if not code:
        print('[write_code] Using Groq fallback.')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        code = response.content

    return {'modified_code': code}


# defining the function which handles the node for writing summary about the code written from scratch
def write_summary(state: intellicode_state):

    # ── Build the prompt exactly as before ─────────────────────
    prompt = f"""You are a coding assistant.
Your task is to generate a brief, point-wise summary of the code that was written from scratch.

User prompt:
\"\"\"{state['prompt']}\"\"\"

Generated code:
\"\"\"{state['modified_code']}\"\"\"

Write a short, clear, point-wise summary explaining what the generated code does.
Do NOT rewrite the code.
Do NOT include unnecessary details.
Only describe the key functionality in concise bullet points.
"""

    # ── Try local coding SLM (still loaded from write_code) ────
    raw_output = run_coding_slm(prompt)
    summary = None

    if raw_output.strip():
        if '### Output:' in raw_output:
            summary = raw_output.split('### Output:')[-1].strip()
        else:
            summary = raw_output.strip()

    # Unload coding SLM — write path is done after this node
    unload_coding_slm()

    # ── Fallback to Groq if SLM failed ─────────────────────────
    if not summary:
        print('[write_summary] Using Groq fallback.')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        summary = response.content

    return {'change_summary': summary}


# defining the function for the node which handles the writing of the documents for the code
def docs_worker(state: intellicode_state):

    # ── Build the prompt exactly as before ─────────────────────
    prompt = f"""You are a coding assistant.
Your task is to create the document requested by the user, using the provided code as context.

User prompt:
\"\"\"{state['prompt']}\"\"\"

Input code (context):
\"\"\"{state['input_code']}\"\"\"

Generate the required document exactly as requested.
Output only the document content.
Do NOT include explanations, comments, markdown formatting, or any extra text.
"""

    # ── Try local docs/explain SLM ─────────────────────────────
    # Do NOT unload — docs_summary runs next and reuses this model.
    raw_output = run_docs_slm(prompt)
    doc = None

    if raw_output.strip():
        if '### Response:' in raw_output:
            doc = raw_output.split('### Response:')[-1].strip()
        else:
            doc = raw_output.strip()

    # ── Fallback to Groq if SLM failed ─────────────────────────
    if not doc:
        print('[docs_worker] Using Groq fallback.')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        doc = response.content

    return {'modified_code': doc, 'latest_code_iteration': doc}


# defining the function for the node which handles wrting response for the document created
def docs_summary(state: intellicode_state):

    # ── Build the prompt exactly as before ─────────────────────
    prompt = f"""You are a coding assistant.
Your task is to generate a brief, point-wise summary of the document that was created based on the user's request.

User prompt:
\"\"\"{state['prompt']}\"\"\"

Generated document content:
\"\"\"{state['modified_code']}\"\"\"

Write a short, clear, point-wise summary explaining:
- what the generated document contains
- what was done to create it
- which file format the document should be saved in (e.g., .md, .txt, .pdf, .docx) based on the user's request

Do NOT rewrite the document.
Do NOT include unnecessary details.
Output only concise bullet points.
"""

    # ── Try local docs/explain SLM (still loaded from docs_worker)
    raw_output = run_docs_slm(prompt)
    summary = None

    if raw_output.strip():
        if '### Response:' in raw_output:
            summary = raw_output.split('### Response:')[-1].strip()
        else:
            summary = raw_output.strip()

    # Unload docs SLM — docs path is done after this node
    unload_docs_slm()

    # ── Fallback to Groq if SLM failed ─────────────────────────
    if not summary:
        print('[docs_summary] Using Groq fallback.')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        summary = response.content

    return {'change_summary': summary}


# defining the function for the collator node which intake summary points from the nodes and create a refined response from the user
# def collator(state: intellicode_state):
#     message_summary = summarize_messages(state.get('messeges', []))

#     change_summary = state.get('change_summary', '')
#     prompt_text    = state.get('prompt', '')
#     task           = state.get('task_type', '')

#     # ── Build a simple formatter prompt matching fine-tuning format ──
#     raw_agent_output = f"Task: {prompt_text}\n\n{change_summary}"

#     formatter_prompt = f"""### Task:
# You are a response formatter. Take the raw agent output below and rewrite it as a clean, professional, well-structured response that is easy for the user to read and understand.
# Do not add new information. Only improve the clarity, structure, and readability of the existing content.

# ### Raw Agent Output:
# {raw_agent_output}

# ### Formatted Response:
# """

#     raw_output = run_formatter(formatter_prompt)
#     final_answer = None

#     if raw_output.strip() and len(raw_output.strip()) > 30:
#         final_answer = raw_output.strip()

#     # ── Fallback — use change_summary directly if formatter fails ──
#     if not final_answer:
#         print('[collator] Formatter produced no output — using change_summary directly.')
#         final_answer = change_summary

#     updated_messages = _append_message(
#         state.get('messeges', []), 'assistant', final_answer
#     )
#     return {
#         'final_answer':     final_answer,
#         'messeges':         updated_messages,
#         'message_summary':  message_summary,
#     }

def collator(state: intellicode_state):
    message_summary = summarize_messages(state.get('messeges', []))

    change_summary = state.get('change_summary', '')

    # Use change_summary directly as the final answer.
    # The formatter SLM (1B) is not reliable enough to reformat
    # arbitrary inputs without hallucinating — the bullet points
    # from the task nodes are already clean and readable.
    final_answer = change_summary if change_summary.strip() else 'Task completed.'

    updated_messages = _append_message(
        state.get('messeges', []), 'assistant', final_answer
    )
    return {
        'final_answer':    final_answer,
        'messeges':        updated_messages,
        'message_summary': message_summary,
    }

# defining the function for the unknown node which handles prompt which are not in default catagories
def unknown(state: intellicode_state):
    message_summary = summarize_messages(state.get('messeges', []))
    user_response = interrupt(
        "Your query could not be handled by the local model. "
        "It needs to be sent to an external AI API. "
        "Do you approve? (yes/no)"
    )

    normalized_response = str(user_response).strip().lower()

    if normalized_response == 'yes':
        prompt_content = f'''You are a coding assistant.
    Your task is to handle a prompt that does not fit the predefined categories.

    User prompt:
    """{state['prompt']}"""

    Conversation summary:
    """{message_summary or 'None'}"""

    Input code (optional; may be null):
    """{state['input_code']}"""

    Instructions:
    - Use the conversation summary only if it is relevant to the current user prompt.
    - If it is not relevant, ignore it completely.
    - Respond in a short, clear, point-wise way.
    - If the request needs code, include the corrected or generated code in modified_code.
    - Otherwise set modified_code to null.

    Return your output strictly as JSON with the fields summary and modified_code.
    '''

        response = llm.invoke([
            {
                'role': 'user',
                'content': prompt_content,
            }
        ])

        parsed_response = _parse_json_response(response.content)
        summary = parsed_response.get('summary', response.content)
        modified_code = parsed_response.get('modified_code')

        return {
            'change_summary': summary,
            'modified_code': modified_code,
            'latest_code_iteration': modified_code,
            'unknown_route': 'collator',
        }

    decline_message = 'Understood. Is there anything else I can help you with ?'
    updated_messages = _append_message(state.get('messeges', []), 'assistant', decline_message)

    return {
        'change_summary': decline_message,
        'final_answer': decline_message,
        'modified_code': None,
        'latest_code_iteration': None,
        'messeges': updated_messages,
        'unknown_route': 'end',
    }


def unknown_router(state: intellicode_state):
    if state.get('unknown_route') == 'collator':
        return 'collator'

    return END

# defining a function which handles the routing of the workflow from classifier node to the needed node for further processing

def task_router(state: intellicode_state) -> Literal['explain_slm','modify_code','debug_code','write_code','docs_worker','unknown']:

    if state['task_type']=='explain':
        return 'explain_slm'
    elif state['task_type']=='debug':
        return 'debug_code'
    elif state['task_type']=='modify':
        return 'modify_code'
    elif state['task_type']=='write':
        return 'write_code'
    elif state['task_type']=='docs':
        return 'docs_worker'
    else:
        return 'unknown'




## DEFINING THE GRAPH/ WORKFLOW FOR THE AGENTIC SYSTEM

graph=StateGraph(intellicode_state)


# adding nodes to the graph
graph.add_node('task_classifier',task_classifier)
graph.add_node('unknown',unknown)
graph.add_node('explain_slm',explain_slm)
graph.add_node('debug_code',debug_code)
graph.add_node('debug_summary',debug_summary)
graph.add_node('modify_code',modify_code)
graph.add_node('modify_summary',modify_summary)
graph.add_node('write_code',write_code)
graph.add_node('write_summary',write_summary)
graph.add_node('docs_worker',docs_worker)
graph.add_node('docs_summary',docs_summary)
graph.add_node('collator',collator)

# adding edges to the graph
graph.add_edge(START,'task_classifier')

graph.add_conditional_edges('task_classifier',task_router)

graph.add_conditional_edges('unknown', unknown_router)

graph.add_edge('explain_slm','collator')

graph.add_edge('debug_code','debug_summary')
graph.add_edge('debug_summary','collator')

graph.add_edge('modify_code','modify_summary')
graph.add_edge('modify_summary','collator')

graph.add_edge('write_code','write_summary')
graph.add_edge('write_summary','collator')

graph.add_edge('docs_worker','docs_summary')
graph.add_edge('docs_summary','collator')

graph.add_edge('collator',END)

#compiling the workflow

workflow=graph.compile(checkpointer=memory)
