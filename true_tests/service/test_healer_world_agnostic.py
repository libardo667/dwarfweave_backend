"""The story healer must be world-agnostic — no hardcoded fictional worlds (item 03).

story_smoother used to carry three baked-in worlds (a cyberpunk-dwarf travel-phrase
table, themed variable storylets, and a clinical location list it *invented* during
spatial repair). Healing should connect whatever world it is given, never import one.
"""

import pathlib

FOSSIL_NAMES = [
    "Clan Hall", "Neon Caverns", "Corporate Stronghold", "Old Clan Library", "Rusted Halls",
    "Diagnostic Laboratory", "Stability Core", "Insight Archive", "Testing Grounds",
    "Protocol Chamber", "quantum_weaving_skill", "corp_reputation", "underground_contacts",
]


def test_no_hardcoded_worlds_in_smoother():
    src = pathlib.Path(__file__).parents[2] / "src" / "services" / "story_smoother.py"
    text = src.read_text(encoding="utf-8")
    leaked = [name for name in FOSSIL_NAMES if name in text]
    assert not leaked, f"hardcoded fictional-world names remain in the healer: {leaked}"
