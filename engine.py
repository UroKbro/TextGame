import json
import re
import random
from typing import Optional, Dict, Any

from schema import GameState, TurnAction, EnemyState
from memory import NarrativeMemory
from config import LLM_MODEL

class TextAdventureEngine:
    def __init__(self, model_name: str = LLM_MODEL):
        self.state = GameState()
        self.model_name = model_name
        self.memory = None
        self.llm = None
        self.offline_mode = False
        
        # Initialize memory safely
        try:
            self.memory = NarrativeMemory()
        except Exception:
            self.memory = None
            
        # Initialize LLM safely
        try:
            from langchain_community.llms import Ollama
            self.llm = Ollama(model=model_name, timeout=15)
        except Exception:
            self.offline_mode = True
            self.llm = None

    def build_system_prompt(self, player_input: str, recalled_memory: str) -> str:
        return f"""
You are the Dungeon Master for an adaptive dark fantasy terminal RPG called 'Chronicles of the Realm'.
The tone is immersive, mysterious, and engaging.

[SYSTEM MANDATE]
You MUST respond strictly with a valid JSON object matching this schema:
{{
  "narrative_response": "2-3 paragraphs of rich, descriptive atmospheric storytelling.",
  "location_change": "New Location name or null",
  "item_added": "Item name with stats if any, or null",
  "item_removed": "Item name used/lost, or null",
  "health_change": 0 (integer damage -10 or heal +15, or null),
  "mana_change": 0 (integer mana spent or restored, or null),
  "gold_change": 0 (integer gold gained or spent, or null),
  "xp_change": 0 (integer XP gained, or null),
  "quest_update": "New or updated quest objective, or null",
  "quest_completed": "Name of completed quest, or null",
  "trigger_combat": {{
      "name": "Enemy Name",
      "max_health": 35,
      "health": 35,
      "attack": 8,
      "defense": 2,
      "xp_reward": 30,
      "gold_reward": 15,
      "sprite_key": "goblin" (one of: goblin, skeleton, troll, dragon, mage, wolf),
      "description": "Short enemy description",
      "special_move": "Special attack name"
  }} or null,
  "suggested_actions": [
      "Short action choice 1",
      "Short action choice 2",
      "Short action choice 3"
  ]
}}

[CURRENT HERO STATE]
- Name: {self.state.player_name} (Level {self.state.level})
- Location: {self.state.location}
- Health: {self.state.health}/{self.state.max_health} | Mana: {self.state.mana}/{self.state.max_mana}
- Stats: ATK {self.state.total_attack} | DEF {self.state.total_defense}
- Weapon: {self.state.equipped_weapon} | Armor: {self.state.equipped_armor}
- Gold: {self.state.gold} | XP: {self.state.xp}/{self.state.xp_to_next}
- Inventory: {', '.join(self.state.inventory)}
- Active Quests: {', '.join(self.state.active_quests)}

[RELEVANT PAST MEMORIES]
{recalled_memory}

[PLAYER ACTION]
{player_input}
"""

    def apply_state_changes(self, action: TurnAction):
        if action.location_change:
            self.state.location = action.location_change
            
        if action.item_added and action.item_added not in self.state.inventory:
            self.state.inventory.append(action.item_added)
            # Auto-equip if weapon or armor
            if "+ " in action.item_added or "ATK" in action.item_added:
                self.state.equipped_weapon = action.item_added
            elif "DEF" in action.item_added or "Armor" in action.item_added:
                self.state.equipped_armor = action.item_added
                
        if action.item_removed and action.item_removed in self.state.inventory:
            self.state.inventory.remove(action.item_removed)
            
        if action.health_change:
            self.state.health = max(0, min(self.state.max_health, self.state.health + action.health_change))
            
        if action.mana_change:
            self.state.mana = max(0, min(self.state.max_mana, self.state.mana + action.mana_change))
            
        if action.gold_change:
            self.state.gold = max(0, self.state.gold + action.gold_change)
            
        if action.xp_change:
            self.state.xp += action.xp_change
            self._check_level_up()
            
        if action.quest_update and action.quest_update not in self.state.active_quests:
            self.state.active_quests.append(action.quest_update)
            
        if action.quest_completed:
            if action.quest_completed in self.state.active_quests:
                self.state.active_quests.remove(action.quest_completed)
            if action.quest_completed not in self.state.completed_quests:
                self.state.completed_quests.append(action.quest_completed)

    def _check_level_up(self):
        if self.state.xp >= self.state.xp_to_next:
            self.state.level += 1
            self.state.xp -= self.state.xp_to_next
            self.state.xp_to_next = int(self.state.xp_to_next * 1.5)
            self.state.max_health += 20
            self.state.health = self.state.max_health
            self.state.max_mana += 10
            self.state.mana = self.state.max_mana
            self.state.base_attack += 3
            self.state.base_defense += 2

    @staticmethod
    def _parse_action(raw_output) -> TurnAction:
        """Parse a model response containing a JSON turn action."""
        response_text = getattr(raw_output, "content", raw_output)
        if not isinstance(response_text, str):
            raise ValueError("The model returned a non-text response.")

        fenced_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL | re.IGNORECASE
        )
        json_text = fenced_match.group(1) if fenced_match else response_text.strip()
        if not fenced_match:
            start = json_text.find("{")
            if start < 0:
                raise ValueError("The model response did not contain a JSON object.")
            json_text = json_text[start:]

        try:
            payload = json.JSONDecoder().raw_decode(json_text)[0]
        except json.JSONDecodeError as error:
            raise ValueError("The model returned invalid JSON.") from error
            
        # Handle nested trigger_combat dict
        if "trigger_combat" in payload and isinstance(payload["trigger_combat"], dict):
            try:
                payload["trigger_combat"] = EnemyState(**payload["trigger_combat"])
            except Exception:
                payload["trigger_combat"] = None
                
        return TurnAction(**payload)

    def generate_simulated_turn(self, player_input: str) -> TurnAction:
        """Dynamic heuristic Dungeon Master for offline mode or fallback."""
        inp = player_input.lower().strip()
        
        # 1. Cellar / Dungeon exploration
        if "cellar" in inp or "down" in inp or "stairs" in inp or "investigate" in inp:
            enemy = EnemyState(
                name="Skeletal Guardian",
                max_health=45,
                health=45,
                attack=10,
                defense=3,
                xp_reward=45,
                gold_reward=20,
                sprite_key="skeleton",
                description="An ancient warrior reanimated by necrotic embers, wielding a rusty broadsword.",
                special_move="Bone Cleave"
            )
            return TurnAction(
                narrative_response="You descend the creaking wooden stairs into the damp Tavern Cellar. The air grows cold and smells of mildew and spilled vintage wine. As your torchlight cuts through the gloom, a pair of glowing red eyes ignites in the shadows. A Skeletal Guardian steps forward from behind shattered casks, raising its blade!",
                location_change="Damp Cellar Catacombs",
                quest_update="Defeat the cellar monstrosity",
                trigger_combat=enemy,
                suggested_actions=[
                    "Strike with weapon",
                    "Cast Fireball spell",
                    "Search broken wine casks for loot"
                ]
            )
            
        # 2. Forest exploration
        elif "forest" in inp or "woods" in inp or "leave" in inp or "outside" in inp:
            enemy = EnemyState(
                name="Dire Shadow Wolf",
                max_health=35,
                health=35,
                attack=9,
                defense=2,
                xp_reward=35,
                gold_reward=12,
                sprite_key="wolf",
                description="A massive black wolf with crimson eyes and razor-sharp fangs dripping with venom.",
                special_move="Shadow Pounce"
            )
            return TurnAction(
                narrative_response="You push open the heavy oak doors and step out into the Whispering Shadow Forest. Thick fog swirls around towering black pine trees. Suddenly, a low growl reverberates from the mist. A Dire Shadow Wolf leaps from the brambles, barring your path with bared fangs!",
                location_change="Whispering Shadow Forest",
                trigger_combat=enemy,
                suggested_actions=[
                    "Attack the beast",
                    "Cast Arcane Strike",
                    "Retreat back to the tavern"
                ]
            )
            
        # 3. Tavern / Rest / Drink
        elif "tavern" in inp or "rest" in inp or "drink" in inp or "barkeep" in inp or "inn" in inp:
            return TurnAction(
                narrative_response="You take a seat near the roaring fireplace in the Whispering Oak Tavern. The barkeep slides over a foaming mug of spiced ale and a bowl of hearty venison stew. The warmth soothes your aching limbs and restores your magical vitality.",
                location_change="Whispering Oak Tavern",
                health_change=25,
                mana_change=20,
                suggested_actions=[
                    "Investigate the cellar noises",
                    "Visit the Mystic Bazaar & Merchant",
                    "Venture out into the Whispering Shadow Forest"
                ]
            )
            
        # 4. Shop / Merchant
        elif "shop" in inp or "merchant" in inp or "buy" in inp or "market" in inp or "bazaar" in inp:
            return TurnAction(
                narrative_response="You enter the Mystic Bazaar. A hooded merchant greets you with a sly grin: 'Welcome, traveler! I carry weapons, potions, and enchanted scrolls. What catches your eye?'",
                location_change="Mystic Bazaar & Armory",
                suggested_actions=[
                    "Buy Health Potion (15 Gold)",
                    "Buy Silver Longsword (+8 ATK) (40 Gold)",
                    "Buy Enchanted Iron Armor (+6 DEF) (50 Gold)"
                ]
            )
            
        # 5. Buy specific items
        elif "buy health potion" in inp or "buy potion" in inp:
            if self.state.gold >= 15:
                return TurnAction(
                    narrative_response="You hand over 15 gold coins. The merchant hands you a bubbling crimson Health Potion.",
                    gold_change=-15,
                    item_added="Health Potion",
                    suggested_actions=["Buy Mana Potion (15 Gold)", "Return to Tavern", "Explore Cellar"]
                )
            else:
                return TurnAction(
                    narrative_response="The merchant scoffs: 'You don't have enough gold for that potion!'",
                    suggested_actions=["Explore cellar for gold", "Venture into forest", "Return to tavern"]
                )
                
        # 6. Buy weapon
        elif "buy silver longsword" in inp or "buy sword" in inp or "buy weapon" in inp:
            if self.state.gold >= 40:
                return TurnAction(
                    narrative_response="You purchase the gleaming Silver Longsword (+8 ATK)! You feel a surge of martial power as you sheath it.",
                    gold_change=-40,
                    item_added="Silver Longsword (+8 ATK)",
                    suggested_actions=["Test sword in cellar", "Explore forest", "Visit tavern"]
                )
            else:
                return TurnAction(
                    narrative_response="The merchant taps the counter: 'The sword costs 40 gold. Slay some beasts in the cellar first!'",
                    suggested_actions=["Go to cellar", "Talk to barkeep", "Check inventory"]
                )
                
        # 7. Search / Loot
        elif "search" in inp or "look" in inp or "chest" in inp or "loot" in inp:
            gold_found = random.randint(10, 25)
            return TurnAction(
                narrative_response=f"You meticulously search the area. Behind a dusty shelf, you discover an old leather pouch containing {gold_found} Gold and a Throwing Dagger!",
                gold_change=gold_found,
                xp_change=20,
                item_added="Throwing Dagger",
                suggested_actions=["Check inventory", "Explore deeper", "Return to tavern"]
            )
            
        # 8. Boss / Ruins / Dragon
        elif "ruins" in inp or "dragon" in inp or "boss" in inp or "crypt" in inp:
            enemy = EnemyState(
                name="Elder Abyssal Wyrm",
                max_health=90,
                health=90,
                attack=16,
                defense=6,
                xp_reward=150,
                gold_reward=100,
                sprite_key="dragon",
                description="A terrifying winged leviathan breathing crimson hellfire and crushing stone beneath its claws.",
                special_move="Infernal Breath"
            )
            return TurnAction(
                narrative_response="You step into the grand rotunda of the Ancient Ruined Citadel. The ceiling has collapsed, revealing a storm-tossed sky. Perched atop the crumbling throne is the legendary Elder Abyssal Wyrm. It unfurls its obsidian wings and unleashes a deafening roar!",
                location_change="Ancient Ruined Citadel",
                trigger_combat=enemy,
                suggested_actions=[
                    "Cast Lightning Bolt spell",
                    "Charge with weapon",
                    "Drink Health Potion"
                ]
            )
            
        # Default fallback story
        else:
            return TurnAction(
                narrative_response=f"You carefully {player_input}. The shadows shift as your surroundings respond to your actions. You sense ancient power and danger lurking nearby.",
                xp_change=10,
                suggested_actions=[
                    "Explore the cellar catacombs",
                    "Visit the mystic merchant",
                    "Venture into the dark forest"
                ]
            )

    def process_turn(self, player_input: str) -> TurnAction:
        self.state.turn_count += 1
        
        # Retrieve context from memory
        recalled_memory = ""
        if self.memory:
            try:
                recalled_memory = self.memory.retrieve_context(player_input)
            except Exception:
                recalled_memory = ""

        action = None
        # Try LLM if available
        if self.llm and not self.offline_mode:
            try:
                prompt = self.build_system_prompt(player_input, recalled_memory)
                raw_output = self.llm.invoke(prompt)
                action = self._parse_action(raw_output)
            except Exception:
                # If LLM failed, fallback to simulated DM
                action = self.generate_simulated_turn(player_input)
        else:
            action = self.generate_simulated_turn(player_input)

        self.apply_state_changes(action)
        
        # Add to memory
        if self.memory:
            try:
                self.memory.add_memory(self.state.turn_count, player_input, action.narrative_response)
            except Exception:
                pass
                
        return action