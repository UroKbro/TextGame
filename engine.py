import json
import re
import random
from typing import Optional, Dict, Any

from schema import GameState, TurnAction, EnemyState
from memory import NarrativeMemory
from config import LLM_MODEL
from factions import modify_reputation

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
        rep_str = ", ".join([f"{k}: {v:+d}" for k, v in self.state.reputation.items()])
        mat_str = ", ".join([f"{k}: {v}x" for k, v in self.state.materials.items()])
        return f"""
You are the Dungeon Master for an adaptive dark fantasy terminal RPG called 'Chronicles of the Realm'.
The game features moral choices, factions, crafting reagents, branching questlines, and tactical combat.

[SYSTEM MANDATE]
You MUST respond strictly with a valid JSON object matching this schema:
{{
  "narrative_response": "2-3 paragraphs of rich, descriptive atmospheric storytelling.",
  "location_change": "New Location name or null",
  "item_added": "Item name with stats if any, or null",
  "item_removed": "Item name used/lost, or null",
  "materials_added": {{"Iron Ore": 2}} or null,
  "materials_removed": {{"Cave Moss": 1}} or null,
  "recipe_unlocked": "Recipe name or null",
  "health_change": 0 (integer damage -10 or heal +15, or null),
  "mana_change": 0 (integer mana spent or restored, or null),
  "gold_change": 0 (integer gold gained or spent, or null),
  "xp_change": 0 (integer XP gained, or null),
  "reputation_change": {{"Kingdom of Oakhaven": 10, "The Shadow Syndicate": -5}} or null,
  "quest_update": "New or updated quest objective, or null",
  "quest_completed": "Name of completed quest, or null",
  "choice_recorded": "Summary of player moral/tactical choice or null",
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
- Faction Standings: {rep_str}
- Crafting Materials: {mat_str}
- Known Recipes: {', '.join(self.state.known_recipes)}
- Inventory: {', '.join(self.state.inventory)}
- Active Quests: {', '.join(self.state.active_quests)}
- Past Key Choices: {', '.join(self.state.choice_history) if self.state.choice_history else 'None yet'}

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
            if "+ " in action.item_added or "ATK" in action.item_added:
                self.state.equipped_weapon = action.item_added
            elif "DEF" in action.item_added or "Armor" in action.item_added:
                self.state.equipped_armor = action.item_added
                
        if action.item_removed and action.item_removed in self.state.inventory:
            self.state.inventory.remove(action.item_removed)

        # Materials
        if action.materials_added:
            for mat, qty in action.materials_added.items():
                self.state.materials[mat] = self.state.materials.get(mat, 0) + qty
                
        if action.materials_removed:
            for mat, qty in action.materials_removed.items():
                if mat in self.state.materials:
                    self.state.materials[mat] -= qty
                    if self.state.materials[mat] <= 0:
                        del self.state.materials[mat]
                        
        if action.recipe_unlocked and action.recipe_unlocked not in self.state.known_recipes:
            self.state.known_recipes.append(action.recipe_unlocked)
            
        if action.health_change:
            self.state.health = max(0, min(self.state.max_health, self.state.health + action.health_change))
            
        if action.mana_change:
            self.state.mana = max(0, min(self.state.max_mana, self.state.mana + action.mana_change))
            
        if action.gold_change:
            self.state.gold = max(0, self.state.gold + action.gold_change)
            
        if action.xp_change:
            self.state.xp += action.xp_change
            self._check_level_up()
            
        # Faction shifts
        if action.reputation_change:
            for fac, delta in action.reputation_change.items():
                modify_reputation(self.state, fac, delta)
                
        if action.choice_recorded and action.choice_recorded not in self.state.choice_history:
            self.state.choice_history.append(action.choice_recorded)
            
        if action.quest_update and action.quest_update not in self.state.active_quests:
            self.state.active_quests.append(action.quest_update)
            
        if action.quest_completed:
            for aq in list(self.state.active_quests):
                if action.quest_completed.lower() in aq.lower():
                    self.state.active_quests.remove(aq)
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
            
        if "trigger_combat" in payload and isinstance(payload["trigger_combat"], dict):
            try:
                payload["trigger_combat"] = EnemyState(**payload["trigger_combat"])
            except Exception:
                payload["trigger_combat"] = None
                
        return TurnAction(**payload)

    def generate_simulated_turn(self, player_input: str) -> TurnAction:
        """Dynamic heuristic Dungeon Master supporting branching quests, factions, crafting, and gathering."""
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
                description="An ancient warrior reanimated by necrotic embers, guarding a concealed iron doorway.",
                special_move="Bone Cleave"
            )
            return TurnAction(
                narrative_response="You descend the creaking stairs into the damp Tavern Cellar. Rotting wine casks and glowing Cave Moss line the cobblestone walls. Beyond the shadows, a Skeletal Guardian steps forth from behind an iron gate, its rusty blade scraping stone!",
                location_change="Damp Cellar Catacombs",
                materials_added={"Cave Moss": 2, "Iron Ore": 1},
                quest_update="Investigate the cellar noises in the Tavern",
                trigger_combat=enemy,
                suggested_actions=[
                    "Inspect the secret chamber behind the cellar gate",
                    "Harvest Cave Moss from the damp walls",
                    "Return upstairs to the Tavern"
                ]
            )
            
        # 2. Secret cellar chamber / Quest dilemma trigger
        elif "secret chamber" in inp or "behind" in inp or "gate" in inp or "doorway" in inp:
            return TurnAction(
                narrative_response="You slip past the shattered iron gate. Inside the hidden alcove, you discover an arcane summoning circle and an injured, mutated Druid apprentice chained to the wall. Nearby, a Goblin courier clutches a contraband ledger of stolen goods! You face a fateful decision...",
                location_change="Cellar Smuggler's Alcove",
                materials_added={"Arcane Dust": 2, "Monster Bone": 2},
                recipe_unlocked="Volatile Fire Bomb",
                suggested_actions=[
                    "Make moral decision regarding the cellar captive [Quest Decision]",
                    "Harvest Arcane Dust from the circle",
                    "Return to the Tavern common room"
                ]
            )
            
        # 3. Forest exploration & Herb Gathering
        elif "forest" in inp or "woods" in inp or "wild" in inp or "gather" in inp or "herb" in inp:
            enemy = EnemyState(
                name="Dire Shadow Wolf",
                max_health=35,
                health=35,
                attack=9,
                defense=2,
                xp_reward=35,
                gold_reward=12,
                sprite_key="wolf",
                description="A massive black wolf with crimson eyes guarding a patch of moonlit Silver Herbs.",
                special_move="Shadow Pounce"
            )
            return TurnAction(
                narrative_response="You wander deep into the Whispering Shadow Forest. Moonlight filters through the canopy, illuminating a vibrant patch of Silver Herbs and ancient mossy boulders. Suddenly, a Dire Shadow Wolf leaps from the misty brambles!",
                location_change="Whispering Shadow Forest",
                materials_added={"Silver Herb": 2, "Cave Moss": 1},
                trigger_combat=enemy,
                reputation_change={"Sylvan Druids": 5},
                suggested_actions=[
                    "Forage for more rare herbs and iron ore",
                    "Venture toward the Ancient Ruined Citadel",
                    "Head back to town"
                ]
            )
            
        # 4. Forge / Blacksmith
        elif "forge" in inp or "smith" in inp or "ironworks" in inp:
            return TurnAction(
                narrative_response="You step into the scorching heat of the Oakhaven Ironworks. Anvil sparks fly as the master blacksmith hammers glowing iron ingots into sharp blades and sturdy plate armor.",
                location_change="Oakhaven Ironworks & Forge",
                recipe_unlocked="Knight's Steel Plate (+8 DEF)",
                suggested_actions=[
                    "Open Merchant Stall to buy or sell equipment [M]",
                    "Use the Forge to craft weapons and armor [K]",
                    "Return to Town Square"
                ]
            )
            
        # 5. Alchemy Workshop / Apothecary
        elif "alchemy" in inp or "apothecary" in inp or "potion" in inp or "lab" in inp:
            return TurnAction(
                narrative_response="You enter the Mystic Alchemy Workshop. Glass alembics bubble with emerald and sapphire distillates while aromatic bundles of mountain herbs hang from wooden rafters.",
                location_change="Mystic Alchemy Workshop",
                recipe_unlocked="Elixir of Titan Strength",
                suggested_actions=[
                    "Open Apothecary Stall to trade ingredients [M]",
                    "Brew potions and elixirs at the Alchemy station [K]",
                    "Return to Town Square"
                ]
            )
            
        # 6. Tavern / Rest / Socialize
        elif "tavern" in inp or "rest" in inp or "drink" in inp or "barkeep" in inp:
            return TurnAction(
                narrative_response="You relax near the roaring fireplace in the Whispering Oak Tavern. The barkeep brings a steaming bowl of venison stew and a mug of honeyed mead, soothing your battle wounds and restoring your magical reserves.",
                location_change="Whispering Oak Tavern",
                health_change=30,
                mana_change=25,
                reputation_change={"Kingdom of Oakhaven": 5},
                suggested_actions=[
                    "Investigate the cellar noises in the Tavern",
                    "Visit the Oakhaven Blacksmith and Forge",
                    "Venture out into the Whispering Shadow Forest"
                ]
            )
            
        # 7. Search / Mining / Looting
        elif "search" in inp or "mine" in inp or "ore" in inp or "chest" in inp or "loot" in inp:
            ore_found = random.randint(2, 4)
            gold_found = random.randint(15, 30)
            return TurnAction(
                narrative_response=f"You meticulously search the area. Behind loose stone masonry, you strike a rich vein of Iron Ore and recover a lost pouch containing {gold_found} Gold and {ore_found}x Iron Ore!",
                gold_change=gold_found,
                materials_added={"Iron Ore": ore_found, "Monster Bone": 1},
                xp_change=25,
                suggested_actions=[
                    "Use Crafting Workshop to forge gear [K]",
                    "Visit the Merchant to trade [M]",
                    "Explore deeper into the wilderness"
                ]
            )
            
        # 8. Boss / Ruined Citadel / Dragon
        elif "ruins" in inp or "dragon" in inp or "boss" in inp or "citadel" in inp:
            enemy = EnemyState(
                name="Elder Abyssal Wyrm",
                max_health=95,
                health=95,
                attack=17,
                defense=6,
                xp_reward=160,
                gold_reward=120,
                sprite_key="dragon",
                description="A terrifying winged leviathan coiled around the glowing Arcane Leyline Crystal.",
                special_move="Infernal Breath"
            )
            return TurnAction(
                narrative_response="You enter the colossal throne chamber of the Ancient Ruined Citadel. Perched atop the crumbling pedestal is the legendary Elder Abyssal Wyrm, guarding the pulsing Arcane Leyline Crystal. It spreads massive wings of obsidian and breathes waves of incinerating heat!",
                location_change="Ancient Ruined Citadel",
                materials_added={"Arcane Dust": 3, "Monster Bone": 3},
                quest_update="The Stolen Arcane Relay",
                trigger_combat=enemy,
                suggested_actions=[
                    "Cast Lightning Bolt spell",
                    "Strike with weapon",
                    "Hurl a Volatile Fire Bomb"
                ]
            )
            
        # Default fallback
        else:
            return TurnAction(
                narrative_response=f"You {player_input}. The world responds dynamically as rumors of your deeds spread through Oakhaven.",
                xp_change=10,
                materials_added={"Cave Moss": 1} if random.random() < 0.5 else None,
                suggested_actions=[
                    "Explore the cellar catacombs",
                    "Visit the Forge or Alchemy Workshop [K]",
                    "Check Faction standings and Quests [F/Q]"
                ]
            )

    def process_turn(self, player_input: str) -> TurnAction:
        self.state.turn_count += 1
        
        recalled_memory = ""
        if self.memory:
            try:
                recalled_memory = self.memory.retrieve_context(player_input)
            except Exception:
                recalled_memory = ""

        action = None
        if self.llm and not self.offline_mode:
            try:
                prompt = self.build_system_prompt(player_input, recalled_memory)
                raw_output = self.llm.invoke(prompt)
                action = self._parse_action(raw_output)
            except Exception:
                action = self.generate_simulated_turn(player_input)
        else:
            action = self.generate_simulated_turn(player_input)

        self.apply_state_changes(action)
        
        if self.memory:
            try:
                self.memory.add_memory(self.state.turn_count, player_input, action.narrative_response)
            except Exception:
                pass
                
        return action