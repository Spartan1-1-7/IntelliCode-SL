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
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start_index = text.find("{")
    if start_index == -1:
        start_index = text.find("[")

    if start_index != -1:
        text = text[start_index:]

    parsed_response, _ = json.JSONDecoder().raw_decode(text)
    if not isinstance(parsed_response, dict):
        raise ValueError('Expected a JSON object response')

    return parsed_response


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

# Defining the task_classifier function to classify the prompt into various catergories
def task_classifier (state:intellicode_state):
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

    response = llm.invoke([
        {
            'role': 'user',
            'content': prompt,
        }
    ])

    try:
        parsed_response = _parse_json_response(response.content)
    except (json.JSONDecodeError, ValueError):
        parsed_response = {'task_type': 'other'}
    task_type = parsed_response.get('task_type', 'other')
    if task_type not in ('explain', 'modify', 'debug', 'write', 'docs', 'other'):
        task_type = 'other'
    
    updated_messages = _append_message(state.get('messeges', []), 'user', state['prompt'])

    return {'task_type':task_type, 'messeges':updated_messages}

# defining the function which handles the explaination node of the workflow
def explain_slm (state:intellicode_state):
    response = run_docs_slm('explain', state['input_code'])
    unload_docs_slm()
    return {'change_summary':response, 'task_output':response}


def _build_code_input(state: intellicode_state) -> str:
    parts = [f"User prompt:
{state['prompt']}"]
    if state.get('input_code') is not None:
        parts.append(f"Input code:
{state['input_code']}")
    return '

'.join(parts)


def _build_summary_input(*sections: str) -> str:
    return '

'.join(
        section for section in sections if section is not None and str(section).strip()
    )

def modify_code (state:intellicode_state):
    combined_input = _build_code_input(state)
    code = run_coding_slm('modify', combined_input)
    return {'modified_code':code, 'latest_code_iteration':code, 'task_output':code}



def modify_summary (state:intellicode_state):
    summary_input = _build_summary_input(
        f"User request:
{state['prompt']}",
        f"Original code:
{state['input_code']}",
        f"Modified code:
{state.get('task_output') or state['modified_code']}",
        "Write a short, clear, point-wise summary describing exactly what was changed based on the user's request.",
        "Focus only on intentional modifications:",
        "- features added or removed",
        "- logic changes",
        "- structural changes",
        "- behavior changes",
        "Do NOT rewrite the code.",
        "Do NOT include extra explanations.",
        "Output only concise bullet points.",
    )

    summary = run_coding_slm('modify', summary_input)
    unload_coding_slm()
    return {'change_summary':summary}


# defining the function which handles the debuggin of the code
def debug_code (state:intellicode_state):
    combined_input = _build_code_input(state)
    code = run_coding_slm('debug', combined_input)
    return {'modified_code':code, 'latest_code_iteration':code, 'task_output':code}

# defining the fuction for the node which handles the response of debugging the code
def debug_summary (state:intellicode_state):
    summary_input = _build_summary_input(
        f"User prompt:
{state['prompt']}",
        f"Original input code:
{state['input_code']}",
        f"Debugged code (final corrected version):
{state.get('task_output') or state['modified_code']}",
        "Write a short, clear, point-wise summary describing exactly what was fixed, changed, or improved.",
        "Focus only on meaningful modifications:",
        "- bug fixes",
        "- syntax corrections",
        "- logic corrections",
        "- improvements required for the code to run",
        "Do NOT rewrite the code.",
        "Do NOT include extra explanations.",
        "Output only concise bullet points.",
    )

    summary = run_coding_slm('debug', summary_input)
    unload_coding_slm()
    return {'change_summary':summary}

# defining the function for the node which handles writing the code from scratch 
def write_code (state: intellicode_state):
    combined_input = _build_summary_input(
        f"User prompt:
{state['prompt']}",
        "Generate only the code that satisfies the request.",
        "Do NOT include explanations, comments, markdown, or any extra text.",
        "Output raw executable code only.",
    )

    code = run_coding_slm('write', combined_input)
    return {'modified_code':code, 'task_output':code}

# defining the function which handles the node for writing summary about the code written from scratch
def write_summary (state: intellicode_state):
    summary_input = _build_summary_input(
        f"User prompt:
{state['prompt']}",
        f"Generated code:
{state.get('task_output') or state['modified_code']}",
        "Write a short, clear, point-wise summary explaining what the generated code does.",
        "Do NOT rewrite the code.",
        "Do NOT include unnecessary details.",
        "Only describe the key functionality in concise bullet points.",
    )

    summary = run_coding_slm('write', summary_input)
    unload_coding_slm()
    return {'change_summary':summary}

# defining the function for the node which handles the writing of the documents for the code
def docs_worker (state: intellicode_state):
    combined_input = _build_summary_input(
        f"User prompt:
{state['prompt']}",
        f"Input code (context):
{state['input_code']}",
        "Generate the required document exactly as requested.",
        "Output only the document content.",
        "Do NOT include explanations, comments, markdown formatting, or any extra text.",
    )

    doc = run_docs_slm('docs', combined_input)
    return {'modified_code':doc, 'latest_code_iteration':doc, 'task_output':doc}

# defining the function for the node which handles wrting response for the document created 
def docs_summary (state: intellicode_state):
    summary_input = _build_summary_input(
        f"User prompt:
{state['prompt']}",
        f"Generated document content:
{state.get('task_output') or state['modified_code']}",
        "Write a short, clear, point-wise summary explaining:",
        "- what the generated document contains",
        "- what was done to create it",
        "- which file format the document should be saved in (e.g., .md, .txt, .pdf, .docx) based on the user's request",
        "Do NOT rewrite the document.",
        "Do NOT include unnecessary details.",
        "Output only concise bullet points.",
    )

    summary = run_docs_slm('docs', summary_input)
    unload_docs_slm()
    return {'change_summary':summary}

# defining the function for the collator node which intake summary points from the nodes and create a refined response from the user
def collator (state: intellicode_state):
    message_summary = summarize_messages(state.get('messeges', []))
    prompt = f"""You are a coding assistant.
Your task is to generate a refined, medium-length response for the user based on:
1. the original user prompt
2. the point-wise summary of the work done
3. the condensed memory summary of the conversation
    Use the previous conversation summary only when it is relevant to the current prompt; otherwise ignore it completely.

User prompt:
\"\"\"{state['prompt']}\"\"\"

 Conversation summary:
 \"\"\"{message_summary or 'None'}\"\"\"

 Summary of changes / generated content:
 \"\"\"{state['change_summary']}\"\"\"

Write a clear, polished response that:

- starts with a short, refined paragraph explaining the result
- follows with brief, organized bullet points summarizing key actions or details
- stays concise and helpful

Do NOT include code unless the user explicitly asked for it.
Output a refined answer only—no extra commentary.
"""

    response = llm.invoke([
        {
            'role': 'user',
            'content': prompt,
        }
    ])
    # extracting the content

    final_answer = response.content
    updated_messages = _append_message(state.get('messeges', []), 'assistant', final_answer)

    return {'final_answer':final_answer, 'messeges':updated_messages, 'message_summary':message_summary}

# defining the function for the unknown node which handles prompt which are not in default catagories
def unknown ( state: intellicode_state):
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

        try:
            parsed_response = _parse_json_response(response.content)
        except (json.JSONDecodeError, ValueError):
            parsed_response = {'summary': response.content.strip(), 'modified_code': None}
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

def task_router (state: intellicode_state)-> Literal['explain_slm','modify_code','debug_code','write_code','docs_worker','unknown']:

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
