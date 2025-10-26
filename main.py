"""
Main entry point for the IntelliCode-SL agentic AI system.

This module provides the main entry point for running the system, including
CLI interface and server startup.
"""

import argparse
import sys
from typing import Optional

from controller import Controller


def run_cli(controller: Controller, args: argparse.Namespace) -> None:
    """
    Run the CLI interface for the IntelliCode-SL system.
    
    Args:
        controller: Controller instance
        args: Parsed command-line arguments
    """
    task_type = args.task_type
    input_data = args.input
    
    # Read from file if specified
    if args.file:
        try:
            with open(args.file, 'r') as f:
                input_data = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    
    if not input_data:
        print("Error: No input provided. Use --input or --file")
        sys.exit(1)
    
    # Prepare parameters
    parameters = {}
    if args.language:
        parameters["language"] = args.language
    if args.context:
        parameters["context"] = args.context
    
    # Route the request
    if args.auto_route and args.description:
        result = controller.auto_route(input_data, args.description, **parameters)
    else:
        result = controller.route(task_type, input_data, **parameters)
    
    # Display result
    print("\n=== IntelliCode-SL Result ===")
    print(f"Task Type: {result.get('agent_type', task_type)}")
    print(f"Success: {result.get('success', False)}")
    
    if result.get("error"):
        print(f"\nError: {result['error']}")
    else:
        print(f"\nResult:")
        for key, value in result.items():
            if key not in ["agent_type", "success", "controller"]:
                print(f"  {key}: {value}")


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """
    Run the FastAPI server.
    
    Args:
        host: Host address to bind to
        port: Port to listen on
    """
    import uvicorn
    from api import app
    
    print(f"Starting IntelliCode-SL API server on {host}:{port}")
    print(f"API documentation available at http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="IntelliCode-SL: Agentic AI system with specialized language models"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # CLI command
    cli_parser = subparsers.add_parser("cli", help="Run CLI interface")
    cli_parser.add_argument(
        "--task-type",
        type=str,
        required=True,
        choices=["classification", "debugging", "generation", "documentation"],
        help="Type of task to perform"
    )
    cli_parser.add_argument(
        "--input",
        type=str,
        help="Input data (code or description)"
    )
    cli_parser.add_argument(
        "--file",
        type=str,
        help="Read input from file"
    )
    cli_parser.add_argument(
        "--language",
        type=str,
        help="Programming language (for generation tasks)"
    )
    cli_parser.add_argument(
        "--context",
        type=str,
        help="Additional context (for debugging tasks)"
    )
    cli_parser.add_argument(
        "--auto-route",
        action="store_true",
        help="Automatically route based on description"
    )
    cli_parser.add_argument(
        "--description",
        type=str,
        help="Description for auto-routing"
    )
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Run API server")
    server_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address to bind to (default: 0.0.0.0)"
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)"
    )
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show system information")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Initialize controller
    controller = Controller()
    
    # Execute command
    if args.command == "cli":
        run_cli(controller, args)
    elif args.command == "server":
        run_server(args.host, args.port)
    elif args.command == "info":
        print("\n=== IntelliCode-SL System Information ===")
        print("\nAvailable Agents:")
        agent_info = controller.get_agent_info()
        for task_type, info in agent_info.items():
            print(f"\n  {task_type}:")
            print(f"    Has SLM: {info['has_slm']}")
            if info.get('slm_info'):
                print(f"    Model: {info['slm_info']['model_name']}")
                print(f"    Loaded: {info['slm_info']['is_loaded']}")
        
        print("\n\nHealth Check:")
        health = controller.health_check()
        print(f"  Controller: {health['controller']}")
        print(f"  Agents: {len(health['agents'])} available")


if __name__ == "__main__":
    main()
