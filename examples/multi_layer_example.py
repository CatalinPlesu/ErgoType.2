"""
Example: Multi-Layer Keyboard Layout Optimization

This example demonstrates how to use the genetic algorithm to optimize
keyboard layouts with multiple layers.
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.core.run_ga import run_genetic_algorithm

def example_single_layer():
    """Example 1: Traditional single-layer optimization (English)"""
    print("="*80)
    print("EXAMPLE 1: Single-Layer Optimization (English)")
    print("="*80)
    print("This optimizes a traditional keyboard layout with just one layer.")
    print("Suitable for languages that fit within the standard key count.\n")
    
    config = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'text_file': 'src/data/text/raw/simple_wikipedia_dataset.txt',
        'population_size': 20,
        'max_iterations': 10,
        'stagnant_limit': 5,
        'max_concurrent_processes': 2,
        'use_rabbitmq': False,
        'save_heuristics': False,
        'num_layers': 1,      # Single layer
        'max_layers': 1       # No layer growth
    }
    
    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    best = run_genetic_algorithm(**config)
    
    print("\n✅ Single-layer optimization complete!")
    print(f"   Best individual: {best.name}")
    print(f"   Fitness: {best.fitness:.6f}")
    print(f"   Layers: {len(best.chromosome)}")
    return best

def example_fixed_multi_layer():
    """Example 2: Fixed two-layer optimization (Romanian)"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Fixed Two-Layer Optimization (Romanian)")
    print("="*80)
    print("This optimizes a keyboard with exactly 2 layers:")
    print("  - Layer 0: Base characters (a-z, punctuation)")
    print("  - Layer 1: Diacritics (ă, â, î, ș, ț)")
    print("\nLayers are fixed - no addition or removal during evolution.\n")
    
    config = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'text_file': 'src/data/text/raw/simple_wikipedia_dataset.txt',  # Use Romanian dataset if available
        'population_size': 20,
        'max_iterations': 10,
        'stagnant_limit': 5,
        'max_concurrent_processes': 2,
        'use_rabbitmq': False,
        'save_heuristics': False,
        'num_layers': 2,      # Start with 2 layers
        'max_layers': 2       # Keep 2 layers fixed
    }
    
    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    best = run_genetic_algorithm(**config)
    
    print("\n✅ Two-layer optimization complete!")
    print(f"   Best individual: {best.name}")
    print(f"   Fitness: {best.fitness:.6f}")
    print(f"   Layers: {len(best.chromosome)}")
    for i, layer in enumerate(best.chromosome):
        print(f"   Layer {i}: {''.join(layer[:20])}... ({len(layer)} keys)")
    return best

def example_dynamic_layers():
    """Example 3: Dynamic layer evolution"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Dynamic Layer Evolution")
    print("="*80)
    print("This lets the GA discover the optimal number of layers:")
    print("  - Starts with 1 layer")
    print("  - Can grow up to 4 layers")
    print("  - Layer addition/removal based on fitness")
    print("\nThe GA will automatically determine if multi-layer is beneficial.\n")
    
    config = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'text_file': 'src/data/text/raw/simple_wikipedia_dataset.txt',
        'population_size': 20,
        'max_iterations': 15,
        'stagnant_limit': 7,
        'max_concurrent_processes': 2,
        'use_rabbitmq': False,
        'save_heuristics': False,
        'num_layers': 1,      # Start with 1 layer
        'max_layers': 4       # Allow up to 4 layers
    }
    
    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    best = run_genetic_algorithm(**config)
    
    print("\n✅ Dynamic layer optimization complete!")
    print(f"   Best individual: {best.name}")
    print(f"   Fitness: {best.fitness:.6f}")
    print(f"   Layers discovered: {len(best.chromosome)}")
    
    if len(best.chromosome) > 1:
        print("   🎉 GA discovered that multiple layers are beneficial!")
    else:
        print("   ℹ️  GA determined single layer is optimal for this dataset")
    
    for i, layer in enumerate(best.chromosome):
        print(f"   Layer {i}: {''.join(layer[:20])}... ({len(layer)} keys)")
    return best

def main():
    """Run all examples"""
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "MULTI-LAYER KEYBOARD OPTIMIZATION EXAMPLES" + " "*21 + "║")
    print("╚" + "="*78 + "╝")
    print()
    print("This script demonstrates three different ways to use multi-layer support:")
    print("  1. Single-layer (traditional)")
    print("  2. Fixed multi-layer (e.g., Romanian with diacritics)")
    print("  3. Dynamic layer evolution (GA decides)")
    print()
    input("Press Enter to start Example 1...")
    
    # Example 1: Single layer
    best1 = example_single_layer()
    
    input("\nPress Enter to start Example 2...")
    
    # Example 2: Fixed two layers
    best2 = example_fixed_multi_layer()
    
    input("\nPress Enter to start Example 3...")
    
    # Example 3: Dynamic layers
    best3 = example_dynamic_layers()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Example 1 (Single-layer):   {len(best1.chromosome)} layer(s),  Fitness: {best1.fitness:.6f}")
    print(f"Example 2 (Fixed 2-layer):   {len(best2.chromosome)} layer(s),  Fitness: {best2.fitness:.6f}")
    print(f"Example 3 (Dynamic layers):  {len(best3.chromosome)} layer(s),  Fitness: {best3.fitness:.6f}")
    print("="*80)
    
    print("\n💡 Tips:")
    print("  - Use single-layer for languages that fit in one layer (English)")
    print("  - Use fixed multi-layer when you know the structure (Romanian: base + diacritics)")
    print("  - Use dynamic layers to let GA discover if multi-layer helps")
    print("  - Larger populations and more iterations give better results")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
