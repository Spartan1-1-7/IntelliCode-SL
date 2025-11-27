"""
Agent module for the IntelliCode-SL agentic AI system.

This module provides base classes and interfaces for agents that utilize
specialized language models to perform code-related tasks.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from enum import Enum


class AgentType(Enum):
    """Enum for different types of agents."""

    CLASSIFICATION = "classification"
    DEBUGGING = "debugging"
    GENERATION = "generation"
    DOCUMENTATION = "documentation"


class BaseAgent(ABC):
    """
    Base class for all agents in the system.

    Each agent is responsible for handling a specific type of code-related
    task by utilizing a specialized language model.
    """

    def __init__(self, agent_type: AgentType, slm=None):
        """
        Initialize the base agent.

        Args:
            agent_type: Type of the agent
            slm: Specialized Language Model instance for this agent
        """
        self.agent_type = agent_type
        self.slm = slm

    @abstractmethod
    def process(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """
        Process input data using the agent's SLM.

        Args:
            input_data: Input data to process
            **kwargs: Additional parameters specific to the agent

        Returns:
            Dictionary containing processing results
        """
        pass

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the agent.

        Returns:
            Dictionary containing agent metadata
        """
        info = {"agent_type": self.agent_type.value, "has_slm": self.slm is not None}

        if self.slm:
            info["slm_info"] = self.slm.get_model_info()

        return info

    def validate_input(self, input_data: str) -> bool:
        """
        Validate input data before processing.

        Args:
            input_data: Input data to validate

        Returns:
            True if input is valid, False otherwise
        """
        if not input_data or not isinstance(input_data, str):
            return False
        return True
