import logging
from typing import Dict, Any
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from threading import Lock

class MetricsVisualizer:
    """Real-time metrics visualization."""
    
    def __init__(self):
        self.logger = logging.getLogger("metrics_visualizer")
        self._lock = Lock()
        
        # Store historical metrics
        self.history = {
            'timestamps': [],
            'shard_counts': [],
            'node_counts': [],
            'latencies': [],
            'success_rates': []
        }
        
        # Setup plots
        plt.style.use('ggplot')  # Use a built-in style that looks nice
        self.fig = None
        self.axes = None
        self.lines = {
            'shard_dist': None,
            'node_util': None,
            'latency': None,
            'success': None
        }
        
        # Initialize plots
        self._init_plots()
        
        self.logger.info("MetricsVisualizer initialized")
        
    def _init_plots(self):
        """Initialize the visualization plots."""
        try:
            plt.ion()  # Enable interactive mode
            self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
            self.fig.canvas.manager.set_window_title('Quantum OS Metrics')
            
            # Shard distribution plot
            self.axes[0,0].set_title('Shard Distribution')
            self.axes[0,0].set_xlabel('Node ID')
            self.axes[0,0].set_ylabel('Shard Count')
            
            # Node utilization plot
            self.axes[0,1].set_title('Node Utilization')
            self.axes[0,1].set_xlabel('Time (s)')
            self.axes[0,1].set_ylabel('Active Nodes')
            self.lines['node_util'], = self.axes[0,1].plot([], [], 'b-', label='Active Nodes')
            
            # Latency plot
            self.axes[1,0].set_title('Operation Latency')
            self.axes[1,0].set_xlabel('Time (s)')
            self.axes[1,0].set_ylabel('Latency (ms)')
            self.lines['latency'], = self.axes[1,0].plot([], [], 'r-', label='Latency')
            self.axes[1,0].set_ylim([0, 100])
            
            # Success rate plot
            self.axes[1,1].set_title('Success Rate')
            self.axes[1,1].set_xlabel('Time (s)')
            self.axes[1,1].set_ylabel('Success Rate (%)')
            self.axes[1,1].set_ylim([0, 150])
            self.lines['success'], = self.axes[1,1].plot([], [], 'g-', label='Success Rate')
            
            # Add legends and grid
            for ax in self.axes.flat:
                ax.grid(True)
                ax.legend()
            
            plt.tight_layout()
            self.fig.show()  # Make sure window is shown
            
        except Exception as e:
            self.logger.error(f"Failed to initialize plots: {str(e)}")
            self.logger.exception("Detailed error:")

    def start(self) -> None:
        """Start the visualization."""
        plt.ion()  # Enable interactive mode
        if self.fig is None:
            self._init_plots()
        self.fig.show()
        plt.pause(0.1)  # Small pause to ensure window appears
        
    def stop(self) -> None:
        """Stop the visualization."""
        plt.ioff()
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.axes = None

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update visualization with new metrics."""
        if self.fig is None or not plt.fignum_exists(self.fig.number):
            self._init_plots()
            
        with self._lock:
            try:
                now = datetime.utcnow()
                
                # Debug logging
                self.logger.info(f"Updating metrics: {metrics}")
                
                # Update history
                self.history['timestamps'].append(now)
                self.history['shard_counts'].append(
                    metrics['shard_manager']['total_shards']
                )
                self.history['node_counts'].append(
                    len(metrics['shard_manager'].get('nodes', {}))
                )
                self.history['latencies'].append(
                    metrics['test']['avg_latency'] * 1000  # Convert to ms
                )
                
                # Calculate success rate
                operations = metrics['test']['data_operations']
                successes = metrics['test']['successful_operations']
                success_rate = (successes / max(operations, 1)) * 100
                self.history['success_rates'].append(success_rate)
                
                self.logger.info(
                    f"Calculating success rate: {successes}/{operations} = {success_rate:.2f}%"
                )
                
                # Update plots
                self._update_plots(metrics)
                
                # Force redraw
                self.fig.canvas.draw_idle()
                self.fig.canvas.flush_events()
                plt.pause(0.01)  # Small pause to allow GUI to update
                
            except Exception as e:
                self.logger.error(f"Failed to update metrics: {str(e)}")
                self.logger.exception("Detailed error:")
                
    def _update_plots(self, metrics: Dict[str, Any]) -> None:
        """Update all plot components."""
        try:
            # Convert timestamps to relative seconds
            start_time = min(self.history['timestamps'])
            times = [(t - start_time).total_seconds() for t in self.history['timestamps']]
            
            # Shard distribution
            self.axes[0,0].clear()
            if 'shard_distribution' in metrics['test']:
                nodes = list(metrics['test']['shard_distribution'].keys())
                counts = list(metrics['test']['shard_distribution'].values())
                self.axes[0,0].bar(nodes, counts)
                self.axes[0,0].set_title('Shard Distribution')
                self.axes[0,0].set_xlabel('Node ID')
                self.axes[0,0].set_ylabel('Shard Count')
                self.axes[0,0].tick_params(axis='x', rotation=45)
                self.axes[0,0].grid(True)
            
            # Update line plots
            self.lines['node_util'].set_data(times, self.history['node_counts'])
            self.lines['latency'].set_data(times, self.history['latencies'])
            self.lines['success'].set_data(times, self.history['success_rates'])
            
            # Update x-axis limits for all line plots
            for ax in [self.axes[0,1], self.axes[1,0], self.axes[1,1]]:
                ax.set_xlim(0, max(times) + 1)
            
            # Update y-axis limits
            if len(self.history['latencies']) > 0:
                max_latency = max(self.history['latencies'])
                self.axes[1,0].set_ylim(0, max(100, max_latency * 1.1))  # Add 10% headroom
            
            self.axes[0,1].set_ylim(0, max(self.history['node_counts']) + 1)
            
            # Redraw grids
            for ax in self.axes.flat:
                ax.grid(True)
            
            plt.tight_layout()
            
        except Exception as e:
            self.logger.error(f"Failed to update plots: {str(e)}")
            self.logger.exception("Detailed error:") 