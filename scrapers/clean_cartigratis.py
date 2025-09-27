import os
import shutil


def remove_cid_lines(root_dir, backup=True):
    """Remove any lines containing (cid: patterns from text files"""

    if backup:
        backup_dir = root_dir + '_backup'
        if not os.path.exists(backup_dir):
            print(f"Creating backup at {backup_dir}")
            shutil.copytree(root_dir, backup_dir)
        else:
            print(f"Backup already exists at {backup_dir}")

    files_processed = 0
    lines_removed = 0

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                try:
                    # Read all lines
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()

                    # Filter out lines containing (cid:
                    clean_lines = []
                    removed_count = 0

                    for line in lines:
                        if '(cid:' in line:
                            removed_count += 1
                        else:
                            clean_lines.append(line)

                    # Write back only if changes were made
                    if removed_count > 0:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.writelines(clean_lines)

                        files_processed += 1
                        lines_removed += removed_count
                        print(f"Removed {removed_count} lines from {file}")

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    print(f"\nCleaning complete:")
    print(f"Files processed: {files_processed}")
    print(f"Lines removed: {lines_removed}")


def main():
    """Clean CID patterns from Romanian dataset"""

    # Adjust this path to your dataset
    data_dir = './data/cartigratis'  # Change this to your actual path

    if not os.path.exists(data_dir):
        print(f"Directory not found: {data_dir}")
        print("Please adjust the data_dir path")
        return

    print(f"Removing lines with (cid: patterns from {data_dir}")
    remove_cid_lines(data_dir)

    print("\nDone! You can now re-run your word frequency analysis.")


if __name__ == "__main__":
    main()
