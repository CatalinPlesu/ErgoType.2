class DatasetConfig:
    # ROOT LEVEL FIELDS (top-level keys in JSON)
    field_config = 'config'
    # CONFIG LEVEL FIELDS (under 'config' key)
    field_config_allowed_letters = 'allowed_letters'
    field_config_allowed_digits = 'allowed_digits'
    field_config_allowed_symbols = 'allowed_symbols'
    field_config_min_word_length = 'min_word_length'

    field_stats = 'stats'
    # STATS LEVEL FIELDS (under 'stats' key)
    field_stats_total_characters = 'total_characters'
    field_stats_unique_characters = 'unique_characters'
    field_stats_total_words = 'total_words'
    field_stats_unique_words = 'unique_words'

    field_character_frequencies = 'character_frequencies'
    # CHARACTER FREQUENCIES LEVEL FIELDS (under 'character_frequencies' key)
    field_character_frequencies_absolute = 'absolute'
    field_character_frequencies_relative = 'relative'

    field_category_frequencies = 'category_frequencies'
    # CATEGORY FREQUENCIES LEVEL FIELDS (under 'category_frequencies' categories)
    field_category_frequencies_absolute = 'absolute'
    field_category_frequencies_relative = 'relative'

    field_word_frequencies = 'word_frequencies'
    # WORD FREQUENCIES LEVEL FIELDS (under 'word_frequencies' list items)
    field_word_frequencies_word = 'word'
    field_word_frequencies_absolute = 'absolute'
    field_word_frequencies_relative = 'relative'

    field_remaining_pool = 'remaining_pool'
    # REMAINING POOL LEVEL FIELDS (under 'remaining_pool' key)
    field_remaining_pool_remaining_frequencies = 'remaining_frequencies'
    field_remaining_pool_percentage_of_original_remaining = 'percentage_of_original_remaining'

    # Processing parameters
    select_top_n_words = 3000
    min_word_length = 1

    # Character sets
    allowed_digits = '0123456789'
    allowed_symbols = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n'

    # File naming patterns
    main_pickle_filename = 'frequency_analysis.pkl'
    dataset_json_pattern = '_analysis.json'

    # Regex patterns
    word_pattern_template = '[{letters}]+'

    # Dataset-specific configurations
    datasets = {
        'cartigratis': {
            'allowed_letters': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZăâîșțĂÂÎȘȚ'
        },
        'default': {
            'allowed_letters': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'allowed_digits': '0123456789',
            'allowed_symbols': '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n'
        }
    }

    # Category names
    character_categories = ['letters', 'digits', 'symbols']

    @classmethod
    def get_allowed_letters(cls, dataset_name: str) -> str:
        dataset_lower = dataset_name.lower()
        dataset_config = cls.datasets.get(
            dataset_lower, cls.datasets['default'])
        return dataset_config.get('allowed_letters', cls.datasets['default']['allowed_letters'])

    @classmethod
    def get_allowed_digits(cls, dataset_name: str) -> str:
        dataset_lower = dataset_name.lower()
        dataset_config = cls.datasets.get(
            dataset_lower, cls.datasets['default'])
        return dataset_config.get('allowed_digits', cls.datasets['default']['allowed_digits'])

    @classmethod
    def get_allowed_symbols(cls, dataset_name: str) -> str:
        dataset_lower = dataset_name.lower()
        dataset_config = cls.datasets.get(
            dataset_lower, cls.datasets['default'])
        return dataset_config.get('allowed_symbols', cls.datasets['default']['allowed_symbols'])


class ProcessorConfig:
    # Directory paths
    raw_dir = '../src/data/text/raw'
    processed_dir = '../src/data/text/processed'


class Config:
    dataset = DatasetConfig()
    processor = ProcessorConfig()
