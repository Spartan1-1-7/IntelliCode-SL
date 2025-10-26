"""
Debugging Agent for code debugging and error analysis tasks.

This agent uses the Debugging SLM to identify bugs and suggest fixes.
"""

from typing import Any, Dict, Optional
from agents import BaseAgent, AgentType
from slms.debugging_slm import DebuggingSLM


class DebuggingAgent(BaseAgent):
    """
    Agent specialized in code debugging tasks.
    
    This agent can:
    - Identify bugs in code
    - Analyze error messages
    - Suggest fixes
    - Detect security vulnerabilities
    """
    
    def __init__(self, slm: Optional[DebuggingSLM] = None):
        """
        Initialize the Debugging Agent.
        
        Args:
            slm: Debugging SLM instance. If None, creates a default instance.
        """
        if slm is None:
            slm = DebuggingSLM()
        super().__init__(AgentType.DEBUGGING, slm)
    
    def process(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """
        Process code or error messages for debugging.
        
        Args:
            input_data: Code snippet or error message to analyze
            **kwargs: Additional parameters (e.g., task_type, context)
            
        Returns:
            Dictionary containing debugging results
        """
        if not self.validate_input(input_data):
            return {
                "error": "Invalid input data",
                "agent_type": self.agent_type.value
            }
        
        task_type = kwargs.get("task_type", "general")
        
        if task_type == "error_analysis":
            context = kwargs.get("context", "")
            result = self.slm.analyze_error(input_data, context)
        elif task_type == "security":
            result = self.slm.detect_vulnerabilities(input_data)
        else:
            result = self.slm.predict(input_data, **kwargs)
        
        # Add agent metadata
        result["agent_type"] = self.agent_type.value
        result["success"] = True
        
        return result
    
    def debug_code(self, code: str, context: str = "") -> Dict[str, Any]:
        """
        Analyze code for bugs and issues.
        
        Args:
            code: Code snippet to debug
            context: Optional context about the code
            
        Returns:
            Dictionary with identified issues and suggested fixes
        """
        return self.process(code, context=context)
    
    def analyze_error(self, error_message: str, code_context: str = "") -> Dict[str, Any]:
        """
        Analyze an error message and suggest fixes.
        
        Args:
            error_message: Error message to analyze
            code_context: Code where the error occurred
            
        Returns:
            Dictionary with error analysis and suggestions
        """
        return self.process(error_message, task_type="error_analysis", context=code_context)
    
    def check_security(self, code: str) -> Dict[str, Any]:
        """
        Check code for security vulnerabilities.
        
        Args:
            code: Code snippet to check
            
        Returns:
            Dictionary with security analysis results
        """
        return self.process(code, task_type="security")
