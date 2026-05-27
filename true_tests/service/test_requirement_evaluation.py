"""Canonical requirement-evaluation semantics (item 01).

Contract: a bare value means equality; thresholds must be explicit operators.
Both the plain evaluator and the state manager must honor this.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.services.conditions import evaluate_requirements, check_scalar
from src.services.game_logic import meets_requirements
from src.services.state_manager import AdvancedStateManager


# --- canonical evaluator ---

def test_bare_value_is_equality():
    assert evaluate_requirements({"danger": 2}, {"danger": 2})
    assert not evaluate_requirements({"danger": 5}, {"danger": 2})   # 5 != 2
    assert not evaluate_requirements({"danger": 1}, {"danger": 2})


def test_bare_bool_and_string_equality():
    assert evaluate_requirements({"has_pickaxe": True}, {"has_pickaxe": True})
    assert not evaluate_requirements({"has_pickaxe": False}, {"has_pickaxe": True})
    assert evaluate_requirements({"location": "cave"}, {"location": "cave"})
    assert not evaluate_requirements({"location": "tavern"}, {"location": "cave"})


def test_explicit_operators():
    assert evaluate_requirements({"danger": 5}, {"danger": {"gte": 2}})
    assert not evaluate_requirements({"danger": 1}, {"danger": {"gte": 2}})
    assert evaluate_requirements({"gold": 1}, {"gold": {"lte": 3}})
    assert evaluate_requirements({"x": 2}, {"x": {"eq": 2}})
    assert evaluate_requirements({"x": 3}, {"x": {"ne": 2}})


def test_missing_var_and_empty_requirements():
    assert not evaluate_requirements({}, {"danger": 2})
    assert evaluate_requirements({}, {})  # no requirements -> trivially true


def test_check_scalar_directly():
    assert check_scalar(2, 2)
    assert not check_scalar(5, 2)
    assert check_scalar(5, {"gte": 2})


# --- meets_requirements is a shim with identical semantics ---

def test_meets_requirements_matches_canonical():
    assert meets_requirements({"danger": 2}, {"danger": 2})
    assert not meets_requirements({"danger": 5}, {"danger": 2})
    assert meets_requirements({"danger": 5}, {"danger": {"gte": 2}})


# --- state manager honors the same bare-value-equality rule (this is the fix) ---

def test_state_manager_bare_value_is_equality_not_gte():
    sm = AdvancedStateManager("t")
    sm.set_variable("danger", 5)
    # Bare {"danger": 2} means == 2, so danger=5 must NOT satisfy it.
    assert not sm.evaluate_condition({"danger": 2})
    sm.set_variable("danger", 2)
    assert sm.evaluate_condition({"danger": 2})


def test_state_manager_explicit_operator_still_works():
    sm = AdvancedStateManager("t")
    sm.set_variable("danger", 5)
    assert sm.evaluate_condition({"danger": {"gte": 2}})
    assert not sm.evaluate_condition({"danger": {"lte": 2}})


def test_state_manager_location_flexible_keywords_preserved():
    sm = AdvancedStateManager("t")
    sm.set_variable("location", "wherever")
    assert sm.evaluate_condition({"location": "any_realm"})
    sm.set_variable("location", "start")
    assert sm.evaluate_condition({"location": "in_vessel"})
