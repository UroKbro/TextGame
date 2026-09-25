import time
from typing import Dict, List, Tuple, Optional
import graphics as gfx
from schema import GameState
from input_utils import read_valid_input

RECIPES: Dict[str, Dict] = {
    # 🧪 Alchemy
    "Health Potion": {
        "category": "Alchemy",
        "ingredients": {"Cave Moss": 2, "Silver Herb": 1},
        "result_type": "consumable",
        "description": "Restores 40 Health instantly."
    },
    "Mana Potion": {
        "category": "Alchemy",
        "ingredients": {"Silver Herb": 2, "Arcane Dust": 1},
        "result_type": "consumable",
        "description": "Restores 30 Mana points."
    },
    "Elixir of Titan Strength": {
        "category": "Alchemy",
        "ingredients": {"Monster Bone": 2, "Iron Ore": 2, "Silver Herb": 1},
        "result_type": "permanent_buff",
        "description": "Permanently increases Base Attack by +2!"
    },
    "Elixir of Iron Skin": {
        "category": "Alchemy",
        "ingredients": {"Iron Ore": 3, "Cave Moss": 2},
        "result_type": "permanent_buff",
        "description": "Permanently increases Base Defense by +2!"
    },
    "Volatile Fire Bomb": {
        "category": "Alchemy",
        "ingredients": {"Arcane Dust": 2, "Iron Ore": 1},
        "result_type": "combat_item",
        "description": "Hurled in combat dealing 35 Explosive Fire Damage."
    },

    # ⚒️ Blacksmithing
    "Throwing Dagger": {
        "category": "Blacksmithing",
        "ingredients": {"Iron Ore": 1},
        "result_type": "combat_item",
        "description": "Quick throwing blade dealing 18 damage in combat."
    },
    "Iron Shortsword (+6 ATK)": {
        "category": "Blacksmithing",
        "ingredients": {"Iron Ore": 3, "Monster Bone": 1},
        "result_type": "weapon",
        "description": "Sturdy forged iron blade (+6 ATK)."
    },
    "Silver Longsword (+9 ATK)": {
        "category": "Blacksmithing",
        "ingredients": {"Iron Ore": 5, "Silver Herb": 2, "Arcane Dust": 1},
        "result_type": "weapon",
        "description": "Finely balanced gleaming silver sword (+9 ATK)."
    },
    "Reinforced Leather (+5 DEF)": {
        "category": "Blacksmithing",
        "ingredients": {"Monster Bone": 3, "Cave Moss": 2},
        "result_type": "armor",
        "description": "Tough hide reinforced with hardened bone plates (+5 DEF)."
    },
    "Knight's Steel Plate (+8 DEF)": {
        "category": "Blacksmithing",
        "ingredients": {"Iron Ore": 6, "Monster Bone": 3},
        "result_type": "armor",
        "description": "Heavy interlocking steel chestpiece (+8 DEF)."
    },

    # ✨ Enchanting
    "Scroll of Arcane Surge": {
        "category": "Enchanting",
        "ingredients": {"Arcane Dust": 3, "Silver Herb": 1},
        "result_type": "consumable",
        "description": "Restores 50 Mana and boosts magic damage."
    },
    "Shadow Poison Vial": {
        "category": "Enchanting",
        "ingredients": {"Cave Moss": 3, "Monster Bone": 2, "Arcane Dust": 1},
        "result_type": "combat_item",
        "description": "Coats blades in venom to deal 10 damage per turn."
    }
}

def can_craft(state: GameState, recipe_name: str) -> Tuple[bool, str]:
    if recipe_name not in RECIPES:
        return False, "Unknown recipe."
    if recipe_name not in state.known_recipes:
        return False, "Recipe has not been discovered yet."
        
    recipe = RECIPES[recipe_name]
    for mat, qty in recipe["ingredients"].items():
        have = state.materials.get(mat, 0)
        if have < qty:
            return False, f"Missing materials: Need {qty}x {mat} (Have {have})"
            
    return True, "Ready to craft."

def craft_item(state: GameState, recipe_name: str) -> Tuple[bool, str]:
    ok, reason = can_craft(state, recipe_name)
    if not ok:
        return False, reason
        
    recipe = RECIPES[recipe_name]
    # Consume materials
    for mat, qty in recipe["ingredients"].items():
        state.materials[mat] -= qty
        if state.materials[mat] <= 0:
            del state.materials[mat]
            
    # Apply Result
    res_type = recipe["result_type"]
    if res_type == "permanent_buff":
        if "Strength" in recipe_name:
            state.base_attack += 2
            msg = f"✨ Drank {recipe_name}! Permanently gained {gfx.BRIGHT_RED}+2 Base ATK{gfx.RESET}!"
        else:
            state.base_defense += 2
            msg = f"✨ Drank {recipe_name}! Permanently gained {gfx.BRIGHT_BLUE}+2 Base DEF{gfx.RESET}!"
    elif res_type in ["weapon", "armor"]:
        state.inventory.append(recipe_name)
        msg = f"⚒️ Crafted {gfx.BRIGHT_GREEN}{recipe_name}{gfx.RESET}! Added to your inventory."
    else:
        state.inventory.append(recipe_name)
        msg = f"🧪 Concocted {gfx.BRIGHT_CYAN}{recipe_name}{gfx.RESET}! Added to your inventory."
        
    return True, msg

def run_crafting_loop(state: GameState):
    while True:
        gfx.clear_screen()
        w = gfx.get_term_width()
        
        # Materials Header
        mat_list = [f"{gfx.BRIGHT_YELLOW}{m}{gfx.RESET}: {q}x" for m, q in state.materials.items()]
        mat_str = " │ ".join(mat_list) if mat_list else f"{gfx.DIM}No materials gathered{gfx.RESET}"
        
        banner_lines = [
            f"{gfx.BOLD}🎒 GATHERED REAGENTS & MATERIALS:{gfx.RESET}",
            f" {mat_str}",
            "─" * (w - 6),
            f"{gfx.BRIGHT_WHITE}Select a recipe to craft with your materials:{gfx.RESET}"
        ]
        
        recipe_options = []
        for name in state.known_recipes:
            if name in RECIPES:
                recipe = RECIPES[name]
                reqs = [f"{q}x {m} (have {state.materials.get(m, 0)})" for m, q in recipe["ingredients"].items()]
                req_str = ", ".join(reqs)
                can_do, _ = can_craft(state, name)
                status_icon = f"{gfx.BRIGHT_GREEN}[CRAFTABLE]{gfx.RESET}" if can_do else f"{gfx.RED}[LACK MATERIALS]{gfx.RESET}"
                recipe_options.append((name, recipe, req_str, can_do, status_icon))
                
        for idx, (name, rec, req_str, can_do, status_icon) in enumerate(recipe_options, 1):
            cat_icon = "🧪" if rec["category"] == "Alchemy" else ("⚒️" if rec["category"] == "Blacksmithing" else "✨")
            banner_lines.append(f" [{idx}] {cat_icon} {gfx.BOLD}{name}{gfx.RESET} {status_icon}")
            banner_lines.append(f"     Cost: {gfx.DIM}{req_str}{gfx.RESET}")
            banner_lines.append(f"     Effect: {gfx.BRIGHT_CYAN}{rec['description']}{gfx.RESET}")
            
        print(gfx.draw_box("⚒️ Workshop, Alchemy Lab & Crafting Forge", banner_lines, width=w, border_color=gfx.BRIGHT_MAGENTA))
        print(f"\n{gfx.BOLD}Enter recipe # to craft, or [0] to return to adventure:{gfx.RESET}")
        
        choice = read_valid_input(
            f"{gfx.BRIGHT_YELLOW}Craft # > {gfx.RESET}",
            ["0"],
            numeric_range=range(1, len(recipe_options) + 1)
        )
        
        if choice == "0":
            break
            
        idx = int(choice) - 1
        if 0 <= idx < len(recipe_options):
            name = recipe_options[idx][0]
            ok, msg = craft_item(state, name)
            if ok:
                print(f"\n{gfx.BRIGHT_GREEN}🔨 CLANG! BUBBLE! {msg}{gfx.RESET}")
            else:
                print(f"\n{gfx.RED}❌ Cannot craft: {msg}{gfx.RESET}")
            time.sleep(1.2)
