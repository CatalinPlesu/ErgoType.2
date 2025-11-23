#!/usr/bin/env python3

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def create_preview_dataset(dataset_name='simple_wikipedia', preview_size_mb=1):
    """Create a preview dataset by sampling from raw text file"""
    import random
    
    # Define paths
    raw_text_path = f"src/data/text/raw/{dataset_name}_dataset.txt"
    preview_path = f"src/data/text/raw/{dataset_name}_dataset_preview.txt"
    
    if not os.path.exists(raw_text_path):
        print(f"❌ Raw text file not found: {raw_text_path}")
        print("   Preview mode requires raw text file to exist")
        return dataset_name
    
    try:
        # Get file size and calculate target size
        file_size = os.path.getsize(raw_text_path)
        target_size = preview_size_mb * 1024 * 1024  # Convert MB to bytes
        
        print(f"📊 Creating preview dataset...")
        print(f"   Original file size: {file_size / (1024*1024):.1f} MB")
        print(f"   Preview size: {target_size / (1024*1024):.1f} MB")
        
        if target_size >= file_size:
            print("   File is smaller than preview size, using full file")
            return dataset_name
        
        # Sample random starting position
        max_start = file_size - target_size
        start_pos = random.randint(0, max_start)
        
        # Read preview chunk
        with open(raw_text_path, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(start_pos)
            preview_data = f.read(target_size)
        
        # Write preview file
        os.makedirs(os.path.dirname(preview_path), exist_ok=True)
        with open(preview_path, 'w', encoding='utf-8') as f:
            f.write(preview_data)
        
        print(f"✅ Preview dataset created: {preview_path}")
        print(f"   Preview size: {len(preview_data)} bytes")
        
        return dataset_name  # Return original dataset name, preview file will be used by typer
        
    except Exception as e:
        print(f"❌ Error creating preview dataset: {e}")
        import traceback
        traceback.print_exc()
        return dataset_name

if __name__ == "__main__":
    print("Testing preview dataset creation...")
    dataset_name = create_preview_dataset('simple_wikipedia', 1)
    print(f"Result: {dataset_name}")
    
    # Check if file was created
    preview_path = "src/data/text/raw/simple_wikipedia_dataset_preview.txt"
    if os.path.exists(preview_path):
        print(f"✅ Preview file created successfully: {os.path.getsize(preview_path)} bytes")
    else:
        print(f"❌ Preview file not created")