"""
Progress tracking for genetic algorithm iterations.
Provides a pinned progress display with iteration and job metrics.
"""

import time
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from typing import Optional


class GAProgressTracker:
    """
    Progress tracker for genetic algorithm with iteration and job metrics.
    Displays a pinned progress bar at the top without hindering other console logs.
    """
    
    def __init__(self, max_iterations: int, stagnation_limit: int, console: Optional[Console] = None):
        """
        Initialize the progress tracker.
        
        Args:
            max_iterations: Maximum number of iterations
            stagnation_limit: Stagnation limit for stopping
            console: Rich console instance (creates new if None)
        """
        self.max_iterations = max_iterations
        self.stagnation_limit = stagnation_limit
        self.console = console or Console()
        
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
        
        # Progress components
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            TimeRemainingColumn(),
            console=self.console
        )
        self.iteration_task = None
        self.job_task = None
        self.live = None
    
    def start(self):
        """Start the progress tracker and display."""
        self.overall_start_time = time.time()
        self.iteration_start_time = time.time()
        
        # Create tasks
        self.iteration_task = self.progress.add_task(
            f"Iterations (0/{self.max_iterations})",
            total=self.max_iterations
        )
        self.job_task = self.progress.add_task(
            "Jobs (0/0)",
            total=1,
            visible=False
        )
        
        # Start live display
        self.live = Live(self._create_display(), console=self.console, refresh_per_second=4)
        self.live.start()
    
    def stop(self):
        """Stop the progress tracker display."""
        if self.live:
            self.live.stop()
            self.live = None
    
    def _create_display(self) -> Panel:
        """Create the display layout with progress and statistics."""
        # Create statistics table
        stats = self._create_stats_table()
        
        # Create a table that combines progress and stats
        from rich.columns import Columns
        from rich.console import Group
        
        # Group progress bars and stats together
        display_group = Group(
            self.progress,
            "",  # Empty line separator
            stats
        )
        
        return Panel(display_group, title="🚀 Genetic Algorithm Progress", border_style="cyan")
    
    def _create_stats_table(self) -> Table:
        """Create statistics table showing timing information."""
        table = Table(show_header=False, box=None, padding=(0, 1), show_edge=False)
        table.add_column("Metric", style="cyan", width=22)
        table.add_column("Value", style="yellow", width=15)
        table.add_column("Metric2", style="cyan", width=22)
        table.add_column("Value2", style="yellow", width=15)
        
        # Row 1: Iteration stats and elapsed time
        avg_iteration_time = self._get_avg_iteration_time()
        elapsed_str = ""
        if self.overall_start_time:
            elapsed = time.time() - self.overall_start_time
            elapsed_str = self._format_duration(elapsed)
        
        if avg_iteration_time:
            table.add_row(
                "⏱️  Avg Iteration", self._format_duration(avg_iteration_time),
                "🕐 Total Elapsed", elapsed_str
            )
        else:
            table.add_row(
                "⏱️  Avg Iteration", "Calculating...",
                "🕐 Total Elapsed", elapsed_str
            )
        
        # Row 2: Estimated remaining and stagnation
        remaining_str = "Calculating..."
        if avg_iteration_time:
            remaining_iterations = self.max_iterations - self.current_iteration
            estimated_remaining = remaining_iterations * avg_iteration_time
            remaining_str = self._format_duration(estimated_remaining)
        
        stag_text = f"{self.stagnation_count}/{self.stagnation_limit}"
        stag_style = "red" if self.stagnation_count >= self.stagnation_limit * 0.8 else "yellow"
        
        table.add_row(
            "⏳ Est. Remaining", remaining_str,
            "🔄 Stagnation", Text(stag_text, style=stag_style)
        )
        
        # Row 3: Job stats (if available)
        avg_job_time = self._get_avg_job_time()
        job_time_str = self._format_duration(avg_job_time) if avg_job_time else "—"
        jobs_text = f"{self.completed_jobs}/{self.total_jobs}" if self.total_jobs > 0 else "—"
        
        table.add_row(
            "⚡ Avg Job Time", job_time_str,
            "📦 Jobs Complete", jobs_text
        )
        
        return table
    
    def _get_avg_iteration_time(self) -> Optional[float]:
        """Get average iteration time in seconds."""
        if not self.iteration_times:
            return None
        return sum(self.iteration_times) / len(self.iteration_times)
    
    def _get_avg_job_time(self) -> Optional[float]:
        """Get average job time in seconds."""
        if not self.job_times:
            return None
        return sum(self.job_times) / len(self.job_times)
    
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
        # Complete previous iteration if exists
        if self.iteration_start_time and self.current_iteration > 0:
            iteration_time = time.time() - self.iteration_start_time
            self.iteration_times.append(iteration_time)
        
        # Start new iteration
        self.current_iteration = iteration_num
        self.stagnation_count = stagnation_count
        self.iteration_start_time = time.time()
        
        # Update progress
        if self.iteration_task is not None:
            self.progress.update(
                self.iteration_task,
                completed=iteration_num - 1,
                description=f"Iterations ({iteration_num-1}/{self.max_iterations})"
            )
            if self.live:
                self.live.update(self._create_display())
    
    def complete_iteration(self):
        """Mark the current iteration as complete."""
        if self.iteration_start_time:
            iteration_time = time.time() - self.iteration_start_time
            self.iteration_times.append(iteration_time)
        
        # Update progress
        if self.iteration_task is not None:
            self.progress.update(
                self.iteration_task,
                completed=self.current_iteration,
                description=f"Iterations ({self.current_iteration}/{self.max_iterations})"
            )
            if self.live:
                self.live.update(self._create_display())
    
    def start_job_batch(self, total_jobs: int):
        """
        Start tracking a batch of jobs.
        
        Args:
            total_jobs: Total number of jobs in this batch
        """
        self.total_jobs = total_jobs
        self.completed_jobs = 0
        self.job_start_time = time.time()
        self.job_times = []
        
        # Update job task
        if self.job_task is not None:
            self.progress.update(
                self.job_task,
                total=total_jobs,
                completed=0,
                description=f"Jobs (0/{total_jobs})",
                visible=True
            )
            if self.live:
                self.live.update(self._create_display())
    
    def update_job_progress(self, completed: int):
        """
        Update job progress.
        
        Args:
            completed: Number of completed jobs
        """
        self.completed_jobs = completed
        
        # Calculate time per job
        if self.job_start_time and completed > 0:
            elapsed = time.time() - self.job_start_time
            avg_time = elapsed / completed
            if completed == self.total_jobs:
                # Store average for this batch
                self.job_times.append(avg_time)
        
        # Update job task
        if self.job_task is not None:
            self.progress.update(
                self.job_task,
                completed=completed,
                description=f"Jobs ({completed}/{self.total_jobs})"
            )
            if self.live:
                self.live.update(self._create_display())
    
    def complete_job_batch(self):
        """Mark the current job batch as complete."""
        if self.job_start_time and self.total_jobs > 0:
            elapsed = time.time() - self.job_start_time
            avg_time = elapsed / self.total_jobs
            self.job_times.append(avg_time)
        
        # Hide job task
        if self.job_task is not None:
            self.progress.update(
                self.job_task,
                visible=False
            )
            if self.live:
                self.live.update(self._create_display())
    
    def update_display(self):
        """Manually trigger a display update."""
        if self.live:
            self.live.update(self._create_display())
