"""Canonical requirement evaluation — the single source of truth for how a
storylet's ``requires`` dict is interpreted against a flat variables mapping.

Semantics (item 01, decided 2026-05-27):

* bare value  -> equality:      ``{"danger": 2}``            means ``danger == 2``
* dict value  -> explicit ops:  ``{"danger": {"gte": 2}}``   means ``danger >= 2``

Supported operators: ``gte``, ``gt``, ``lte``, ``lt``, ``eq``, ``ne``. A bare
scalar NEVER means ">="; thresholds must be written explicitly. Both
``game_logic.meets_requirements`` and ``state_manager.evaluate_condition`` defer
to this module so the two storylet-selection paths agree.
"""

from typing import Any, Dict


def check_scalar(value: Any, requirement: Any) -> bool:
    """Evaluate one requirement against one variable's current value.

    A dict requirement is a set of comparison operators; any other value is an
    equality check.
    """
    if isinstance(requirement, dict):
        for op, target in requirement.items():
            if op == 'gte' and not (value is not None and value >= target):
                return False
            if op == 'gt' and not (value is not None and value > target):
                return False
            if op == 'lte' and not (value is not None and value <= target):
                return False
            if op == 'lt' and not (value is not None and value < target):
                return False
            if op == 'eq' and not (value == target):
                return False
            if op == 'ne' and not (value != target):
                return False
        return True
    return value == requirement


def evaluate_requirements(variables: Dict[str, Any], requirements: Dict[str, Any]) -> bool:
    """True iff every requirement is satisfied by ``variables`` (bare = equality)."""
    for key, requirement in (requirements or {}).items():
        if not check_scalar(variables.get(key), requirement):
            return False
    return True
