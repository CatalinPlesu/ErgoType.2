"""
Test for path conversion between absolute and relative paths in distributed GA.
"""
import os
import sys
from pathlib import Path

# Add both project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class MockGA:
    """Mock GA class to test path conversion methods only."""
    
    def _to_relative_path(self, absolute_path):
        """
        Convert absolute path to relative path from PROJECT_ROOT.
        This allows distributed workers to find files in their local repository.
        
        Args:
            absolute_path: Absolute file path
            
        Returns:
            Relative path from PROJECT_ROOT, or original path if conversion fails
        """
        try:
            # Convert to Path objects for easier manipulation
            abs_path = os.path.abspath(absolute_path)
            rel_path = os.path.relpath(abs_path, PROJECT_ROOT)
            return rel_path
        except (ValueError, TypeError):
            # If conversion fails (e.g., different drives on Windows), return original
            return absolute_path
    
    def _to_absolute_path(self, relative_path):
        """
        Convert relative path to absolute path based on PROJECT_ROOT.
        This allows workers to resolve relative paths from distributed jobs.
        
        Args:
            relative_path: Relative file path from PROJECT_ROOT
            
        Returns:
            Absolute path, or original if already absolute
        """
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(PROJECT_ROOT, relative_path)


def test_path_conversion():
    """Test that paths are correctly converted between absolute and relative."""
    
    # Create a mock GA instance
    ga = MockGA()
    
    # Test 1: Relative to absolute conversion
    rel_path = 'src/data/keyboards/ansi_60_percent.json'
    abs_path = ga._to_absolute_path(rel_path)
    print(f"Test 1 - Relative to absolute:")
    print(f"  Input:  {rel_path}")
    print(f"  Output: {abs_path}")
    assert os.path.isabs(abs_path), "Output should be an absolute path"
    assert 'src/data/keyboards/ansi_60_percent.json' in abs_path, "Path should contain original relative path"
    print("  ✅ PASSED\n")
    
    # Test 2: Absolute to relative conversion
    abs_path_test = os.path.join(PROJECT_ROOT, 'src/data/keyboards/ansi_60_percent.json')
    rel_path_result = ga._to_relative_path(abs_path_test)
    print(f"Test 2 - Absolute to relative:")
    print(f"  Input:  {abs_path_test}")
    print(f"  Output: {rel_path_result}")
    assert not os.path.isabs(rel_path_result), "Output should be a relative path"
    assert rel_path_result.replace('\\', '/').endswith('src/data/keyboards/ansi_60_percent.json'), \
        "Relative path should match expected path"
    print("  ✅ PASSED\n")
    
    # Test 3: Round-trip conversion
    original_path = 'src/data/text/raw/simple_wikipedia_dataset.txt'
    abs_path = ga._to_absolute_path(original_path)
    rel_path_back = ga._to_relative_path(abs_path)
    print(f"Test 3 - Round-trip conversion:")
    print(f"  Original: {original_path}")
    print(f"  To abs:   {abs_path}")
    print(f"  Back rel: {rel_path_back}")
    # Normalize path separators for comparison
    assert rel_path_back.replace('\\', '/') == original_path, \
        f"Round-trip should return original path, got {rel_path_back}"
    print("  ✅ PASSED\n")
    
    # Test 4: Already absolute path stays absolute
    already_abs = ga._to_absolute_path(abs_path_test)
    print(f"Test 4 - Already absolute path:")
    print(f"  Input:  {abs_path_test}")
    print(f"  Output: {already_abs}")
    assert already_abs == abs_path_test, "Absolute path should remain unchanged"
    print("  ✅ PASSED\n")
    
    print("="*80)
    print("ALL TESTS PASSED! ✅")
    print("="*80)


if __name__ == "__main__":
    test_path_conversion()
