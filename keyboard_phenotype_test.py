from keyboard_phenotype import KeyboardPhenotype
from kle.kle_model import Serial


with open('kle_keyboards/ansi_60_percent_hands.json', 'r') as f:
    keyboard = Serial.parse(f.read())

# remap_ro = {
#     "base": (list(zip(list("[];'\\"), list("{}:\"|"))), list(zip(list("ăîșțâ"), list("ĂÎȘȚÂ")))),
#     "altgr": list(zip(list("[];'\\"), list("{}:\"|")))
# }


keyboard = KeyboardPhenotype(keyboard, {})

keyboard.select_remap_keys(['q', 'e', 'r'])
keyboard.remap_to_keys(['q', 'w', 'e'])
