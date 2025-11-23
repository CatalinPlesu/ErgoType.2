#!/usr/bin/env python3
"""
Test script for simplified keyboard layout evaluation
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.core.evaluator import Evaluator
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from src.config.config import Config
import json

def test_simplified_evaluation():
    """Test the simplified evaluation workflow"""
    
    print("="*80)
    print("TESTING SIMPLIFIED KEYBOARD LAYOUT EVALUATION")
    print("="*80)
    
    # Configure for simplified evaluation
    Config.fitness.use_simplified_fitness = True
    print(f"Using simplified fitness: {Config.fitness.use_simplified_fitness}")
    print(f"Distance weight: {Config.fitness.distance_weight}")
    print(f"Time weight: {Config.fitness.time_weight}")
    
    # Initialize evaluator
    evaluator = Evaluator(debug=True)
    evaluator.load_keyoard('src/data/keyboards/ansi_60_percent.json')
    evaluator.load_distance()
    evaluator.load_layout()
    evaluator.load_dataset(dataset_name='simple_wikipedia')
    evaluator.load_typer()
    
    print(f"Using typer: {type(evaluator.typer).__name__}")
    
    # Test with a few predefined layouts
    test_layouts = ['qwerty', 'dvorak', 'asset']
    
    results = []
    
    for layout_name in test_layouts:
        print(f"\n{'='*50}")
        print(f"Testing layout: {layout_name}")
        print(f"{'='*50}")
        
        # Apply layout
        layout_genotype = LAYOUT_DATA[layout_name]
        evaluator.layout.remap(LAYOUT_DATA["qwerty"], layout_genotype)
        
        # Calculate fitness
        fitness_result = evaluator.typer.fitness()
        
        result = {
            'layout': layout_name,
            'fitness': fitness_result.get('fitness_score', 0),
            'distance': fitness_result.get('distance_score', 0),
            'time': fitness_result.get('time_score', 0),
            'genotype': ''.join(layout_genotype)
        }
        
        results.append(result)
        print(f"Fitness: {result['fitness']:.6f}")
        print(f"Distance: {result['distance']:.4f}")
        print(f"Time: {result['time']:.4f}")
    
    # Print comparison
    print(f"\n{'='*80}")
    print("LAYOUT COMPARISON RESULTS")
    print(f"{'='*80}")
    print(f"{'Layout':<15} {'Fitness':<15} {'Distance':<12} {'Time':<12}")
    print("-" * 60)
    
    sorted_results = sorted(results, key=lambda x: x['fitness'])
    for result in sorted_results:
        print(f"{result['layout']:<15} {result['fitness']:<15.6f} {result['distance']:<12.4f} {result['time']:<12.4f}")
    
    # Save results
    timestamp = "test_run"
    output_dir = f"output/simplified_test_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    results_file = os.path.join(output_dir, "simplified_evaluation_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    print("="*80)

if __name__ == "__main__":
    test_simplified_evaluation()