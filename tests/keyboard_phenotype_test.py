import os
import pickle
import time
from src.domain.keyboard_phenotype import KeyboardPhenotype
from src.domain.keyboard import Serial
from src.domain.hand_finger_enum import *
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA


with open('src/data/keyboards/ansi_60_percent_hands.json', 'r') as f:
    keyboard = Serial.parse(f.read())

keyboard_phenotype = KeyboardPhenotype(keyboard, {})

keyboard_phenotype.select_remap_keys(LAYOUT_DATA['qwerty'])
keyboard_phenotype.remap_to_keys(LAYOUT_DATA['asset'])

with open('src/data/text/processed/frequency_analysis.pkl', 'rb') as f:
    frequency_data = pickle.load(f)

# Time the fitness function
print("Timing fitness function with frequency data...")
start_time = time.time()
fitness_score = keyboard_phenotype.fitness(frequency_data['simple_wikipedia'])
end_time = time.time()
fitness_freq_time = end_time - start_time
print(f"Fitness function (frequency data) took: {fitness_freq_time:.4f} seconds")
print(f"Fitness score: {fitness_score}")

keyboard_phenotype.get_phisical_keyboard()

print(f"\nCompleted fitness calculation in {fitness_freq_time:.4f} seconds")
