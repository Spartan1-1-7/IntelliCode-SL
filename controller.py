"""
Central Controller for the IntelliCode-SL agentic AI system.

This module provides the main controller that routes input requests to
the appropriate specialized agents based on the task type.
"""

from typing import Any, Dict, Optional
from enum import Enum

from agents.classification_agent import ClassificationAgent
from agents.debugging_agent import DebuggingAgent
from agents.generation_agent import GenerationAgent
from agents.documentation_agent import DocumentationAgent


class TaskType(Enum):
    """Enum for different task types that can be routed."""

    CLASSIFICATION = "classification"
    DEBUGGING = "debugging"
    GENERATION = "generation"
    DOCUMENTATION = "documentation"


class Controller:
    """
    Central controller for routing requests to specialized agents.

    The controller maintains instances of all specialized agents and routes
    incoming requests to the appropriate agent based on the task type.
    """

    def __init__(self):
        """Initialize the controller with all specialized agents."""
        self.agents = {
            TaskType.CLASSIFICATION: ClassificationAgent(),
            TaskType.DEBUGGING: DebuggingAgent(),
            TaskType.GENERATION: GenerationAgent(),
            TaskType.DOCUMENTATION: DocumentationAgent(),
        }

        self.task_keywords = {
            TaskType.CLASSIFICATION: [
                "classify",
                "classification",
                "identify language",
                "detect language",
                "complexity",
                "code type",
                "analyze type",
            ],
            TaskType.DEBUGGING: [
                "debug",
                "debugging",
                "bug",
                "error",
                "fix",
                "issue",
                "vulnerability",
                "security",
                "analyze error",
            ],
            TaskType.GENERATION: [
                "generate",
                "generation",
                "create",
                "write code",
                "complete",
                "refactor",
                "implement",
                "code completion",
            ],
            TaskType.DOCUMENTATION: [
                "document",
                "documentation",
                "docstring",
                "readme",
                "comments",
                "api docs",
                "explain code",
            ],
        }

    def route(self, task_type: str, input_data: str, **kwargs) -> Dict[str, Any]:
        """
        Route a request to the appropriate agent.

        Args:
            task_type: Type of task (classification, debugging, generation, documentation)
            input_data: Input data to process
            **kwargs: Additional parameters to pass to the agent

        Returns:
            Dictionary containing the agent's response
        """
        try:
            task_enum = TaskType(task_type.lower())
        except ValueError:
            return {
                "error": f"Invalid task type: {task_type}",
                "valid_types": [t.value for t in TaskType],
                "success": False,
            }

        agent = self.agents.get(task_enum)
        if not agent:
            return {
                "error": f"No agent found for task type: {task_type}",
                "success": False,
            }

        result = agent.process(input_data, **kwargs)
        result["controller"] = "central"

        return result

    def auto_route(
        self, input_data: str, description: str = "", **kwargs
    ) -> Dict[str, Any]:
        """
        Automatically route a request based on keywords in the description.

        Args:
            input_data: Input data to process
            description: Description of the task to help with routing
            **kwargs: Additional parameters to pass to the agent

        Returns:
            Dictionary containing the agent's response
        """
        description_lower = description.lower()

        # Check for keywords to determine task type
        for task_type, keywords in self.task_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return self.route(task_type.value, input_data, **kwargs)

        # Default to classification if no keywords match
        return {
            "error": "Could not determine task type from description",
            "suggestion": "Please specify task_type explicitly",
            "available_types": [t.value for t in TaskType],
            "success": False,
        }

    def get_agent_info(self, task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about agents.

        Args:
            task_type: Optional task type to get info for specific agent

        Returns:
            Dictionary containing agent information
        """
        if task_type:
            try:
                task_enum = TaskType(task_type.lower())
                agent = self.agents.get(task_enum)
                if agent:
                    return agent.get_agent_info()
                return {"error": f"No agent found for task type: {task_type}"}
            except ValueError:
                return {"error": f"Invalid task type: {task_type}"}

        # Return info for all agents
        return {
            task_type.value: agent.get_agent_info()
            for task_type, agent in self.agents.items()
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on all agents.

        Returns:
            Dictionary containing health status of all agents
        """
        status = {"controller": "healthy", "agents": {}}

        for task_type, agent in self.agents.items():
            status["agents"][task_type.value] = {
                "status": "healthy",
                "has_slm": agent.slm is not None,
                "slm_loaded": agent.slm.is_loaded if agent.slm else False,
            }

        return status
