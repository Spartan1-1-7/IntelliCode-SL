"""
Documentation Agent for code documentation tasks.

This agent uses the Documentation SLM to generate and improve documentation.
"""

from typing import Any, Dict, List, Optional
from agents import BaseAgent, AgentType
from slms.documentation_slm import DocumentationSLM


class DocumentationAgent(BaseAgent):
    """
    Agent specialized in code documentation tasks.

    This agent can:
    - Generate docstrings
    - Create README files
    - Generate API documentation
    - Improve existing documentation
    """

    def __init__(self, slm: Optional[DocumentationSLM] = None):
        """
        Initialize the Documentation Agent.

        Args:
            slm: Documentation SLM instance. If None, creates a default instance.
        """
        if slm is None:
            slm = DocumentationSLM()
        super().__init__(AgentType.DOCUMENTATION, slm)

    def process(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """
        Process input for documentation generation.

        Args:
            input_data: Code or project description
            **kwargs: Additional parameters (e.g., task_type, doc_style)

        Returns:
            Dictionary containing generated documentation
        """
        if not self.validate_input(input_data):
            return {"error": "Invalid input data", "agent_type": self.agent_type.value}

        task_type = kwargs.get("task_type", "general")

        if task_type == "docstring":
            style = kwargs.get("doc_style", "google")
            result = self.slm.generate_docstring(input_data, style)
        elif task_type == "readme":
            code_samples = kwargs.get("code_samples", None)
            result = self.slm.generate_readme(input_data, code_samples)
        elif task_type == "improve":
            existing_docs = kwargs.get("existing_docs", "")
            result = self.slm.improve_documentation(input_data, existing_docs)
        else:
            result = self.slm.predict(input_data, **kwargs)

        # Add agent metadata
        result["agent_type"] = self.agent_type.value
        result["success"] = True

        return result

    def generate_docstring(self, code: str, style: str = "google") -> Dict[str, Any]:
        """
        Generate a docstring for code.

        Args:
            code: Code to document
            style: Documentation style (google, numpy, sphinx)

        Returns:
            Dictionary with generated docstring
        """
        return self.process(code, task_type="docstring", doc_style=style)

    def generate_readme(
        self, project_description: str, code_samples: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a README file for a project.

        Args:
            project_description: Description of the project
            code_samples: Optional code samples to include

        Returns:
            Dictionary with generated README
        """
        return self.process(
            project_description, task_type="readme", code_samples=code_samples
        )

    def improve_documentation(self, code: str, existing_docs: str) -> Dict[str, Any]:
        """
        Improve existing documentation.

        Args:
            code: The code being documented
            existing_docs: Current documentation

        Returns:
            Dictionary with improved documentation
        """
        return self.process(code, task_type="improve", existing_docs=existing_docs)

    def document_api(self, code: str) -> Dict[str, Any]:
        """
        Generate API documentation for code.

        Args:
            code: Code to generate API docs for

        Returns:
            Dictionary with API documentation
        """
        return self.process(code, task_type="api_docs")
