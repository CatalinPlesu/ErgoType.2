TOP_N_WORDS = 2000

# Configuration for text processing module
# Processing parameters
TOP_N_WORDS = 1000
MIN_WORD_LENGTH = 1

# Directory paths
TEXT_RAW_DIR = '../src/data/text/raw'
TEXT_PROCESSED_DIR = '../src/data/text/processed'

# Dataset-specific configurations
DATASET_CONFIGS = {
    'cartigratis': {
        'allowed_letters': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZăâîșțĂÂÎȘȚ'
    },
    'default': {
        'allowed_letters': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    }
}

# Character sets
ALLOWED_DIGITS = '0123456789'
ALLOWED_SYMBOLS = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n'
