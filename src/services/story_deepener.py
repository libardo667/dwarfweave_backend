"""
Story Deepener Algorithm
Analyzes storylet connections and generates intermediate storylets to create
more coherent, engaging narrative flow with meaningful choice consequences.
"""

import sqlite3
import json
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
import random
import os


class StoryDeepener:
    """
    Narrative flow enhancer that adds depth, context, and meaningful transitions
    between storylets to create a more engaging player experience.
    """
    
    def __init__(self, db_path: str = 'dwarfweave.db'):
        self.db_path = db_path
        self.storylets = []
        self.choice_transitions = []  # (from_storylet, choice, to_storylet)
        self.weak_transitions = []    # Transitions that need deepening
        self.missing_context = []     # Storylets that need setup
        
    def load_and_analyze(self):
        """Load storylets and analyze narrative flow."""
        print("📚 Loading storylets for deepening analysis...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all storylets
        cursor.execute("SELECT id, title, text_template, requires, choices FROM storylets")
        self.storylets = []
        storylet_map = {}
        
        for row in cursor.fetchall():
            storylet = {
                'id': row[0],
                'title': row[1],
                'text': row[2],
                'requires': json.loads(row[3]) if row[3] else {},
                'choices': json.loads(row[4]) if row[4] else []
            }
            self.storylets.append(storylet)
            storylet_map[storylet['id']] = storylet
        
        # Analyze choice-to-storylet connections
        self._analyze_transitions(storylet_map)
        conn.close()
        
        print(f"🔍 Found {len(self.choice_transitions)} choice transitions")
        print(f"⚠️  Identified {len(self.weak_transitions)} weak transitions")
    
    def _analyze_transitions(self, storylet_map: Dict):
        """Analyze how choices connect to resulting storylets."""
        self.choice_transitions = []
        self.weak_transitions = []
        
        for storylet in self.storylets:
            current_location = storylet['requires'].get('location', 'No Location')
            
            for choice_idx, choice in enumerate(storylet['choices']):
                choice_sets = choice.get('set', {})
                choice_text = choice.get('label', choice.get('text', ''))  # Try both label and text
                
                # Find what storylets this choice could lead to
                possible_next = self._find_matching_storylets(choice_sets, storylet_map)
                
                if possible_next:
                    for next_storylet in possible_next:
                        transition = {
                            'from': storylet,
                            'choice': choice,
                            'choice_idx': choice_idx,
                            'to': next_storylet,
                            'coherence_score': self._rate_transition_coherence(storylet, choice, next_storylet)
                        }
                        
                        self.choice_transitions.append(transition)
                        
                        # Flag weak transitions for deepening
                        if transition['coherence_score'] < 0.6:
                            self.weak_transitions.append(transition)
                else:
                    # Choice leads nowhere - needs a destination storylet
                    self.weak_transitions.append({
                        'from': storylet,
                        'choice': choice,
                        'choice_idx': choice_idx,
                        'to': None,
                        'coherence_score': 0.0
                    })
    
    def _find_matching_storylets(self, choice_sets: Dict, storylet_map: Dict) -> List[Dict]:
        """Find storylets that could be reached by this choice."""
        matches = []
        
        for storylet in self.storylets:
            # Check if choice sets match storylet requirements
            requirements_met = True
            
            for req_key, req_value in storylet['requires'].items():
                if req_key in choice_sets:
                    if choice_sets[req_key] != req_value:
                        requirements_met = False
                        break
                elif req_key == 'location' and choice_sets.get('location'):
                    # Location is being set by choice
                    if choice_sets['location'] != req_value:
                        requirements_met = False
                        break
            
            if requirements_met:
                matches.append(storylet)
        
        return matches
    
    def _rate_transition_coherence(self, from_storylet: Dict, choice: Dict, to_storylet: Dict) -> float:
        """Rate how coherent a transition is (0.0 = nonsensical, 1.0 = perfect)."""
        score = 0.5  # Base score
        
        choice_text = choice.get('label', choice.get('text', '')).lower()  # Try both label and text
        from_text = from_storylet.get('text_template', from_storylet.get('text', '')).lower()
        to_text = to_storylet.get('text_template', to_storylet.get('text', '')).lower()
        
        # Check for thematic consistency
        if 'crystal' in choice_text and 'crystal' in to_text:
            score += 0.3
        if 'library' in choice_text and 'library' in to_text:
            score += 0.3
        if 'corporate' in choice_text and 'corporate' in to_text:
            score += 0.3
        
        # Check for narrative continuity keywords
        continuity_words = ['ask', 'investigate', 'examine', 'talk', 'look']
        if any(word in choice_text for word in continuity_words):
            if any(word in to_text for word in ['respond', 'explain', 'show', 'tell']):
                score += 0.2
        
        # Penalize abrupt topic changes
        from_topics = self._extract_topics(from_text)
        to_topics = self._extract_topics(to_text)
        
        if from_topics and to_topics:
            overlap = len(from_topics.intersection(to_topics)) / len(from_topics.union(to_topics))
            score += overlap * 0.3
        
        return min(score, 1.0)
    
    def _extract_topics(self, text: str) -> Set[str]:
        """Extract key topics from text."""
        topics = set()
        topic_keywords = {
            'crystals': ['crystal', 'gem', 'stone', 'mineral'],
            'technology': ['quantum', 'tech', 'device', 'machine', 'computer'],
            'corporate': ['corp', 'company', 'business', 'suit'],
            'clan': ['clan', 'family', 'tradition', 'ancestor'],
            'underground': ['tunnel', 'cave', 'underground', 'hidden'],
            'library': ['book', 'text', 'library', 'archive', 'knowledge']
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.add(topic)
        
        return topics
    
    def _call_llm(self, prompt: str) -> str:
        """Make a call to the OpenAI API."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-5-2025-08-07",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            return content if content is not None else '{"title": "Generated Content", "text": "Content generated."}'
        except Exception as e:
            print(f"⚠️  LLM call failed: {e}")
            return '{"title": "Generated Content", "text": "Content generated."}'
    
    def generate_bridge_storylets(self) -> List[Dict]:
        """Generate intermediate storylets to bridge weak transitions."""
        print("🌉 Generating bridge storylets for weak transitions...")
        
        bridge_storylets = []
        
        # Limit to prevent overwhelming number of bridges
        weak_sample = self.weak_transitions[:3]  # Process only top 3 weak transitions
        
        for transition in weak_sample:
            if transition['to'] is None:
                # Choice leads nowhere - create a destination
                bridge = self._create_choice_destination(transition)
            else:
                # Weak transition - create intermediate storylet
                bridge = self._create_transition_bridge(transition)
            
            if bridge:
                bridge_storylets.append(bridge)
                print(f"🌉 Created bridge: '{bridge['title']}'")
        
        return bridge_storylets
    
    def _create_choice_destination(self, transition: Dict) -> Optional[Dict]:
        """Create a storylet that responds to a choice that currently leads nowhere."""
        from_storylet = transition['from']
        choice = transition['choice']
        
        # Safely get text content
        from_text = from_storylet.get('text_template', from_storylet.get('text', ''))
        
        # Use AI to generate a contextual response
        prompt = f"""
        Create a short storylet that responds to this player choice:
        
        Current scene: "{from_text[:200]}..."
        Player choice: "{choice.get('label', choice.get('text', 'Unknown choice'))}"
        
        Generate a brief (2-3 sentence) response that:
        1. Directly addresses what the player chose to do
        2. Provides meaningful information or consequence
        3. Feels like a natural continuation
        
        Return JSON with: title, text
        """
        
        try:
            response = self._call_llm(prompt)
            # Parse AI response (simplified - assumes proper JSON)
            ai_content = json.loads(response)
            
            # Create the new storylet
            new_storylet = {
                'title': ai_content.get('title', f"Response to {choice.get('label', choice.get('text', 'choice'))[:20]}..."),
                'text_template': ai_content.get('text', f"You {choice.get('label', choice.get('text', 'act')).lower()}."),
                'requires': choice.get('set', {}),
                'choices': [
                    {
                        "text": "Continue",
                        "set": {},
                        "condition": None
                    }
                ],
                'weight': 1.0
            }
            
            return new_storylet
            
        except Exception as e:
            print(f"⚠️  AI generation failed: {e}")
            # Fallback to template
            return {
                'title': f"Following Up",
                'text_template': f"You {choice.get('label', choice.get('text', 'take action')).lower()}. The situation develops further.",
                'requires': choice.get('set', {}),
                'choices': [{"text": "Continue", "set": {}, "condition": None}],
                'weight': 1.0
            }
    
    def _create_transition_bridge(self, transition: Dict) -> Optional[Dict]:
        """Create an intermediate storylet to smooth the transition."""
        from_storylet = transition['from']
        choice = transition['choice']
        to_storylet = transition['to']
        
        # Safely get text content
        from_text = from_storylet.get('text_template', from_storylet.get('text', ''))
        to_text = to_storylet.get('text_template', to_storylet.get('text', ''))
        
        # Use AI to create a bridge
        prompt = f"""
        Create a brief transition storylet between these two scenes:
        
        Scene A: "{from_text[:150]}..."
        Player chooses: "{choice.get('label', choice.get('text', 'Unknown choice'))}"
        Scene B: "{to_text[:150]}..."
        
        Create a 1-2 sentence bridge that smoothly connects A to B.
        The bridge should show the immediate result of the choice before leading to Scene B.
        
        Return JSON with: title, text
        """
        
        try:
            response = self._call_llm(prompt)
            ai_content = json.loads(response)
            
            bridge_storylet = {
                'title': ai_content.get('title', 'Transition'),
                'text_template': ai_content.get('text', f"You {choice.get('label', choice.get('text', 'act')).lower()}."),
                'requires': choice.get('set', {}),
                'choices': [
                    {
                        "text": "Continue",
                        "set": to_storylet['requires'],
                        "condition": None
                    }
                ],
                'weight': 1.0
            }
            
            return bridge_storylet
            
        except Exception as e:
            print(f"⚠️  Bridge generation failed: {e}")
            return None
    
    def add_choice_previews(self):
        """Add preview text to choices showing what they might lead to."""
        print("👁️  Adding choice previews...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = 0
        
        for storylet in self.storylets:
            updated_choices = []
            choice_updated = False
            
            for choice in storylet['choices']:
                choice_sets = choice.get('set', {})
                
                # Find what this choice leads to
                next_location = choice_sets.get('location')
                preview_hint = ""
                
                if next_location:
                    preview_hint = f" (→ {next_location})"
                elif choice_sets:
                    # Show what variables are set
                    var_changes = [f"{k}+{v}" for k, v in choice_sets.items() if k != 'location']
                    if var_changes:
                        preview_hint = f" ({', '.join(var_changes[:2])})"
                
                if preview_hint and not choice.get('label', choice.get('text', '')).endswith(')'):
                    updated_choice = choice.copy()
                    updated_choice['label'] = choice.get('label', choice.get('text', '')) + preview_hint
                    updated_choices.append(updated_choice)
                    choice_updated = True
                else:
                    updated_choices.append(choice)
            
            if choice_updated:
                cursor.execute("""
                    UPDATE storylets 
                    SET choices = ? 
                    WHERE id = ?
                """, (json.dumps(updated_choices), storylet['id']))
                updates += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ Updated {updates} storylets with choice previews")
    
    def deepen_story(self, add_previews: bool = True) -> Dict:
        """Main deepening process."""
        print("🕳️  Starting story deepening process...")
        
        # Load and analyze current state
        self.load_and_analyze()
        
        results = {
            'bridge_storylets_created': 0,
            'choice_previews_added': 0,
            'coherence_improved': 0
        }
        
        # Generate bridge storylets
        bridge_storylets = self.generate_bridge_storylets()
        
        if bridge_storylets:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for bridge in bridge_storylets:
                cursor.execute("""
                    INSERT INTO storylets (title, text_template, requires, choices, weight)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    bridge['title'],
                    bridge['text_template'],
                    json.dumps(bridge['requires']),
                    json.dumps(bridge['choices']),
                    bridge['weight']
                ))
            
            conn.commit()
            conn.close()
            
            results['bridge_storylets_created'] = len(bridge_storylets)
        
        # Add choice previews
        if add_previews:
            self.add_choice_previews()
            results['choice_previews_added'] = 1
        
        total_improvements = sum(results.values())
        print(f"🎉 Story deepening complete! Made {total_improvements} improvements")
        
        return results


def main():
    """Run the story deepening algorithm."""
    deepener = StoryDeepener()
    
    print("🕳️  Running story deepening analysis...")
    results = deepener.deepen_story()
    
    print("\n📊 DEEPENING RESULTS:")
    print("=" * 50)
    print(f"Bridge storylets created: {results['bridge_storylets_created']}")
    print(f"Choice previews added: {results['choice_previews_added']}")
    
    print("\n🗺️  Generating updated map...")
    import subprocess
    subprocess.run(['python', './db/storylet_map.py'])


if __name__ == "__main__":
    main()
