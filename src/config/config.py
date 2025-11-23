"""
Configuration file for keyboard layout optimization
"""

from src.core.keyboard import FingerName, Hand


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
    raw_dir = 'src/data/text/raw'
    processed_dir = 'src/data/text/processed'


class FitnessConfig:
    # Simplified evaluation parameters
    # Use simplified fitness function: fitness = weight1 * normalized_distance + weight2 * normalized_time
    use_simplified_fitness = True
    
    # Fitness component weights for simplified formula
    distance_weight = 0.5
    time_weight = 0.5
    
    # Finger strength parameters for time calculation
    # Base time constants for each finger (lower = faster)
    finger_time_base = {
        FingerName.LEFT_PINKY: 1.8,
        FingerName.LEFT_RING: 1.5,
        FingerName.LEFT_MIDDLE: 1.2,
        FingerName.LEFT_INDEX: 1.0,
        FingerName.LEFT_THUMB: 1.3,
        FingerName.RIGHT_INDEX: 1.0,
        FingerName.RIGHT_MIDDLE: 1.2,
        FingerName.RIGHT_RING: 1.5,
        FingerName.RIGHT_PINKY: 1.8,
        FingerName.RIGHT_THUMB: 1.3
    }
    
    # Parallel typing parameters
    parallel_typing_enabled = True  # Allow parallel finger movements
    synchronous_end = True  # Movements end synchronously for faster typing
    
    # 256-character window for distance simulation
    simulation_window_size = 256
    finger_state_persistence = True  # Finger state is kept within window
    
    # Fitts law parameters for time calculation (adjusted for 40 WPM = 200 chars/min)
    fitts_a = 0.05  # Fitts law intercept - reduced for faster typing
    fitts_b = 0.025  # Fitts law slope - reduced for faster typing
    
    # Distance-based calculation config (legacy)
    # use_words: simulate typing select_top_n_words, it will type at once biggest n-gram it can
    use_words = True
    # use_symbols: simulate pressing the rest of symbols not typed in a word, alternatively, only symbols when disabling words
    use_symbols = True
    # fluid_typing: personal assumption that is easier to type from outside keyboard inside if it is a n-gram
    # a -> f | j <- ; (alternating hands moving inward)
    fluid_typing = True

    # Whether to use finger_strength configs
    # effort is simply added
    use_finger_effort = False
    # penalties are added with scaling depending distance related to 1
    use_x_penality = False
    use_y_penality = False
    use_z_penality = False

    # Legacy fitness component weights
    legacy_distance_weight = 0.3
    # Prefer typing longer bigrams at once as opposed to shorter ones
    n_gram_weight = 0.2
    # Give higher score to higher ngrams: ngram_count * ngram_rank * bias
    n_gram_multiplier = 1.0
    # Prefer typing on the home row
    homerow_weight = 0.3
    hand_distribution = 0.1
    finger_distribution = 0.1


class GeneticAlgorithmConfig:
    """Genetic algorithm parameters"""
    # Population
    default_population_size = 50

    # Selection
    tournament_size = 3

    # Crossover
    offsprings_per_pair = 4
    crossover_bias_base = 0.75  # Bias towards better parent
    crossover_bias_increment = 1/30.0  # How much to increase bias per offspring

    # Mutation
    base_mutation_rate = 0.05
    stagnation_mutation_multiplier = 0.5  # Multiply mutation rate when stagnant
    max_mutation_swaps = 5  # Maximum number of swaps during stagnation

    # Termination
    default_max_iterations = 100
    default_stagnation_limit = 15


class KeyboardConfig:
    """Keyboard-specific configuration"""
    default_keyboard = 'src/data/keyboards/ansi_60_percent.json'

    available_keyboards = {
        'ansi_60': 'src/data/keyboards/ansi_60_percent.json',
        'ansi_60_thinkpad': 'src/data/keyboards/ansi_60_percent_thinkpad.json',
        'dactyl': 'src/data/keyboards/dactyl_manuform_6x6_4.json',
        'ferris': 'src/data/keyboards/ferris_sweep.json'
    }


class CacheConfig:
    """Cache configuration"""
    distance_cache_enabled = True
    fitness_cache_enabled = True


class Config:
    """Main configuration class"""
    dataset = DatasetConfig()
    processor = ProcessorConfig()
    fitness = FitnessConfig()
    ga = GeneticAlgorithmConfig()
    keyboard = KeyboardConfig()
    cache = CacheConfig()

    @classmethod
    def print_config(cls):
        """Print all configuration values"""
        print("="*80)
        print("CONFIGURATION")
        print("="*80)

        print("\nDataset Configuration:")
        for attr in dir(cls.dataset):
            if not attr.startswith('_') and not callable(getattr(cls.dataset, attr)):
                print(f"  {attr}: {getattr(cls.dataset, attr)}")

        print("\nProcessor Configuration:")
        for attr in dir(cls.processor):
            if not attr.startswith('_') and not callable(getattr(cls.processor, attr)):
                print(f"  {attr}: {getattr(cls.processor, attr)}")

        print("\nFitness Configuration:")
        for attr in dir(cls.fitness):
            if not attr.startswith('_') and not callable(getattr(cls.fitness, attr)):
                print(f"  {attr}: {getattr(cls.fitness, attr)}")

        print("\nGenetic Algorithm Configuration:")
        for attr in dir(cls.ga):
            if not attr.startswith('_') and not callable(getattr(cls.ga, attr)):
                print(f"  {attr}: {getattr(cls.ga, attr)}")

        print("\nKeyboard Configuration:")
        for attr in dir(cls.keyboard):
            if not attr.startswith('_') and not callable(getattr(cls.keyboard, attr)):
                value = getattr(cls.keyboard, attr)
                if isinstance(value, dict):
                    print(f"  {attr}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"  {attr}: {value}")

        print("\nCache Configuration:")
        for attr in dir(cls.cache):
            if not attr.startswith('_') and not callable(getattr(cls.cache, attr)):
                print(f"  {attr}: {getattr(cls.cache, attr)}")

        print("="*80)


if __name__ == "__main__":
    # Print configuration
    Config.print_config()
