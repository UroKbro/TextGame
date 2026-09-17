import sys
import time
import random
import os
import shutil

# ==============================================================================
# ANSI Color & Style Constants
# ==============================================================================
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Standard Foreground Colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Bright Foreground Colors
BRIGHT_BLACK = "\033[90m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

# Background Colors
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_DARK = "\033[40m"

def get_term_width(default=75) -> int:
    try:
        w = shutil.get_terminal_size((default, 24)).columns
        return min(max(w, 60), 100)
    except Exception:
        return default

def clear_screen():
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.flush()

def typewriter(text: str, delay: float = 0.015, color: str = ""):
    """Print text with an animated typewriter effect."""
    sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        if char in [".", "!", "?"]:
            time.sleep(delay * 3)
        elif char == ",":
            time.sleep(delay * 2)
        else:
            time.sleep(delay)
    sys.stdout.write(RESET + "\n")
    sys.stdout.flush()

# ==============================================================================
# Progress & Status Bars
# ==============================================================================
def progress_bar(current: int, maximum: int, length: int = 15, fill_char="█", empty_char="░", color=BRIGHT_GREEN) -> str:
    current = max(0, min(current, maximum))
    pct = (current / maximum) if maximum > 0 else 0
    filled_len = int(round(length * pct))
    empty_len = length - filled_len
    bar = f"{color}{fill_char * filled_len}{BRIGHT_BLACK}{empty_char * empty_len}{RESET}"
    return f"[{bar}] {current}/{maximum}"

def health_bar(hp: int, max_hp: int, length: int = 15) -> str:
    pct = hp / max(1, max_hp)
    if pct > 0.5:
        c = BRIGHT_GREEN
    elif pct > 0.25:
        c = BRIGHT_YELLOW
    else:
        c = BRIGHT_RED
    return progress_bar(hp, max_hp, length=length, color=c)

def mana_bar(mana: int, max_mana: int, length: int = 15) -> str:
    return progress_bar(mana, max_mana, length=length, color=BRIGHT_CYAN)

def xp_bar(xp: int, xp_to_next: int, length: int = 15) -> str:
    return progress_bar(xp, xp_to_next, length=length, fill_char="▓", empty_char="░", color=BRIGHT_YELLOW)

# ==============================================================================
# Box & Window Rendering
# ==============================================================================
def draw_box(title: str, content_lines: list, width: int = 72, border_color: str = CYAN, title_color: str = BRIGHT_WHITE) -> str:
    """Render a framed box with title and border."""
    out = []
    inner_width = width - 4
    
    # Header
    if title:
        title_str = f"┤ {title_color}{BOLD}{title}{RESET}{border_color} ├"
        padding_left = 3
        dash_right = width - padding_left - len(title) - 6
        header = f"{border_color}┌─{title_str}{'─' * max(0, dash_right)}┐{RESET}"
    else:
        header = f"{border_color}┌{'─' * (width - 2)}┐{RESET}"
    out.append(header)
    
    # Body lines
    for line in content_lines:
        import re
        visible_len = len(re.sub(r'\033\[[0-9;]*m', '', line))
        pad = inner_width - visible_len
        if pad < 0:
            pad = 0
        out.append(f"{border_color}│ {RESET}{line}{' ' * pad} {border_color}│{RESET}")
    
    # Footer
    out.append(f"{border_color}└{'─' * (width - 2)}┘{RESET}")
    return "\n".join(out)

# ==============================================================================
# ASCII Visual Banners & Titles
# ==============================================================================
GAME_LOGO = f"""{BRIGHT_CYAN}
 ╔══════════════════════════════════════════════════════════════════════╗
 ║  {BRIGHT_YELLOW}███████╗██╗  ██╗ ██████╗██╗  ██╗ ██████╗ ███╗   ██╗██╗ ████████╗ {BRIGHT_CYAN}║
 ║  {BRIGHT_YELLOW}██╔════╝██║  ██║██╔════╝██║  ██║██╔═══██╗████╗  ██║██║ ╚══██╔══╝ {BRIGHT_CYAN}║
 ║  {BRIGHT_YELLOW}█████╗  ███████║██║     ███████║██║   ██║██╔██╗ ██║██║    ██║    {BRIGHT_CYAN}║
 ║  {BRIGHT_YELLOW}██╔══╝  ██╔══██║██║     ██╔══██║██║   ██║██║╚██╗██║██║    ██║    {BRIGHT_CYAN}║
 ║  {BRIGHT_YELLOW}███████╗██║  ██║╚██████╗██║  ██║╚██████╔╝██║ ╚████║██║    ██║    {BRIGHT_CYAN}║
 ║  {BRIGHT_YELLOW}╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝    ╚═╝    {BRIGHT_CYAN}║
 ║                 {BRIGHT_MAGENTA}⚔️   CHRONICLES OF THE REALM  ⚔️                     {BRIGHT_CYAN}║
 ╚══════════════════════════════════════════════════════════════════════╝{RESET}"""

VICTORY_BANNER = f"""{BRIGHT_YELLOW}
  ░█░█░▀█▀░█▀▀░▀█▀░█▀█░█▀▄░█░█░█
  ░▀▄▀░░█░░█░░░░█░░█░█░█▀▄░░█░░▀
  ░░▀░░▀▀▀░▀▀▀░░▀░░▀▀▀░▀░▀░░▀░░▀{RESET}"""

GAME_OVER_BANNER = f"""{BRIGHT_RED}
  ▄████████    ▄████████   ▄▄▄▄███▄▄▄▄      ▄████████ 
  ███    ███   ███    ███ ▄██▀▀▀███▀▀▀██▄   ███    ███ 
  ███    █▀    ███    ███ ███   ███   ███   ███    █▀  
 ▄███▄▄▄       ███    ███ ███   ███   ███  ▄███▄▄▄     
▀▀███▀▀▀     ▀███████████ ███   ███   ███ ▀▀███▀▀▀     
  ███    █▄    ███    ███ ███   ███   ███   ███    █▄  
  ███    ███   ███    ███ ███   ███   ███   ███    ███ 
  ██████████   ███    █▀   ▀█   ███   █▀    ██████████ 
                 {BRIGHT_WHITE}Y O U   H A V E   F A L L E N{RESET}"""

# ==============================================================================
# Location ASCII Scenery Art
# ==============================================================================
LOCATION_SCENES = {
    "tavern": f"""{YELLOW}
   (             )
    )  (        (
   (    )        )     {BRIGHT_YELLOW}╭───────────────────────────────╮{YELLOW}
  [============]       {BRIGHT_YELLOW}│ 🍺  WHISPERING OAK TAVERN    │{YELLOW}
  |  _     _   |       {BRIGHT_YELLOW}╰───────────────────────────────╯{YELLOW}
  | | |   | |  |  {BRIGHT_BLACK}Warm hearth flames flicker across wooden tables.{YELLOW}
  | |_|   |_|  |  {BRIGHT_BLACK}Mugs of ale clink as patrons whisper rumors.{YELLOW}
  [============]{RESET}""",

    "cellar": f"""{BRIGHT_BLACK}
   ┌─────────┐
   │ ░░░░░░░ │   {BRIGHT_RED}╭───────────────────────────────╮{BRIGHT_BLACK}
   │ ░░ 🚪 ░░ │   {BRIGHT_RED}│ 🕸️  DAMP CELLAR & CATACOMBS   │{BRIGHT_BLACK}
   │ ░░░░░░░ │   {BRIGHT_RED}╰───────────────────────────────╯{BRIGHT_BLACK}
  ┌┴─────────┴┐  {DIM}Cobwebs drape over rotting wine casks and ancient stone.{RESET}
  │ ☠️  [===]  │  {DIM}Skittering footsteps echo from the dark corners...{RESET}
  └───────────┘""",

    "forest": f"""{GREEN}
       /\\      /\\      /\\      {BRIGHT_GREEN}╭───────────────────────────────╮{GREEN}
      /  \\    /  \\    /  \\     {BRIGHT_GREEN}│ 🌲  WHISPERING SHADOW FOREST  │{GREEN}
     / /\\ \\  / /\\ \\  / /\\ \\    {BRIGHT_GREEN}╰───────────────────────────────╯{GREEN}
    /_/  \\_\\/_/  \\_\\/_/  \\_\\   {BRIGHT_BLACK}Fog twists between ancient mossy trunks.{GREEN}
       ||      ||      ||      {BRIGHT_BLACK}Eyes gleam from the shrouded undergrowth.{RESET}""",

    "ruins": f"""{BRIGHT_CYAN}
       _/\\_       |==|        {BRIGHT_WHITE}╭───────────────────────────────╮{BRIGHT_CYAN}
      /    \\      |  |        {BRIGHT_WHITE}│ 🏛️  ANCIENT RUINED CITADEL   │{BRIGHT_CYAN}
     /  /\\  \\   __|  |__      {BRIGHT_WHITE}╰───────────────────────────────╯{BRIGHT_CYAN}
    /__/  \\__\\ [________]     {BRIGHT_BLACK}Crumbled marble pillars infused with forgotten magic.{BRIGHT_CYAN}
     ||    ||   |  🚪  |      {BRIGHT_BLACK}Arcane glyphs pulse faintly with blue light.{RESET}""",

    "shop": f"""{BRIGHT_YELLOW}
   ╔══════════════════╗      {BRIGHT_YELLOW}╭───────────────────────────────╮{BRIGHT_YELLOW}
   ║  ⚔️ 🛡️  MERCHANT  ║      {BRIGHT_YELLOW}│ 💰  MYSTIC BAZAAR & ARMORY    │{BRIGHT_YELLOW}
   ╚══════════╦═══════╝      {BRIGHT_YELLOW}╰───────────────────────────────╯{BRIGHT_YELLOW}
     | 🧪 📜  |   | 💎 🪙 |   {BRIGHT_WHITE}Shelves lined with glowing vials, sharp blades,{RESET}
    [=========┴===┴=======]   {BRIGHT_WHITE}and enchanted spell scrolls for sale.{RESET}""",

    "dungeon": f"""{MAGENTA}
    .-----------------.      {BRIGHT_MAGENTA}╭───────────────────────────────╮{MAGENTA}
   /  /\\           /\\  \\     {BRIGHT_MAGENTA}│ 💀  ABYSSAL CRYPT & DUNGEON   │{MAGENTA}
  |  |  \\  💀 💀  /  |  |    {BRIGHT_MAGENTA}╰───────────────────────────────╯{MAGENTA}
  |  |   '-------'   |  |    {BRIGHT_BLACK}Iron braziers burn with ethereal purple flame.{MAGENTA}
  |  |___[=======]___|  |    {BRIGHT_BLACK}Chains rattle somewhere deep below the grate.{RESET}"""
}

def get_location_scene(location_name: str) -> str:
    loc = location_name.lower()
    if "tavern" in loc or "inn" in loc or "oak" in loc:
        return LOCATION_SCENES["tavern"]
    elif "cellar" in loc or "basement" in loc:
        return LOCATION_SCENES["cellar"]
    elif "forest" in loc or "woods" in loc or "grove" in loc or "wild" in loc:
        return LOCATION_SCENES["forest"]
    elif "ruin" in loc or "castle" in loc or "citadel" in loc or "tower" in loc:
        return LOCATION_SCENES["ruins"]
    elif "shop" in loc or "market" in loc or "merchant" in loc or "bazaar" in loc:
        return LOCATION_SCENES["shop"]
    elif "crypt" in loc or "dungeon" in loc or "cave" in loc or "catacomb" in loc:
        return LOCATION_SCENES["dungeon"]
    else:
        return LOCATION_SCENES["cellar"]

# ==============================================================================
# Monster & Enemy ASCII Sprites
# ==============================================================================
ENEMY_SPRITES = {
    "goblin": f"""{GREEN}
       (o.o)
     <(  -  )>  🗡️
      /  |  \\
     (___|_|_)
    {BRIGHT_GREEN}[ Goblin Skulker ]{RESET}""",

    "skeleton": f"""{BRIGHT_WHITE}
       .-''''-.
      /  _  _  \\
     |  (o)(o)  |
      \\   /\\   /
       '-'--'-'  ⚔️
       /|    |\\
      (_|_/\\_|_)
    {WHITE}[ Skeletal Warrior ]{RESET}""",

    "troll": f"""{YELLOW}
      .-----.
     /  - -  \\
    |  (O)(O) |  💥
     \\   __  /
    .-'------'-.
   /  \\      /  \\
  (____)----(____)
    {BRIGHT_YELLOW}[ Cave Troll ]{RESET}""",

    "dragon": f"""{BRIGHT_RED}
      / \\\\__
     (    @\\\\___     🔥
     /         O    🔥 🔥
    /   (_____/
   /_____/   U
  {RED}[ Abyssal Wyrm ]{RESET}""",

    "mage": f"""{BRIGHT_MAGENTA}
        /\\
       /  \\
      /____\\
      ( 👁️  )   ✨
     <[░░░░]>  ⚡
      / || \\
     (__||__)
   {MAGENTA}[ Dark Cultist ]{RESET}""",

    "wolf": f"""{BRIGHT_BLACK}
      /\\___/\\
     (  o.o  )  🩸
      >  ^  <
     /  / \\  \\
    (__/   \\__)
   {BRIGHT_RED}[ Dire Shadow Wolf ]{RESET}""",

    "default": f"""{BRIGHT_RED}
       (\\___/)
       ( •_• )
       / >⚔️ <\\
      (_______)
     [ Hostile Entity ]{RESET}"""
}

def get_enemy_sprite(sprite_key: str) -> str:
    key = sprite_key.lower().strip() if sprite_key else "default"
    for name in ENEMY_SPRITES:
        if name in key:
            return ENEMY_SPRITES[name]
    return ENEMY_SPRITES["default"]

# ==============================================================================
# HUD and Status Displays
# ==============================================================================
def render_player_hud(state) -> str:
    """Render a compact, styled RPG status HUD."""
    w = get_term_width()
    
    # Progress bars
    hp_line = f"{BRIGHT_RED}❤️  HP  {RESET}" + health_bar(state.health, state.max_health, 16)
    mp_line = f"{BRIGHT_CYAN}💧 MP  {RESET}" + mana_bar(state.mana, state.max_mana, 16)
    xp_line = f"{BRIGHT_YELLOW}⭐ XP  {RESET}" + xp_bar(state.xp, state.xp_to_next, 16)
    
    # Stats badges
    stat_badges = (
        f"{BRIGHT_WHITE}{BOLD}LVL {state.level}{RESET}  │  "
        f"{BRIGHT_YELLOW}🪙 {state.gold} Gold{RESET}  │  "
        f"{BRIGHT_RED}⚔️  ATK: {state.total_attack}{RESET}  │  "
        f"{BRIGHT_BLUE}🛡️  DEF: {state.total_defense}{RESET}"
    )
    
    equip_line = (
        f"{BRIGHT_BLACK}Weapon:{RESET} {BRIGHT_WHITE}{state.equipped_weapon}{RESET}  │  "
        f"{BRIGHT_BLACK}Armor:{RESET} {BRIGHT_WHITE}{state.equipped_armor}{RESET}"
    )

    lines = [
        f" {stat_badges}",
        f" {hp_line}    {mp_line}",
        f" {xp_line}",
        f" {equip_line}"
    ]
    
    return draw_box(f"👤 {state.player_name} @ {state.location}", lines, width=w, border_color=CYAN)

def render_quests_and_inventory(state) -> str:
    """Render clean collapsible Quest & Inventory view."""
    w = get_term_width()
    inv_items = ", ".join([f"{BRIGHT_YELLOW}•{RESET} {item}" for item in state.inventory]) if state.inventory else f"{DIM}Empty{RESET}"
    quest_items = "\n".join([f"  {BRIGHT_CYAN}📜 [ACTIVE]{RESET} {q}" for q in state.active_quests]) if state.active_quests else f"  {DIM}No active quests{RESET}"
    
    lines = [
        f"{BOLD}🎒 INVENTORY:{RESET} {inv_items}",
        f"{BOLD}📜 QUEST LOG:{RESET}",
        quest_items
    ]
    return draw_box("Journal & Backpack", lines, width=w, border_color=BRIGHT_BLACK)

# ==============================================================================
# Animated FX & Rolls
# ==============================================================================
def animated_dice_roll(stat_name: str = "STR", modifier: int = 0) -> int:
    """Animate a rolling d20 with suspense."""
    sys.stdout.write(f"\n{BRIGHT_MAGENTA}🎲 Rolling d20 + {stat_name}({modifier:+d})... {RESET}")
    sys.stdout.flush()
    
    # Roll sequence
    for _ in range(12):
        fake = random.randint(1, 20)
        sys.stdout.write(f"\b\b\b\b{BRIGHT_YELLOW}[{fake:2d}]{RESET}")
        sys.stdout.flush()
        time.sleep(0.06)
    
    roll = random.randint(1, 20)
    total = roll + modifier
    
    if roll == 20:
        res_text = f"\b\b\b\b{BG_RED}{BRIGHT_YELLOW}{BOLD} [20! CRITICAL HIT!] {RESET} {BRIGHT_GREEN}(Total: {total}){RESET}\n"
    elif roll == 1:
        res_text = f"\b\b\b\b{BG_RED}{WHITE}{BOLD} [ 1! CRITICAL FAIL] {RESET} {RED}(Total: {total}){RESET}\n"
    elif roll >= 12:
        res_text = f"\b\b\b\b{BRIGHT_GREEN}{BOLD}[{roll:2d}] SUCCESS!{RESET} {BRIGHT_WHITE}(Total: {total}){RESET}\n"
    else:
        res_text = f"\b\b\b\b{BRIGHT_RED}{BOLD}[{roll:2d}] STRUGGLE!{RESET} {BRIGHT_WHITE}(Total: {total}){RESET}\n"
        
    sys.stdout.write(res_text)
    sys.stdout.flush()
    time.sleep(0.4)
    return total

def slash_animation():
    """Visual sword slash effect."""
    frames = [
        f"{BRIGHT_RED}      \\ \n       \\ \n        \\ {RESET}",
        f"{BRIGHT_YELLOW}   ═════════💥 {RESET}",
        f"{BRIGHT_WHITE}        / \n       / \n      / {RESET}",
    ]
    for f in frames:
        sys.stdout.write(f"\r{f}")
        sys.stdout.flush()
        time.sleep(0.08)
    sys.stdout.write("\n")

def spell_animation(spell_name: str):
    """Visual spell burst effect."""
    sys.stdout.write(f"\n{BRIGHT_CYAN}✨ Chanting {spell_name}... ")
    symbols = ["•", "✦", "★", "✴", "💥", "⚡", "🌟"]
    for s in symbols:
        sys.stdout.write(f"{BRIGHT_MAGENTA}{s} {RESET}")
        sys.stdout.flush()
        time.sleep(0.06)
    sys.stdout.write(f"{BRIGHT_YELLOW}BOOM!{RESET}\n")

def level_up_animation(new_level: int):
    """Visual Level Up fanfare."""
    print("\n" + "=" * 60)
    print(f"{BRIGHT_YELLOW}{BOLD}  🌟 ✨  LEVEL UP! YOU ARE NOW LEVEL {new_level}!  ✨ 🌟{RESET}")
    print(f"{BRIGHT_GREEN}  +Max HP increased! +Max MP increased! +ATK & DEF boosted!{RESET}")
    print("=" * 60 + "\n")
    time.sleep(1.0)
