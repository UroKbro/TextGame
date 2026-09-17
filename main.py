from __future__ import annotations

import os
import sys
import json
import time
from typing import TYPE_CHECKING, Optional

from config import SAVE_FILE_PATH
import graphics as gfx
from combat import CombatManager

if TYPE_CHECKING:
    from engine import TextAdventureEngine

def show_character_sheet(engine: TextAdventureEngine):
    w = gfx.get_term_width()
    st = engine.state
    lines = [
        f"{gfx.BRIGHT_WHITE}{gfx.BOLD}NAME:{gfx.RESET} {st.player_name}   │  {gfx.BRIGHT_YELLOW}{gfx.BOLD}CLASS:{gfx.RESET} Spellblade Adventurer",
        f"{gfx.BRIGHT_WHITE}{gfx.BOLD}LEVEL:{gfx.RESET} {st.level}  │  {gfx.BRIGHT_YELLOW}GOLD:{gfx.RESET} {st.gold} coins  │  {gfx.CYAN}XP:{gfx.RESET} {st.xp}/{st.xp_to_next}",
        "─" * (w - 6),
        f"{gfx.BRIGHT_RED}❤️  MAX HEALTH:{gfx.RESET} {st.max_health}   (Current: {st.health})",
        f"{gfx.BRIGHT_CYAN}💧 MAX MANA:  {gfx.RESET} {st.max_mana}   (Current: {st.mana})",
        f"{gfx.BRIGHT_RED}⚔️  ATTACK:    {gfx.RESET} {st.total_attack}  (Base: {st.base_attack} + Lvl: {st.level*2} + Wep bonus)",
        f"{gfx.BRIGHT_BLUE}🛡️  DEFENSE:   {gfx.RESET} {st.total_defense}  (Base: {st.base_defense} + Lvl: {st.level} + Arm bonus)",
        "─" * (w - 6),
        f"{gfx.BOLD}EQUIPPED WEAPON:{gfx.RESET} {gfx.BRIGHT_GREEN}{st.equipped_weapon}{gfx.RESET}",
        f"{gfx.BOLD}EQUIPPED ARMOR: {gfx.RESET} {gfx.BRIGHT_GREEN}{st.equipped_armor}{gfx.RESET}",
    ]
    print("\n" + gfx.draw_box("Character Sheet", lines, width=w, border_color=gfx.BRIGHT_MAGENTA))
    input(f"\n{gfx.DIM}Press Enter to return...{gfx.RESET}")

def manage_inventory(engine: TextAdventureEngine):
    while True:
        w = gfx.get_term_width()
        st = engine.state
        print("\n" + gfx.draw_box("Backpack & Inventory", [
            f"{gfx.BRIGHT_YELLOW}Gold:{gfx.RESET} {st.gold} coins",
            f"{gfx.BRIGHT_GREEN}Equipped Weapon:{gfx.RESET} {st.equipped_weapon}",
            f"{gfx.BRIGHT_GREEN}Equipped Armor:{gfx.RESET}  {st.equipped_armor}",
            "─" * (w - 6),
            *[f" [{idx}] {item}" for idx, item in enumerate(st.inventory, 1)]
        ], width=w, border_color=gfx.YELLOW))
        
        print(f"\n{gfx.BOLD}Enter item number to use/equip, or [0] to exit inventory:{gfx.RESET}")
        choice = input(f"{gfx.BRIGHT_YELLOW}Inventory # > {gfx.RESET}").strip()
        
        if not choice.isdigit() or choice == "0":
            break
            
        idx = int(choice) - 1
        if 0 <= idx < len(st.inventory):
            item = st.inventory[idx]
            item_lower = item.lower()
            
            # Health potion
            if "health potion" in item_lower:
                heal = min(40, st.max_health - st.health)
                st.health += heal
                st.inventory.remove(item)
                print(f"{gfx.BRIGHT_GREEN}✨ Drank {item} and restored {heal} HP!{gfx.RESET}")
            # Mana potion
            elif "mana potion" in item_lower:
                mana_r = min(30, st.max_mana - st.mana)
                st.mana += mana_r
                st.inventory.remove(item)
                print(f"{gfx.BRIGHT_CYAN}✨ Drank {item} and restored {mana_r} MP!{gfx.RESET}")
            # Weapon equip
            elif "atk" in item_lower or "sword" in item_lower or "blade" in item_lower or "dagger" in item_lower:
                st.equipped_weapon = item
                print(f"{gfx.BRIGHT_GREEN}⚔️  Equipped {item} as primary weapon!{gfx.RESET}")
            # Armor equip
            elif "def" in item_lower or "armor" in item_lower or "tunic" in item_lower or "cuirass" in item_lower:
                st.equipped_armor = item
                print(f"{gfx.BRIGHT_BLUE}🛡️  Equipped {item} as primary armor!{gfx.RESET}")
            else:
                print(f"{gfx.YELLOW}Inspected {item}. Keep it safe!{gfx.RESET}")
            time.sleep(1.0)

def show_spellbook(engine: TextAdventureEngine):
    w = gfx.get_term_width()
    st = engine.state
    lines = [
        f"{gfx.BRIGHT_CYAN}Current Mana:{gfx.RESET} {st.mana}/{st.max_mana}",
        "─" * (w - 6),
        f" • {gfx.BRIGHT_RED}Fireball{gfx.RESET} (15 MP) - Hurls explosive flames dealing heavy fire damage",
        f" • {gfx.BRIGHT_GREEN}Minor Heal{gfx.RESET} (20 MP) - Channels holy energy restoring 35 HP",
        f" • {gfx.BRIGHT_MAGENTA}Arcane Strike{gfx.RESET} (10 MP) - Infuses weapon with piercing arcane energy",
        f" • {gfx.BRIGHT_YELLOW}Lightning Bolt{gfx.RESET} (25 MP) - Strikes with lethal thunderbolt"
    ]
    print("\n" + gfx.draw_box("Spellbook & Grimoire", lines, width=w, border_color=gfx.BRIGHT_CYAN))
    input(f"\n{gfx.DIM}Press Enter to return...{gfx.RESET}")

def show_quest_log(engine: TextAdventureEngine):
    w = gfx.get_term_width()
    st = engine.state
    active = [f" {gfx.BRIGHT_YELLOW}⚡ [ACTIVE]{gfx.RESET} {q}" for q in st.active_quests] if st.active_quests else [f" {gfx.DIM}No active quests{gfx.RESET}"]
    completed = [f" {gfx.BRIGHT_GREEN}✓ [COMPLETED]{gfx.RESET} {q}" for q in st.completed_quests] if st.completed_quests else [f" {gfx.DIM}None yet{gfx.RESET}"]
    lines = [
        f"{gfx.BOLD}ACTIVE QUESTS:{gfx.RESET}",
        *active,
        "─" * (w - 6),
        f"{gfx.BOLD}COMPLETED QUESTS:{gfx.RESET}",
        *completed
    ]
    print("\n" + gfx.draw_box("Quest Journal", lines, width=w, border_color=gfx.BRIGHT_YELLOW))
    input(f"\n{gfx.DIM}Press Enter to return...{gfx.RESET}")

def save_game(engine: TextAdventureEngine, filename: str = SAVE_FILE_PATH):
    data = engine.state.model_dump()
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n{gfx.BRIGHT_GREEN}💾 [System] Game state successfully saved to {filename}{gfx.RESET}")
    time.sleep(0.8)

def load_game(engine: TextAdventureEngine, filename: str = SAVE_FILE_PATH):
    if not os.path.exists(filename):
        print(f"\n{gfx.BRIGHT_RED}❌ [System] Save file '{filename}' not found.{gfx.RESET}")
        time.sleep(0.8)
        return
    with open(filename, "r") as f:
        data = json.load(f)
    engine.state = engine.state.__class__(**data)
    print(f"\n{gfx.BRIGHT_GREEN}📂 [System] Game state loaded from {filename}{gfx.RESET}")
    time.sleep(0.8)

def print_help():
    w = gfx.get_term_width()
    lines = [
        f"{gfx.BOLD}COMMANDS:{gfx.RESET}",
        f" • {gfx.BRIGHT_CYAN}1, 2, 3...{gfx.RESET}  : Select quick suggested action",
        f" • {gfx.BRIGHT_WHITE}[text]{gfx.RESET}      : Free-form action (e.g. 'search the altar', 'talk to merchant')",
        f" • {gfx.BRIGHT_YELLOW}status{gfx.RESET}      : Open full character attributes & stats",
        f" • {gfx.BRIGHT_YELLOW}inventory{gfx.RESET}   : Open backpack to equip gear or drink potions",
        f" • {gfx.BRIGHT_YELLOW}spells{gfx.RESET}      : Open spellbook & view magic costs",
        f" • {gfx.BRIGHT_YELLOW}quests{gfx.RESET}      : View active quest log",
        f" • {gfx.BRIGHT_MAGENTA}roll{gfx.RESET}        : Roll animated d20 dice check",
        f" • {gfx.BRIGHT_GREEN}save / load{gfx.RESET} : Save or restore your adventure",
        f" • {gfx.BRIGHT_RED}quit / exit{gfx.RESET} : Exit the game"
    ]
    print("\n" + gfx.draw_box("Game Commands & Guide", lines, width=w, border_color=gfx.CYAN))
    input(f"\n{gfx.DIM}Press Enter to return...{gfx.RESET}")

def main():
    try:
        from engine import TextAdventureEngine
    except Exception as error:
        print(f"[Error] Could not load game dependencies: {error}")
        return

    gfx.clear_screen()
    print(gfx.GAME_LOGO)
    print(f"\n{gfx.BRIGHT_WHITE}{gfx.BOLD}Welcome to the Enhanced LLM Terminal RPG!{gfx.RESET}")
    print(f"{gfx.BRIGHT_BLACK}Featuring ASCII Scenery, Tactical Combat, Equipment, and Magic.{gfx.RESET}\n")
    
    player_name = input(f"{gfx.BRIGHT_CYAN}Enter your hero's name [Default: Adventurer] > {gfx.RESET}").strip()
    
    engine = TextAdventureEngine()
    if player_name:
        engine.state.player_name = player_name
        
    current_suggestions = [
        "Investigate the strange noises in the Tavern Cellar",
        "Talk to the Barkeep about local rumors",
        "Visit the Mystic Bazaar & Merchant"
    ]
    
    last_narrative = (
        f"Welcome, {engine.state.player_name}. You are resting in the Whispering Oak Tavern. "
        "A warm fire roars in the hearth, but ominous scratching noises echo from the cellar trapdoor below..."
    )

    while True:
        try:
            gfx.clear_screen()
            
            # 1. Render Location Scene Art
            scene_art = gfx.get_location_scene(engine.state.location)
            print(scene_art)
            
            # 2. Render Player Status HUD
            print(gfx.render_player_hud(engine.state))
            
            # 3. Render Story Box
            w = gfx.get_term_width()
            story_lines = [last_narrative]
            print(gfx.draw_box(f"📖 The Tale Continues...", story_lines, width=w, border_color=gfx.BRIGHT_WHITE))
            
            # 4. Render Action Menu / Quick Suggestions
            print(f"\n{gfx.BOLD}Available Actions:{gfx.RESET}")
            for idx, sugg in enumerate(current_suggestions, 1):
                print(f" [{gfx.BRIGHT_YELLOW}{idx}{gfx.RESET}] {sugg}")
            print(f" [{gfx.BRIGHT_BLACK}C{gfx.RESET}] Character Sheet  │ [{gfx.BRIGHT_BLACK}I{gfx.RESET}] Inventory  │ [{gfx.BRIGHT_BLACK}S{gfx.RESET}] Spellbook  │ [{gfx.BRIGHT_BLACK}Q{gfx.RESET}] Quests  │ [{gfx.BRIGHT_BLACK}H{gfx.RESET}] Help")
            
            # 5. Prompt User Input
            user_input = input(f"\n{gfx.BRIGHT_GREEN}What do you do? > {gfx.RESET}").strip()
            if not user_input:
                continue

            cmd = user_input.lower()
            
            # Global Menu Commands
            if cmd in ["quit", "exit"]:
                print(f"\n{gfx.BRIGHT_YELLOW}Farewell, {engine.state.player_name}! May your blade stay sharp.{gfx.RESET}")
                break
            elif cmd in ["status", "stats", "sheet", "c"]:
                show_character_sheet(engine)
                continue
            elif cmd in ["inventory", "inv", "bag", "items", "i"]:
                manage_inventory(engine)
                continue
            elif cmd in ["spells", "magic", "spellbook", "s"]:
                show_spellbook(engine)
                continue
            elif cmd in ["quests", "quest", "journal", "q"]:
                show_quest_log(engine)
                continue
            elif cmd in ["save"]:
                save_game(engine)
                continue
            elif cmd in ["load"]:
                load_game(engine)
                last_narrative = f"Game state loaded! You are in {engine.state.location}."
                continue
            elif cmd in ["roll", "dice", "d20"]:
                gfx.animated_dice_roll("D20", engine.state.level)
                input(f"\n{gfx.DIM}Press Enter to continue...{gfx.RESET}")
                continue
            elif cmd in ["help", "h", "?"]:
                print_help()
                continue
                
            # Quick Number Selection
            if user_input.isdigit():
                choice_idx = int(user_input) - 1
                if 0 <= choice_idx < len(current_suggestions):
                    user_input = current_suggestions[choice_idx]
                else:
                    print(f"{gfx.RED}Invalid option number.{gfx.RESET}")
                    time.sleep(0.5)
                    continue

            # Process Turn through Engine
            print(f"\n{gfx.DIM}The realm reacts to your decision...{gfx.RESET}")
            action = engine.process_turn(user_input)
            last_narrative = action.narrative_response
            
            if action.suggested_actions:
                current_suggestions = action.suggested_actions
                
            # Check Combat Encounter Trigger
            if action.trigger_combat:
                time.sleep(0.6)
                combat_mgr = CombatManager(engine.state, action.trigger_combat)
                battle_summary = combat_mgr.run_battle()
                last_narrative += f"\n\n{battle_summary}"

        except KeyboardInterrupt:
            print(f"\n\n{gfx.BRIGHT_YELLOW}Exiting game. Farewell, adventurer!{gfx.RESET}")
            break
        except Exception as e:
            print(f"\n{gfx.RED}[Error] {e}{gfx.RESET}")
            time.sleep(1.5)

if __name__ == "__main__":
    main()