from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class EnemyState(BaseModel):
    name: str = "Cellar Goblin"
    max_health: int = 40
    health: int = 40
    attack: int = 8
    defense: int = 2
    xp_reward: int = 35
    gold_reward: int = 15
    sprite_key: str = "goblin"
    description: str = "A snarling goblin clutching a rusted cleaver."
    special_move: Optional[str] = "Sneak Bite"

class GameState(BaseModel):
    player_name: str = "Adventurer"
    location: str = "Whispering Oak Tavern"
    health: int = 100
    max_health: int = 100
    mana: int = 50
    max_mana: int = 50
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    gold: int = 25
    base_attack: int = 10
    base_defense: int = 5
    equipped_weapon: str = "Rusty Dagger (+4 ATK)"
    equipped_armor: str = "Leather Tunic (+3 DEF)"
    inventory: List[str] = Field(default_factory=lambda: [
        "Torch", 
        "Rusty Dagger (+4 ATK)", 
        "Health Potion", 
        "Mana Potion", 
        "Throwing Dagger"
    ])
    spells: List[str] = Field(default_factory=lambda: [
        "Fireball (15 Mana)", 
        "Minor Heal (20 Mana)", 
        "Arcane Strike (10 Mana)"
    ])
    active_quests: List[str] = Field(default_factory=lambda: [
        "Investigate the cellar noises in the Tavern"
    ])
    completed_quests: List[str] = Field(default_factory=list)
    turn_count: int = 0
    in_combat: bool = False
    current_enemy: Optional[EnemyState] = None

    @property
    def total_attack(self) -> int:
        bonus = 0
        if "+" in self.equipped_weapon:
            import re
            m = re.search(r"\+(\d+)\s*ATK", self.equipped_weapon, re.IGNORECASE)
            if m:
                bonus = int(m.group(1))
        return self.base_attack + (self.level * 2) + bonus

    @property
    def total_defense(self) -> int:
        bonus = 0
        if "+" in self.equipped_armor:
            import re
            m = re.search(r"\+(\d+)\s*DEF", self.equipped_armor, re.IGNORECASE)
            if m:
                bonus = int(m.group(1))
        return self.base_defense + self.level + bonus

class TurnAction(BaseModel):
    narrative_response: str = Field(description="Narrative story describing the outcome.")
    location_change: Optional[str] = Field(default=None, description="New location if moved.")
    item_added: Optional[str] = Field(default=None, description="Acquired item name.")
    item_removed: Optional[str] = Field(default=None, description="Lost or used item name.")
    health_change: Optional[int] = Field(default=None, description="Damage (-) or Heal (+).")
    mana_change: Optional[int] = Field(default=None, description="Mana spend (-) or restore (+).")
    gold_change: Optional[int] = Field(default=None, description="Gold gained (+) or spent (-).")
    xp_change: Optional[int] = Field(default=None, description="XP gained.")
    quest_update: Optional[str] = Field(default=None, description="Quest progress or new quest.")
    quest_completed: Optional[str] = Field(default=None, description="Completed quest name.")
    trigger_combat: Optional[EnemyState] = Field(default=None, description="Spawns an enemy combat encounter.")
    suggested_actions: Optional[List[str]] = Field(default=None, description="3-4 quick choice suggestions for player.")