"""
GA Run Analysis Module

Provides tools for analyzing genetic algorithm run results:
- Single run inspection: Browse generations and chromosomes
- Multi-run comparison: Compare results across different GA runs
"""

from .ga_run_loader import GARunLoader
from .single_run_inspector import SingleRunInspector
from .multi_run_comparator import MultiRunComparator

__all__ = ['GARunLoader', 'SingleRunInspector', 'MultiRunComparator']
