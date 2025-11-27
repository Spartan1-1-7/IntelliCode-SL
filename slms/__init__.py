"""
SLM (Specialized Language Model) module interfaces.

This module provides base classes and interfaces for interacting with
specialized language models for various code-related tasks.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum


class ModelType(Enum):
    """Enum for different types of specialized language models."""

    CLASSIFICATION = "classification"
    DEBUGGING = "debugging"
    GENERATION = "generation"
    DOCUMENTATION = "documentation"


class BaseSLM(ABC):
    """
    Base class for all Specialized Language Models.

    This abstract class defines the interface that all SLM implementations
    must follow, ensuring consistency across different model types.
    """

    def __init__(
        self,
        model_name: str,
        model_type: ModelType,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the base SLM.

        Args:
            model_name: Name or identifier of the model
            model_type: Type of the specialized model
            config: Optional configuration dictionary for model parameters
        """
        self.model_name = model_name
        self.model_type = model_type
        self.config = config or {}
        self.is_loaded = False

    @abstractmethod
    def load_model(self) -> None:
        """
        Load the model into memory.

        This method should handle all model initialization and loading logic.
        """
        pass

    @abstractmethod
    def predict(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """
        Make a prediction using the loaded model.

        Args:
            input_data: The input text/code to process
            **kwargs: Additional arguments specific to the model type

        Returns:
            Dictionary containing the model's prediction and metadata
        """
        pass

    def unload_model(self) -> None:
        """
        Unload the model from memory.

        This method can be overridden to implement proper resource cleanup.
        """
        self.is_loaded = False

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.

        Returns:
            Dictionary containing model metadata
        """
        return {
            "model_name": self.model_name,
            "model_type": self.model_type.value,
            "is_loaded": self.is_loaded,
            "config": self.config,
        }
