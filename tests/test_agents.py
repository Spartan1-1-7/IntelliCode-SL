"""
Test suite for the IntelliCode-SL agents.
"""

import pytest
from agents.classification_agent import ClassificationAgent
from agents.debugging_agent import DebuggingAgent
from agents.generation_agent import GenerationAgent
from agents.documentation_agent import DocumentationAgent


class TestClassificationAgent:
    """Tests for ClassificationAgent."""

    def test_agent_initialization(self):
        """Test that agent initializes correctly."""
        agent = ClassificationAgent()
        assert agent is not None
        assert agent.slm is not None

    def test_process_valid_input(self):
        """Test processing valid input."""
        agent = ClassificationAgent()
        result = agent.process("def hello(): pass")
        assert result["success"] is True
        assert "predictions" in result

    def test_process_invalid_input(self):
        """Test processing invalid input."""
        agent = ClassificationAgent()
        result = agent.process("")
        assert "error" in result

    def test_classify_language(self):
        """Test language classification."""
        agent = ClassificationAgent()
        result = agent.classify_language("def hello(): pass")
        assert result["success"] is True


class TestDebuggingAgent:
    """Tests for DebuggingAgent."""

    def test_agent_initialization(self):
        """Test that agent initializes correctly."""
        agent = DebuggingAgent()
        assert agent is not None
        assert agent.slm is not None

    def test_debug_code(self):
        """Test code debugging."""
        agent = DebuggingAgent()
        result = agent.debug_code("def hello(): pass")
        assert result["success"] is True
        assert "issues" in result

    def test_analyze_error(self):
        """Test error analysis."""
        agent = DebuggingAgent()
        result = agent.analyze_error("NullPointerException", "some context")
        assert result["success"] is True


class TestGenerationAgent:
    """Tests for GenerationAgent."""

    def test_agent_initialization(self):
        """Test that agent initializes correctly."""
        agent = GenerationAgent()
        assert agent is not None
        assert agent.slm is not None

    def test_generate_code(self):
        """Test code generation."""
        agent = GenerationAgent()
        result = agent.generate_code("create a hello world function")
        assert result["success"] is True
        assert "generated_code" in result

    def test_complete_code(self):
        """Test code completion."""
        agent = GenerationAgent()
        result = agent.complete_code("def hello():")
        assert result["success"] is True


class TestDocumentationAgent:
    """Tests for DocumentationAgent."""

    def test_agent_initialization(self):
        """Test that agent initializes correctly."""
        agent = DocumentationAgent()
        assert agent is not None
        assert agent.slm is not None

    def test_generate_docstring(self):
        """Test docstring generation."""
        agent = DocumentationAgent()
        result = agent.generate_docstring("def hello(): pass")
        assert result["success"] is True
        assert "documentation" in result

    def test_generate_readme(self):
        """Test README generation."""
        agent = DocumentationAgent()
        result = agent.generate_readme("A test project")
        assert result["success"] is True
