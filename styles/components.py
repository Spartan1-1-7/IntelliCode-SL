"""
UI Components for IntelliCode-SL application.

Contains reusable visual elements and styling helpers.
"""

import streamlit as st
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


def render_chat_container_end():
    """Render the end of the chat container."""
    return '</div>'


def render_chat_history(chat_history: list):
    """Render the complete chat history."""
    if len(chat_history) == 0:
        st.markdown(render_welcome_message(), unsafe_allow_html=True)
    else:
        for message in chat_history:
            if message['role'] == 'user':
                st.markdown(render_user_message(message['content']), unsafe_allow_html=True)
            else:
                st.markdown(render_assistant_message(message['content']), unsafe_allow_html=True)
