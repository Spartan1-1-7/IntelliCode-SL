"""
UI Components for IntelliCode-SL application.

Contains reusable visual elements and styling helpers.
"""

import streamlit as st
import streamlit.components.v1 as components
import base64
from pathlib import Path


def load_css(file_path: str) -> str:
    """Load CSS from a file."""
    with open(file_path, 'r') as f:
        return f'<style>{f.read()}</style>'


def get_image_base64(image_path: str) -> str:
    """Convert image to base64 string."""
    with open(image_path, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def render_welcome_message():
    """Render the welcome message when chat is empty."""
    return """
    <div style="text-align: center; padding: 40px 20px; color: #888;">
        <div style="font-size: 48px; margin-bottom: 16px;">💬</div>
        <div style="font-size: 16px; font-weight: 500; margin-bottom: 8px;">How can I help you today?</div>
        <div style="font-size: 13px; opacity: 0.7;">Ask me anything about your code</div>
    </div>
    """


def render_user_message(content: str) -> str:
    """Render a user message bubble."""
    return f"""
    <div class="chat-message user-message">
        <div>
            <div class="message-label user-label">You</div>
            <div class="message-content">{content}</div>
        </div>
    </div>
    """


def render_assistant_message(content: str) -> str:
    """Render an assistant message bubble."""
    return f"""
    <div class="chat-message assistant-message">
        <div>
            <div class="message-label assistant-label">Assistant</div>
            <div class="message-content">{content}</div>
        </div>
    </div>
    """


def render_chat_container_start():
    """Render the start of the chat container."""
    return '<div class="chat-container">'


def render_send_button():
    """Render the send button with SVG icon."""
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
    return st.button("", key="send_btn", type="secondary")


def render_chat_history(chat_history: list):
    """Render the complete chat history in a scrollable container."""
    import html as html_lib
    
    # Build complete HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    body {
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
    }
    .chat-scroll-wrapper {
        height: 680px;
        overflow-y: auto;
        overflow-x: hidden;
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 10px;
    }
    .chat-scroll-wrapper::-webkit-scrollbar {
        width: 8px;
    }
    .chat-scroll-wrapper::-webkit-scrollbar-track {
        background: #1a1a1a;
    }
    .chat-scroll-wrapper::-webkit-scrollbar-thumb {
        background: #3a3a3a;
        border-radius: 4px;
    }
    .chat-message {
        display: flex;
        padding: 16px;
        border-radius: 12px;
        font-size: 14px;
        line-height: 1.6;
        margin-bottom: 16px;
        animation: fadeIn 0.3s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .user-message {
        background-color: #2f2f2f;
        color: #ececec;
        margin-left: 20px;
        border: 1px solid #3f3f3f;
    }
    .assistant-message {
        background-color: #1a1a1a;
        color: #d1d1d1;
        margin-right: 20px;
        border: 1px solid #2a2a2a;
    }
    .message-label {
        font-weight: 600;
        margin-bottom: 8px;
        font-size: 13px;
        opacity: 0.8;
    }
    .user-label {
        color: #4a9eff;
    }
    .assistant-label {
        color: #10a37f;
    }
    .message-content {
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    </style>
    </head>
    <body>
    <div class="chat-scroll-wrapper">
    """
    
    if len(chat_history) == 0:
        html_content += """
        <div style="text-align: center; padding: 40px 20px; color: #888;">
            <div style="font-size: 48px; margin-bottom: 16px;">💬</div>
            <div style="font-size: 16px; font-weight: 500; margin-bottom: 8px;">How can I help you today?</div>
            <div style="font-size: 13px; opacity: 0.7;">Ask me anything about your code</div>
        </div>
        """
    else:
        for message in chat_history:
            # Escape HTML entities
            content = html_lib.escape(str(message['content']))
            
            if message['role'] == 'user':
                html_content += f"""
                <div class="chat-message user-message">
                    <div>
                        <div class="message-label user-label">You</div>
                        <div class="message-content">{content}</div>
                    </div>
                </div>
                """
            else:
                html_content += f"""
                <div class="chat-message assistant-message">
                    <div>
                        <div class="message-label assistant-label">Assistant</div>
                        <div class="message-content">{content}</div>
                    </div>
                </div>
                """
    
    html_content += """
    </div>
    </body>
    </html>
    """
    
    # Use components.html to render
    components.html(html_content, height=700, scrolling=False)
