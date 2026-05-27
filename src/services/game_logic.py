"""Core game logic and utilities."""

import random
from typing import Any, Dict, List, Optional, cast
from sqlalchemy.orm import Session

from ..models import Storylet


class SafeDict(dict):
    """Dictionary that returns placeholder for missing keys in template rendering."""
    def __missing__(self, key):
        return '{' + key + '}'


def render(template: str, vars: Dict[str, Any]) -> str:
    """Render a template string with variables, handling missing keys gracefully."""
    return template.format_map(SafeDict(vars))


def meets_requirements(vars: Dict[str, Any], req: Dict[str, Any]) -> bool:
    """Deprecated shim -> delegates to the canonical evaluator in `conditions`.

    Retained for callers using this name; remove once
    `conditions.evaluate_requirements` is used directly everywhere (item 01).
    """
    from .conditions import evaluate_requirements
    return evaluate_requirements(vars, req)


def pick_storylet(db: Session, vars: Dict[str, Any]) -> Optional[Storylet]:
    """Pick a random storylet based on requirements and weights."""
    all_rows = db.query(Storylet).all()
    eligible = [s for s in all_rows if meets_requirements(vars, cast(Dict[str, Any], s.requires or {}))]
    
    # If we have very few eligible storylets, try to generate some new ones
    if len(eligible) < 3:
        try:
            from ..services.llm_service import generate_contextual_storylets
            new_storylets_data = generate_contextual_storylets(vars, n=5)
            
            # Add new storylets to database
            storylets_added = 0
            for storylet_data in new_storylets_data:
                new_storylet = Storylet(
                    title=storylet_data.get("title", "Generated Story"),
                    text_template=storylet_data.get("text_template", "Something happens..."),
                    requires=storylet_data.get("requires", {}),
                    choices=storylet_data.get("choices", []),
                    weight=storylet_data.get("weight", 1.0)
                )
                db.add(new_storylet)
                storylets_added += 1
            
            # Commit and refresh our query
            db.commit()
            
            # Auto-improve storylets if we added a significant number
            if storylets_added >= 3:
                try:
                    from ..services.auto_improvement import auto_improve_storylets
                    auto_improve_storylets(
                        db=db,
                        trigger=f"contextual-generation ({storylets_added} storylets)",
                        run_smoothing=True,
                        run_deepening=True
                    )
                    print(f"🤖 Auto-improved storylets after adding {storylets_added} contextual storylets")
                except Exception as improve_error:
                    print(f"⚠️  Auto-improvement failed: {improve_error}")
            
            all_rows = db.query(Storylet).all()
            eligible = [s for s in all_rows if meets_requirements(vars, cast(Dict[str, Any], s.requires or {}))]
            
        except Exception as e:
            # Log the error but continue with existing storylets
            print(f"Error generating new storylets: {e}")
    
    if not eligible:
        return None
    weights = [max(0.0, cast(float, s.weight or 0.0)) for s in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]


def apply_choice_set(vars: Dict[str, Any], set_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply choice effects to variables.
    
    Supports:
        - direct assignment: {'has_pickaxe': True, "notes": "Msg"}
        - numeric inc/dec: {'ore': {'inc': 1}, 'danger': {'dec': 1}}
    """
    out = dict(vars)
    for key, val in (set_obj or {}).items():
        if isinstance(val, dict) and ("inc" in val or 'dec' in val):
            curr = out.get(key, 0)
            out[key] = curr + int(val.get("inc", 0)) - int(val.get('dec', 0))
        else:
            out[key] = val
    return out


def auto_populate_storylets(db: Session, target_count: int = 20) -> int:
    """
    Automatically populate the database with AI-generated storylets if below target.
    
    Returns:
        Number of storylets added
    """
    current_count = db.query(Storylet).count()
    if current_count >= target_count:
        return 0
    
    try:
        from ..services.llm_service import llm_suggest_storylets
        
        # Generate storylets with better thematic and logical coherence
        themes_sets = [
            # Exploration and Discovery
            {
                "themes": ["exploration", "discovery", "mystery"],
                "bible": {
                    "setting": "cave_system",
                    "focus": "finding_new_areas",
                    "variables": ["danger", "location", "has_pickaxe", "ore"]
                }
            },
            # Danger and Survival
            {
                "themes": ["danger", "survival", "escape"],
                "bible": {
                    "setting": "dangerous_situations", 
                    "focus": "managing_threats",
                    "variables": ["danger", "health", "location"]
                }
            },
            # Resource Management
            {
                "themes": ["resource_management", "crafting", "preparation"],
                "bible": {
                    "setting": "strategic_planning",
                    "focus": "gathering_resources", 
                    "variables": ["ore", "food", "has_pickaxe", "gold"]
                }
            },
            # Social and Story
            {
                "themes": ["social", "encounter", "story_development"],
                "bible": {
                    "setting": "character_interactions",
                    "focus": "narrative_progression",
                    "variables": ["reputation", "location", "met_stranger"]
                }
            },
            # Puzzle and Challenge
            {
                "themes": ["puzzle", "challenge", "skill"],
                "bible": {
                    "setting": "problem_solving",
                    "focus": "overcoming_obstacles",
                    "variables": ["danger", "has_pickaxe", "location"]
                }
            }
        ]
        
        added_count = 0
        for theme_set in themes_sets:
            if current_count + added_count >= target_count:
                break
                
            new_storylets = llm_suggest_storylets(
                3, 
                theme_set["themes"], 
                theme_set["bible"]
            )
            
            for storylet_data in new_storylets:
                if current_count + added_count >= target_count:
                    break
                    
                new_storylet = Storylet(
                    title=storylet_data.get("title", "Generated Story"),
                    text_template=storylet_data.get("text_template", "Something happens..."),
                    requires=storylet_data.get("requires", {}),
                    choices=storylet_data.get("choices", []),
                    weight=storylet_data.get("weight", 1.0)
                )
                db.add(new_storylet)
                added_count += 1
        
        db.commit()
        
        # Auto-improve storylets if we added a significant number
        if added_count >= 3:
            try:
                from ..services.auto_improvement import auto_improve_storylets
                auto_improve_storylets(
                    db=db,
                    trigger=f"auto-populate ({added_count} storylets)",
                    run_smoothing=True,
                    run_deepening=True
                )
                print(f"🤖 Auto-improved storylets after populating {added_count} storylets")
            except Exception as improve_error:
                print(f"⚠️  Auto-improvement failed: {improve_error}")
        
        return added_count
        
    except Exception as e:
        print(f"Error auto-populating storylets: {e}")
        return 0
