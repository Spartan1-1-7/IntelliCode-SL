# Quick Start Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/Spartan1-1-7/IntelliCode-SL.git
cd IntelliCode-SL

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### 1. Run Examples

```bash
python examples.py
```

This will demonstrate all four agent types with sample inputs.

### 2. Command Line Interface

#### Classification
```bash
python main.py cli --task-type classification --input "def hello(): pass"
```

#### Debugging
```bash
python main.py cli --task-type debugging --input "def divide(a,b): return a/b"
```

#### Code Generation
```bash
python main.py cli --task-type generation --input "create a function to sort a list" --language python
```

#### Documentation
```bash
python main.py cli --task-type documentation --input "def add(a,b): return a+b"
```

### 3. Using in Python Code

```python
from controller import Controller

# Initialize controller
controller = Controller()

# Use a specific agent
result = controller.route(
    task_type="classification",
    input_data="def hello(): pass"
)
print(result)

# Auto-route based on description
result = controller.auto_route(
    input_data="some code",
    description="I need to debug this code"
)
print(result)
```

### 4. REST API Server

```bash
# Start the server
python main.py server

# Access API documentation
# Open http://localhost:8000/docs in your browser
```

#### API Examples

```bash
# Classification
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"task_type":"classification","input_data":"def test(): pass"}'

# Health Check
curl http://localhost:8000/health

# Get Agent Info
curl http://localhost:8000/agents/classification
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## System Information

```bash
python main.py info
```

This displays:
- Available agents and their status
- Model information
- System health check

## Project Structure

```
IntelliCode-SL/
├── agents/              # Agent implementations
├── slms/                # Specialized Language Model interfaces
├── api/                 # FastAPI REST API
├── tests/               # Test suite
├── controller.py        # Central routing controller
├── main.py             # CLI entry point
├── examples.py         # Usage examples
└── README.md           # Full documentation
```

## Next Steps

1. **Add Real Models**: Replace placeholder implementations in `slms/` with actual model loading and inference
2. **Customize Agents**: Extend or modify agents in `agents/` for your specific use cases
3. **Add New Agents**: Follow the pattern to add new specialized agents
4. **Integration**: Use the API or Python SDK to integrate into your workflow

## Troubleshooting

### Import Errors
```bash
# Make sure you're in the project directory
cd IntelliCode-SL
# Ensure dependencies are installed
pip install -r requirements.txt
```

### API Server Issues
```bash
# Check if port is already in use
# Use a different port
python main.py server --port 8080
```

## Additional Resources

- Full documentation: See README.md
- API documentation: Run server and visit http://localhost:8000/docs
- Examples: Run `python examples.py`
