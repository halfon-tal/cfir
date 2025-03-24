import logging
import random
from quantum_console.core.hybrid_executer import (
    HybridExecutionManager,
    Task,
    TaskPriority,
    ProcessorType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demonstrate_hybrid_execution():
    """Demonstrate hybrid task execution."""
    
    # Initialize execution manager
    executor = HybridExecutionManager(
        cpu_count=2,
        qpu_count=1,
        complexity_threshold=5.0
    )
    
    # Create various tasks
    tasks = [
        # CPU tasks (complexity <= 5)
        Task(
            "data_preprocessing",
            {"data": "sample1"},
            complexity=3.0,
            priority=TaskPriority.MEDIUM
        ),
        Task(
            "simple_calculation",
            {"numbers": [1, 2, 3]},
            complexity=2.0,
            priority=TaskPriority.LOW
        ),
        
        # QPU tasks (complexity > 5)
        Task(
            "quantum_simulation",
            {"particles": 1000},
            complexity=8.0,
            priority=TaskPriority.HIGH
        ),
        Task(
            "optimization",
            {"dimensions": 50},
            complexity=7.0,
            priority=TaskPriority.CRITICAL
        )
    ]
    
    # Submit tasks
    task_ids = []
    for task in tasks:
        task_id = executor.submit_task(task)
        task_ids.append(task_id)
        print(f"\nSubmitted task: {task.task_type}")
        print(f"Task ID: {task_id}")
        print(f"Complexity: {task.complexity}")
        print(f"Priority: {task.priority.name}")
    
    # Process queue
    executor.process_queue()
    
    # Get results
    print("\nResults:")
    for task_id in task_ids:
        result = executor.get_result(task_id)
        if result:
            print(f"\nTask {task_id}:")
            print(f"Success: {result.success}")
            if result.success:
                print(f"Result: {result.result}")
            else:
                print(f"Error: {result.error}")
    
    # Show metrics
    print("\nExecution Metrics:")
    metrics = executor.get_metrics()
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    # Cleanup
    executor.shutdown()

def demonstrate_error_handling():
    """Demonstrate error handling and retries."""
    executor = HybridExecutionManager()
    
    # Create a task that might fail
    task = Task(
        "risky_operation",
        {"data": "sensitive"},
        complexity=6.0,
        priority=TaskPriority.HIGH,
        max_retries=2
    )
    
    task_id = executor.submit_task(task)
    executor.process_queue()
    
    result = executor.get_result(task_id)
    print("\nError Handling Demo:")
    print(f"Task {task_id} result:")
    print(f"Success: {result.success}")
    if not result.success:
        print(f"Error: {result.error}")
    
    executor.shutdown()

def main():
    demonstrate_hybrid_execution()
    demonstrate_error_handling()

if __name__ == "__main__":
    main() 