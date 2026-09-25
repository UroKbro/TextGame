import time
from typing import Dict, List, Tuple, Optional
import graphics as gfx
from schema import GameState
from factions import get_reputation_tier
from input_utils import read_valid_input

SHOPS: Dict[str, Dict] = {
    "tavern": {
        "name": "🍺 Whispering Oak Tavern Barkeep",
        "faction": "Kingdom of Oakhaven",
        "description": "Hearty stews, spiced ale, torches, and local traveling supplies.",
        "inventory": [
            {"name": "Health Potion", "base_price": 20, "type": "consumable", "desc": "Restores 40 HP instantly."},
            {"name": "Mana Potion", "base_price": 20, "type": "consumable", "desc": "Restores 30 MP instantly."},
            {"name": "Traveler's Rations", "base_price": 10, "type": "consumable", "desc": "Restores 15 HP and 10 MP."},
            {"name": "Torch", "base_price": 5, "type": "tool", "desc": "Illuminates dark catacombs and caves."}
        ]
    },
    "blacksmith": {
        "name": "⚒️ Oakhaven Ironworks & Armory",
        "faction": "Kingdom of Oakhaven",
        "description": "Anvil-forged steel swords, spiked shields, plate armor, and crafting ore.",
        "inventory": [
            {"name": "Iron Shortsword (+6 ATK)", "base_price": 35, "type": "weapon", "desc": "Sturdy forged iron blade."},
            {"name": "Silver Longsword (+9 ATK)", "base_price": 65, "type": "weapon", "desc": "Balanced blade gleaming with silver."},
            {"name": "Reinforced Leather (+5 DEF)", "base_price": 40, "type": "armor", "desc": "Hardened beast leather armor."},
            {"name": "Knight's Steel Plate (+8 DEF)", "base_price": 80, "type": "armor", "desc": "Heavy interlocking steel armor."},
            {"name": "Throwing Dagger", "base_price": 12, "type": "combat_item", "desc": "Quick throwing blade (18 DMG)."},
            {"name": "Iron Ore", "base_price": 8, "type": "material", "desc": "Crafting reagent for smithing."}
        ]
    },
    "apothecary": {
        "name": "🧪 Mystic Herbalist & Alchemist",
        "faction": "Sylvan Druids",
        "description": "Rare forest herbs, distilled concoctions, arcane dust, and alchemy recipes.",
        "inventory": [
            {"name": "Health Potion", "base_price": 18, "type": "consumable", "desc": "Restores 40 HP instantly."},
            {"name": "Mana Potion", "base_price": 18, "type": "consumable", "desc": "Restores 30 MP instantly."},
            {"name": "Cave Moss", "base_price": 6, "type": "material", "desc": "Alchemy reagent found in deep cellars."},
            {"name": "Silver Herb", "base_price": 10, "type": "material", "desc": "Rare medicinal herb blessed by moonlight."},
            {"name": "Arcane Dust", "base_price": 15, "type": "material", "desc": "Shimmering residual magical particles."},
            {"name": "Recipe: Elixir of Titan Strength", "base_price": 50, "type": "recipe", "desc": "Teaches permanent +2 ATK elixir."}
        ]
    },
    "black_market": {
        "name": "🕶️ Shadow Syndicate Black Market",
        "faction": "The Shadow Syndicate",
        "description": "Contraband weapons, forbidden alchemy, throwing poisons, and stolen relics.",
        "inventory": [
            {"name": "Shadow Poison Vial", "base_price": 30, "type": "combat_item", "desc": "Venom coating dealing poison over time."},
            {"name": "Volatile Fire Bomb", "base_price": 28, "type": "combat_item", "desc": "Combat explosive dealing 35 DMG."},
            {"name": "Monster Bone", "base_price": 10, "type": "material", "desc": "Hardened skeleton and beast bone."},
            {"name": "Recipe: Knight's Steel Plate (+8 DEF)", "base_price": 60, "type": "recipe", "desc": "Heavy armor smithing schematic."},
            {"name": "Gleaming Ruby (+50 Gold)", "base_price": 45, "type": "gem", "desc": "Stolen gemstone of high value."}
        ]
    }
}

ITEM_SELL_PRICES = {
    "Health Potion": 10,
    "Mana Potion": 10,
    "Torch": 2,
    "Rusty Dagger (+4 ATK)": 5,
    "Iron Shortsword (+6 ATK)": 18,
    "Silver Longsword (+9 ATK)": 35,
    "Leather Tunic (+3 DEF)": 8,
    "Reinforced Leather (+5 DEF)": 20,
    "Knight's Steel Plate (+8 DEF)": 45,
    "Throwing Dagger": 6,
    "Iron Ore": 4,
    "Cave Moss": 3,
    "Silver Herb": 5,
    "Arcane Dust": 8,
    "Monster Bone": 5,
    "Gleaming Ruby (+50 Gold)": 50,
    "Volatile Fire Bomb": 14,
    "Shadow Poison Vial": 15
}

def get_item_price(base_price: int, state: GameState, faction_name: str) -> int:
    """Calculate price based on base price and Faction reputation tier."""
    rep = state.reputation.get(faction_name, 0)
    _, _, price_mult = get_reputation_tier(rep)
    return max(1, int(round(base_price * price_mult)))

def get_sell_price(item_name: str) -> int:
    """Return sell gold value for an item."""
    if item_name in ITEM_SELL_PRICES:
        return ITEM_SELL_PRICES[item_name]
    if "+ " in item_name or "ATK" in item_name:
        return 15
    if "DEF" in item_name:
        return 15
    return 5

def buy_item(state: GameState, shop_key: str, item_idx: int) -> Tuple[bool, str]:
    if shop_key not in SHOPS:
        return False, "Shop not found."
    shop = SHOPS[shop_key]
    if item_idx < 0 or item_idx >= len(shop["inventory"]):
        return False, "Invalid item selection."
        
    item = shop["inventory"][item_idx]
    price = get_item_price(item["base_price"], state, shop["faction"])
    
    if state.gold < price:
        return False, f"Not enough gold! Costs {price} Gold, you have {state.gold}."
        
    state.gold -= price
    name = item["name"]
    
    if item["type"] == "material":
        state.materials[name] = state.materials.get(name, 0) + 1
        msg = f"Bought {gfx.BRIGHT_YELLOW}{name}{gfx.RESET} (stored in Materials bag)."
    elif item["type"] == "recipe":
        recipe_name = name.replace("Recipe: ", "")
        if recipe_name not in state.known_recipes:
            state.known_recipes.append(recipe_name)
        msg = f"Learned recipe {gfx.BRIGHT_MAGENTA}{recipe_name}{gfx.RESET}!"
    else:
        state.inventory.append(name)
        msg = f"Purchased {gfx.BRIGHT_GREEN}{name}{gfx.RESET}! Added to your inventory."
        
    return True, msg

def sell_item(state: GameState, item_name: str) -> Tuple[bool, str]:
    if item_name in state.inventory:
        state.inventory.remove(item_name)
        val = get_sell_price(item_name)
        state.gold += val
        return True, f"Sold {gfx.BRIGHT_WHITE}{item_name}{gfx.RESET} for {gfx.BRIGHT_YELLOW}{val} Gold{gfx.RESET}!"
    elif item_name in state.materials and state.materials[item_name] > 0:
        state.materials[item_name] -= 1
        if state.materials[item_name] <= 0:
            del state.materials[item_name]
        val = get_sell_price(item_name)
        state.gold += val
        return True, f"Sold 1x {gfx.BRIGHT_WHITE}{item_name}{gfx.RESET} for {gfx.BRIGHT_YELLOW}{val} Gold{gfx.RESET}!"
    return False, "You do not own this item."

def run_shop_ui(state: GameState, initial_shop: str = "tavern"):
    """Interactive Merchant & Trading Interface."""
    current_shop = initial_shop
    
    while True:
        gfx.clear_screen()
        w = gfx.get_term_width()
        shop_data = SHOPS.get(current_shop, SHOPS["tavern"])
        fac_name = shop_data["faction"]
        rep = state.reputation.get(fac_name, 0)
        tier, color, mult = get_reputation_tier(rep)
        disc_text = f"{int((1.0-mult)*100)}% Discount" if mult < 1.0 else (f"{int((mult-1.0)*100)}% Surcharge" if mult > 1.0 else "Normal Prices")
        
        banner_lines = [
            f"{gfx.BRIGHT_WHITE}{shop_data['description']}{gfx.RESET}",
            f"{gfx.BOLD}Faction Standing:{gfx.RESET} {color}{tier}{gfx.RESET} with {fac_name} ({disc_text})",
            f"{gfx.BOLD}Your Purse:{gfx.RESET} {gfx.BRIGHT_YELLOW}{state.gold} Gold coins{gfx.RESET}",
            "─" * (w - 6),
            f"{gfx.BOLD}ITEMS FOR SALE:{gfx.RESET}"
        ]
        
        for idx, it in enumerate(shop_data["inventory"], 1):
            price = get_item_price(it["base_price"], state, fac_name)
            can_afford = state.gold >= price
            afford_tag = f"{gfx.BRIGHT_GREEN}{price}g{gfx.RESET}" if can_afford else f"{gfx.RED}{price}g{gfx.RESET}"
            banner_lines.append(f" [{idx}] {gfx.BRIGHT_WHITE}{it['name']}{gfx.RESET} - {afford_tag}")
            banner_lines.append(f"     {gfx.DIM}{it['desc']}{gfx.RESET}")
            
        banner_lines.append("─" * (w - 6))
        banner_lines.append(f"{gfx.BOLD}SWITCH STALLS:{gfx.RESET} [T] Tavern  [B] Blacksmith  [A] Apothecary  [M] Black Market")
        banner_lines.append(f"{gfx.BOLD}SELL ITEMS:{gfx.RESET}    [S] Open Sell Counter")
        
        print(gfx.draw_box(f"{shop_data['name']}", banner_lines, width=w, border_color=gfx.BRIGHT_YELLOW))
        print(f"\n{gfx.BOLD}Enter item # to buy, stall key (T/B/A/M/S), or [0] to exit:{gfx.RESET}")
        
        choice = read_valid_input(
            f"{gfx.BRIGHT_YELLOW}Merchant Choice > {gfx.RESET}",
            ["0", "t", "b", "a", "m", "s"],
            numeric_range=range(1, len(shop_data["inventory"]) + 1)
        )
        
        if choice == "0":
            break
        elif choice == "t":
            current_shop = "tavern"
        elif choice == "b":
            current_shop = "blacksmith"
        elif choice == "a":
            current_shop = "apothecary"
        elif choice == "m":
            synd_rep = state.reputation.get("The Shadow Syndicate", 0)
            if synd_rep < -10:
                print(f"\n{gfx.RED}❌ The Shadow Syndicate doors are barred to you! Your reputation is too hostile.{gfx.RESET}")
                time.sleep(1.2)
            else:
                current_shop = "black_market"
        elif choice == "s":
            run_sell_ui(state)
        elif choice.isdigit():
            idx = int(choice) - 1
            ok, msg = buy_item(state, current_shop, idx)
            if ok:
                print(f"\n{gfx.BRIGHT_GREEN}🪙 Clink! {msg}{gfx.RESET}")
            else:
                print(f"\n{gfx.RED}❌ {msg}{gfx.RESET}")
            time.sleep(1.0)

def run_sell_ui(state: GameState):
    while True:
        gfx.clear_screen()
        w = gfx.get_term_width()
        sellable = list(state.inventory)
        
        lines = [
            f"{gfx.BOLD}Your Purse:{gfx.RESET} {gfx.BRIGHT_YELLOW}{state.gold} Gold coins{gfx.RESET}",
            f"{gfx.DIM}Select an item from your pack to sell for gold:{gfx.RESET}",
            "─" * (w - 6)
        ]
        
        for idx, it in enumerate(sellable, 1):
            val = get_sell_price(it)
            lines.append(f" [{idx}] {it} -> {gfx.BRIGHT_YELLOW}+{val} Gold{gfx.RESET}")
            
        print(gfx.draw_box("💰 Merchant Counter: Sell Items", lines, width=w, border_color=gfx.YELLOW))
        print(f"\n{gfx.BOLD}Enter item # to sell, or [0] to return to merchant:{gfx.RESET}")
        
        choice = read_valid_input(
            f"{gfx.BRIGHT_YELLOW}Sell # > {gfx.RESET}",
            ["0"],
            numeric_range=range(1, len(sellable) + 1)
        )
        
        if choice == "0":
            break
            
        idx = int(choice) - 1
        if 0 <= idx < len(sellable):
            it_name = sellable[idx]
            ok, msg = sell_item(state, it_name)
            if ok:
                print(f"\n{gfx.BRIGHT_GREEN}🪙 {msg}{gfx.RESET}")
            time.sleep(0.9)
