from keyboard_phenotype import KeyboardPhenotype
from kle.kle_model import Serial, FingerName


with open('kle_keyboards/ansi_60_percent_hands.json', 'r') as f:
    keyboard = Serial.parse(f.read())

# remap_ro = {
#     "base": (list(zip(list("[];'\\"), list("{}:\"|"))), list(zip(list("ăîșțâ"), list("ĂÎȘȚÂ")))),
#     "altgr": list(zip(list("[];'\\"), list("{}:\"|")))
# }

# print(keyboard.get_homing_key_for_finger_name(FingerName.LEFT_THUMB))

keyboard = KeyboardPhenotype(keyboard, {})

keyboard.select_remap_keys(['q', 'e', 'r'])
keyboard.remap_to_keys(['q', 'e', 'r'])

import pickle
import os

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

# print(data['simple_wikipedia'])

keyboard.fitness(data['simple_wikipedia'])
# keyboard.fitness(data['cartigratis'])
