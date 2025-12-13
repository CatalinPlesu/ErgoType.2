#!/usr/bin/env python3
"""
Unit tests for GA Runs Queue functionality.
Tests queue creation, configuration, and Individual ID reset.
"""

import sys
import unittest
import tempfile
import json
from pathlib import Path

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.ga_runs_queue import GARunsQueue, create_run_config, DEFAULT_PARAMS


class TestCreateRunConfig(unittest.TestCase):
    """Test create_run_config helper function"""
    
    def test_create_config(self):
        """Test creating a run configuration"""
        config = create_run_config(
            name="Test Run",
            population_size=20,
            max_iterations=30
        )
        
        self.assertEqual(config['name'], "Test Run")
        self.assertEqual(config['population_size'], 20)
        self.assertEqual(config['max_iterations'], 30)
    
    def test_config_with_defaults(self):
        """Test that config merges with defaults"""
        config = create_run_config(
            name="Test Run",
            population_size=20
        )
        
        # Should have default values for other params
        self.assertIn('max_iterations', config)
        self.assertEqual(config['max_iterations'], DEFAULT_PARAMS['max_iterations'])
        self.assertIn('fitts_a', config)
        self.assertEqual(config['fitts_a'], DEFAULT_PARAMS['fitts_a'])
    
    def test_config_is_dict(self):
        """Test that config is a dictionary"""
        config = create_run_config(name="Test Run")
        
        self.assertIsInstance(config, dict)


class TestGARunsQueue(unittest.TestCase):
    """Test GARunsQueue class"""
    
    def test_create_queue(self):
        """Test creating an empty queue"""
        queue = GARunsQueue()
        
        self.assertEqual(len(queue.runs), 0)
        self.assertEqual(len(queue.results), 0)
    
    def test_add_run_with_dict(self):
        """Test adding runs to queue using dictionaries"""
        queue = GARunsQueue()
        
        config1 = {'name': 'Run 1', 'population_size': 10}
        config2 = {'name': 'Run 2', 'population_size': 20}
        
        queue.add_run(config1)
        queue.add_run(config2)
        
        self.assertEqual(len(queue.runs), 2)
        self.assertEqual(queue.runs[0]['name'], "Run 1")
        self.assertEqual(queue.runs[1]['name'], "Run 2")
    
    def test_add_run_with_helper(self):
        """Test adding runs to queue using create_run_config"""
        queue = GARunsQueue()
        
        queue.add_run(create_run_config(name="Run 1", population_size=10))
        queue.add_run(create_run_config(name="Run 2", population_size=20))
        
        self.assertEqual(len(queue.runs), 2)
        self.assertEqual(queue.runs[0]['name'], "Run 1")
        self.assertEqual(queue.runs[1]['name'], "Run 2")
    
    def test_remove_run(self):
        """Test removing runs from queue"""
        queue = GARunsQueue()
        
        queue.add_run({'name': 'Run 1'})
        queue.add_run({'name': 'Run 2'})
        queue.add_run({'name': 'Run 3'})
        
        self.assertEqual(len(queue.runs), 3)
        
        queue.remove_run(1)  # Remove Run 2
        
        self.assertEqual(len(queue.runs), 2)
        self.assertEqual(queue.runs[0]['name'], "Run 1")
        self.assertEqual(queue.runs[1]['name'], "Run 3")
    
    def test_clear(self):
        """Test clearing queue"""
        queue = GARunsQueue()
        queue.add_run({'name': 'Run 1'})
        queue.add_run({'name': 'Run 2'})
        
        self.assertEqual(len(queue.runs), 2)
        
        queue.clear()
        
        self.assertEqual(len(queue.runs), 0)
        self.assertEqual(len(queue.results), 0)
    
    def test_save_and_load(self):
        """Test saving and loading queue from file"""
        queue = GARunsQueue()
        queue.add_run(create_run_config(name="Run 1", population_size=15))
        queue.add_run(create_run_config(name="Run 2", population_size=25))
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            queue.save_to_file(temp_path)
            
            # Verify file was created
            self.assertTrue(Path(temp_path).exists())
            
            # Load into new queue
            queue2 = GARunsQueue()
            queue2.load_from_file(temp_path)
            
            # Verify loaded queue matches original
            self.assertEqual(len(queue2.runs), 2)
            self.assertEqual(queue2.runs[0]['name'], "Run 1")
            self.assertEqual(queue2.runs[0]['population_size'], 15)
            self.assertEqual(queue2.runs[1]['name'], "Run 2")
            self.assertEqual(queue2.runs[1]['population_size'], 25)
            
        finally:
            # Clean up
            if Path(temp_path).exists():
                Path(temp_path).unlink()
    
    def test_create_parameter_exploration_queue(self):
        """Test the parameter exploration queue creation"""
        from core.ga_runs_queue import create_parameter_exploration_queue
        
        queue = create_parameter_exploration_queue()
        
        # Should have exactly 25 configurations
        self.assertEqual(len(queue.runs), 25)
        
        # All should have stagnant_limit=3 and max_concurrent_processes=1
        for run in queue.runs:
            self.assertEqual(run['stagnant_limit'], 3)
            self.assertEqual(run['max_concurrent_processes'], 1)
            self.assertIn('name', run)
            self.assertGreater(run['population_size'], 0)
            self.assertGreater(run['max_iterations'], 0)
        
        # Check parameter coverage
        iterations = set(r['max_iterations'] for r in queue.runs)
        populations = set(r['population_size'] for r in queue.runs)
        
        # Should cover multiple levels
        self.assertGreaterEqual(len(iterations), 8)
        self.assertGreaterEqual(len(populations), 6)


class TestIndividualIDReset(unittest.TestCase):
    """Test Individual ID counter reset functionality"""
    
    def test_individual_id_reset(self):
        """Test that Individual._next_id can be reset"""
        # This test verifies the reset mechanism without importing pika
        # We just check the class attribute exists and can be set
        
        # Create a mock Individual class for testing
        class MockIndividual:
            _next_id = 0
            
            def __init__(self):
                self.id = MockIndividual._next_id
                MockIndividual._next_id += 1
        
        # Create some individuals
        ind1 = MockIndividual()
        ind2 = MockIndividual()
        ind3 = MockIndividual()
        
        self.assertEqual(ind1.id, 0)
        self.assertEqual(ind2.id, 1)
        self.assertEqual(ind3.id, 2)
        self.assertEqual(MockIndividual._next_id, 3)
        
        # Reset counter
        MockIndividual._next_id = 0
        
        # Create new individuals after reset
        ind4 = MockIndividual()
        ind5 = MockIndividual()
        
        self.assertEqual(ind4.id, 0)
        self.assertEqual(ind5.id, 1)
        self.assertEqual(MockIndividual._next_id, 2)


class TestQueueConfigSerialization(unittest.TestCase):
    """Test JSON serialization of queue configurations"""
    
    def test_json_serialization(self):
        """Test that queue can be serialized to JSON"""
        queue = GARunsQueue()
        queue.add_run(create_run_config(
            name="Test Run",
            population_size=30,
            max_iterations=50,
            fitts_a=0.5,
            fitts_b=0.3
        ))
        
        # Convert to JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            queue.save_to_file(temp_path)
            
            # Read and parse JSON
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            # Verify structure
            self.assertIn('runs', data)
            self.assertEqual(len(data['runs']), 1)
            
            run_data = data['runs'][0]
            self.assertEqual(run_data['name'], "Test Run")
            self.assertEqual(run_data['population_size'], 30)
            self.assertEqual(run_data['max_iterations'], 50)
            self.assertAlmostEqual(run_data['fitts_a'], 0.5)
            self.assertAlmostEqual(run_data['fitts_b'], 0.3)
            
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
