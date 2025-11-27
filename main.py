"""
Streamlit application for IntelliCode-SL with VS Code-like interface.

Features:
- Code editor with syntax highlighting
- Chat interface
"""

import streamlit as st
from streamlit_ace import st_ace
from styles.components import (
    load_css,
    render_chat_container_start,
    render_chat_container_end,
    render_chat_history,
    get_image_base64
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

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'code_content' not in st.session_state:
    st.session_state.code_content = "# Write your code here\ndef hello_world():\n    print('Hello, World!')\n"

if 'selected_language' not in st.session_state:
    st.session_state.selected_language = 'python'

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
    
    # Code editor using streamlit-ace
    code_content = st_ace(
        value=st.session_state.code_content,
        language=st.session_state.selected_language,
        theme="monokai",
        keybinding="vscode",
        font_size=14,
        tab_size=4,
        show_gutter=True,
        show_print_margin=False,
        wrap=False,
        auto_update=True,
        readonly=False,
        min_lines=30,
        key="code_editor",
        height=700
    )
    
    # Update session state with code content
    if code_content != st.session_state.code_content:
        st.session_state.code_content = code_content
    
    # Code stats
    st.markdown(f"**Lines:** {len(st.session_state.code_content.split(chr(10)))} | **Characters:** {len(st.session_state.code_content)}")

# Right column - Chat Interface
with col_right:
    st.markdown("### 💬 Chat Assistant")
    
    # Chat history display with ChatGPT-style layout
    st.markdown(render_chat_container_start(), unsafe_allow_html=True)
    render_chat_history(st.session_state.chat_history)
    st.markdown(render_chat_container_end(), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create columns for input and send button side by side
    col_input, col_send = st.columns([10, 1])
    
    with col_input:
        user_input = st.text_input(
            "Message",
            placeholder="Type your message here... (Press Enter to send)",
            key="chat_input",
            label_visibility="collapsed"
        )
    
    with col_send:
        st.markdown('''
        <style>
            button[kind="secondary"] {
                background: none !important;
                background-color: transparent !important;
                border: none !important;
                padding: 0 !important;
                box-shadow: none !important;
                width: 32px !important;
                height: 32px !important;
            }
            button[kind="secondary"]:hover {
                background: none !important;
                background-color: transparent !important;
            }
            .send-icon {
                opacity: 0.5;
                cursor: pointer;
                transition: opacity 0.2s ease;
            }
            .send-icon:hover {
                opacity: 1 !important;
            }
        </style>
        <div style="display: flex; align-items: center; height: 40px;">
            <svg class="send-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="24" height="24"
                 onclick="document.querySelector('button[kind=\\'secondary\\']').click()">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
        </div>
        ''', unsafe_allow_html=True)
        send_button = st.button("", key="send_btn", type="secondary")
    
    # Automatically trigger send when Enter is pressed (user_input changes)
    if user_input and user_input != st.session_state.get('_last_sent_message', ''):
        send_button = True
    
    st.session_state['_last_input'] = user_input
    
    # Process chat input
    if send_button and user_input:
        # Store the sent message
        st.session_state['_last_sent_message'] = user_input
        
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Placeholder response - AI functionality coming soon
        response_content = "Thank you for your question! AI agent functionality is coming soon.\n\n"
        response_content += f"**Your Question:** {user_input}\n"
        response_content += f"\n**Code Length:** {len(st.session_state.code_content)} characters\n"
        response_content += f"**Language:** {st.session_state.selected_language}\n"
        response_content += "\n*This is a placeholder response. The actual AI agents will be integrated soon.*"
        
        # Add assistant response to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response_content
        })
        
        st.rerun()
