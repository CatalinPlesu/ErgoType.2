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


class FitnessConfig:
    # distance based calculation config
    # use_words simulate typing select_top_n_words, it will type at once biggest n-gram it can
    use_words = True
    # use_symbols simulate pressing the rest of symbols not typed in a word, alternatively, only symbols when disabling words
    use_symbols = True
    # fluid_typing - personal assumption that is easier to tpye from outside keyboard inside if it is a n-gram
    # a -> f | j <- ;
    fluid_typing = False

    # wether to use finger_strength configs.
    # effort is simply added
    use_finger_effort = False
    # penalities are added with scaling depending distance related to 1
    use_x_penality = False
    use_y_penality = False
    use_z_penality = False

    distance_weight = 0.3
    # prefere tpyhing longre bygrams at once as oposed to shorter ones.
    n_gram_weight = 0.2
    # prefre typing on the home row
    homerow_weight = 0.3
    hand_distribution = 0.1
    finger_distribution = 0.1


class Config:
    dataset = DatasetConfig()
    processor = ProcessorConfig()
    fitness = FitnessConfig()
