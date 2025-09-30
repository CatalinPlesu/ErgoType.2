"""
Romanian Programmers layout (Windows variant)
Places diacritics on AltGr+letter combinations
"""

# Romanian Programmers layout configuration
ROMANIAN_PROGRAMMERS = {
    "name": "Romanian Programmers",
    "base_remaps": {},
    "altgr_remaps": {
        "a": ("ă", "Ă"),
        "i": ("î", "Î"),
        "s": ("ș", "Ș"),
        "t": ("ț", "Ț"),
        "q": ("â", "Â")
    },
    "altgr_recovery": {}
}

# Standalone function to get this layout
def get_layout():
    return ROMANIAN_PROGRAMMERS
