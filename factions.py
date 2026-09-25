from typing import Dict, Tuple, List
import graphics as gfx
from schema import GameState

FACTION_INFO = {
    "Kingdom of Oakhaven": {
        "emblem": "🛡️",
        "description": "Town guards and knights upholding justice, order, and civilization.",
        "perk": "Shop discounts with local merchants, knight gear access, guard protection."
    },
    "The Shadow Syndicate": {
        "emblem": "🗡️",
        "description": "Underworld network of rogues, fences, poisoners, and smugglers.",
        "perk": "Unlocks the Black Market, lockpicking contracts, and poison recipes."
    },
    "The Arcane Order": {
        "emblem": "🔮",
        "description": "Scholars and mages researching ancient leylines, ruins, and grimoires.",
        "perk": "Unlocks spell tomes, magic crafting reagents, and arcane relics."
    },
    "Sylvan Druids": {
        "emblem": "🌿",
        "description": "Circle of forest guardians, beast-tamers, and master herbalists.",
        "perk": "Unlocks rare potion recipes, herbal gathering bonuses, and nature blessings."
    }
}

def get_reputation_tier(score: int) -> Tuple[str, str, float]:
    if score >= 75:
        return "Exalted", gfx.BRIGHT_YELLOW, 0.70  # 30% discount
    elif score >= 50:
        return "Honored", gfx.BRIGHT_CYAN, 0.80    # 20% discount
    elif score >= 25:
        return "Friendly", gfx.BRIGHT_GREEN, 0.90  # 10% discount
    elif score >= 0:
        return "Neutral", gfx.BRIGHT_WHITE, 1.00   # standard price
    elif score >= -30:
        return "Suspicious", gfx.YELLOW, 1.20      # 20% markup
    else:
        return "Hostile", gfx.BRIGHT_RED, 1.50     # 50% markup / hostile

def modify_reputation(state: GameState, faction_name: str, delta: int) -> str:
    if faction_name not in state.reputation:
        state.reputation[faction_name] = 0
        
    old_score = state.reputation[faction_name]
    new_score = max(-100, min(100, old_score + delta))
    state.reputation[faction_name] = new_score
    
    old_tier, _, _ = get_reputation_tier(old_score)
    new_tier, color, _ = get_reputation_tier(new_score)
    
    sign = "+" if delta > 0 else ""
    msg = f"{FACTION_INFO.get(faction_name, {}).get('emblem', '🏛️')} {faction_name}: {sign}{delta} Rep (Now {new_score} - {color}{new_tier}{gfx.RESET})"
    return msg

def render_faction_sheet(state: GameState) -> str:
    w = gfx.get_term_width()
    lines = []
    
    for fac, info in FACTION_INFO.items():
        score = state.reputation.get(fac, 0)
        tier, color, discount = get_reputation_tier(score)
    
        pct = (score + 100) / 200.0
        bar_len = 16
        filled = int(round(pct * bar_len))
        empty = bar_len - filled
        bar_str = f"{color}{'■' * filled}{gfx.BRIGHT_BLACK}{'░' * empty}{gfx.RESET}"
        
        disc_str = f"({int((1.0 - discount)*100)}% Discount)" if discount < 1.0 else (f"({int((discount - 1.0)*100)}% Markup)" if discount > 1.0 else "")
        
        lines.append(f"{info['emblem']} {gfx.BOLD}{fac}{gfx.RESET}  [{bar_str}]  Score: {score:+d}")
        lines.append(f"   Standing: {color}{tier}{gfx.RESET} {disc_str}")
        lines.append(f"   {gfx.DIM}{info['description']}{gfx.RESET}")
        lines.append(f"   {gfx.BRIGHT_MAGENTA}Perks:{gfx.RESET} {info['perk']}")
        lines.append("─" * (w - 6))
        
    if lines:
        lines.pop() # remove last divider
        
    return gfx.draw_box("Faction Standing & Global Reputation", lines, width=w, border_color=gfx.BRIGHT_BLUE)
