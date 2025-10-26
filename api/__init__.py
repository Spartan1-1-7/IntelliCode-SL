"""
API module for the IntelliCode-SL agentic AI system.

This module provides RESTful API endpoints using FastAPI for interacting
with the specialized agents and language models.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from enum import Enum

from controller import Controller, TaskType


# Pydantic models for request/response validation
class TaskRequest(BaseModel):
    """Request model for processing tasks."""

    task_type: str = Field(
        ...,
        description="Type of task (classification, debugging, generation, documentation)",
    )
    input_data: str = Field(
        ..., description="Input data to process (code or description)"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional parameters for the task"
    )


class AutoRouteRequest(BaseModel):
    """Request model for auto-routing based on description."""

    input_data: str = Field(..., description="Input data to process")
    description: str = Field(
        ..., description="Description of the task for automatic routing"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional parameters for the task"
    )


class TaskResponse(BaseModel):
    """Response model for task results."""

    success: bool
    result: Dict[str, Any]
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    agents: Dict[str, Any]


# Initialize FastAPI app
app = FastAPI(
    title="IntelliCode-SL API",
    description="API for the IntelliCode-SL agentic AI system with specialized language models",
    version="1.0.0",
)

# Initialize controller
controller = Controller()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "IntelliCode-SL API",
        "version": "1.0.0",
        "description": "Agentic AI system with specialized language models for code tasks",
        "endpoints": {
            "POST /process": "Process a task with specified task type",
            "POST /auto-route": "Automatically route based on task description",
            "GET /health": "Check system health",
            "GET /agents": "Get information about all agents",
            "GET /agents/{task_type}": "Get information about a specific agent",
        },
    }


@app.post("/process", response_model=TaskResponse)
async def process_task(request: TaskRequest):
    """
    Process a task using the specified agent.

    Args:
        request: Task request containing task_type, input_data, and parameters

    Returns:
        Task response with results or error
    """
    try:
        parameters = request.parameters or {}
        result = controller.route(request.task_type, request.input_data, **parameters)

        if result.get("error"):
            return TaskResponse(success=False, result=result, error=result.get("error"))

        return TaskResponse(success=True, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auto-route", response_model=TaskResponse)
async def auto_route_task(request: AutoRouteRequest):
    """
    Automatically route a task based on description keywords.

    Args:
        request: Auto-route request with input_data, description, and parameters

    Returns:
        Task response with results or error
    """
    try:
        parameters = request.parameters or {}
        result = controller.auto_route(
            request.input_data, request.description, **parameters
        )

        if result.get("error"):
            return TaskResponse(success=False, result=result, error=result.get("error"))

        return TaskResponse(success=True, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health status of the system.

    Returns:
        Health status of controller and all agents
    """
    health_status = controller.health_check()
    return HealthResponse(
        status=health_status["controller"], agents=health_status["agents"]
    )


@app.get("/agents")
async def get_agents_info():
    """
    Get information about all available agents.

    Returns:
        Dictionary containing information about all agents
    """
    return controller.get_agent_info()


@app.get("/agents/{task_type}")
async def get_agent_info(task_type: str):
    """
    Get information about a specific agent.

    Args:
        task_type: Type of agent (classification, debugging, generation, documentation)

    Returns:
        Dictionary containing agent information
    """
    info = controller.get_agent_info(task_type)
    if info.get("error"):
        raise HTTPException(status_code=404, detail=info["error"])
    return info


@app.get("/task-types")
async def get_task_types():
    """
    Get list of available task types.

    Returns:
        List of available task types with descriptions
    """
    return {
        "task_types": [
            {
                "type": "classification",
                "description": "Classify code by language, type, complexity, etc.",
            },
            {
                "type": "debugging",
                "description": "Debug code, analyze errors, detect vulnerabilities",
            },
            {
                "type": "generation",
                "description": "Generate code from descriptions, complete code, refactor",
            },
            {
                "type": "documentation",
                "description": "Generate docstrings, README files, API documentation",
            },
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
