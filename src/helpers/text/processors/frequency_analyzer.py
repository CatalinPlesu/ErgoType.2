import os
import pickle
import json
import string
import re
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional
from src.config.config import (
    TOP_N_WORDS, MIN_WORD_LENGTH, TEXT_RAW_DIR, TEXT_PROCESSED_DIR,
    DATASET_CONFIGS, ALLOWED_DIGITS, ALLOWED_SYMBOLS
)


def is_valid_word(word: str, allowed_letters: str, min_length: int = MIN_WORD_LENGTH) -> bool:
    """Check if a word is valid (contains only letters and meets minimum length)"""
    if len(word) < min_length:
        return False

    # Word should contain only allowed letters
    return all(char in allowed_letters for char in word)


def extract_words_from_text(text: str, allowed_letters: str) -> List[str]:
    """Extract valid words from text using regex and validation"""
    # Create character class for regex from allowed letters
    # Escape special regex characters
    escaped_letters = re.escape(''.join(sorted(set(allowed_letters))))

    # Find sequences of allowed letters
    word_pattern = f'[{escaped_letters}]+'

    # Extract all letter sequences
    potential_words = re.findall(word_pattern, text, re.IGNORECASE)

    # Filter for valid words
    valid_words = []
    for word in potential_words:
        if is_valid_word(word, allowed_letters):
            valid_words.append(word.lower())  # Normalize to lowercase

    return valid_words


def calculate_remaining_character_pool_scaled(
    results: Dict[str, Any],
    top_n_words: int = TOP_N_WORDS
) -> Dict[str, Any]:
    """Calculate remaining character pool with proper scaling based on relative frequencies"""
    updated_results = {}

    for dataset_name, dataset_result in results.items():
        # Get the original character frequencies (relative and absolute)
        original_char_frequencies = dataset_result['character_frequencies']
        original_char_counter = Counter()
        for char, freq_data in original_char_frequencies.items():
            original_char_counter[char] = freq_data['absolute']

        # Get total original characters
        total_original_chars = dataset_result['stats']['total_characters']

        # Get top N words
        top_words = dataset_result['word_frequencies'][:top_n_words]

        # Calculate characters used in typing top N words
        characters_used = Counter()

        for word_data in top_words:
            word = word_data['word']
            word_count = word_data['absolute']

            for char in word:
                # Each character typed as many times as the word appears
                characters_used[char] += word_count

        # Calculate remaining pool by subtracting used characters from original
        remaining_pool = Counter()
        for char, original_count in original_char_counter.items():
            used_count = characters_used.get(char, 0)
            # Ensure non-negative
            remaining_count = max(0, original_count - used_count)
            if remaining_count > 0:
                remaining_pool[char] = remaining_count

        # Calculate remaining frequencies based on remaining total
        total_remaining_chars = sum(remaining_pool.values())
        remaining_char_frequencies = {}

        for char, count in remaining_pool.items():
            relative_freq = count / total_remaining_chars if total_remaining_chars > 0 else 0
            remaining_char_frequencies[char] = {
                'absolute': count,
                'relative': relative_freq,
                'percentage_of_remaining': relative_freq * 100
            }

        # Also calculate what percentage of original each remaining character represents
        original_percentage_remaining = {}
        for char, remaining_count in remaining_pool.items():
            original_count = original_char_counter[char]
            original_percentage = (
                remaining_count / original_count) * 100 if original_count > 0 else 0
            original_percentage_remaining[char] = original_percentage

        # Create updated result with remaining pool
        updated_dataset_result = dataset_result.copy()
        updated_dataset_result[f'{top_n_words}_remaining_characters_pool'] = {
            'remaining_pool': dict(remaining_pool),
            'remaining_frequencies': remaining_char_frequencies,
            'total_remaining_characters': total_remaining_chars,
            'characters_used_in_top_words': dict(characters_used),
            'original_total_characters': total_original_chars,
            'characters_subtracted': sum(characters_used.values()),
            'percentage_of_original_remaining': original_percentage_remaining,
            'top_words_used': [w['word'] for w in top_words],
            'top_words_absolute_counts': [w['absolute'] for w in top_words],
        }

        updated_results[dataset_name] = updated_dataset_result

    return updated_results


def process_text_datasets(
    root_dir: str = TEXT_RAW_DIR,
    output_dir: str = TEXT_PROCESSED_DIR,
    top_n_words: int = TOP_N_WORDS
) -> Dict[str, Any]:
    """Main processing function - analyzes character and word frequencies in datasets."""

    os.makedirs(output_dir, exist_ok=True)

    print("Starting dataset processing...")

    # Discover datasets
    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"Root directory does not exist: {root_dir}")

    datasets = [item for item in os.listdir(
        root_dir) if os.path.isdir(os.path.join(root_dir, item))]
    print(f"Found {len(datasets)} datasets: {datasets}")

    # Process each dataset
    results = {}
    for dataset_name in datasets:
        # Define character sets based on dataset
        allowed_letters = get_allowed_letters_for_dataset(dataset_name)
        allowed_digits = ALLOWED_DIGITS
        allowed_symbols = ALLOWED_SYMBOLS

        # Initialize counters
        char_counter = Counter()
        category_counters = {
            'letters': Counter(),
            'digits': Counter(),
            'symbols': Counter()
        }
        word_counter = Counter()

        total_chars = 0
        total_words = 0

        # Process all files in the dataset
        dataset_path = os.path.join(root_dir, dataset_name)

        # Walk through all files in the dataset directory
        for root, dirs, files in os.walk(dataset_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                        # Process characters (unchanged)
                        for char in content:
                            total_chars += 1

                            if char in allowed_letters:
                                char_counter[char] += 1
                                category_counters['letters'][char] += 1
                            elif char in allowed_digits:
                                char_counter[char] += 1
                                category_counters['digits'][char] += 1
                            elif char in allowed_symbols:
                                char_counter[char] += 1
                                category_counters['symbols'][char] += 1

                        # Extract valid words using improved method
                        valid_words = extract_words_from_text(
                            content, allowed_letters)

                        # Count words
                        for word in valid_words:
                            word_counter[word] += 1
                            total_words += 1

                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")

        # Calculate character frequencies (unchanged)
        char_frequencies = {}
        for char, count in char_counter.items():
            relative_freq = count / total_chars if total_chars > 0 else 0
            char_frequencies[char] = {
                'absolute': count,
                'relative': relative_freq,
                'percentage': relative_freq * 100
            }

        # Calculate category-specific frequencies (unchanged)
        category_frequencies = {}
        for category, counter in category_counters.items():
            category_frequencies[category] = {}
            category_total = sum(counter.values())
            for char, count in counter.items():
                relative_freq = count / category_total if category_total > 0 else 0
                category_frequencies[category][char] = {
                    'absolute': count,
                    'relative': relative_freq,
                    'category_relative': relative_freq
                }

        # Convert word counter to sorted list by frequency
        sorted_words = []
        for word, count in word_counter.most_common():
            relative_freq = count / total_words if total_words > 0 else 0
            sorted_words.append({
                'word': word,
                'absolute': count,
                'relative': relative_freq,
                'percentage': relative_freq * 100
            })

        # Prepare result for this dataset
        result = {
            'config': {
                'allowed_letters': allowed_letters,
                'allowed_digits': allowed_digits,
                'allowed_symbols': allowed_symbols,
                'min_word_length': MIN_WORD_LENGTH
            },
            'stats': {
                'total_characters': total_chars,
                'unique_characters': len(char_counter),
                'total_words': total_words,
                'unique_words': len(word_counter)
            },
            'character_frequencies': char_frequencies,
            'category_frequencies': category_frequencies,
            'word_frequencies': sorted_words
        }

        results[dataset_name] = result
        print(f"""Processed {dataset_name}: {total_chars} chars, {
              len(word_counter)} unique words""")

        # Show sample of top words for debugging
        print(f"  Top 10 words: {[w['word'] for w in sorted_words[:10]]}")

    # Calculate remaining character pool after typing top N words
    print(f"""\nCalculating remaining character pool for top {
          top_n_words} words...""")
    results_with_remaining_pool = calculate_remaining_character_pool_scaled(
        results, top_n_words)

    # Save single combined pickle file
    pickle_file = os.path.join(output_dir, 'frequency_analysis.pkl')
    with open(pickle_file, 'wb') as f:
        pickle.dump(results_with_remaining_pool, f)

    # Save individual JSON files for each dataset
    for dataset_name, dataset_data in results_with_remaining_pool.items():
        dataset_json_file = os.path.join(
            output_dir, f'{dataset_name}_analysis.json')
        with open(dataset_json_file, 'w', encoding='utf-8') as f:
            json.dump({dataset_name: dataset_data},
                      f, ensure_ascii=False, indent=2)

    # Also save combined JSON file
    json_file = os.path.join(output_dir, 'frequency_analysis.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results_with_remaining_pool, f, ensure_ascii=False, indent=2)

    print(f"\nProcessing complete. Results saved to:")
    print(f"  Single Pickle: {pickle_file}")
    print(f"  Combined JSON: {json_file}")
    print(f"  Individual JSON files saved for each dataset")

    return results_with_remaining_pool


def analyze_word_patterns(results: Dict[str, Any], dataset_name: str) -> None:
    """Analyze patterns in the word data for debugging"""
    if dataset_name not in results:
        print(f"Dataset {dataset_name} not found")
        return

    words = results[dataset_name]['word_frequencies']

    print(f"\nAnalysis for {dataset_name}:")
    print(f"Total unique words: {len(words)}")

    # Length distribution
    length_dist = Counter()
    for word_data in words:
        length_dist[len(word_data['word'])] += 1

    print("Word length distribution:")
    for length in sorted(length_dist.keys()):
        print(f"  Length {length}: {length_dist[length]} words")

    # Show words with unusual patterns
    suspicious_words = []
    for word_data in words[:50]:  # Check top 50
        word = word_data['word']
        if any(char.isdigit() for char in word) or len(word) == 1:
            suspicious_words.append(word)

    if suspicious_words:
        print(f"Suspicious words found: {suspicious_words}")
    else:
        print("No suspicious words in top 50")


def load_and_update_pickle(pickle_path: Optional[str] = None, top_n_words: int = TOP_N_WORDS) -> Optional[Dict[str, Any]]:
    """Load existing pickle file and update with remaining character pool"""
    if pickle_path is None:
        pickle_path = os.path.join(
            TEXT_PROCESSED_DIR, 'frequency_analysis.pkl')

    if not os.path.exists(pickle_path):
        print(f"ERROR: Pickle file does not exist: {pickle_path}")
        return None

    # Load existing results
    with open(pickle_path, 'rb') as f:
        results = pickle.load(f)

    print(f"Loaded existing results with {len(results)} datasets")

    # Update with remaining character pool
    print(f"""Calculating remaining character pool for top {
          top_n_words} words...""")
    updated_results = calculate_remaining_character_pool_scaled(
        results, top_n_words)

    # Save single updated pickle file
    output_dir = os.path.dirname(pickle_path)
    updated_pickle_file = os.path.join(
        output_dir, f'frequency_analysis_updated_top_{top_n_words}.pkl')
    with open(updated_pickle_file, 'wb') as f:
        pickle.dump(updated_results, f)

    # Save individual updated JSON files
    for dataset_name, dataset_data in updated_results.items():
        dataset_json_file = os.path.join(
            output_dir, f'{dataset_name}_analysis_updated.json')
        with open(dataset_json_file, 'w', encoding='utf-8') as f:
            json.dump({dataset_name: dataset_data},
                      f, ensure_ascii=False, indent=2)

    # Also save combined updated JSON file
    updated_json_file = os.path.join(
        output_dir, f'frequency_analysis_updated_top_{top_n_words}.json')
    with open(updated_json_file, 'w', encoding='utf-8') as f:
        json.dump(updated_results, f, ensure_ascii=False, indent=2)

    print(f"Updated results saved to:")
    print(f"  Single Pickle: {updated_pickle_file}")
    print(f"  Combined JSON: {updated_json_file}")
    print(f"  Individual updated JSON files saved for each dataset")

    return updated_results


def get_allowed_letters_for_dataset(dataset_name: str) -> str:
    """Get allowed letters for a specific dataset"""
    dataset_lower = dataset_name.lower()
    if dataset_lower in DATASET_CONFIGS:
        return DATASET_CONFIGS[dataset_lower]['allowed_letters']
    else:
        return DATASET_CONFIGS['default']['allowed_letters']
