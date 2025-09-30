import os
import pickle
import time
from keyboard_phenotype import KeyboardPhenotype
from src.domain.keyboard import Serial
from src.domain.hand_finger_enum import *
from keyboard_genotypes import LAYOUT_DATA


with open('kle_keyboards/ansi_60_percent_hands.json', 'r') as f:
    keyboard = Serial.parse(f.read())

keyboard = KeyboardPhenotype(keyboard, {})

keyboard.select_remap_keys(LAYOUT_DATA['qwerty'])
keyboard.remap_to_keys(LAYOUT_DATA['asset'])

try:
    data_file = './processed/markov_chains.pkl'
    if not os.path.exists(data_file):
        print(f"ERROR: Data file not found: {data_file}")
        data = {}
    else:
        with open(data_file, 'rb') as f:
            data = pickle.load(f)
        print(f"✅ Successfully loaded data from {data_file}")
except Exception as e:
    print(f"ERROR loading data: {e}")
    data = {}

# Load frequency data
with open('./processed/frequency_analysis.pkl', 'rb') as f:
    frequency_data = pickle.load(f)

# Time the first fitness function
print("Timing fitness function with markov chains...")
start_time = time.time()
keyboard.fitness(data['simple_wikipedia'], depth=3)
end_time = time.time()
fitness_time = end_time - start_time
print(f"Fitness function (markov chains) took: {fitness_time:.4f} seconds")

# Time the second fitness function
print("Timing fitness function with frequency data...")
start_time = time.time()
keyboard.fitness_with_frequency_data(frequency_data['simple_wikipedia'])
end_time = time.time()
fitness_freq_time = end_time - start_time
print(f"""Fitness function (frequency data) took: {
      fitness_freq_time:.4f} seconds""")

keyboard.get_phisical_keyboard()

# Optional: Compare the times
print(f"\nComparison:")
print(f"Markov chains fitness: {fitness_time:.4f} seconds")
print(f"Frequency data fitness: {fitness_freq_time:.4f} seconds")
print(f"Difference: {abs(fitness_time - fitness_freq_time):.4f} seconds")
