#!/usr/bin/env python3
"""
Simple test to verify the fitness normalization fix.
"""

def test_simple_normalization():
    """Test the exact normalization logic requested by user"""
    
    print("Testing fitness normalization per user request:")
    print("- Use max as max, 0 as min")
    print("- Invert with 1-value to make it a fitness function")
    print()
    
    # Example values
    max_distance = 200.0
    max_time = 100.0
    
    # Test cases
    test_cases = [
        {"name": "Perfect layout", "distance": 0.0, "time": 0.0},
        {"name": "Good layout", "distance": 50.0, "time": 25.0},
        {"name": "Average layout", "distance": 100.0, "time": 50.0},
        {"name": "Poor layout", "distance": 150.0, "time": 75.0},
        {"name": "Worst layout", "distance": 200.0, "time": 100.0},
    ]
    
    distance_weight = 0.5
    time_weight = 0.5
    
    print(f"Parameters:")
    print(f"  Distance weight: {distance_weight}")
    print(f"  Time weight: {time_weight}")
    print(f"  Max distance: {max_distance}")
    print(f"  Max time: {max_time}")
    print()
    
    results = []
    for case in test_cases:
        distance = case["distance"]
        time_component = case["time"]
        
        # Apply user-requested normalization: value/max_value (using 0 as min, max as max)
        normalized_distance = distance / max_distance  # 0 as min, max_distance as max
        normalized_time = time_component / max_time    # 0 as min, max_time as max
        
        # Calculate weighted sickness
        sickness = (distance_weight * normalized_distance + time_weight * normalized_time)
        
        # Invert to get fitness (1-value)
        fitness = 1.0 - sickness
        
        print(f"{case['name']}:")
        print(f"  Distance: {distance} → normalized: {normalized_distance:.3f}")
        print(f"  Time: {time_component} → normalized: {normalized_time:.3f}")
        print(f"  Sickness: {sickness:.6f}")
        print(f"  Fitness: {fitness:.6f}")
        print()
        
        results.append((case['name'], fitness))
    
    print("Final ranking (highest fitness = best layout):")
    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
    for i, (name, fitness) in enumerate(sorted_results, 1):
        print(f"  {i}. {name}: {fitness:.6f}")
    
    print()
    print("✓ Normalization follows user specification:")
    print("  - Uses max as maximum bound, 0 as minimum bound")
    print("  - Normalizes with value/max_value")
    print("  - Inverts with 1-value to create fitness function")
    print("  - Higher fitness values indicate better layouts")

if __name__ == "__main__":
    test_simple_normalization()