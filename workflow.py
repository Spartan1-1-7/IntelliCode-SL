## IMPORTING THE NEEDED LIBRARIES

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage
from typing import TypedDict, Literal,Optional
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import os




## LOADING THE REQUIRED API KEYS AND VALIDATION LOGIC

# API key 
load_dotenv()
open_router_api=os.getenv('open_router_api')

# validation 
model=OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=open_router_api,
)




## DEFINING SCHEMAS FOR VARIOUS LLM/SLM POMPTS

# defining the schema for the task classifier node
class task_classifier_schema(BaseModel):
    task_type: Literal['explain','debug','write','docs','other']= Field(description='classify the prompt in various categories')

# defining the schema for the uknown node 
class unknown_node_schema(BaseModel):
    summary: str= Field(description='Point-wise brief response explaining the action taken for prompts that do not fit any predefined category.')
    modified_code : Optional[str] = Field(default=None, description='The final modified code produced by the node, containing only the corrected or generated code.')



## DEFINING THE STATE FOR THE WORKFLOW

# defining the literal for task_type
task_type= Literal['explain','debug','write','docs','other']

# defining the state
class intellicode_state( TypedDict):

    # user inputs
    prompt:str
    input_code: Optional[str] 

    # context
    messeges: list[BaseMessage]

    # Routing and task info
    task_type: task_type
    task_output: Optional[str]
    change_summary: Optional[str]

    # final response
    final_answer: Optional[str]
    modified_code: Optional[str]

    # metasdata (left empty for future additions)




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

Return only one word: explain, debug, write, docs, or other.
"""

    completion = model.beta.chat.completions.parse(

    model="x-ai/grok-4.1-fast",
    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ],
    response_format=task_classifier_schema,
    )

    task_type=completion.choices[0].message.parsed.task_type
    
    return {'task_type':task_type}

# defining the function which handles the explaination node of the workflow
def explain_slm (state:intellicode_state):
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


    completion = model.chat.completions.create(
    
    model="x-ai/grok-4.1-fast",
    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ]
    )
    # extracting the content

    explain=completion.choices[0].message.content
    return {'change_summary':explain}

# defining the function which handles the debuggin of the code
def debug_code (state:intellicode_state):
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

    completion = model.chat.completions.create(
    
    model="x-ai/grok-4.1-fast",
    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ]
    )
    # extracting the content

    code=completion.choices[0].message.content
    return {'modified_code':code}

# defining the fuction for the node which handles the response of debugging the code
def debug_summary (state:intellicode_state):
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

    completion = model.chat.completions.create(
    
    model="x-ai/grok-4.1-fast",
    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ]
    )
    # extracting the content

    summary=completion.choices[0].message.content
    return {'change_summary':summary}

# defining the function for the node which handles writing the code from scratch 
def write_code (state: intellicode_state):
    prompt = f"""You are a coding assistant.
Your task is to write the required code from scratch based on the user's prompt.

User prompt:
\"\"\"{state['prompt']}\"\"\"

Generate only the code that satisfies the request.
Do NOT include explanations, comments, markdown, or any extra text.
Output raw executable code only.
"""

    completion = model.chat.completions.create(
    
    model="x-ai/grok-4.1-fast",
    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ]
    )
    # extracting the content

    code=completion.choices[0].message.content
    return {'modified_code':code}

# defining the function which handles the node for writing summary about the code written from scratch
def write_summary (state: intellicode_state):
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

    completion = model.chat.completions.create(
    
    model="x-ai/grok-4.1-fast",
    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ]
    )
    # extracting the content

    summary=completion.choices[0].message.content
    return {'change_summary':summary}

# defining the function for the node which handles the writing of the documents for the code
def docs_worker (state: intellicode_state):
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

    completion = model.chat.completions.create(
    
    model="x-ai/grok-4.1-fast",
    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ]
    )
    # extracting the content

    doc=completion.choices[0].message.content
    return {'modified_code':doc}

# defining the function for the node which handles wrting response for the document created 
def docs_summary (state: intellicode_state):
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

    completion = model.chat.completions.create(
    
    model="x-ai/grok-4.1-fast",
    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ]
    )
    # extracting the content

    summary=completion.choices[0].message.content
    return {'change_summary':summary}

# defining the function for the collator node which intake summary points from the nodes and create a refined response from the user
def collator (state: intellicode_state):
    prompt = f"""You are a coding assistant.
Your task is to generate a refined, medium-length response for the user based on:
1. the original user prompt
2. the point-wise summary of the work done

User prompt:
\"\"\"{state['prompt']}\"\"\"

Summary of changes / generated content:
\"\"\"{state['change_summary']}\"\"\"

Write a clear, polished response that:
- starts with a short, refined paragraph explaining the result
- follows with brief, organized bullet points summarizing key actions or details
- stays concise and helpful

Do NOT include code unless the user explicitly asked for it.
Output a refined answer only—no extra commentary.
"""

    completion = model.chat.completions.create(
    
    model="x-ai/grok-4.1-fast",
    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ]
    )
    # extracting the content

    final_answer=completion.choices[0].message.content
    return {'final_answer':final_answer}

# defining the function for the unknown node which handles prompt which are not in default catagories
def unknown ( state: intellicode_state):
    prompt = f"""You are a coding assistant.
This node handles prompts that do not fit any predefined category. 
Your task is to produce output that matches the schema with the fields:
- summary: a brief, point-wise explanation of how the request was handled
- modified_code: optional, only include corrected or generated code if the user's prompt explicitly requires code

User prompt:
\"\"\"{state['prompt']}\"\"\"

Input code (optional; may be null):
\"\"\"{state['input_code']}\"\"\"

Generate output following these rules:

1. **summary**  
   - Provide a short, clear, point-wise response addressing the user's request.  
   - If input code is irrelevant or null, ignore it.  
   - Keep the points concise and helpful.  
   - No unnecessary details or commentary.

2. **modified_code**  
   - If the user's prompt requires producing or modifying code, return only the raw code here.  
   - If not required, return null.

Return your final output strictly in this JSON structure:

{{
  "summary": "...",
  "modified_code": "..." or null
}}
"""

    completion = model.beta.chat.completions.parse(

    model="x-ai/grok-4.1-fast",
    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ],
    response_format=unknown_node_schema,
    )

    response=completion.choices[0].message.parsed
    change_summary=response.summary
    modified_code=response.modified_code
    
    return {'change_summary':change_summary,'modified_code': modified_code}

# defining a function which handles the routing of the workflow from classifier node to the needed node for further processing 

def task_router (state: intellicode_state)-> Literal['explain_slm','debug_code','write_code','docs_worker','unknown']:

    if state['task_type']=='explain':
        return 'explain_slm'
    elif state['task_type']=='debug':
        return 'debug_code'
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
graph.add_node('write_code',write_code)
graph.add_node('write_summary',write_summary)
graph.add_node('docs_worker',docs_worker)
graph.add_node('docs_summary',docs_summary)
graph.add_node('collator',collator)

# adding edges to the graph
graph.add_edge(START,'task_classifier')

graph.add_conditional_edges('task_classifier',task_router)

graph.add_edge('unknown','collator')

graph.add_edge('explain_slm','collator')

graph.add_edge('debug_code','debug_summary')
graph.add_edge('debug_summary','collator')

graph.add_edge('write_code','write_summary')
graph.add_edge('write_summary','collator')

graph.add_edge('docs_worker','docs_summary')
graph.add_edge('docs_summary','collator')

graph.add_edge('collator',END)

#compiling the workflow
workflow=graph.compile()
