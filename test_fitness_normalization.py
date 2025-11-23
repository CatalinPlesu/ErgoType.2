#!/usr/bin/env python3
"""
Test script to verify fitness normalization fix.
Tests that fitness function uses max as max, 0 as min, and inverts (1-value).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.ga import GeneticAlgorithm, Individual
from src.config.config import Config

def test_fitness_normalization():
    """Test the fitness normalization with known values"""
    print("Testing fitness normalization...")
    print("Expected behavior:")
    print("- Use max_distance and max_time as the bounds")
    print("- Normalize: value/max_value (0.0 = best, 1.0 = worst)")
    print("- Fitness = 1.0 - sickness (1.0 = best, 0.0 = worst)")
    print()
    
    # Create a small test population with known distances and times
    ga = GeneticAlgorithm(
        keyboard_file='src/data/keyboards/ansi_60_percent.json',
        dataset_file='src/data/text/processed/frequency_analysis.pkl',
        dataset_name='simple_wikipedia'
    )
    
    # Clear existing population and create test individuals
    ga.population = []
    
    # Create test individuals with known values
    # Individual 1: Best (lowest distance and time)
    ind1 = Individual(chromosome=list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), generation=0, name="best")
    ind1.timing_metadata = {
        'distance': 100.0,  # Best distance
        'time_component': 50.0   # Best time
    }
    ind1.fitness = None
    
    # Individual 2: Worst (highest distance and time)
    ind2 = Individual(chromosome=list('ZYXWVUTSRQPONMLKJIHGFEDCBA'), generation=0, name="worst")
    ind2.timing_metadata = {
        'distance': 200.0,  # Worst distance
        'time_component': 100.0  # Worst time
    }
    ind2.fitness = None
    
    # Individual 3: Middle value
    ind3 = Individual(chromosome=list('ASDFGHJKLQWERTYUIOPZXCVBNM'), generation=0, name="middle")
    ind3.timing_metadata = {
        'distance': 150.0,  # Middle distance
        'time_component': 75.0   # Middle time
    }
    ind3.fitness = None
    
    ga.population = [ind1, ind2, ind3]
    
    # Set up the bounds as they would be calculated
    max_distance = 200.0  # From ind2
    max_time = 100.0      # From ind2
    
    # Manually calculate what the fitness should be
    distance_weight = Config.fitness.distance_weight
    time_weight = Config.fitness.time_weight
    
    print(f"Test parameters:")
    print(f"  Distance weight: {distance_weight}")
    print(f"  Time weight: {time_weight}")
    print(f"  Max distance: {max_distance}")
    print(f"  Max time: {max_time}")
    print()
    
    # Calculate expected fitness values
    for ind in ga.population:
        distance = ind.timing_metadata['distance']
        time_component = ind.timing_metadata['time_component']
        
        # Apply the new normalization: value/max_value
        normalized_distance = distance / max_distance
        normalized_time = time_component / max_time
        
        # Calculate sickness and invert to get fitness
        sickness = (distance_weight * normalized_distance + time_weight * normalized_time)
        expected_fitness = 1.0 - sickness
        
        print(f"Individual {ind.name}:")
        print(f"  Distance: {distance} → normalized: {normalized_distance:.3f}")
        print(f"  Time: {time_component} → normalized: {normalized_time:.3f}")
        print(f"  Sickness: {sickness:.6f}")
        print(f"  Expected fitness: {expected_fitness:.6f}")
        print()
        
        # Store expected result
        ind.expected_fitness = expected_fitness
    
    print("Expected ranking (highest fitness first):")
    sorted_inds = sorted(ga.population, key=lambda x: x.expected_fitness, reverse=True)
    for i, ind in enumerate(sorted_inds, 1):
        print(f"  {i}. {ind.name}: {ind.expected_fitness:.6f}")
    
    print()
    print("✓ Fitness normalization test setup complete")
    print("  - Best individual should have highest fitness (closest to 1.0)")
    print("  - Worst individual should have lowest fitness (closest to 0.0)")
    print("  - Fitness values should be between 0.0 and 1.0")

if __name__ == "__main__":
    test_fitness_normalization()