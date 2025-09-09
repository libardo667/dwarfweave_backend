"""Database seeding functionality."""

from typing import List
from sqlalchemy.orm import Session

from ..models import Storylet


import asyncio

async def seed_if_empty(db: Session) -> None:
    """Seed the database with initial storylets if empty. Async version."""
    def _seed():
        if db.query(Storylet).count() > 0:
            return
        seeds: List[Storylet] = [
            Storylet(
                title="A Dark Cave",
                text_template="You find yourself at the entrance of a dark cave. The air is damp and you can hear faint sounds from within.",
                requires={"location": "forest", "has_torch": True},
                choices=[
                    {"text": "Enter the cave", "set_vars": {"location": "cave_entrance"}},
                    {"text": "Go back to the forest", "set_vars": {"location": "forest"}}
                ],
                weight=1.0
            ),
            Storylet(
                title="Mysterious Stranger",
                text_template="A mysterious stranger approaches you in the market. They seem to be in a hurry and glance around nervously.",
                requires={"location": "market"},
                choices=[
                    {"text": "Talk to the stranger", "set_vars": {"met_stranger": True}},
                    {"text": "Ignore and walk away", "set_vars": {}}
                ],
                weight=1.0
            ),
            Storylet(
                title="Abandoned Hut",
                text_template="You stumble upon an abandoned hut. It looks old and worn, but there might be something useful inside.",
                requires={"location": "forest"},
                choices=[
                    {"text": "Enter the hut", "set_vars": {"location": "hut_interior"}},
                    {"text": "Continue through the forest", "set_vars": {"location": "deep_forest"}}
                ],
                weight=1.0
            ),
            Storylet(
                title="Hidden Treasure",
                text_template="You discover a hidden treasure chest buried under some leaves. It looks ancient and valuable.",
                requires={"location": "cave_entrance", "has_key": True},
                choices=[
                    {"text": "Open the chest", "set_vars": {"found_treasure": True}},
                    {"text": "Leave it alone", "set_vars": {}}
                ],
                weight=1.0
            ),
            Storylet(
                title="Glittering Vein",
                text_template="⛏️ {name} spots a glittering vein in the rock. Danger: {danger}. The air smells like iron.",
                requires={"danger": {"lte": 1}},
                choices=[
                    {"label": "Chip at the vein", "set": {"ore": {"inc": 1}, "danger": {"inc": 1}}},
                    {"label": "Mark it for later", "set": {"notes": "Marked a vein", "danger": {"inc": 0}}},
                ],
                weight=2.0,
            ),
            Storylet(
                title="Shaky Beam",
                text_template="🪵 A support beam groans. {name} freezes. Danger: {danger}.",
                requires={"danger": {"gte": 1}},
                choices=[
                    {"label": "Brace the beam", "set": {"danger": {"dec": 1}}},
                    {"label": "Sprint past",    "set": {"danger": {"inc": 1}}},
                ],
                weight=1.5,
            ),
            Storylet(
                title="Where's My Pickaxe?",
                text_template="🔍 {name} pats their belt. No pickaxe! Danger: {danger}.",
                requires={"has_pickaxe": False},
                choices=[
                    {"label": "Search tool rack", "set": {"has_pickaxe": True}},
                    {"label": "Improvise with a rock", "set": {"danger": {"inc": 1}}},
                ],
                weight=1.0,
            ),
        ]
        db.add_all(seeds)
        db.commit()
    await asyncio.to_thread(_seed)
