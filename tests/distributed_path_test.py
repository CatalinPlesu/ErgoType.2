"""
Integration test simulating distributed GA path handling.
This test simulates what happens when master pushes config and worker receives it.
"""
import os
import sys
import json
from pathlib import Path

# Add both project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class SimulatedMaster:
    """Simulates master node behavior."""
    
    def __init__(self, keyboard_file, text_file):
        # Master stores absolute paths internally
        self.keyboard_file = os.path.join(PROJECT_ROOT, keyboard_file) if not os.path.isabs(keyboard_file) else keyboard_file
        self.text_file = os.path.join(PROJECT_ROOT, text_file) if not os.path.isabs(text_file) else text_file
        print(f"Master initialized with:")
        print(f"  Keyboard: {self.keyboard_file}")
        print(f"  Text:     {self.text_file}")
    
    def _to_relative_path(self, absolute_path):
        """Convert absolute to relative for distribution."""
        try:
            abs_path = os.path.abspath(absolute_path)
            rel_path = os.path.relpath(abs_path, PROJECT_ROOT)
            return rel_path
        except (ValueError, TypeError):
            return absolute_path
    
    def push_config(self):
        """Simulate pushing config with relative paths."""
        config = {
            'keyboard_file': self._to_relative_path(self.keyboard_file),
            'text_file': self._to_relative_path(self.text_file),
        }
        print(f"\nMaster pushing config (relative paths):")
        print(f"  keyboard_file: {config['keyboard_file']}")
        print(f"  text_file:     {config['text_file']}")
        return json.dumps(config)


class SimulatedWorker:
    """Simulates worker node behavior on a different machine."""
    
    def __init__(self, worker_project_root):
        # Worker has its own PROJECT_ROOT (simulating different machine)
        self.project_root = worker_project_root
        print(f"\nWorker initialized with PROJECT_ROOT: {self.project_root}")
    
    def _to_absolute_path(self, relative_path):
        """Convert relative to absolute based on worker's PROJECT_ROOT."""
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(self.project_root, relative_path)
    
    def receive_config(self, config_json):
        """Simulate receiving and processing config."""
        config = json.loads(config_json)
        print(f"\nWorker received config:")
        print(f"  keyboard_file (relative): {config['keyboard_file']}")
        print(f"  text_file (relative):     {config['text_file']}")
        
        # Convert to absolute paths based on worker's PROJECT_ROOT
        self.keyboard_file = self._to_absolute_path(config['keyboard_file'])
        self.text_file = self._to_absolute_path(config['text_file'])
        
        print(f"\nWorker converted to absolute paths:")
        print(f"  keyboard_file: {self.keyboard_file}")
        print(f"  text_file:     {self.text_file}")
        
        return self.keyboard_file, self.text_file


def test_distributed_scenario():
    """Test distributed scenario with master and worker on different paths."""
    print("="*80)
    print("SIMULATED DISTRIBUTED GA PATH HANDLING TEST")
    print("="*80)
    
    # Scenario 1: Worker on same machine (most common during development)
    print("\n" + "="*80)
    print("SCENARIO 1: Worker on same machine")
    print("="*80)
    
    master = SimulatedMaster(
        keyboard_file='src/data/keyboards/ansi_60_percent.json',
        text_file='src/data/text/raw/simple_wikipedia_dataset.txt'
    )
    
    config_json = master.push_config()
    
    worker = SimulatedWorker(PROJECT_ROOT)
    worker_keyboard, worker_text = worker.receive_config(config_json)
    
    # Verify worker gets correct absolute paths
    assert os.path.isabs(worker_keyboard), "Worker keyboard path should be absolute"
    assert os.path.isabs(worker_text), "Worker text path should be absolute"
    assert 'src/data/keyboards/ansi_60_percent.json' in worker_keyboard, "Path should contain expected file"
    assert 'src/data/text/raw/simple_wikipedia_dataset.txt' in worker_text, "Path should contain expected file"
    
    print("\n✅ SCENARIO 1 PASSED: Worker resolved paths correctly")
    
    # Scenario 2: Worker on different machine with different PROJECT_ROOT
    print("\n" + "="*80)
    print("SCENARIO 2: Worker on different machine (simulated)")
    print("="*80)
    
    # Simulate a different project root (like /opt/ergotype on worker machine)
    different_root = "/opt/ergotype_worker"
    print(f"Simulating worker with PROJECT_ROOT: {different_root}")
    
    worker2 = SimulatedWorker(different_root)
    worker2_keyboard, worker2_text = worker2.receive_config(config_json)
    
    # Verify worker gets paths relative to its own PROJECT_ROOT
    assert worker2_keyboard == os.path.join(different_root, 'src/data/keyboards/ansi_60_percent.json')
    assert worker2_text == os.path.join(different_root, 'src/data/text/raw/simple_wikipedia_dataset.txt')
    
    print("\n✅ SCENARIO 2 PASSED: Worker on different machine would resolve to its local paths")
    
    # Scenario 3: Verify no hardcoded absolute paths in config
    print("\n" + "="*80)
    print("SCENARIO 3: Verify config contains only relative paths")
    print("="*80)
    
    config = json.loads(config_json)
    print(f"Config contents:")
    print(f"  keyboard_file: {config['keyboard_file']}")
    print(f"  text_file:     {config['text_file']}")
    
    assert not os.path.isabs(config['keyboard_file']), "Config should contain relative keyboard path"
    assert not os.path.isabs(config['text_file']), "Config should contain relative text path"
    assert PROJECT_ROOT not in config['keyboard_file'], "Config should not contain absolute PROJECT_ROOT"
    assert PROJECT_ROOT not in config['text_file'], "Config should not contain absolute PROJECT_ROOT"
    
    print("\n✅ SCENARIO 3 PASSED: Config contains only relative paths")
    
    print("\n" + "="*80)
    print("ALL DISTRIBUTED PATH TESTS PASSED! ✅")
    print("="*80)
    print("\nSummary:")
    print("  ✅ Master converts absolute paths to relative before distribution")
    print("  ✅ Workers convert relative paths to absolute based on their PROJECT_ROOT")
    print("  ✅ Config transmitted over network contains only relative paths")
    print("  ✅ Workers on different machines can find files in their local repository")


if __name__ == "__main__":
    test_distributed_scenario()
