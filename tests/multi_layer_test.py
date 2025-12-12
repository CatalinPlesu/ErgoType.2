"""
Test multi-layer chromosome support in genetic algorithm
"""

import sys
import os

# Add both parent and src to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from core.ga import Individual

def test_individual_single_layer():
    """Test Individual with single layer chromosome"""
    print("Testing single layer Individual...")
    
    # Create single layer chromosome (legacy format)
    chromosome = ['a', 'b', 'c', 'd', 'e']
    ind = Individual(chromosome=chromosome, generation=0, name="test_single")
    
    # Check it's stored as multi-layer internally
    assert len(ind.chromosome) == 1, f"Expected 1 layer, got {len(ind.chromosome)}"
    assert ind.chromosome[0] == chromosome, "Base layer doesn't match input"
    assert ind.get_layer_count() == 1, "Layer count should be 1"
    assert ind.get_layer(0) == chromosome, "get_layer(0) should return base layer"
    
    print("✓ Single layer Individual works correctly")

def test_individual_multi_layer():
    """Test Individual with multi-layer chromosome"""
    print("\nTesting multi-layer Individual...")
    
    # Create multi-layer chromosome
    layer0 = ['a', 'b', 'c', 'd', 'e']
    layer1 = ['ă', 'â', 'î', 'ș', 'ț']
    chromosome = [layer0, layer1]
    
    ind = Individual(chromosome=chromosome, generation=0, name="test_multi")
    
    # Check layers
    assert len(ind.chromosome) == 2, f"Expected 2 layers, got {len(ind.chromosome)}"
    assert ind.chromosome[0] == layer0, "Layer 0 doesn't match"
    assert ind.chromosome[1] == layer1, "Layer 1 doesn't match"
    assert ind.get_layer_count() == 2, "Layer count should be 2"
    assert ind.get_layer(0) == layer0, "get_layer(0) should return layer 0"
    assert ind.get_layer(1) == layer1, "get_layer(1) should return layer 1"
    
    print("✓ Multi-layer Individual works correctly")

def test_crossover_single_layer():
    """Test crossover produces valid single-layer offspring"""
    print("\nTesting single-layer crossover...")
    
    import random
    random.seed(42)  # For reproducibility
    
    # Create a minimal mock GA object for testing
    class MockGA:
        def __init__(self):
            self.current_generation = 0
            self.previous_population_iteration = 0
            self.individual_names = {}
            self.population = []
            self.parents = []
            self.children = []
            self.num_layers = 1
            self.max_layers = 1
        
        # Import the methods we want to test
        from core.ga import GeneticAlgorithmSimulation
        uniform_crossover = GeneticAlgorithmSimulation.uniform_crossover
    
    ga = MockGA()
    
    # Create two parent individuals with single layer
    parent1_layer = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    parent2_layer = ['j', 'i', 'h', 'g', 'f', 'e', 'd', 'c', 'b', 'a']
    
    parent1 = Individual(chromosome=[parent1_layer], generation=0, fitness=0.5, name="parent1")
    parent2 = Individual(chromosome=[parent2_layer], generation=0, fitness=0.6, name="parent2")
    
    ga.population = [parent1, parent2]
    ga.parents = [parent1, parent2]
    ga.children = []
    
    # Perform crossover
    ga.uniform_crossover(offsprings_per_pair=2)
    
    # Check results
    assert len(ga.children) > 0, "Should produce at least one child"
    for child in ga.children:
        assert len(child.chromosome) == 1, f"Child should have 1 layer, got {len(child.chromosome)}"
        child_layer = child.chromosome[0]
        assert len(child_layer) == len(parent1_layer), "Child layer should have same length as parents"
        # Check all genes present
        assert set(child_layer) == set(parent1_layer), "Child should contain all genes from parents"
        # Check no duplicates
        assert len(child_layer) == len(set(child_layer)), "Child should have no duplicate genes"
    
    print(f"✓ Single-layer crossover works correctly (produced {len(ga.children)} children)")

def test_crossover_multi_layer():
    """Test crossover produces valid multi-layer offspring"""
    print("\nTesting multi-layer crossover...")
    
    import random
    random.seed(42)
    
    # Create a minimal mock GA object for testing
    class MockGA:
        def __init__(self):
            self.current_generation = 0
            self.previous_population_iteration = 0
            self.individual_names = {}
            self.population = []
            self.parents = []
            self.children = []
            self.num_layers = 2
            self.max_layers = 3
        
        # Import the methods we want to test
        from core.ga import GeneticAlgorithmSimulation
        uniform_crossover = GeneticAlgorithmSimulation.uniform_crossover
    
    ga = MockGA()
    
    # Create two parent individuals with 2 layers
    parent1_l0 = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    parent1_l1 = ['k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']
    parent2_l0 = ['j', 'i', 'h', 'g', 'f', 'e', 'd', 'c', 'b', 'a']
    parent2_l1 = ['t', 's', 'r', 'q', 'p', 'o', 'n', 'm', 'l', 'k']
    
    parent1 = Individual(chromosome=[parent1_l0, parent1_l1], generation=0, fitness=0.5, name="parent1")
    parent2 = Individual(chromosome=[parent2_l0, parent2_l1], generation=0, fitness=0.6, name="parent2")
    
    ga.population = [parent1, parent2]
    ga.parents = [parent1, parent2]
    ga.children = []
    
    # Perform crossover
    ga.uniform_crossover(offsprings_per_pair=2)
    
    # Check results
    assert len(ga.children) > 0, "Should produce at least one child"
    for child in ga.children:
        assert len(child.chromosome) == 2, f"Child should have 2 layers, got {len(child.chromosome)}"
        
        # Check layer 0
        child_l0 = child.chromosome[0]
        assert len(child_l0) == len(parent1_l0), "Child layer 0 should have same length as parents"
        assert set(child_l0) == set(parent1_l0), "Child layer 0 should contain all genes from parent layer 0"
        assert len(child_l0) == len(set(child_l0)), "Child layer 0 should have no duplicates"
        
        # Check layer 1
        child_l1 = child.chromosome[1]
        assert len(child_l1) == len(parent1_l1), "Child layer 1 should have same length as parents"
        assert set(child_l1) == set(parent1_l1), "Child layer 1 should contain all genes from parent layer 1"
        assert len(child_l1) == len(set(child_l1)), "Child layer 1 should have no duplicates"
    
    print(f"✓ Multi-layer crossover works correctly (produced {len(ga.children)} children)")

def test_mutation_single_layer():
    """Test mutation on single-layer individuals"""
    print("\nTesting single-layer mutation...")
    
    import random
    random.seed(42)
    
    # Create a minimal mock GA object for testing
    class MockGA:
        def __init__(self):
            self.num_layers = 1
            self.max_layers = 3
        
        # Import the methods we want to test
        from core.ga import GeneticAlgorithmSimulation
        mutate_permutation = GeneticAlgorithmSimulation.mutate_permutation
    
    ga = MockGA()
    
    # Create individual
    original_layer = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    ind = Individual(chromosome=[original_layer.copy()], generation=1, name="test")
    
    # Mutate
    mutated_chromosome = ga.mutate_permutation(ind.chromosome, mutation_rate=1.0, num_mutations=5)
    
    # Check result
    assert len(mutated_chromosome) == 1, "Should still have 1 layer"
    mutated_layer = mutated_chromosome[0]
    assert len(mutated_layer) == len(original_layer), "Layer length should be same"
    assert set(mutated_layer) == set(original_layer), "Should have same genes"
    assert mutated_layer != original_layer, "Should be different from original"
    
    print("✓ Single-layer mutation works correctly")

def test_layer_addition_removal():
    """Test layer addition and removal mutations"""
    print("\nTesting layer addition/removal...")
    
    import random
    random.seed(42)
    
    # Create a minimal mock GA object for testing
    class MockGA:
        def __init__(self):
            self.num_layers = 1
            self.max_layers = 3
        
        # Import the methods we want to test
        from core.ga import GeneticAlgorithmSimulation
        add_layer_mutation = GeneticAlgorithmSimulation.add_layer_mutation
        remove_layer_mutation = GeneticAlgorithmSimulation.remove_layer_mutation
    
    ga = MockGA()
    
    # Create individual with 1 layer
    layer = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    ind = Individual(chromosome=[layer.copy()], generation=1, name="test")
    
    # Test layer addition
    original_count = len(ind.chromosome)
    ga.add_layer_mutation(ind)
    assert len(ind.chromosome) == original_count + 1, "Should add one layer"
    assert len(ind.chromosome[1]) == len(layer), "New layer should have same length"
    print(f"✓ Layer addition works (1 -> {len(ind.chromosome)} layers)")
    
    # Test layer removal
    ga.remove_layer_mutation(ind)
    assert len(ind.chromosome) == original_count, "Should remove one layer"
    print(f"✓ Layer removal works ({original_count + 1} -> {len(ind.chromosome)} layers)")
    
    # Test can't remove base layer when only 1 layer
    ga.remove_layer_mutation(ind)
    assert len(ind.chromosome) >= 1, "Should always keep at least base layer"
    print("✓ Base layer protection works")

def test_serialization():
    """Test chromosome serialization"""
    print("\nTesting serialization...")
    
    # Test multi-layer serialization
    layer0 = ['a', 'b', 'c']
    layer1 = ['d', 'e', 'f']
    ind = Individual(chromosome=[layer0, layer1], generation=0, name="test")
    
    # Simulate what happens in survivor_selection
    if isinstance(ind.chromosome[0], list):
        serialized = [''.join(layer) for layer in ind.chromosome]
    else:
        serialized = [''.join(ind.chromosome)]
    
    assert serialized == ['abc', 'def'], f"Expected ['abc', 'def'], got {serialized}"
    print("✓ Multi-layer serialization works")
    
    # Test single-layer serialization
    ind2 = Individual(chromosome=['x', 'y', 'z'], generation=0, name="test2")
    
    if isinstance(ind2.chromosome[0], list):
        serialized2 = [''.join(layer) for layer in ind2.chromosome]
    else:
        serialized2 = [''.join(ind2.chromosome)]
    
    assert serialized2 == ['xyz'], f"Expected ['xyz'], got {serialized2}"
    print("✓ Single-layer serialization works")

if __name__ == "__main__":
    print("="*80)
    print("MULTI-LAYER CHROMOSOME TESTS")
    print("="*80)
    
    try:
        test_individual_single_layer()
        test_individual_multi_layer()
        test_crossover_single_layer()
        test_crossover_multi_layer()
        test_mutation_single_layer()
        test_layer_addition_removal()
        test_serialization()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
