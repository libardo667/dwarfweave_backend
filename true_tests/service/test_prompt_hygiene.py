"""Generation prompts must stay world-agnostic — no baked-in genre vocab (item 09)."""

import pathlib

# Vocabulary that used to be hardcoded as "examples" in the world-gen prompt and
# quietly biased every generated world toward a cosmic/ethereal register.
FOSSIL_VOCAB = [
    "quantum_resonance", "void_attunement", "stellar_knowledge", "dimensional_stability",
    "weaving_skill", "reality_threads", "cosmic_reputation", "harmonic_mastery",
    "dream_essence", "spectral_connections", "planar_knowledge", "ethereal_power",
]


def test_no_fossil_world_vocab_in_generation_prompts():
    src = pathlib.Path(__file__).parents[2] / "src" / "services" / "llm_service.py"
    text = src.read_text(encoding="utf-8")
    leaked = [term for term in FOSSIL_VOCAB if term in text]
    assert not leaked, f"fossil genre vocab leaked back into the prompts: {leaked}"
