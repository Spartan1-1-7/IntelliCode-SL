"""
Classification Agent for code classification tasks.

This agent uses the Classification SLM to classify code into various categories.
"""

from typing import Any, Dict, Optional
from agents import BaseAgent, AgentType
from slms.classification_slm import ClassificationSLM


class ClassificationAgent(BaseAgent):
    """
    Agent specialized in code classification tasks.

    This agent can classify code by:
    - Programming language
    - Code type (function, class, module)
    - Complexity level
    - Code quality
    """

    def __init__(self, slm: Optional[ClassificationSLM] = None):
        """
        Initialize the Classification Agent.

        Args:
            slm: Classification SLM instance. If None, creates a default instance.
        """
        if slm is None:
            slm = ClassificationSLM()
        super().__init__(AgentType.CLASSIFICATION, slm)

    def process(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """
        Process code for classification.

        Args:
            input_data: Code snippet to classify
            **kwargs: Additional parameters (e.g., task_type, top_k)

        Returns:
            Dictionary containing classification results
        """
        if not self.validate_input(input_data):
            return {"error": "Invalid input data", "agent_type": self.agent_type.value}

        task_type = kwargs.get("task_type", "general")

        if task_type == "language":
            result = self.slm.classify_language(input_data)
        elif task_type == "complexity":
            result = self.slm.classify_complexity(input_data)
        else:
            result = self.slm.predict(input_data, **kwargs)

        # Add agent metadata
        result["agent_type"] = self.agent_type.value
        result["success"] = True

        return result

    def classify_language(self, code: str) -> Dict[str, Any]:
        """
        Classify the programming language of the code.

        Args:
            code: Code snippet to classify

        Returns:
            Dictionary with language classification results
        """
        return self.process(code, task_type="language")

    def classify_complexity(self, code: str) -> Dict[str, Any]:
        """
        Classify the complexity level of the code.

        Args:
            code: Code snippet to classify

        Returns:
            Dictionary with complexity classification results
        """
        return self.process(code, task_type="complexity")

    def classify_code_type(self, code: str) -> Dict[str, Any]:
        """
        Classify the type of code (function, class, module, etc.).

        Args:
            code: Code snippet to classify

        Returns:
            Dictionary with code type classification results
        """
        return self.process(code, task_type="code_type")
