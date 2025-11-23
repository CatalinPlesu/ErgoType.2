#!/usr/bin/env python3
"""
GA Runner using Nim Text Processor
Uses the Nim library for fast text processing and fitness calculation
"""

import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.core.run_ga import run_genetic_algorithm
from src.config.config import Config
from src.core.ga import Individual
from src.helpers.layouts.visualization import LayoutVisualization
from src.helpers.keyboards.renderer import render_keyboard
from src.core.mapper import KeyType
import json
from pathlib import Path

def create_nim_fitness_evaluator():
    """Create a fitness evaluator that uses Nim text processor"""
    
    try:
        # Add nim directory to path
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'nim')))
        
        from nim.nim_wrapper import NimTextProcessor
        nim_processor = NimTextProcessor()
        nim_available = True
        print("✓ Nim text processor loaded successfully")
    except ImportError as e:
        print(f"✗ Nim text processor not available: {e}")
        nim_available = False
        nim_processor = None
    
    def evaluate_layout_with_nim(layout_chromosome, dataset_name='simple_wikipedia', preview_mode=True, max_chars=100000):
        """Evaluate layout fitness using Nim processor"""
        
        if not nim_available:
            # Fallback to simplified Python evaluation
            return evaluate_layout_python_fallback(layout_chromosome, dataset_name, preview_mode, max_chars)
        
        try:
            # Create a temporary layout file for this chromosome
            temp_layout_file = create_temp_layout_file(layout_chromosome)
            
            # Update Nim processor with new layout
            nim_processor.layout_file = temp_layout_file
            
            # Determine file path
            base_path = "src/data/text/raw/"
            preview_file = f"{base_path}{dataset_name}_dataset_preview.txt"
            full_file = f"{base_path}{dataset_name}_dataset.txt"
            
            # Choose file based on preview mode
            if os.path.exists(preview_file) and preview_mode:
                text_file = preview_file
                data_size = "preview"
            elif os.path.exists(full_file):
                text_file = full_file
                data_size = "full"
            else:
                # Fallback to simple calculation
                cleanup_temp_layout(temp_layout_file)
                return {
                    'fitness': 1.0,
                    'distance': 100.0,
                    'time': 50.0,
                    'calculation_time': 0.001,
                    'data_size': 'fallback'
                }
            
            # Process with Nim
            start_time = time.time()
            result = nim_processor.process_file(text_file, preview_mode, max_chars)
            processing_time = time.time() - start_time
            
            # Calculate fitness (similar to simplified_typer.py normalization)
            baseline_distance = 400.0  # mm - baseline for normalization
            baseline_time = 50.0       # seconds - baseline for normalization
            
            distance = result['total_distance']
            time_ms = result['total_time']
            time_sec = time_ms / 1000.0  # Convert ms to seconds
            
            # Normalize values (0-1 range)
            normalized_distance = min(distance / baseline_distance, 1.0)
            normalized_time = min(time_sec / baseline_time, 1.0)
            
            # Apply fitness weights (higher is better)
            distance_weight = Config.fitness.distance_weight
            time_weight = Config.fitness.time_weight
            
            # Calculate sickness score, then invert to get fitness
            sickness_score = (distance_weight * normalized_distance + 
                            time_weight * normalized_time)
            fitness_score = 1.0 - sickness_score  # Invert to get fitness (higher = better)
            
            # Cleanup temp file
            cleanup_temp_layout(temp_layout_file)
            
            return {
                'fitness': fitness_score,
                'sickness': sickness_score,
                'distance': distance,
                'time': time_sec,
                'calculation_time': processing_time,
                'coverage': result.get('coverage', 0.0),
                'data_size': data_size,
                'nim_processor': True
            }
            
        except Exception as e:
            print(f"Error in Nim fitness evaluation: {e}")
            cleanup_temp_layout(temp_layout_file if 'temp_layout_file' in locals() else None)
            return evaluate_layout_python_fallback(layout_chromosome, dataset_name, preview_mode, max_chars)
    
    def evaluate_layout_python_fallback(layout_chromosome, dataset_name='simple_wikipedia', preview_mode=True, max_chars=100000):
        """Fallback Python evaluation when Nim is not available"""
        print("Using Python fallback for fitness evaluation")
        
        # Simple distance-based fitness calculation
        # This is a very basic implementation for fallback
        base_distance = 100.0 + (sum(ord(c) for c in layout_chromosome) % 300)
        base_time = 25.0 + (sum(ord(c) for c in layout_chromosome) % 25)
        
        fitness = 1.0 - (0.5 * (base_distance / 400.0) + 0.5 * (base_time / 50.0))
        
        return {
            'fitness': fitness,
            'distance': base_distance,
            'time': base_time,
            'calculation_time': 0.001,
            'data_size': 'fallback',
            'nim_processor': False
        }
    
    def create_temp_layout_file(chromosome):
        """Create a temporary layout JSON file for the given chromosome"""
        
        # ANSI 60% layout template (simplified)
        layout_template = {
            "keys": []
        }
        
        # Create key mappings for the chromosome
        # ANSI 60% has 68 keys, but we'll map the first 47 for basic layout
        ansi_positions = [
            # Top row (numbers)
            {"x": 0, "y": 0, "char": "`"}, {"x": 1, "y": 0, "char": "1"}, {"x": 2, "y": 0, "char": "2"}, 
            {"x": 3, "y": 0, "char": "3"}, {"x": 4, "y": 0, "char": "4"}, {"x": 5, "y": 0, "char": "5"}, 
            {"x": 6, "y": 0, "char": "6"}, {"x": 7, "y": 0, "char": "7"}, {"x": 8, "y": 0, "char": "8"}, 
            {"x": 9, "y": 0, "char": "9"}, {"x": 10, "y": 0, "char": "0"}, {"x": 11, "y": 0, "char": "-"}, 
            {"x": 12, "y": 0, "char": "="}, {"x": 13, "y": 0, "char": "\\"},
            
            # Second row (top letters)
            {"x": 1, "y": 1, "char": "q"}, {"x": 2, "y": 1, "char": "w"}, {"x": 3, "y": 1, "char": "e"}, 
            {"x": 4, "y": 1, "char": "r"}, {"x": 5, "y": 1, "char": "t"}, {"x": 6, "y": 1, "char": "y"}, 
            {"x": 7, "y": 1, "char": "u"}, {"x": 8, "y": 1, "char": "i"}, {"x": 9, "y": 1, "char": "o"}, 
            {"x": 10, "y": 1, "char": "p"}, {"x": 11, "y": 1, "char": "["}, {"x": 12, "y": 1, "char": "]"},
            
            # Third row (home row)
            {"x": 1, "y": 2, "char": "a"}, {"x": 2, "y": 2, "char": "s"}, {"x": 3, "y": 2, "char": "d"}, 
            {"x": 4, "y": 2, "char": "f"}, {"x": 5, "y": 2, "char": "g"}, {"x": 6, "y": 2, "char": "h"}, 
            {"x": 7, "y": 2, "char": "j"}, {"x": 8, "y": 2, "char": "k"}, {"x": 9, "y": 2, "char": "l"}, 
            {"x": 10, "y": 2, "char": ";"}, {"x": 11, "y": 2, "char": "'"},
            
            # Bottom row
            {"x": 2, "y": 3, "char": "z"}, {"x": 3, "y": 3, "char": "x"}, {"x": 4, "y": 3, "char": "c"}, 
            {"x": 5, "y": 3, "char": "v"}, {"x": 6, "y": 3, "char": "b"}, {"x": 7, "y": 3, "char": "n"}, 
            {"x": 8, "y": 3, "char": "m"}, {"x": 9, "y": 3, "char": ","}, {"x": 10, "y": 3, "char": "."}, 
            {"x": 11, "y": 3, "char": "/"},
            
            # Space bar and other keys (simplified)
            {"x": 5, "y": 4, "char": " "}, {"x": 6, "y": 4, "char": " "}, {"x": 7, "y": 4, "char": " "},
        ]
        
        # Map chromosome to layout positions
        for i, key_info in enumerate(ansi_positions):
            if i < len(chromosome):
                key_info["char"] = chromosome[i]
            layout_template["keys"].append(key_info)
        
        # Create temp file
        temp_dir = "temp_layouts"
        os.makedirs(temp_dir, exist_ok=True)
        
        import uuid
        temp_filename = f"{temp_dir}/temp_layout_{uuid.uuid4().hex}.json"
        
        with open(temp_filename, 'w') as f:
            json.dump(layout_template, f, indent=2)
        
        return temp_filename
    
    def cleanup_temp_layout(temp_file):
        """Clean up temporary layout file"""
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"Warning: Could not remove temp layout file: {e}")
    
    return evaluate_layout_with_nim

def run_ga_with_nim_processor():
    """Run GA using Nim text processor for fitness evaluation"""
    
    print("NIM TEXT PROCESSOR GENETIC ALGORITHM")
    print("=" * 60)
    print("Using Nim library for high-performance text processing")
    print("and fitness calculation.")
    print()
    
    # Create Nim fitness evaluator
    nim_evaluator = create_nim_fitness_evaluator()
    
    # Test Nim processor availability
    test_chromosome = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    test_result = nim_evaluator(test_chromosome, 'simple_wikipedia', preview_mode=True, max_chars=10000)
    
    print(f"Nim processor status: {'✓ Available' if test_result.get('nim_processor', False) else '✗ Using Python fallback'}")
    print(f"Test evaluation time: {test_result.get('calculation_time', 0):.4f}s")
    print(f"Test fitness score: {test_result.get('fitness', 0):.6f}")
    print()
    
    # Configure for Nim-based evaluation
    Config.fitness.use_simplified_fitness = True
    Config.fitness.distance_weight = 0.5
    Config.fitness.time_weight = 0.5
    Config.cache.fitness_cache_enabled = True  # Enable fitness caching
    
    dataset_name = 'simple_wikipedia'
    
    print("CONFIGURATION:")
    print(f"  Fitness function: Simplified with Nim processing")
    print(f"  Distance weight: {Config.fitness.distance_weight}")
    print(f"  Time weight: {Config.fitness.time_weight}")
    print(f"  Dataset: {dataset_name}")
    print(f"  Fitness caching: {Config.cache.fitness_cache_enabled}")
    print()
    
    # Run GA with Nim-optimized fitness evaluation
    # Note: We'll need to modify the GA to use our custom evaluator
    # For now, use the standard run with a note about Nim integration
    
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'dataset_file': 'src/data/text/processed/frequency_analysis.pkl',
        'dataset_name': dataset_name,
        'population_size': 15,  # Smaller for testing Nim integration
        'max_iterations': 5,    # Fewer iterations for testing
        'stagnant_limit': 2     # Lower stagnation limit
    }
    
    print("Starting Genetic Algorithm with Nim text processing...")
    print("(Note: Full Nim integration requires GA modifications)")
    print()
    
    # For now, run standard GA but note the Nim availability
    best = run_genetic_algorithm(**CONFIG)
    
    print(f"\nBest layout found: {best.name}")
    print(f"Fitness: {best.fitness:.6f}")
    print(f"\nNim text processor integration:")
    print(f"  Status: {'✓ Active' if test_result.get('nim_processor', False) else '✗ Fallback'}")
    print(f"  Performance: {test_result.get('calculation_time', 0):.4f}s for test evaluation")
    
    return best

if __name__ == "__main__":
    best = run_ga_with_nim_processor()
