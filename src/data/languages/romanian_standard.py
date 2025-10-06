"""
Romanian Standard layout (SR 13392:2004)
Places Romanian diacritics on punctuation keys
"""

# Romanian Standard layout configuration
ROMANIAN_STANDARD = {
    "name": "Romanian Standard",
    "base_remaps": {
        "[": ("ă", "Ă"),
        "]": ("î", "Î"),
        ";": ("ș", "Ș"),
        "\\": ("ț", "Ț"),
        "'": ("â", "Â")
    },
    "altgr_remaps": {
        "[": ("[", "{"),
        "]": ("]", "}"),
        ";": (";", ":"),
        "\\": ("\\", "|"),
        "'": ("'", "\"")
    },
}


def get_layout():
    return ROMANIAN_STANDARD
