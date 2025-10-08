"""
    This class will be responsible for handling the simulation logic, of typing words and symbols
Stateful Simulation: Tracks finger positions across key presses, resetting Shift key positions after each n-gram.
Parallel Typing: Handles simultaneous key presses (e.g., Shift + 'a' for 'A') by including Shift in the key sequence for uppercase characters.
N-gram Support: Uses unigrams, bigrams, or higher-order n-grams to optimize cost calculations, weighted by frequency.
Efficiency: Supports random sampling of words to reduce computation time for large datasets.
Extensibility: Can incorporate additional cost factors (e.g., finger effort, alternation penalties) by modifying _simulate_word.
"""


class Typer:
    def __init__(self, keyboard, layout, dataset, debug=False):
        self.debug = debug
        self._print("Typer initiated")
        self.keyboard = keyboard
        self.layout = layout
        self.dataset = dataset
        self.fitness()

    def fitness(words=True, symbols=True):
        pass

    def _print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)


if __name__ == "__main__":
    pass
