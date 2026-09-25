import time
from typing import Dict, List, Tuple, Optional
import graphics as gfx
from schema import GameState, QuestState, QuestChoice
from factions import modify_reputation
from input_utils import read_valid_input

BRANCHING_QUESTS: Dict[str, Dict] = {
    "cellar_mystery": {
        "id": "cellar_mystery",
        "title": "The Whispering Cellar Mystery",
        "description": "Strange unearthly sounds echo from the cellar beneath the Whispering Oak Tavern.",
        "stage": 1,
        "max_stages": 2,
        "branches": {
            "slay": {
                "title": "🗡️ Path of the Mercenary: Slay the Beast",
                "summary": "You slew the cellar monstrosity without hesitation, bringing peace to the Barkeep.",
                "reputation": {"Kingdom of Oakhaven": 20, "Sylvan Druids": -10},
                "gold": 40,
                "xp": 40,
                "item": "Health Potion",
                "recipe": None
            },
            "cure": {
                "title": "🌿 Path of Compassion: Cure the Mutated Druid",
                "summary": "You recognized the beast was a transformed Druid apprentice and cured them with herbs.",
                "reputation": {"Sylvan Druids": 30, "Kingdom of Oakhaven": 10},
                "gold": 20,
                "xp": 55,
                "item": "Silver Herb",
                "recipe": "Silver Longsword (+9 ATK)"
            },
            "smuggle": {
                "title": "🕶️ Path of the Outlaw: Deal with the Smugglers",
                "summary": "You struck a secret pact with the Goblin smugglers using the cellar tunnel.",
                "reputation": {"The Shadow Syndicate": 30, "Kingdom of Oakhaven": -15},
                "gold": 75,
                "xp": 35,
                "item": "Shadow Poison Vial",
                "recipe": "Shadow Poison Vial"
            }
        }
    },
    "arcane_crystal": {
        "id": "arcane_crystal",
        "title": "The Stolen Arcane Relay",
        "description": "An ancient pulsing leyline crystal lies in the heart of the Ruined Citadel.",
        "stage": 1,
        "max_stages": 2,
        "branches": {
            "arcane_order": {
                "title": "🔮 Return to the Arcane Order",
                "summary": "You restored the crystal to the Mage Academy, unlocking grand wizardry.",
                "reputation": {"The Arcane Order": 35, "The Shadow Syndicate": -10},
                "gold": 30,
                "xp": 60,
                "item": "Scroll of Arcane Surge",
                "recipe": "Scroll of Arcane Surge"
            },
            "black_market": {
                "title": "💰 Sell on the Black Market",
                "summary": "You sold the enchanted crystal for a staggering pouch of gold to the Syndicate.",
                "reputation": {"The Shadow Syndicate": 35, "The Arcane Order": -20},
                "gold": 120,
                "xp": 30,
                "item": "Gleaming Ruby (+50 Gold)",
                "recipe": None
            },
            "sylvan_grove": {
                "title": "🌿 Infuse the Sylvan Grove",
                "summary": "You planted the crystal into the ancient World Tree root, blessing all life.",
                "reputation": {"Sylvan Druids": 40, "Kingdom of Oakhaven": 10},
                "gold": 10,
                "xp": 50,
                "item": "Elixir of Titan Strength",
                "recipe": "Elixir of Titan Strength"
            }
        }
    },
    "town_stand": {
        "id": "town_stand",
        "title": "Shadows Over Oakhaven",
        "description": "Tensions boil over as three powers vie for dominion over the frontier settlement.",
        "stage": 1,
        "max_stages": 2,
        "branches": {
            "guard_order": {
                "title": "🛡️ Stand with the Oakhaven Town Guard",
                "summary": "You rallied the town watch and established lawful order across the realm.",
                "reputation": {"Kingdom of Oakhaven": 45, "The Shadow Syndicate": -30},
                "gold": 60,
                "xp": 80,
                "item": "Knight's Steel Plate (+8 DEF)",
                "recipe": "Knight's Steel Plate (+8 DEF)"
            },
            "syndicate_takeover": {
                "title": "🗡️ Back the Shadow Syndicate Heist",
                "summary": "You orchestrated a coup, seizing the treasury and placing outlaws in power.",
                "reputation": {"The Shadow Syndicate": 50, "Kingdom of Oakhaven": -40},
                "gold": 180,
                "xp": 60,
                "item": "Gleaming Ruby (+50 Gold)",
                "recipe": None
            },
            "druid_sanctuary": {
                "title": "🌿 Reclaim the Land for the Sylvan Circle",
                "summary": "You channeled the earth leylines, transforming the town into a sacred grove.",
                "reputation": {"Sylvan Druids": 50, "The Shadow Syndicate": -20},
                "gold": 40,
                "xp": 90,
                "item": "Elixir of Iron Skin",
                "recipe": "Elixir of Iron Skin"
            }
        }
    }
}

def resolve_quest_branch(state: GameState, quest_id: str, branch_key: str) -> str:
    """Apply rewards, reputation shifts, recipes, and record choice."""
    if quest_id not in BRANCHING_QUESTS:
        return "Unknown quest."
    q_data = BRANCHING_QUESTS[quest_id]
    if branch_key not in q_data["branches"]:
        return "Unknown branch choice."
        
    branch = q_data["branches"][branch_key]
    
    # 1. Apply Rewards
    state.gold += branch["gold"]
    state.xp += branch["xp"]
    
    # 2. Apply Reputation Changes
    rep_msgs = []
    for fac, delta in branch["reputation"].items():
        msg = modify_reputation(state, fac, delta)
        rep_msgs.append(msg)
        
    # 3. Item & Recipe unlocks
    if branch["item"]:
        state.inventory.append(branch["item"])
    if branch["recipe"] and branch["recipe"] not in state.known_recipes:
        state.known_recipes.append(branch["recipe"])
        
    # 4. Quest Log & History Tracking
    choice_entry = f"[{q_data['title']}] {branch['title']}: {branch['summary']}"
    state.choice_history.append(choice_entry)
    
    # Move quest from active to completed
    for active_title in list(state.active_quests):
        if q_data["title"].lower() in active_title.lower() or "cellar" in active_title.lower() and quest_id == "cellar_mystery":
            state.active_quests.remove(active_title)
            
    completed_str = f"{q_data['title']} ({branch['title']})"
    if completed_str not in state.completed_quests:
        state.completed_quests.append(completed_str)
        
    summary = (
        f"\n{gfx.BRIGHT_YELLOW}⭐ QUEST RESOLVED: {q_data['title']}{gfx.RESET}\n"
        f"  {gfx.BRIGHT_WHITE}{branch['summary']}{gfx.RESET}\n"
        f"  + Earned {gfx.BRIGHT_YELLOW}{branch['gold']} Gold{gfx.RESET} and {gfx.BRIGHT_CYAN}{branch['xp']} XP{gfx.RESET}!\n"
    )
    if branch["item"]:
        summary += f"  + Acquired Item: {gfx.BRIGHT_GREEN}{branch['item']}{gfx.RESET}\n"
    if branch["recipe"]:
        summary += f"  + Unlocked Recipe: {gfx.BRIGHT_MAGENTA}{branch['recipe']}{gfx.RESET}\n"
    summary += f"  Faction Shifts:\n    " + "\n    ".join(rep_msgs)
    
    return summary

def present_branching_decision(state: GameState, quest_id: str) -> Optional[str]:
    """Render interactive multi-choice decision modal."""
    if quest_id not in BRANCHING_QUESTS:
        return None
    q_data = BRANCHING_QUESTS[quest_id]
    w = gfx.get_term_width()
    
    lines = [
        f"{gfx.BRIGHT_YELLOW}{gfx.BOLD}CRITICAL STORY DECISION POINT{gfx.RESET}",
        f"{gfx.BRIGHT_WHITE}{q_data['description']}{gfx.RESET}",
        "─" * (w - 6),
        f"{gfx.BOLD}Choose your path and its consequences:{gfx.RESET}"
    ]
    
    branch_keys = list(q_data["branches"].keys())
    for idx, key in enumerate(branch_keys, 1):
        b = q_data["branches"][key]
        rep_preview = ", ".join([f"{f}: {d:+d}" for f, d in b["reputation"].items()])
        lines.append(f" [{idx}] {gfx.BOLD}{b['title']}{gfx.RESET}")
        lines.append(f"     Outcome: {gfx.DIM}{b['summary']}{gfx.RESET}")
        lines.append(f"     Rewards: {gfx.BRIGHT_YELLOW}{b['gold']}g{gfx.RESET}, {gfx.CYAN}{b['xp']} XP{gfx.RESET} │ Rep: {gfx.MAGENTA}{rep_preview}{gfx.RESET}")
        
    gfx.clear_screen()
    print(gfx.draw_box(f"⚔️ Moral Choice: {q_data['title']}", lines, width=w, border_color=gfx.BRIGHT_YELLOW))
    
    print(f"\n{gfx.BOLD}Enter your chosen path [1-{len(branch_keys)}]:{gfx.RESET}")
    choice = read_valid_input(
        f"{gfx.BRIGHT_YELLOW}Your Decision > {gfx.RESET}",
        [str(i) for i in range(1, len(branch_keys) + 1)]
    )
    
    idx = int(choice) - 1
    selected_branch = branch_keys[idx]
    res_msg = resolve_quest_branch(state, quest_id, selected_branch)
    print(res_msg)
    input(f"\n{gfx.DIM}Press Enter to continue your journey...{gfx.RESET}")
    return res_msg

def render_detailed_quest_log(state: GameState) -> str:
    """Render comprehensive branching Quest Journal & History."""
    w = gfx.get_term_width()
    lines = [
        f"{gfx.BRIGHT_YELLOW}{gfx.BOLD}📜 ACTIVE QUESTS:{gfx.RESET}"
    ]
    
    if state.active_quests:
        for q in state.active_quests:
            lines.append(f"  • {gfx.BRIGHT_CYAN}{q}{gfx.RESET}")
    else:
        lines.append(f"  {gfx.DIM}No active quests. Explore or talk to NPCs!{gfx.RESET}")
        
    lines.append("─" * (w - 6))
    lines.append(f"{gfx.BRIGHT_GREEN}{gfx.BOLD}✓ COMPLETED BRANCHES & STORY CHOICES:{gfx.RESET}")
    
    if state.choice_history:
        for ch in state.choice_history:
            lines.append(f"  • {gfx.BRIGHT_WHITE}{ch}{gfx.RESET}")
    elif state.completed_quests:
        for comp in state.completed_quests:
            lines.append(f"  • {gfx.BRIGHT_WHITE}{comp}{gfx.RESET}")
    else:
        lines.append(f"  {gfx.DIM}No major branch choices made yet.{gfx.RESET}")
        
    return gfx.draw_box("Chronicles: Branching Quest Journal", lines, width=w, border_color=gfx.BRIGHT_YELLOW)
