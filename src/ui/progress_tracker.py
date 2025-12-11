"""
Progress tracking for genetic algorithm iterations.

This module provides a compact single-line progress tracker that displays:
- Graphical progress bar with completion percentage
- Iteration count (current/total)
- Job batch progress when active
- Elapsed time and estimated time remaining
- Stagnation count monitoring

The progress is printed periodically (every 10 seconds) or on completion events
to avoid conflicts with other console output.

Display format:
    🚀 [████████████░░░░░░░░] 60.0% | Iter:3/5 | Jobs:35/35(100%) | Elapsed:10.2s | ETA:6.7s | Stag:2/3

Example usage:
    tracker = GAProgressTracker(max_iterations=50, stagnation_limit=10)
    tracker.start()
    
    for iteration in range(max_iterations):
        tracker.start_iteration(iteration + 1, stagnation_count)
        
        # Start job batch
        tracker.start_job_batch(total_jobs=100)
        
        # Process jobs and update progress
        for job in range(100):
            # ... process job ...
            tracker.update_job_progress(job + 1)
        
        tracker.complete_job_batch()
        tracker.complete_iteration()
    
    tracker.stop()
"""

import time
from typing import Optional


class GAProgressTracker:
    """
    Progress tracker for genetic algorithm with iteration and job metrics.
    
    This tracker prints a compact single-line progress summary periodically
    to avoid interfering with other console output. The line includes:
    
    - Graphical progress bar (█ = completed, ░ = remaining)
    - Percentage completion
    - Iteration count (current/total)
    - Job batch progress when active (current/total with percentage)
    - Elapsed time
    - Estimated time remaining (when available)
    - Stagnation count (current/limit)
    
    Progress is printed every 10 seconds or when a job batch/iteration completes.
    """
    
    def __init__(self, max_iterations: int, stagnation_limit: int, console: Optional[object] = None):
        """
        Initialize the progress tracker.
        
        Args:
            max_iterations: Maximum number of iterations
            stagnation_limit: Stagnation limit for stopping
            console: Unused, kept for compatibility
        """
        self.max_iterations = max_iterations
        self.stagnation_limit = stagnation_limit
        
        # Iteration tracking
        self.current_iteration = 0
        self.stagnation_count = 0
        self.iteration_start_time = None
        self.overall_start_time = None
        self.iteration_times = []
        
        # Job tracking
        self.total_jobs = 0
        self.completed_jobs = 0
        self.job_start_time = None
        self.job_times = []
        
        # Last print time for periodic updates
        self.last_print_time = None
        self.print_interval = 10.0  # Print every 10 seconds
    
    def start(self):
        """Start the progress tracker."""
        self.overall_start_time = time.time()
        self.iteration_start_time = time.time()
        self.last_print_time = time.time()
        self._print_progress()
    
    def stop(self):
        """Stop the progress tracker and print final summary."""
        self._print_progress(force=True)
    
    def _print_progress(self, force: bool = False):
        """
        Print progress summary if enough time has elapsed or if forced.
        
        Args:
            force: If True, always print regardless of time elapsed
        """
        current_time = time.time()
        if not force and self.last_print_time and (current_time - self.last_print_time) < self.print_interval:
            return
        
        self.last_print_time = current_time
        
        # Calculate statistics
        avg_iteration_time = self._get_avg_iteration_time()
        elapsed = current_time - self.overall_start_time if self.overall_start_time else 0
        
        # Build compact single-line progress
        iter_pct = (self.current_iteration / self.max_iterations * 100) if self.max_iterations > 0 else 0
        
        # Create text-based progress bar for iterations
        bar_width = 20
        filled = int(bar_width * iter_pct / 100)
        bar = '█' * filled + '░' * (bar_width - filled)
        
        # Build the status line
        parts = []
        parts.append(f"[{bar}] {iter_pct:.1f}%")
        parts.append(f"Iter:{self.current_iteration}/{self.max_iterations}")
        
        # Add job progress if active
        if self.total_jobs > 0:
            job_pct = (self.completed_jobs / self.total_jobs * 100)
            parts.append(f"Jobs:{self.completed_jobs}/{self.total_jobs}({job_pct:.0f}%)")
        
        # Add timing
        parts.append(f"Elapsed:{self._format_duration(elapsed)}")
        
        if avg_iteration_time:
            remaining_iterations = self.max_iterations - self.current_iteration
            estimated_remaining = remaining_iterations * avg_iteration_time
            parts.append(f"ETA:{self._format_duration(estimated_remaining)}")
        
        parts.append(f"Stag:{self.stagnation_count}/{self.stagnation_limit}")
        
        # Print the compact line
        print("🚀 " + " | ".join(parts))
    
    def _get_avg_iteration_time(self) -> Optional[float]:
        """Get average iteration time in seconds."""
        if not self.iteration_times:
            return None
        return sum(self.iteration_times) / len(self.iteration_times)
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in a human-readable way."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def start_iteration(self, iteration_num: int, stagnation_count: int):
        """
        Mark the start of a new iteration.
        
        Args:
            iteration_num: Current iteration number (1-based)
            stagnation_count: Current stagnation count
        """
        # Start new iteration
        self.current_iteration = iteration_num
        self.stagnation_count = stagnation_count
        self.iteration_start_time = time.time()
        
        # Print progress periodically
        self._print_progress()
    
    def complete_iteration(self):
        """Mark the current iteration as complete."""
        if self.iteration_start_time:
            iteration_time = time.time() - self.iteration_start_time
            self.iteration_times.append(iteration_time)
            self.iteration_start_time = None  # Reset to avoid double-counting
        
        # Print progress on iteration completion
        self._print_progress(force=True)
    
    def start_job_batch(self, total_jobs: int):
        """
        Start tracking a batch of jobs.
        
        Args:
            total_jobs: Total number of jobs in this batch
        """
        self.total_jobs = total_jobs
        self.completed_jobs = 0
        self.job_start_time = time.time()
        
        # Print progress when starting job batch
        self._print_progress()
    
    def update_job_progress(self, completed: int):
        """
        Update job progress.
        
        Args:
            completed: Number of completed jobs
        """
        self.completed_jobs = completed
        
        # Print progress periodically
        self._print_progress()
    
    def complete_job_batch(self):
        """Mark the current job batch as complete."""
        if self.job_start_time and self.total_jobs > 0:
            elapsed = time.time() - self.job_start_time
            avg_time = elapsed / self.total_jobs
            self.job_times.append(avg_time)
            self.job_start_time = None  # Reset to avoid double-counting
        
        # Print progress when batch completes
        self._print_progress(force=True)
        
        # Reset job tracking
        self.total_jobs = 0
        self.completed_jobs = 0
    
    def update_display(self):
        """Manually trigger a display update."""
        self._print_progress()
