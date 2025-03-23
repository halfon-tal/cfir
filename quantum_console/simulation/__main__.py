"""Main entry point for quantum simulation."""

import asyncio
import logging
from ..scaling.integration_test import main

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the simulation
    print("\nStarting Quantum OS Simulation")
    print("============================")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    except Exception as e:
        print(f"\nSimulation failed: {str(e)}") 