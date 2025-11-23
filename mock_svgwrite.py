"""
Simple SVG writer replacement to avoid svgwrite dependency
"""

class MockSvgwrite:
    """Mock svgwrite module for basic SVG generation"""
    
    class Drawing:
        def __init__(self, filename, size):
            self.filename = filename
            self.size = size
            self.elements = []
            
        def add(self, element):
            self.elements.append(element)
            
        def save(self):
            # For now, just print that SVG would be saved
            print(f"SVG would be saved to {self.filename} with size {self.size}")
            
    class Rectangle:
        def __init__(self, insert, size, **kwargs):
            self.insert = insert
            self.size = size
            self.kwargs = kwargs
            
    class Text:
        def __init__(self, text, insert, **kwargs):
            self.text = text
            self.insert = insert
            self.kwargs = kwargs

# Create module-level functions to mimic svgwrite
def Drawing(filename, size):
    return MockSvgwrite.Drawing(filename, size)