#!/bin/bash

uv run python scrapers/get_100_cartigratis.py
uv run python scrapers/get_top_100_gutenberg_books.py
uv run python scrapers/newsgroup_20.py
uv run python scrapers/the_algorithms.py
uv run python scrapers/wikipedia_simple_english.py
