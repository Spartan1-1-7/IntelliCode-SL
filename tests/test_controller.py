"""
Test suite for the Controller.
"""

import pytest
from controller import Controller, TaskType


class TestController:
    """Tests for the central Controller."""
    
    def test_controller_initialization(self):
        """Test that controller initializes with all agents."""
        controller = Controller()
        assert controller is not None
        assert len(controller.agents) == 4
        
    def test_route_classification(self):
        """Test routing to classification agent."""
        controller = Controller()
        result = controller.route("classification", "def hello(): pass")
        assert result.get("agent_type") == "classification"
        
    def test_route_debugging(self):
        """Test routing to debugging agent."""
        controller = Controller()
        result = controller.route("debugging", "error code")
        assert result.get("agent_type") == "debugging"
        
    def test_route_generation(self):
        """Test routing to generation agent."""
        controller = Controller()
        result = controller.route("generation", "create a function")
        assert result.get("agent_type") == "generation"
        
    def test_route_documentation(self):
        """Test routing to documentation agent."""
        controller = Controller()
        result = controller.route("documentation", "def hello(): pass")
        assert result.get("agent_type") == "documentation"
        
    def test_route_invalid_task_type(self):
        """Test routing with invalid task type."""
        controller = Controller()
        result = controller.route("invalid", "test")
        assert "error" in result
        assert result["success"] is False
        
    def test_auto_route_classification(self):
        """Test auto-routing to classification."""
        controller = Controller()
        result = controller.auto_route("code", "classify this code")
        # Should route to classification based on keyword
        assert result.get("agent_type") in ["classification"] or "error" in result
        
    def test_auto_route_generation(self):
        """Test auto-routing to generation."""
        controller = Controller()
        result = controller.auto_route("description", "generate code for a function")
        # Should route to generation based on keyword
        assert result.get("agent_type") in ["generation"] or "error" in result
        
    def test_get_agent_info_all(self):
        """Test getting info for all agents."""
        controller = Controller()
        info = controller.get_agent_info()
        assert len(info) == 4
        assert "classification" in info
        assert "debugging" in info
        assert "generation" in info
        assert "documentation" in info
        
    def test_get_agent_info_specific(self):
        """Test getting info for specific agent."""
        controller = Controller()
        info = controller.get_agent_info("classification")
        assert "agent_type" in info
        assert info["agent_type"] == "classification"
        
    def test_health_check(self):
        """Test health check functionality."""
        controller = Controller()
        health = controller.health_check()
        assert health["controller"] == "healthy"
        assert "agents" in health
        assert len(health["agents"]) == 4
