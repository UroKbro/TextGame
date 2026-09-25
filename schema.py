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

class QuestChoice(BaseModel):
    choice_id: str
    description: str
    consequence_summary: str
    faction_impact: Dict[str, int] = Field(default_factory=dict)
    gold_reward: int = 0
    xp_reward: int = 0
    item_reward: Optional[str] = None
    recipe_reward: Optional[str] = None

class QuestState(BaseModel):
    quest_id: str
    title: str
    description: str
    stage: int = 1
    max_stages: int = 3
    is_completed: bool = False
    is_failed: bool = False
    chosen_branch: Optional[str] = None
    aligned_faction: Optional[str] = None
    available_choices: List[QuestChoice] = Field(default_factory=list)

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
    gold: int = 45
    base_attack: int = 10
    base_defense: int = 5
    equipped_weapon: str = "Rusty Dagger (+4 ATK)"
    equipped_armor: str = "Leather Tunic (+3 DEF)"
    
    # Inventory items (consumables, gear, tools)
    inventory: List[str] = Field(default_factory=lambda: [
        "Torch", 
        "Rusty Dagger (+4 ATK)", 
        "Health Potion", 
        "Mana Potion", 
        "Throwing Dagger"
    ])
    
    # Crafting Materials / Reagents
    materials: Dict[str, int] = Field(default_factory=lambda: {
        "Iron Ore": 3,
        "Cave Moss": 4,
        "Silver Herb": 2,
        "Arcane Dust": 1,
        "Monster Bone": 2
    })
    
    # Unlocked Crafting Recipes
    known_recipes: List[str] = Field(default_factory=lambda: [
        "Health Potion",
        "Mana Potion",
        "Throwing Dagger",
        "Iron Shortsword (+6 ATK)",
        "Reinforced Leather (+5 DEF)"
    ])
    
    # Faction Standings (-100 to +100)
    reputation: Dict[str, int] = Field(default_factory=lambda: {
        "Kingdom of Oakhaven": 10,
        "The Shadow Syndicate": 0,
        "The Arcane Order": 5,
        "Sylvan Druids": 5
    })
    
    # Spells known
    spells: List[str] = Field(default_factory=lambda: [
        "Fireball (15 Mana)", 
        "Minor Heal (20 Mana)", 
        "Arcane Strike (10 Mana)"
    ])
    
    # Quests
    active_quests: List[str] = Field(default_factory=lambda: [
        "Investigate the cellar noises in the Tavern"
    ])
    completed_quests: List[str] = Field(default_factory=list)
    quests_data: Dict[str, QuestState] = Field(default_factory=dict)
    
    # Decision / Choice Log
    choice_history: List[str] = Field(default_factory=list)
    
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
    location_change: Optional[str] = Field(default=None, description="New Location if moved.")
    item_added: Optional[str] = Field(default=None, description="Acquired item name.")
    item_removed: Optional[str] = Field(default=None, description="Lost or used item name.")
    materials_added: Optional[Dict[str, int]] = Field(default=None, description="Crafting materials gathered.")
    materials_removed: Optional[Dict[str, int]] = Field(default=None, description="Crafting materials consumed.")
    recipe_unlocked: Optional[str] = Field(default=None, description="New crafting recipe discovered.")
    health_change: Optional[int] = Field(default=None, description="Damage (-) or Heal (+).")
    mana_change: Optional[int] = Field(default=None, description="Mana spend (-) or restore (+).")
    gold_change: Optional[int] = Field(default=None, description="Gold gained (+) or spent (-).")
    xp_change: Optional[int] = Field(default=None, description="XP gained.")
    reputation_change: Optional[Dict[str, int]] = Field(default=None, description="Faction reputation shifts.")
    quest_update: Optional[str] = Field(default=None, description="Quest progress or new quest title.")
    quest_completed: Optional[str] = Field(default=None, description="Completed quest title.")
    choice_recorded: Optional[str] = Field(default=None, description="Key decision recorded in hero history.")
    trigger_combat: Optional[EnemyState] = Field(default=None, description="Spawns an enemy combat encounter.")
    suggested_actions: Optional[List[str]] = Field(default=None, description="3-4 quick choice suggestions for player.")