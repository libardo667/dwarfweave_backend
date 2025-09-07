"""LLM integration service for generating storylets."""

import os
import json
from typing import Any, Dict, List


def generate_contextual_storylets(current_vars: Dict[str, Any], n: int = 3) -> List[Dict[str, Any]]:
    """
    Generate storylets that are contextually relevant to the current game state.
    
    Args:
        current_vars: Current game variables/state
        n: Number of storylets to generate
        
    Returns:
        List of contextually relevant storylet dictionaries
    """
    # Extract context from current variables
    themes = []
    location = current_vars.get("location", "unknown")
    danger_level = current_vars.get("danger", 0)
    
    # Determine themes based on current state
    if danger_level > 2:
        themes.extend(["danger", "survival", "tension", "escape"])
    elif danger_level < 1:
        themes.extend(["exploration", "discovery", "mystery", "preparation"])
    else:
        themes.extend(["adventure", "decision", "progress", "challenge"])
    
    # Add location-based themes and logical connections
    location_str = str(location).lower()
    if "cave" in location_str or "underground" in location_str:
        themes.extend(["underground", "darkness", "minerals", "depths"])
    elif "forest" in location_str:
        themes.extend(["nature", "wildlife", "hidden_paths", "surface"])
    elif "market" in location_str:
        themes.extend(["social", "trade", "information", "civilization"])
    
    # Build a comprehensive contextual bible with story continuity
    bible = {
        "current_state": current_vars,
        "story_continuity": {
            "location": location,
            "danger_level": danger_level,
            "previous_actions": "Consider the player's current situation",
            "logical_progression": True
        },
        "connection_rules": {
            "location_transitions": {
                "cave_entrance": ["deeper_cave", "surface", "hidden_passage"],
                "deep_cave": ["cavern", "underground_river", "crystal_chamber"],
                "forest": ["cave_entrance", "clearing", "deep_forest"],
                "market": ["forest", "inn", "guild_hall"]
            },
            "danger_progression": {
                "low": "Introduce new challenges or discoveries",
                "medium": "Present meaningful choices with clear consequences", 
                "high": "Focus on survival and risk mitigation"
            }
        },
        "required_variables": list(current_vars.keys()),
        "story_coherence": {
            "maintain_established_facts": True,
            "logical_cause_and_effect": True,
            "progressive_difficulty": True
        }
    }
    
    return llm_suggest_storylets(n, themes, bible)


def llm_suggest_storylets(n: int, themes: List[str], bible: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate storylets using LLM with enhanced context awareness.
    
    Args:
        n: Number of storylets to generate
        themes: List of themes to incorporate
        bible: Dictionary of world/setting constraints and feedback
        
    Returns:
        List of storylet dictionaries
    """
    if not os.getenv("OPENAI_API_KEY"):
        # Fallback storylets when no API key is available
        base = [
            {
                "title": "Creak in the Dark",
                "text_template": "👂 {name} hears a faint creak behind the support beam. Danger: {danger}.",
                "requires": {"danger": {"lte": 1}},
                "choices": [
                    {"label": "Probe with pick", "set": {"danger": {"inc": 1}}},
                    {"label": "Wedge a shim",    "set": {"danger": {"dec": 1}}},
                ],
                "weight": 1.2,
            },
            {
                "title": "Mushroom Cache",
                "text_template": "🍄 A pale cluster of cave mushrooms glows softly.",
                "requires": {"has_pickaxe": True},
                "choices": [
                    {"label": "Harvest carefully", "set": {"food": {"inc": 1}}},
                    {"label": "Leave them be",     "set": {}},
                ],
                "weight": 1.0,
            },
        ]
        return base[:max(1, int(n or 1))]
        
    # Call OpenAI API with enhanced feedback-aware prompting
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Build context-aware system prompt
    system_prompt = build_feedback_aware_prompt(bible)
    
    # Build enhanced user prompt with feedback integration
    user_prompt = {
        "request": f"Generate {n} unique storylets",
        "themes": themes,
        "world_context": bible,
        "feedback_integration": extract_feedback_requirements(bible),
        "requirements": "Each storylet should address identified gaps while maintaining narrative quality"
    }

    response = client.chat.completions.create(
        model=os.getenv("MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt, indent=2)},
        ],
        max_completion_tokens=2500,  # Allow for more detailed responses
    )
    
    data = json.loads(response.choices[0].message.content or "{}")
    return data.get("storylets", [])


def build_feedback_aware_prompt(bible: Dict[str, Any]) -> str:
    """Build a system prompt that incorporates storylet analysis feedback."""
    
    base_prompt = (
        "You are a master storyteller creating interconnected storylets for an interactive fiction game. "
        "Your goal is to create LOGICAL, COHERENT storylets that flow naturally from the player's current situation. "
        "\n\nSTORY CONTINUITY RULES:"
        "\n- Build upon the player's current location and situation logically"
        "\n- Create natural transitions between locations (don't teleport randomly)"
        "\n- Respect established danger levels and previous choices"
        "\n- Ensure choices lead to believable consequences"
        "\n- Maintain internal consistency within the story world"
    )
    
    # Add feedback-specific instructions
    feedback_additions = []
    
    if "urgent_need" in bible:
        feedback_additions.append(f"\n🚨 CRITICAL PRIORITY: {bible['urgent_need']}")
        feedback_additions.append(f"   Gap Analysis: {bible.get('gap_analysis', '')}")
        
    if "optimization_need" in bible:
        feedback_additions.append(f"\n🎯 OPTIMIZATION FOCUS: {bible['optimization_need']}")
        feedback_additions.append(f"   Improvement Opportunity: {bible.get('gap_analysis', '')}")
        
    if "location_need" in bible:
        feedback_additions.append(f"\n🗺️ LOCATION CONNECTIVITY: {bible['location_need']}")
        feedback_additions.append(f"   Flow Issue: {bible.get('gap_analysis', '')}")
    
    if "world_state_analysis" in bible:
        analysis = bible["world_state_analysis"]
        feedback_additions.append(f"\n📊 CURRENT STORY STATE:")
        feedback_additions.append(f"   - Total Content: {analysis.get('total_content', 0)} storylets")
        feedback_additions.append(f"   - Connectivity Health: {analysis.get('connectivity_health', 0):.1%}")
        if analysis.get('story_flow_issues'):
            feedback_additions.append(f"   - Flow Issues: {', '.join(analysis['story_flow_issues'])}")
    
    if "improvement_priorities" in bible and bible["improvement_priorities"]:
        feedback_additions.append(f"\n🎯 TOP IMPROVEMENT PRIORITIES:")
        for i, priority in enumerate(bible["improvement_priorities"][:3], 1):
            feedback_additions.append(f"   {i}. {priority.get('suggestion', 'Unknown priority')}")
    
    if "successful_patterns" in bible and bible["successful_patterns"]:
        feedback_additions.append(f"\n✅ MAINTAIN THESE SUCCESSFUL PATTERNS:")
        for pattern in bible["successful_patterns"]:
            feedback_additions.append(f"   - {pattern}")
    
    # Add technical requirements
    technical_prompt = (
        "\n\nSTRICT FORMAT REQUIREMENTS:"
        "\n- Output ONLY valid JSON with a top-level 'storylets' array"
        "\n- Each storylet MUST have: title, text_template, requires, choices, weight"
        "\n- text_template should use {variable} syntax for dynamic content"
        "\n- requires should specify conditions like {'location': 'cave'} or {'danger': {'lte': 2}}"
        "\n- choices is an array with {label, set} where 'set' modifies variables"
        "\n- weight is a float (higher = more likely to appear)"
        "\n\nVARIABLE OPERATIONS:"
        "\n- Direct assignment: {'has_item': true, 'location': 'new_place'}"
        "\n- Numeric increment/decrement: {'danger': {'inc': 1}, 'gold': {'dec': 5}}"
        "\n- Operators in requires: {'health': {'gte': 10}, 'danger': {'lte': 3}}"
        "\n\nCREATIVE GUIDELINES:"
        "\n- Each storylet should feel like a natural continuation of the story"
        "\n- Include sensory details that match the location"
        "\n- Create meaningful choices with clear, logical consequences"
        "\n- Build tension through logical progression, not random events"
        "\n- Reference the current state meaningfully in the text"
        "\n- Use emojis sparingly for atmosphere (⛏️🕯️🍄👁️💎🚪)"
    )
    
    return base_prompt + "".join(feedback_additions) + technical_prompt


def extract_feedback_requirements(bible: Dict[str, Any]) -> Dict[str, Any]:
    """Extract specific requirements from feedback for the AI to focus on."""
    requirements = {}
    
    # Extract required choices/sets from feedback
    if "required_choice_example" in bible:
        requirements["must_include_choice_type"] = bible["required_choice_example"]
    
    if "required_requirement_example" in bible:
        requirements["must_include_requirement_type"] = bible["required_requirement_example"]
    
    if "connectivity_focus" in bible:
        requirements["primary_focus"] = bible["connectivity_focus"]
    
    # Extract variable ecosystem needs
    if "variable_ecosystem" in bible:
        ecosystem = bible["variable_ecosystem"]
        requirements["variable_priorities"] = {
            "create_sources_for": ecosystem.get("needs_sources", []),
            "create_usage_for": ecosystem.get("needs_usage", []),
            "maintain_flow_for": ecosystem.get("well_connected", [])
        }
    
    return requirements


def generate_learning_enhanced_storylets(db, current_vars: Dict[str, Any], n: int = 3) -> List[Dict[str, Any]]:
    """
    Generate storylets using AI learning from current storylet analysis.
    
    This function combines contextual generation with storylet gap analysis.
    """
    from .storylet_analyzer import get_ai_learning_context
    
    # Get AI learning context
    learning_context = get_ai_learning_context(db)
    
    # Enhance the bible with learning context
    enhanced_bible = {
        **learning_context,
        "current_state": current_vars,
        "story_continuity": {
            "location": current_vars.get("location", "unknown"),
            "danger_level": current_vars.get("danger", 0),
            "logical_progression": True
        },
        "ai_instructions": (
            "Use the world_state_analysis to understand what's working and what needs improvement. "
            "Focus on addressing the improvement_priorities while maintaining successful_patterns. "
            "Create storylets that enhance variable_ecosystem connectivity and improve location_network flow."
        )
    }
    
    # Determine themes based on current state and learning context
    themes = []
    danger_level = current_vars.get("danger", 0)
    
    if danger_level > 2:
        themes.extend(["danger", "survival", "tension", "escape"])
    elif danger_level < 1:
        themes.extend(["exploration", "discovery", "mystery", "preparation"])
    else:
        themes.extend(["adventure", "decision", "progress", "challenge"])
    
    # Add themes based on improvement priorities
    for priority in learning_context.get("improvement_priorities", []):
        if priority.get("themes"):
            themes.extend(priority["themes"])
    
    return llm_suggest_storylets(n, themes, enhanced_bible)


def generate_world_storylets(description: str, theme: str, player_role: str = "adventurer", 
                           key_elements: List[str] | None = None, tone: str = "adventure", 
                           count: int = 15) -> List[Dict[str, Any]]:
    """Generate a complete storylet ecosystem from a world description."""
    
    if key_elements is None:
        key_elements = []
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Build the world generation prompt
        world_prompt = f"""You are a master interactive fiction writer creating a dynamic, interconnected story world.

WORLD DESCRIPTION: {description}
THEME: {theme}
PLAYER ROLE: {player_role}
KEY ELEMENTS: {', '.join(key_elements) if key_elements else 'To be determined from description'}
TONE: {tone}

Create {count} interconnected storylets that form a cohesive, immersive experience. Each storylet should:

1. FIT THE WORLD: Match the theme, tone, and setting described
2. CREATE WORLD VARIABLES: Establish key world-specific variables that matter to this universe
3. BUILD CONNECTIONS: Reference variables that other storylets can set
4. OFFER MEANINGFUL CHOICES: 2-3 choices that affect the world state meaningfully

WORLD VARIABLES TO CREATE (extract from the world description):
- Extract 3-5 key concepts from the description and make them trackable variables
- Use location names that fit this specific world
- Create resource/status/relationship variables that matter to this universe
- Ensure variables connect storylets into a coherent narrative web

EXAMPLE VARIABLE TYPES FOR DIFFERENT WORLDS:
- Space whales: quantum_resonance, whale_trust, cosmic_current_strength, star_navigator_rank
- Cyberpunk dwarves: neural_jack_level, corp_reputation, quantum_weaving_skill, underground_contacts
- Medieval fantasy: honor, magic_power, kingdom_favor, mystical_knowledge

Return EXACTLY {count} storylets in this JSON format:
[
  {{
    "title": "Engaging Title That Fits The World",
    "text": "Immersive story text that brings the world to life. Use {{variable_name}} for dynamic content.",
    "choices": [
      {{"label": "Choice 1", "set": {{"variable": "value"}}}},
      {{"label": "Choice 2", "set": {{"other_var": "value"}}}}
    ],
    "requires": {{"location": "starting_area_name"}},
    "weight": 1.0
  }}
]

Focus on creating an interconnected web of storylets where choices in one storylet unlock or influence others. Make the world feel alive and responsive to player choices."""

        response = client.chat.completions.create(
            model=os.getenv("MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are an expert interactive fiction world builder. Create interconnected storylets that form a cohesive narrative ecosystem."},
                {"role": "user", "content": world_prompt}
            ],
            temperature=0.8,  # More creative for world building
            max_tokens=4000
        )
        
        response_text = (response.choices[0].message.content or "").strip()
        
        # Extract JSON from response
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON array found in response")
        
        json_text = response_text[json_start:json_end]
        storylets = json.loads(json_text)
        
        # Validate and normalize the storylets
        normalized_storylets = []
        for storylet in storylets:
            normalized = {
                "title": storylet.get("title", "Untitled Adventure"),
                "text": storylet.get("text", "An adventure awaits..."),
                "choices": storylet.get("choices", [{"label": "Continue", "set": {}}]),
                "requires": storylet.get("requires", {}),
                "weight": float(storylet.get("weight", 1.0))
            }
            
            # Ensure choices have proper format
            normalized_choices = []
            for choice in normalized["choices"]:
                normalized_choice = {
                    "label": choice.get("label") or choice.get("text", "Continue"),
                    "set": choice.get("set") or choice.get("set_vars", {})
                }
                normalized_choices.append(normalized_choice)
            
            normalized["choices"] = normalized_choices
            normalized_storylets.append(normalized)
        
        print(f"✅ Generated {len(normalized_storylets)} world storylets for theme: {theme}")
        return normalized_storylets
        
    except Exception as e:
        print(f"❌ Error generating world storylets: {e}")
        # Return a fallback set of generic storylets
        return [
            {
                "title": "A New Beginning",
                "text": f"You find yourself in the world of {theme}. Your journey as a {player_role} begins here.",
                "choices": [
                    {"label": "Explore the area", "set": {"exploration": 1}},
                    {"label": "Gather information", "set": {"knowledge": 1}}
                ],
                "requires": {},
                "weight": 1.0
            }
        ]
