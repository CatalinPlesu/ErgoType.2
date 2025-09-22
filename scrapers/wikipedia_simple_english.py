import kagglehub
from pathlib import Path
import shutil
import os

def download_simple_wikipedia(output_dir: str = "data/simple_wikipedia"):
    """
    Downloads the Plain Text Wikipedia (SimpleEnglish) dataset using kagglehub,
    and extracts only the 'AllCombined.txt' file to a specified directory.

    Args:
        output_dir (str): The local directory path where the combined file should be saved.
                          Defaults to "data/simple_wikipedia".
    """
    dataset_handle = "ffatty/plain-text-wikipedia-simpleenglish"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Specified output directory: {output_path.resolve()}")

    try:
        # Download all files from the dataset to a cached location managed by kagglehub
        print(f"Downloading '{dataset_handle}' dataset from Kaggle...")
        cache_path = kagglehub.dataset_download(dataset_handle)
        print(f"Dataset downloaded to cache: {cache_path}")

        cache_path_obj = Path(cache_path)

        # Look for AllCombined.txt in the root or subdirectories
        combined_file = None
        for txt_file in cache_path_obj.rglob("AllCombined.txt"):
            combined_file = txt_file
            break

        if not combined_file or not combined_file.exists():
            raise FileNotFoundError("Could not find 'AllCombined.txt' in the downloaded dataset.")

        destination = output_path / "AllCombined.txt"
        if destination.exists():
            print(f"Warning: '{destination}' already exists. Skipping copy.")
        else:
            print(f"Copying '{combined_file.name}' to {destination}...")
            shutil.copy2(combined_file, destination)

        print(f"File successfully saved to: {destination.resolve()}")

    except Exception as e:
        print(f"An error occurred during download or copy: {e}")
        # Optionally re-raise: raise


# --- Main Execution ---
if __name__ == "__main__":
    YOUR_OUTPUT_FOLDER = "data/simple_wikipedia"
    download_simple_wikipedia(output_dir=YOUR_OUTPUT_FOLDER)
