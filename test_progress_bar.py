#!/usr/bin/env python3
"""
Test script for the progress bar functionality.
"""

import sys
from pathlib import Path
import time

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.progress_tracker import GAProgressTracker


def test_progress_tracker():
    """Test the progress tracker with simulated GA run."""
    print("Testing Progress Tracker...\n")
    
    max_iterations = 5
    stagnation_limit = 3
    
    tracker = GAProgressTracker(
        max_iterations=max_iterations,
        stagnation_limit=stagnation_limit
    )
    
    tracker.start()
    
    try:
        for iteration in range(1, max_iterations + 1):
            # Start iteration
            stagnation = min(iteration - 1, stagnation_limit - 1)
            tracker.start_iteration(iteration, stagnation)
            
            # Simulate console output that should not be hindered
            print(f"\n{'='*80}")
            print(f"ITERATION {iteration}")
            print(f"{'='*80}")
            
            # Simulate job batch
            total_jobs = 20 + (iteration * 5)
            tracker.start_job_batch(total_jobs)
            
            print(f"Processing {total_jobs} jobs...")
            
            # Simulate job processing
            for job in range(total_jobs):
                time.sleep(0.1)  # Simulate job processing time
                tracker.update_job_progress(job + 1)
                
                # Occasional console output
                if (job + 1) % 10 == 0:
                    print(f"  Completed {job + 1} jobs")
            
            tracker.complete_job_batch()
            
            # Simulate other GA steps
            print("Tournament selection...")
            time.sleep(0.2)
            print("Crossover...")
            time.sleep(0.2)
            print("Mutation...")
            time.sleep(0.2)
            
            # Complete iteration
            tracker.complete_iteration()
            
            print(f"Iteration {iteration} complete")
    
    finally:
        tracker.stop()
    
    print("\n\n✅ Test complete!")
    print(f"Ran {max_iterations} iterations successfully")
    print("Progress bar displayed without hindering console output")


if __name__ == "__main__":
    test_progress_tracker()
