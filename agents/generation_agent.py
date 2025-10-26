"""
Generation Agent for code generation tasks.

This agent uses the Generation SLM to generate code from descriptions.
"""

from typing import Any, Dict, Optional
from agents import BaseAgent, AgentType
from slms.generation_slm import GenerationSLM


class GenerationAgent(BaseAgent):
    """
    Agent specialized in code generation tasks.
    
    This agent can:
    - Generate code from natural language descriptions
    - Complete partial code snippets
    - Refactor existing code
    - Generate test cases
    """
    
    def __init__(self, slm: Optional[GenerationSLM] = None):
        """
        Initialize the Generation Agent.
        
        Args:
            slm: Generation SLM instance. If None, creates a default instance.
        """
        if slm is None:
            slm = GenerationSLM()
        super().__init__(AgentType.GENERATION, slm)
    
    def process(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """
        Process input for code generation.
        
        Args:
            input_data: Description or partial code
            **kwargs: Additional parameters (e.g., task_type, language)
            
        Returns:
            Dictionary containing generated code
        """
        if not self.validate_input(input_data):
            return {
                "error": "Invalid input data",
                "agent_type": self.agent_type.value
            }
        
        task_type = kwargs.get("task_type", "general")
        
        if task_type == "function":
            language = kwargs.get("language", "python")
            result = self.slm.generate_function(input_data, language)
        elif task_type == "completion":
            language = kwargs.get("language", "python")
            result = self.slm.complete_code(input_data, language)
        elif task_type == "refactor":
            instructions = kwargs.get("instructions", "")
            result = self.slm.refactor_code(input_data, instructions)
        else:
            result = self.slm.predict(input_data, **kwargs)
        
        # Add agent metadata
        result["agent_type"] = self.agent_type.value
        result["success"] = True
        
        return result
    
    def generate_code(self, description: str, language: str = "python") -> Dict[str, Any]:
        """
        Generate code from a natural language description.
        
        Args:
            description: Natural language description of desired code
            language: Target programming language
            
        Returns:
            Dictionary with generated code
        """
        return self.process(description, language=language)
    
    def generate_function(self, description: str, language: str = "python") -> Dict[str, Any]:
        """
        Generate a function from a description.
        
        Args:
            description: Description of the function
            language: Target programming language
            
        Returns:
            Dictionary with generated function
        """
        return self.process(description, task_type="function", language=language)
    
    def complete_code(self, partial_code: str, language: str = "python") -> Dict[str, Any]:
        """
        Complete a partial code snippet.
        
        Args:
            partial_code: Incomplete code snippet
            language: Programming language
            
        Returns:
            Dictionary with completed code
        """
        return self.process(partial_code, task_type="completion", language=language)
    
    def refactor_code(self, code: str, instructions: str = "") -> Dict[str, Any]:
        """
        Refactor existing code.
        
        Args:
            code: Code to refactor
            instructions: Refactoring instructions
            
        Returns:
            Dictionary with refactored code
        """
        return self.process(code, task_type="refactor", instructions=instructions)
