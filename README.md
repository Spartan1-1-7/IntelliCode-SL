# IntelliCode-SL

An agentic AI system powered by specialized language models (SLMs) for code-related tasks. Each specialized model is paired with a dedicated agent, providing modular and extensible architecture for classification, debugging, code generation, and documentation tasks.

## 🏗️ Architecture

The system follows a modular architecture with clear separation of concerns:

```
IntelliCode-SL/
├── agents/              # Agent classes for task handling
│   ├── __init__.py
│   ├── classification_agent.py
│   ├── debugging_agent.py
│   ├── generation_agent.py
│   └── documentation_agent.py
├── slms/                # Specialized Language Model interfaces
│   ├── __init__.py
│   ├── classification_slm.py
│   ├── debugging_slm.py
│   ├── generation_slm.py
│   └── documentation_slm.py
├── api/                 # FastAPI REST API
│   └── __init__.py
├── tests/               # Test suite
├── controller.py        # Central routing controller
├── main.py             # Entry point (CLI & server)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## ✨ Features

### Specialized Agents & Models

1. **Classification Agent + SLM**
   - Programming language detection
   - Code type identification (function, class, module)
   - Complexity analysis
   - Code quality assessment

2. **Debugging Agent + SLM**
   - Bug detection and analysis
   - Error message interpretation
   - Fix suggestions
   - Security vulnerability detection

3. **Generation Agent + SLM**
   - Code generation from natural language
   - Code completion
   - Code refactoring
   - Test case generation

4. **Documentation Agent + SLM**
   - Docstring generation (Google, NumPy, Sphinx styles)
   - README creation
   - API documentation
   - Comment generation

### Central Controller

The controller routes requests to appropriate agents based on:
- Explicit task type specification
- Automatic routing via keyword detection in descriptions
- Extensible routing logic

### REST API

FastAPI-based REST API with:
- OpenAPI/Swagger documentation
- Request validation via Pydantic
- Health check endpoints
- Agent information endpoints

## 🚀 Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/Spartan1-1-7/IntelliCode-SL.git
cd IntelliCode-SL

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the System

#### 1. CLI Interface

```bash
# Basic usage
python main.py cli --task-type classification --input "def hello(): print('world')"

# From file
python main.py cli --task-type generation --file code.py --language python

# With context for debugging
python main.py cli --task-type debugging --input "error message" --context "code context"

# Auto-routing based on description
python main.py cli --task-type classification --input "code" --auto-route --description "classify this code"
```

#### 2. API Server

```bash
# Start the server (default: http://0.0.0.0:8000)
python main.py server

# Custom host and port
python main.py server --host 127.0.0.1 --port 8080

# Access API documentation at: http://localhost:8000/docs
```

#### 3. System Information

```bash
# Display system info and health status
python main.py info
```

## 📡 API Usage

### Example API Requests

#### Process a Task

```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "classification",
    "input_data": "def hello(): print(\"world\")",
    "parameters": {"top_k": 3}
  }'
```

#### Auto-Route Based on Description

```bash
curl -X POST "http://localhost:8000/auto-route" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": "def hello(): pass",
    "description": "generate documentation for this function",
    "parameters": {"doc_style": "google"}
  }'
```

#### Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

#### Get Agent Information

```bash
# All agents
curl -X GET "http://localhost:8000/agents"

# Specific agent
curl -X GET "http://localhost:8000/agents/classification"
```

## 🔧 Extending the System

### Adding a New Agent

1. Create a new SLM in `slms/`:

```python
from slms import BaseSLM, ModelType

class NewSLM(BaseSLM):
    def __init__(self, model_name="new-slm-v1", config=None):
        super().__init__(model_name, ModelType.NEW_TYPE, config)
    
    def load_model(self):
        # Implement model loading
        pass
    
    def predict(self, input_data, **kwargs):
        # Implement prediction logic
        pass
```

2. Create a corresponding agent in `agents/`:

```python
from agents import BaseAgent, AgentType

class NewAgent(BaseAgent):
    def __init__(self, slm=None):
        if slm is None:
            slm = NewSLM()
        super().__init__(AgentType.NEW_TYPE, slm)
    
    def process(self, input_data, **kwargs):
        # Implement processing logic
        pass
```

3. Register in the controller (`controller.py`):

```python
from agents.new_agent import NewAgent

# In Controller.__init__:
self.agents[TaskType.NEW_TYPE] = NewAgent()
```

### Integrating Real Models

Replace placeholder implementations in SLM classes with actual model loading:

```python
def load_model(self):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    
    self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
    self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
    self.is_loaded = True

def predict(self, input_data, **kwargs):
    inputs = self.tokenizer(input_data, return_tensors="pt")
    outputs = self.model(**inputs)
    # Process outputs...
    return results
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py
```

## 📋 Development

### Code Style

The project follows standard Python conventions:
- Type hints for function signatures
- Comprehensive docstrings (Google style)
- PEP 8 style guide

### Linting

```bash
# Format code
black .

# Type checking
mypy .

# Linting
flake8 .
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the web framework
- Pydantic for data validation
- The open-source AI/ML community

## 📞 Contact

For questions or feedback, please open an issue on GitHub.