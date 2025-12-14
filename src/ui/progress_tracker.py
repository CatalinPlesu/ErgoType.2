"""
Progress tracking for genetic algorithm iterations.

This module provides a compact single-line progress tracker that displays:
- Graphical progress bar with completion percentage
- Iteration count (current/total)
- Job batch progress when active
- Elapsed time and estimated time remaining
- Stagnation count monitoring

The progress is printed periodically (every 10 seconds) or on completion events
to avoid conflicts with other console output. Uses Rich library for colorful,
visually appealing output.

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
from rich.console import Console
from rich.text import Text


class GAProgressTracker:
    """
    Progress tracker for genetic algorithm with iteration and job metrics.
    
    This tracker prints a compact single-line progress summary periodically
    to avoid interfering with other console output. Uses Rich library for
    colorful, visually appealing formatting. The line includes:
    
    - Graphical progress bar (█ = completed, ░ = remaining)
    - Percentage completion
    - Iteration count (current/total)
    - Job batch progress when active (current/total with percentage)
    - Elapsed time
    - Estimated time remaining (when available)
    - Stagnation count (current/limit)
    
    Progress is printed every 10 seconds or when a job batch/iteration completes.
    """
    
    def __init__(self, max_iterations: int, stagnation_limit: int, console: Optional[Console] = None, population_phases: Optional[list] = None):
        """
        Initialize the progress tracker.
        
        Args:
            max_iterations: Maximum number of iterations
            stagnation_limit: Stagnation limit for stopping
            console: Rich Console instance (creates new if None)
            population_phases: Optional list of (iterations, max_population) tuples for phases mode
        """
        self.max_iterations = max_iterations
        self.stagnation_limit = stagnation_limit
        self.console = console or Console()
        self.population_phases = population_phases
        
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
        
        # Stagnation color thresholds
        self.STAGNATION_WARNING_THRESHOLD = 0.5  # Yellow warning at 50%
        self.STAGNATION_CRITICAL_THRESHOLD = 0.7  # Red critical at 70%
    
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
        Uses Rich library for colorful, visually appealing output.
        
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
        
        # Build compact single-line progress with colors
        iter_pct = (self.current_iteration / self.max_iterations * 100) if self.max_iterations > 0 else 0
        
        # Create colorful text-based progress bar
        bar_width = 20
        filled = int(bar_width * iter_pct / 100)
        
        # Build the styled progress line using Rich
        text = Text()
        text.append("🚀 ", style="bold cyan")
        text.append("[", style="white")
        text.append("█" * filled, style="bold green")
        text.append("░" * (bar_width - filled), style="dim white")
        text.append("]", style="white")
        text.append(f" {iter_pct:.1f}%", style="bold yellow")
        
        # Add iteration info
        text.append(" │ ", style="dim white")
        text.append("Iter:", style="cyan")
        text.append(f"{self.current_iteration}/{self.max_iterations}", style="bold white")
        
        # Add job progress if active
        if self.total_jobs > 0:
            job_pct = (self.completed_jobs / self.total_jobs * 100)
            text.append(" │ ", style="dim white")
            text.append("Jobs:", style="cyan")
            text.append(f"{self.completed_jobs}/{self.total_jobs}", style="bold white")
            text.append(f"({job_pct:.0f}%)", style="yellow")
        
        # Add timing
        text.append(" │ ", style="dim white")
        text.append("Elapsed:", style="cyan")
        text.append(self._format_duration(elapsed), style="bold white")
        
        # Calculate ETA based on population phases if available
        eta = self._calculate_eta()
        if eta is not None:
            text.append(" │ ", style="dim white")
            text.append("ETA:", style="cyan")
            text.append(self._format_duration(eta), style="bold green")
        
        # Add stagnation with color coding
        text.append(" │ ", style="dim white")
        text.append("Stag:", style="cyan")
        stag_style = self._get_stagnation_style()
        text.append(f"{self.stagnation_count}/{self.stagnation_limit}", style=stag_style)
        
        # Print the styled line
        self.console.print(text)
    
    def _calculate_eta(self) -> Optional[float]:
        """
        Calculate estimated time to completion.
        
        If population_phases is available, estimates based on weighted average
        of work per individual across remaining phases. Otherwise, uses simple
        average iteration time.
        
        Returns:
            Estimated time in seconds, or None if not enough data
        """
        if not self.iteration_times:
            return None
        
        avg_iteration_time = sum(self.iteration_times) / len(self.iteration_times)
        
        if not self.population_phases:
            # Standard mode: simple average iteration time
            remaining_iterations = self.max_iterations - self.current_iteration
            return remaining_iterations * avg_iteration_time
        
        # Population phases mode: estimate based on work per individual
        # Calculate average time per individual from completed iterations
        total_individuals_evaluated = 0
        total_time = sum(self.iteration_times)
        
        # Estimate individuals per iteration (assumes population + children)
        # We'll use job counts from recent iterations if available
        if self.job_times:
            # Use actual job counts from recent batches
            avg_jobs_per_iteration = len(self.job_times) / len(self.iteration_times) if self.iteration_times else 0
            time_per_job = sum(self.job_times) / len(self.job_times) if self.job_times else 0
        else:
            # Fallback: estimate based on average iteration time
            time_per_job = 0
        
        # Calculate remaining work based on remaining phases
        remaining_work = 0
        current_iter = self.current_iteration
        
        for phase_iterations, phase_population in self.population_phases:
            if current_iter >= phase_iterations:
                # This phase is complete
                current_iter -= phase_iterations
            elif current_iter > 0:
                # We're in the middle of this phase
                remaining_in_phase = phase_iterations - current_iter
                # Estimate: population + children (roughly 2x population work)
                remaining_work += remaining_in_phase * phase_population * 2 * (time_per_job if time_per_job else 0.01)
                current_iter = 0
            else:
                # This phase hasn't started yet
                remaining_work += phase_iterations * phase_population * 2 * (time_per_job if time_per_job else 0.01)
        
        # If we don't have job timing data yet, fall back to simple average
        if not time_per_job and avg_iteration_time:
            remaining_iterations = self.max_iterations - self.current_iteration
            return remaining_iterations * avg_iteration_time
        
        return remaining_work if remaining_work > 0 else None
    
    def _get_avg_iteration_time(self) -> Optional[float]:
        """Get average iteration time in seconds."""
        if not self.iteration_times:
            return None
        return sum(self.iteration_times) / len(self.iteration_times)
    
    def _get_stagnation_style(self) -> str:
        """
        Get the Rich style for stagnation display based on severity.
        
        Returns:
            Rich style string: 'bold white' (safe), 'bold yellow' (warning), or 'bold red' (critical)
        """
        if self.stagnation_limit == 0:
            return "bold white"
        
        stag_ratio = self.stagnation_count / self.stagnation_limit
        
        if stag_ratio > self.STAGNATION_CRITICAL_THRESHOLD:
            return "bold red"
        elif stag_ratio > self.STAGNATION_WARNING_THRESHOLD:
            return "bold yellow"
        else:
            return "bold white"
    
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
    
    def get_total_elapsed_time(self) -> float:
        """
        Get the total elapsed time since the tracker started.
        
        Returns:
            Total elapsed time in seconds, or 0 if not started
        """
        if self.overall_start_time is None:
            return 0.0
        return time.time() - self.overall_start_time
    
    def get_average_job_time(self) -> Optional[float]:
        """
        Get the average time per job across all completed job batches.
        
        This method returns the mean of per-job times calculated for each batch.
        Each batch's per-job time is computed as (batch_elapsed_time / jobs_in_batch),
        and this method returns the average of those values across all batches.
        
        Returns:
            Average job time in seconds, or None if no jobs completed
        """
        if not self.job_times:
            return None
        return sum(self.job_times) / len(self.job_times)
