import kagglehub
from pathlib import Path
import shutil
import os

def download_newsgroups_kaggle(output_dir: str = "data/newsgroups_kaggle"):
    """
    Downloads the 20 Newsgroups dataset using kagglehub to a specified directory.

    Args:
        output_dir (str): The local directory path where the dataset should be saved.
                          Defaults to "data/newsgroups_kaggle".
    """
    dataset_handle = "crawford/20-newsgroups" # Kaggle dataset identifier
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Specified output directory: {output_path.resolve()}")

    try:
        # Download all files from the dataset to a cached location managed by kagglehub
        print(f"Downloading '{dataset_handle}' dataset from Kaggle...")
        cache_path = kagglehub.dataset_download(dataset_handle)
        print(f"Dataset downloaded to cache: {cache_path}")

        cache_path_obj = Path(cache_path)

        # Check if the cache contains the expected structure or just files
        items_in_cache = list(cache_path_obj.iterdir())

        if not items_in_cache:
             print("Warning: Downloaded cache appears empty.")
             return

        # If there's a single directory inside (common), copy its contents
        if len(items_in_cache) == 1 and items_in_cache[0].is_dir():
            source_dir = items_in_cache[0]
            print(f"Copying contents from '{source_dir.name}'...")
            for item in source_dir.iterdir():
                destination = output_path / item.name
                # Handle potential name conflicts if copying multiple times
                if destination.exists():
                    print(f"  Warning: Destination '{destination}' already exists. Skipping {item.name}")
                    continue
                if item.is_dir():
                    shutil.copytree(item, destination)
                else: # It's a file
                    shutil.copy2(item, destination)
        else:
            # If files are directly in the cache root, copy them all
            print("Copying files directly from cache root...")
            for item in cache_path_obj.iterdir():
                 destination = output_path / item.name
                 if destination.exists():
                    print(f"  Warning: Destination '{destination}' already exists. Skipping {item.name}")
                    continue
                 if item.is_dir():
                    shutil.copytree(item, destination)
                 else: # It's a file
                    shutil.copy2(item, destination)

        print(f"Dataset files successfully copied to: {output_path.resolve()}")

    except Exception as e:
        print(f"An error occurred during download or copy: {e}")
        # Re-raise the exception if you want the script to stop
        # raise


# --- Main Execution ---
if __name__ == "__main__":
    # Specify your desired output folder here
    YOUR_OUTPUT_FOLDER = "data/newsgroup"

    download_newsgroups_kaggle(output_dir=YOUR_OUTPUT_FOLDER)
