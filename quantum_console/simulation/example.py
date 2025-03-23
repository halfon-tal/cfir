import asyncio
import logging
from datetime import datetime
import json

from .manager import SimulationManager, SimulationConfig
from ..visualization import SimulationVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def run_simulation():
    """Run the simulation demo."""
    
    # Create simulation config
    config = SimulationConfig(
        vehicle_count=50,
        traffic_light_count=10,
        utility_sensor_count=20,
        update_interval=0.1,
        simulation_area=1000.0
    )
    
    # Initialize simulation
    manager = SimulationManager(config)
    visualizer = SimulationVisualizer()
    
    try:
        # Start visualization
        visualizer.start()
        
        # Run simulation
        print("\nStarting simulation...")
        start_time = datetime.utcnow()
        
        # Run for 5 minutes
        simulation_task = asyncio.create_task(manager.run())
        await asyncio.sleep(300)  # 5 minutes
        
        # Stop simulation
        manager.stop()
        await simulation_task
        
        # Get final metrics
        duration = (datetime.utcnow() - start_time).total_seconds()
        metrics = manager.get_metrics()
        
        print("\nSimulation completed:")
        print(f"Duration: {duration:.1f} seconds")
        print(f"Updates: {metrics['update_count']}")
        print(f"Collision Alerts: {metrics['collision_alerts']}")
        print(f"Avg Traffic Congestion: {metrics['traffic_congestion']:.2f}")
        print(f"Avg Utility Efficiency: {metrics['utility_efficiency']:.2%}")
        
    except Exception as e:
        print(f"Simulation failed: {str(e)}")
        
    finally:
        visualizer.stop()

def main():
    asyncio.run(run_simulation())

if __name__ == "__main__":
    main() 