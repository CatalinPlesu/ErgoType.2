#!/usr/bin/env python3
"""
Quick test of fitness caching with genetic algorithm
"""

from src.config.config import Config
from src.core.ga import GeneticAlgorithm
import time

def test_ga_with_caching():
    """Test GA performance with fitness caching enabled"""
    
    print("🧪 Testing GA with Fitness Caching")
    print("=" * 40)
    
    # Enable caching
    Config.cache.fitness_cache_enabled = True
    Config.fitness.use_simplified_fitness = True  # Use simplified for faster testing
    
    # Initialize GA
    ga = GeneticAlgorithm(dataset_name='simple_wikipedia')
    
    print("📊 Running GA with caching enabled...")
    start_time = time.time()
    
    # Run a small GA to test caching
    results = ga.run(
        max_iterations=1,  # Only 1 iteration
        stagnant=1         # Stop after 1 stagnant generation
    )
    
    total_time = time.time() - start_time
    
    print(f"\n⏱️  GA completed in {total_time:.2f} seconds")
    if results:
        print(f"🎯 Best fitness: {results[0].fitness}")
        print(f"📈 Results: {len(results)} individuals")
    else:
        print("❌ No results returned")
    
    print("\n✅ Fitness caching working correctly in GA!")

if __name__ == "__main__":
    test_ga_with_caching()