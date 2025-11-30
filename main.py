"""
Streamlit application for IntelliCode-SL with VS Code-like interface.

Features:
- Code editor with syntax highlighting
- Chat interface
"""

from workflow import workflow
import streamlit as st
from streamlit_ace import st_ace
from styles.components import (
    load_css,
    render_chat_history,
    render_send_button,
    render_page_title,
    render_code_editor_wrapper_start,
    render_code_stats
)

# Page configuration
st.set_page_config(
    page_title="IntelliCode-SL IDE",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load CSS styles
st.markdown(load_css('styles/chat_styles.css'), unsafe_allow_html=True)

# Add page title/heading
render_page_title()

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'code_content' not in st.session_state:
    st.session_state.code_content = "# Write your code here\ndef hello_world():\n    print('Hello, World!')\n"

if 'selected_language' not in st.session_state:
    st.session_state.selected_language = 'python'

if 'input_counter' not in st.session_state:
    st.session_state.input_counter = 0

if 'editor_counter' not in st.session_state:
    st.session_state.editor_counter = 0

# Create two-column layout
col_left, col_right = st.columns([1.5, 1])

# Left column - Code Editor
with col_left:
    st.markdown("### 💻 Code Editor")
    
    # Language selector
    language = st.selectbox(
        "Language",
        ["python", "javascript", "java", "cpp", "c", "go", "rust", "typescript"],
        key="language_selector"
    )
    st.session_state.selected_language = language
    
    # Start code editor wrapper with styling
    render_code_editor_wrapper_start()
    
    # Code editor using streamlit-ace
    code_content = st_ace(
        value=st.session_state.code_content,
        language=st.session_state.selected_language,
        theme="twilight",
        keybinding="vscode",
        font_size=14,
        tab_size=4,
        show_gutter=True,
        show_print_margin=False,
        wrap=False,
        auto_update=True,
        readonly=False,
        min_lines=30,
        key=f"code_editor_{st.session_state.editor_counter}",
        height=630
    )
    
    # Update session state with code content
    if code_content != st.session_state.code_content:
        st.session_state.code_content = code_content
    
    # Render code stats overlay at bottom right
    lines = len(st.session_state.code_content.split(chr(10)))
    chars = len(st.session_state.code_content)
    render_code_stats(lines, chars)

# Right column - Chat Interface
with col_right:
    st.markdown("### 💬 Chat Assistant")
    
    # Render chat history from components module
    render_chat_history(st.session_state.chat_history)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create columns for input and send button side by side
    col_input, col_send = st.columns([10, 1])
    
    with col_input:
        user_input = st.text_input(
            "Message",
            placeholder="Type your message here... (Press Enter to send)",
            key=f"chat_input_{st.session_state.input_counter}",
            label_visibility="collapsed"
        )
    
    with col_send:
        send_button = render_send_button()
    
    # Automatically trigger send when Enter is pressed (user_input changes)
    if user_input and user_input != st.session_state.get('_last_sent_message', ''):
        send_button = True
    
    st.session_state['_last_input'] = user_input
    
    # Process chat input
    if send_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # # Placeholder response - AI functionality coming soon
        # response_content = "Thank you for your question! AI agent functionality is coming soon.\n\n"
        # response_content += f"Your Question: {user_input}\n"
        # response_content += f"\nCode Length: {len(st.session_state.code_content)} characters\n"
        # response_content += f"Language: {st.session_state.selected_language}\n"
        # response_content += "\nThis is a placeholder response. The actual AI agents will be integrated soon."
        
        # Create initial_state for workflow
        initial_state = {
            'prompt': user_input,
            'input_code': st.session_state.code_content if st.session_state.code_content.strip() else None
        }

        # Invoke workflow
        final_state = workflow.invoke(initial_state)

        # Extract final_answer for chat
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
            st.session_state.code_content = cleaned_code
            # Increment counter to force editor refresh
            st.session_state.editor_counter += 1

        # Add assistant response to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response_content
        })
        
        # Increment counter to reset input field
        st.session_state.input_counter += 1
        st.session_state['_last_sent_message'] = user_input
        st.rerun()
