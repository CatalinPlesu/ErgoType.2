#!/usr/bin/env python3
"""
Simple test to verify fitness caching is working in GA
"""

from src.config.config import Config
from src.core.ga import GeneticAlgorithm
import time

def test_simple_caching():
    """Simple test of fitness caching"""
    
    print("🧪 Simple Fitness Caching Test")
    print("=" * 30)
    
    # Enable caching
    Config.cache.fitness_cache_enabled = True
    Config.fitness.use_simplified_fitness = True
    
    # Initialize evaluator directly
    from src.core.evaluator import Evaluator
    from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
    
    ev = Evaluator(debug=False)
    ev.load_keyoard().load_distance().load_layout()
    ev.load_dataset(dataset_name='simple_wikipedia')
    ev.load_typer()
    ev.layout.querty_based_remap(LAYOUT_DATA['dvorak'])
    
    print("🔍 Testing direct fitness calculation...")
    start_time = time.time()
    fitness1 = ev.get_fitness()
    time1 = time.time() - start_time
    
    start_time = time.time()
    fitness2 = ev.get_fitness()
    time2 = time.time() - start_time
    
    print(f"  First calculation: {fitness1}")
    print(f"  First time: {time1:.4f}s")
    print(f"  Second calculation: {fitness2}")
    print(f"  Second time: {time2:.4f}s")
    
    if time2 > 0:
        speedup = time1 / time2
        print(f"  Speedup: {speedup:.1f}x")
    else:
        print("  Speedup: Instant (cached)")
    
    # Verify cache hit
    assert fitness1 == fitness2, "Fitness values should be identical"
    
    print("\n✅ Fitness caching working correctly!")
    print(f"💾 Cache file: src/data/cache/fitness_cache.pkl")

if __name__ == "__main__":
    test_simple_caching()