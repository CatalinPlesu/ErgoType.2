"""
GA Run Loader

Loads and parses GA run metadata and individual data from saved results.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class GARunLoader:
    """Loads GA run data from disk"""
    
    def __init__(self, run_dir: Path):
        """
        Initialize loader for a specific GA run directory.
        
        Args:
            run_dir: Path to the ga_run_{timestamp} directory
        """
        self.run_dir = Path(run_dir)
        self.metadata: Optional[Dict[str, Any]] = None
        self.all_individuals: Optional[Dict[str, Any]] = None
        
        if not self.run_dir.exists():
            raise FileNotFoundError(f"Run directory not found: {self.run_dir}")
    
    def load_metadata(self) -> Dict[str, Any]:
        """Load GA run metadata"""
        metadata_path = self.run_dir / "ga_run_metadata.json"
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        return self.metadata
    
    def load_all_individuals(self) -> Dict[str, Any]:
        """Load all individuals data"""
        individuals_path = self.run_dir / "ga_all_individuals.json"
        
        if not individuals_path.exists():
            raise FileNotFoundError(f"Individuals file not found: {individuals_path}")
        
        with open(individuals_path, 'r', encoding='utf-8') as f:
            self.all_individuals = json.load(f)
        
        return self.all_individuals
    
    def get_individuals_by_generation(self) -> Dict[int, List[Dict[str, Any]]]:
        """
        Organize individuals by generation.
        
        Returns:
            Dictionary mapping generation number to list of individuals
        """
        if self.all_individuals is None:
            self.load_all_individuals()
        
        by_generation: Dict[int, List[Dict[str, Any]]] = {}
        
        for individual in self.all_individuals.get('all_individuals', []):
            gen = individual.get('generation', 0)
            if gen not in by_generation:
                by_generation[gen] = []
            by_generation[gen].append(individual)
        
        return by_generation
    
    def get_individual_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific individual by name.
        
        Args:
            name: Individual name (e.g., "gen_0-1")
        
        Returns:
            Individual data or None if not found
        """
        if self.all_individuals is None:
            self.load_all_individuals()
        
        for individual in self.all_individuals.get('all_individuals', []):
            if individual.get('name') == name:
                return individual
        
        return None
    
    def get_run_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the GA run.
        
        Returns:
            Dictionary with run summary information
        """
        if self.metadata is None:
            self.load_metadata()
        
        if self.all_individuals is None:
            self.load_all_individuals()
        
        by_gen = self.get_individuals_by_generation()
        
        summary = {
            'run_dir': str(self.run_dir),
            'timestamp': self.metadata.get('timestamp'),
            'keyboard_file': self.metadata.get('keyboard_file'),
            'text_file': self.metadata.get('text_file'),
            'population_size': self.metadata.get('population_size'),
            'max_iterations': self.metadata.get('max_iterations'),
            'stagnant_limit': self.metadata.get('stagnant_limit'),
            'best_fitness': self.metadata.get('best_fitness'),
            'best_layout_name': self.metadata.get('best_layout_name'),
            'total_individuals': self.metadata.get('total_unique_individuals'),
            'total_generations': len(by_gen),
            'fitts_a': self.metadata.get('fitts_a'),
            'fitts_b': self.metadata.get('fitts_b'),
            'finger_coefficients': self.metadata.get('finger_coefficients')
        }
        
        # Add mode-specific information
        mode = self.metadata.get('mode', 'standard')
        summary['mode'] = mode
        
        if mode == 'population_phases':
            summary['population_phases'] = self.metadata.get('population_phases')
            summary['total_max_iterations'] = self.metadata.get('total_max_iterations')
            summary['average_population'] = self.metadata.get('average_population')
        
        # Add actual iterations if available
        if 'actual_iterations' in self.metadata:
            summary['actual_iterations'] = self.metadata.get('actual_iterations')
        
        return summary
    
    @staticmethod
    def find_ga_runs(base_dir: Optional[Path] = None) -> List[Path]:
        """
        Find all GA run directories.
        
        Args:
            base_dir: Base directory to search (default: output/ga_results)
        
        Returns:
            List of paths to GA run directories
        """
        if base_dir is None:
            base_dir = Path("output/ga_results")
        
        if not base_dir.exists():
            return []
        
        # Find all directories matching ga_run_* pattern
        run_dirs = sorted([d for d in base_dir.iterdir() 
                          if d.is_dir() and d.name.startswith("ga_run_")],
                         reverse=True)  # Most recent first
        
        return run_dirs
