"""Tests for database seeding functionality."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import Base
from src.models import Storylet
from src.services.seed_data import seed_if_empty

@pytest.mark.asyncio
class TestEmptyDatabaseSeeding:
    """Test suite for empty database seeding functionality (Task: seed-005)."""

    def setup_method(self):
        """Create a fresh in-memory database for each test."""
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",        # use the pysqlite driver explicitly
            echo=False,
            connect_args={"check_same_thread": False},  # allow cross-thread use
            poolclass=StaticPool,                       # single shared connection
        )

        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()

    def teardown_method(self):
        """Clean up after each test."""
        self.db.close()
        self.engine.dispose()

    async def test_seed_if_empty_adds_expected_storylets(self):
        initial_count = self.db.query(Storylet).count()
        assert initial_count == 0
        await seed_if_empty(self.db)
        final_count = self.db.query(Storylet).count()
        assert final_count == 7, f"Expected 7 storylets, but got {final_count}"

    async def test_seed_if_empty_does_not_seed_non_empty_database(self):
        existing_storylet = Storylet(
            title="Existing Storylet",
            text_template="This storylet already exists",
            requires={},
            choices=[{"label": "Continue", "set": {}}],
            weight=1.0
        )
        self.db.add(existing_storylet)
        self.db.commit()
        pre_seed_count = self.db.query(Storylet).count()
        assert pre_seed_count == 1
        await seed_if_empty(self.db)
        post_seed_count = self.db.query(Storylet).count()
        assert post_seed_count == 1, "seed_if_empty should not add storylets to non-empty database"

    async def test_seeded_storylets_have_correct_structure(self):
        await seed_if_empty(self.db)
        storylets = self.db.query(Storylet).all()
        assert len(storylets) == 7, "Should have 7 seeded storylets"
        for storylet in storylets:
            assert hasattr(storylet, 'title')
            assert hasattr(storylet, 'text_template')
            assert hasattr(storylet, 'requires')
            assert hasattr(storylet, 'choices')
            assert hasattr(storylet, 'weight')
            assert str(storylet.title).strip() != ""
            assert str(storylet.text_template).strip() != ""
            assert storylet.requires is not None
            assert storylet.choices is not None

    async def test_seeded_storylets_specific_content(self):
        await seed_if_empty(self.db)
        storylets = self.db.query(Storylet).all()
        storylet_titles = [str(s.title) for s in storylets]
        expected_titles = [
            "A Dark Cave",
            "Mysterious Stranger",
            "Abandoned Hut",
            "Hidden Treasure",
            "Glittering Vein",
            "Shaky Beam",
            "Where's My Pickaxe?"
        ]
        for expected_title in expected_titles:
            assert expected_title in storylet_titles, f"Expected storylet '{expected_title}' not found"

    async def test_seeded_storylets_requirements_and_choices(self):
        await seed_if_empty(self.db)
        dark_cave = self.db.query(Storylet).filter_by(title="A Dark Cave").first()
        assert dark_cave is not None
        assert isinstance(dark_cave.requires, dict)
        assert isinstance(dark_cave.choices, list)
        assert len(dark_cave.choices) >= 1
        glittering_vein = self.db.query(Storylet).filter_by(title="Glittering Vein").first()
        assert glittering_vein is not None
        assert isinstance(glittering_vein.requires, dict)
        assert isinstance(glittering_vein.choices, list)

    async def test_seed_multiple_calls_idempotent(self):
        await seed_if_empty(self.db)
        first_count = self.db.query(Storylet).count()
        assert first_count == 7
        await seed_if_empty(self.db)
        second_count = self.db.query(Storylet).count()
        assert second_count == 7, "Multiple calls to seed_if_empty should not add duplicate storylets"
        await seed_if_empty(self.db)
        third_count = self.db.query(Storylet).count()
        assert third_count == 7, "seed_if_empty should remain idempotent"

    async def test_seeded_storylets_database_persistence(self):
        await seed_if_empty(self.db)
        self.db.commit()
        self.db.close()
        new_session = self.SessionLocal()
        try:
            count = new_session.query(Storylet).count()
            assert count == 7, "Seeded storylets should persist after session close"
            storylet = new_session.query(Storylet).filter_by(title="Glittering Vein").first()
            assert storylet is not None
            assert storylet.text_template is not None
            assert isinstance(storylet.choices, list)
        finally:
            new_session.close()

    async def test_seed_with_transaction_rollback(self):
        self.db.begin()
        try:
            await seed_if_empty(self.db)
            count_in_transaction = self.db.query(Storylet).count()
            assert count_in_transaction == 7
            self.db.rollback()
            count_after_rollback = self.db.query(Storylet).count()
            assert count_after_rollback == 0, "Storylets should be rolled back"
        except Exception:
            self.db.rollback()
            raise

    async def test_storylet_choice_format_consistency(self):
        await seed_if_empty(self.db)
        storylets = self.db.query(Storylet).all()
        for storylet in storylets:
            choices = storylet.choices
            assert isinstance(choices, list), f"Choices for '{storylet.title}' should be a list"
            assert len(choices) > 0, f"Storylet '{storylet.title}' should have at least one choice"
            for choice in choices:
                assert isinstance(choice, dict), f"Each choice in '{storylet.title}' should be a dict"
                has_label = "label" in choice
                has_text = "text" in choice
                assert has_label or has_text, f"Choice in '{storylet.title}' missing label/text"
                has_set = "set" in choice
                has_set_vars = "set_vars" in choice
                assert has_set or has_set_vars, f"Choice in '{storylet.title}' missing set/set_vars"
