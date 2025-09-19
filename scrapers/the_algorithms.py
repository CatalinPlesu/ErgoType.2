import os
import shutil
from pathlib import Path
import git  

# --- Configuration ---

# Base directory to store downloaded repositories and final code
BASE_OUTPUT_DIR = Path("data") / "the_algorithms_code"
BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Temporary directory for cloning (will be deleted after processing)
TEMP_CLONE_DIR = Path("temp_clones")
TEMP_CLONE_DIR.mkdir(parents=True, exist_ok=True)

# Define target languages/repos using the full list you provided.
# Key: Simple language identifier (used for folder naming and file extension)
# Value: List of full GitHub repository URLs
TARGET_REPOS = {
    "py": ["https://github.com/TheAlgorithms/Python"],
    "java": ["https://github.com/TheAlgorithms/Java"],
    "js": ["https://github.com/TheAlgorithms/Javascript"],
    "cpp": ["https://github.com/TheAlgorithms/C-Plus-Plus"],
    "rs": ["https://github.com/TheAlgorithms/Rust"],
    "c": ["https://github.com/TheAlgorithms/C"],
    "go": ["https://github.com/TheAlgorithms/Go"],
    "cs": ["https://github.com/TheAlgorithms/C-Sharp"],
    "md": ["https://github.com/TheAlgorithms/Algorithms-Explanation"],
    "php": ["https://github.com/TheAlgorithms/PHP"],
    "ts": ["https://github.com/TheAlgorithms/TypeScript"],
    "dart": ["https://github.com/TheAlgorithms/Dart"],
    "kt": ["https://github.com/TheAlgorithms/Kotlin"],
    "rb": ["https://github.com/TheAlgorithms/Ruby"],
    "scala": ["https://github.com/TheAlgorithms/Scala"],
    "r": ["https://github.com/TheAlgorithms/R"],
    "swift": ["https://github.com/TheAlgorithms/Swift"],
    "jl": ["https://github.com/TheAlgorithms/Julia"],
    "hs": ["https://github.com/TheAlgorithms/Haskell"],
    "m": ["https://github.com/TheAlgorithms/MATLAB-Octave"],
    "sol": ["https://github.com/TheAlgorithms/Solidity"],
    "lua": ["https://github.com/TheAlgorithms/Lua"],
    "zig": ["https://github.com/TheAlgorithms/Zig"],
    "ex": ["https://github.com/TheAlgorithms/Elixir"],
    "ml": ["https://github.com/TheAlgorithms/OCaml"],
    "clj": ["https://github.com/TheAlgorithms/Clojure"],
    "nim": ["https://github.com/TheAlgorithms/Nim"],
    "erl": ["https://github.com/TheAlgorithms/Erlang"],
    "sh": ["https://github.com/TheAlgorithms/scripts"],
}


def clone_repo(repo_url, clone_path):
    """Clones a Git repository (given a full URL) to a local path."""
    print(f"Cloning {repo_url}...")
    try:
        clone_path.parent.mkdir(parents=True, exist_ok=True)
        git.Repo.clone_from(repo_url, clone_path)
        print(f"Successfully cloned {repo_url} to {clone_path}")
        return True
    except git.exc.GitCommandError as e:
        print(f"Error cloning {repo_url}: Git command failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error cloning {repo_url}: {e}")
        return False


def extract_code_files(repo_path, extension, output_dir):
    """Recursively finds files with a specific extension and copies them."""
    print(f"Extracting *{extension} files from {repo_path}...")
    file_count = 0
    pattern = f"*{extension}"
    for file_path in repo_path.rglob(pattern):
        if file_path.is_file() and file_path.suffix.lower() == extension.lower():
            try:
                relative_path = file_path.relative_to(repo_path)
                destination_path = output_dir / relative_path
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, destination_path)
                file_count += 1
            except ValueError as e:
                print(f"Error calculating relative path for {file_path}: {e}")
            except Exception as e:
                print(f"Error copying {file_path} to {destination_path}: {e}")

    print(f"Extracted {file_count} *{extension} files to {output_dir}")


def process_language(lang_id, repo_urls):
    """Main logic to process all repos for a single language identifier."""
    print(f"\n--- Processing language identifier: '{lang_id}' ---")
    extension = f".{lang_id}"

    lang_output_base_dir = BASE_OUTPUT_DIR / lang_id

    for i, repo_url in enumerate(repo_urls):
        try:
            repo_part = repo_url.split("github.com/")[-1].split(".git")[0]
            safe_repo_name = repo_part.replace("/", "_")
        except IndexError:
            print(f"Error parsing repo URL '{repo_url}'. Skipping.")
            continue

        temp_repo_path = TEMP_CLONE_DIR / f"{lang_id}_{safe_repo_name}_{i}_temp_clone"
        repo_specific_output_dir = lang_output_base_dir / safe_repo_name

        if temp_repo_path.exists():
            shutil.rmtree(temp_repo_path)

        if clone_repo(repo_url, temp_repo_path):
            extract_code_files(temp_repo_path, extension, repo_specific_output_dir)
            print(f"Finished processing repo '{repo_url}' for language ID '{lang_id}' (extension {extension})\n")
        else:
            print(f"Skipping extraction for repo '{repo_url}' due to clone failure.\n")

        if temp_repo_path.exists():
            try:
                shutil.rmtree(temp_repo_path)
            except Exception as e:
                print(f"Warning: Could not remove temporary clone directory {temp_repo_path}: {e}")

# --- Main Execution ---


if __name__ == "__main__":
    print("Starting download and extraction of code from TheAlgorithms repositories (v2)...")
    print(f"Target Languages/Repos: {list(TARGET_REPOS.keys())}")
    print("-" * 20)

    for lang_id, repo_urls in TARGET_REPOS.items():
        process_language(lang_id, repo_urls)

    print("-" * 20)
    print("Download and extraction process (v2) completed.")
    print(f"You can find the extracted code in: {BASE_OUTPUT_DIR.resolve()}")
