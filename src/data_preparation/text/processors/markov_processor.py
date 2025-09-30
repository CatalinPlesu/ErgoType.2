import os
from collections import Counter
import string
import unicodedata

class MarkovProcessor:
    def __init__(self, allowed_letters=None, allowed_digits=None, allowed_symbols=None):
        """
        Initialize the MarkovProcessor with customizable character sets.
        
        Args:
            allowed_letters: String of allowed letter characters (default: ASCII + Romanian)
            allowed_digits: String of allowed digit characters (default: 0-9)
            allowed_symbols: String of allowed symbol characters (default: punctuation + whitespace)
        """
        # Set defaults if not provided
        self.allowed_letters = allowed_letters or (string.ascii_letters + "ăâîșțĂÂÎȘȚ")
        self.allowed_digits = allowed_digits or string.digits
        self.allowed_symbols = allowed_symbols or (string.punctuation + " \t\n")
        
        # Build whitelist
        self.whitelist_chars = (
            self.allowed_letters + 
            self.allowed_digits + 
            self.allowed_symbols
        )
        self.whitelist_set = set(self.whitelist_chars)
        
        # Character categorization
        self.letter_set = set(self.allowed_letters)
        self.digit_set = set(self.allowed_digits)
        self.symbol_set = set(self.allowed_symbols)

    def filter_content(self, content):
        """Filter content to keep only whitelisted characters."""
        return ''.join(filter(self.whitelist_set.__contains__, content))

    def read_file_content(self, file_path):
        """Read file content as UTF-8, ignoring errors."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"  ERROR reading {file_path}: {e}")
            return ""

    def categorize_character(self, char):
        """Categorize a character as 'letter', 'digit', or 'symbol'."""
        if char in self.letter_set:
            return 'letter'
        elif char in self.digit_set:
            return 'digit'
        elif char in self.symbol_set:
            return 'symbol'
        else:
            return 'unknown'  # Shouldn't happen if whitelist is correct

    def build_markov_chain(self, content):
        """Build 2-level Markov chain dictionary from content."""
        char_counts = Counter()
        transitions = {}  # char -> { next_char: count }
        
        prev_char = None
        for char in content:
            char_counts[char] += 1
            
            if prev_char is not None:
                if prev_char not in transitions:
                    transitions[prev_char] = Counter()
                transitions[prev_char][char] += 1
            
            prev_char = char
        
        return char_counts, transitions

    def calculate_markov_model(self, char_counts, transitions):
        """Calculate Markov model with percentages."""
        total_chars = sum(char_counts.values())
        
        # Calculate category totals for relative percentages
        category_totals = {'letter': 0, 'digit': 0, 'symbol': 0, 'unknown': 0}
        for char in char_counts:
            category = self.categorize_character(char)
            category_totals[category] += char_counts[char]

        # Build final markov model
        markov_model = {}
        for char, count in char_counts.items():
            category = self.categorize_character(char)
            global_percentage = (count / total_chars) * 100 if total_chars > 0 else 0
            category_percentage = (count / category_totals[category]) * 100 if category_totals[category] > 0 else 0

            next_chars = {}
            if char in transitions:
                for next_char, next_count in transitions[char].items():
                    next_chars[next_char] = {
                        'count': next_count,
                        'percentage': round((next_count / count) * 100, 4) if count > 0 else 0
                    }

            markov_model[char] = {
                'count': count,
                'global_percentage': round(global_percentage, 4),
                'category_percentage': round(category_percentage, 4),
                'category': category,
                'next': next_chars
            }
        
        return markov_model

    def process_file(self, file_path):
        """Process a single file and return its content."""
        content = self.read_file_content(file_path)
        filtered_content = self.filter_content(content)
        return filtered_content

    def process_dataset(self, dataset_path, dataset_name):
        """Process dataset and build Markov chain."""
        print(f"\nProcessing dataset: {dataset_name}")

        all_content = []
        file_count = 0

        # Process files
        for root, dirs, files in os.walk(dataset_path):
            for file in files:
                file_path = os.path.join(root, file)
                content = self.process_file(file_path)
                
                if content:
                    all_content.append(content)
                    file_count += 1

                    if file_count % 100 == 0:
                        print(f"    Progress: {file_count} files processed")

        # Combine all content
        combined_content = ''.join(all_content)
        
        # Build Markov chain
        char_counts, transitions = self.build_markov_chain(combined_content)
        markov_model = self.calculate_markov_model(char_counts, transitions)

        # Prepare result with character configuration info
        result = {
            'markov_chain': markov_model,
            'config': {
                'allowed_letters': self.allowed_letters,
                'allowed_digits': self.allowed_digits,
                'allowed_symbols': self.allowed_symbols,
                'total_whitelist_chars': len(self.whitelist_set)
            },
            'stats': {
                'file_count': file_count,
                'total_characters': len(combined_content),
                'unique_characters': len(char_counts),
                'dataset_name': dataset_name
            }
        }

        return result