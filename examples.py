"""
Example usage of the IntelliCode-SL agentic AI system.

This script demonstrates how to use the various agents and features
of the IntelliCode-SL system.
"""

from controller import Controller


def main():
    """Run examples demonstrating the system's capabilities."""

    # Initialize the controller
    controller = Controller()

    print("=" * 60)
    print("IntelliCode-SL System Examples")
    print("=" * 60)

    # Example 1: Code Classification
    print("\n1. Code Classification Example:")
    print("-" * 60)
    code_sample = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    result = controller.route("classification", code_sample.strip())
    print(f"Task: Classify code snippet")
    print(f"Result: {result.get('predictions', [])}")

    # Example 2: Code Debugging
    print("\n2. Code Debugging Example:")
    print("-" * 60)
    buggy_code = """
def divide(a, b):
    result = a / b
    return result
"""
    result = controller.route("debugging", buggy_code.strip())
    print(f"Task: Analyze code for potential issues")
    print(f"Issues found: {len(result.get('issues', []))}")
    for issue in result.get("issues", [])[:2]:
        print(f"  - {issue.get('type')}: {issue.get('description')}")

    # Example 3: Code Generation
    print("\n3. Code Generation Example:")
    print("-" * 60)
    description = "Create a function that calculates the factorial of a number"
    result = controller.route("generation", description, language="python")
    print(f"Task: {description}")
    print(f"Generated code preview:")
    print(result.get("generated_code", "")[:200] + "...")

    # Example 4: Documentation Generation
    print("\n4. Documentation Generation Example:")
    print("-" * 60)
    code_to_document = """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
"""
    result = controller.route("documentation", code_to_document.strip())
    print(f"Task: Generate documentation for quicksort function")
    print(f"Documentation preview:")
    print(result.get("documentation", "")[:200] + "...")

    # Example 5: Auto-routing
    print("\n5. Auto-routing Example:")
    print("-" * 60)
    code = "def test(): pass"
    description = "I need to generate documentation for this function"
    result = controller.auto_route(code, description)
    print(f"Description: {description}")
    print(f"Routed to: {result.get('agent_type', 'unknown')} agent")
    print(f"Success: {result.get('success', False)}")

    # System Health Check
    print("\n6. System Health Check:")
    print("-" * 60)
    health = controller.health_check()
    print(f"Controller status: {health['controller']}")
    print(f"Available agents: {len(health['agents'])}")
    for agent_name, agent_status in health["agents"].items():
        print(f"  - {agent_name}: {agent_status['status']}")

    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
