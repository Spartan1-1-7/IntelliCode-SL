from workflow import workflow

initial_state = {
            'prompt': 'modify this code to a fucntion ' ,
            'input_code': """evens = []
odds = []
while True:
    try:
        num = int(input("Enter a number (0 to stop): "))
        if num == 0:
            break
        if num % 2 == 0:
            evens.append(num)
        else:
            odds.append(num)
    except:
        continue
print("Even numbers:", evens)
print("Odd numbers:", odds)
"""
        }


final_state = workflow.invoke(initial_state)


response_content = final_state.get('final_answer', 'No response generated.')

# Extract modified_code for IDE
modified_code = final_state.get('modified_code', None)

# If workflow returned modified code, update the editor
if modified_code is not None and modified_code.strip():
    # Strip markdown code blocks if LLM wrapped code in ```
    cleaned_code = modified_code.strip()
    if cleaned_code.startswith('```'):
        lines = cleaned_code.split('\n')
        # Remove first line if it's ```python or similar
        if lines[0].startswith('```'):
            lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        cleaned_code = '\n'.join(lines)

    # Update the code in editor
    # st.session_state.code_content = cleaned_code
    # Increment counter to force editor refresh
    # st.session_state.editor_counter += 1

out = f"response: {response_content}\n\n\nmodified code: {modified_code}\n\n\ncleaned code:{cleaned_code}"
# out = f"response: {response_content}\n\n\nmodified code: {modified_code}\n\n\n"
print(out)