import time
import random
import sys
from schema import GameState, EnemyState
import graphics as gfx

class CombatManager:
    def __init__(self, state: GameState, enemy: EnemyState):
        self.state = state
        self.enemy = enemy
        self.combat_log = [f"A menacing {enemy.name} appeared!"]
        self.is_defending = False

    def log(self, message: str):
        self.combat_log.append(message)
        if len(self.combat_log) > 4:
            self.combat_log.pop(0)

    def render_combat_screen(self):
        w = gfx.get_term_width()
        
        # Enemy Banner
        sprite = gfx.get_enemy_sprite(self.enemy.sprite_key)
        enemy_hp = gfx.health_bar(self.enemy.health, self.enemy.max_health, 18)
        
        enemy_box = gfx.draw_box(
            f"⚔️ ENEMY: {self.enemy.name}", 
            [
                f"{sprite}",
                f"{self.enemy.description}",
                f"HP: {enemy_hp}   ATK: {self.enemy.attack}  DEF: {self.enemy.defense}"
            ], 
            width=w, 
            border_color=gfx.BRIGHT_RED
        )
        
        # Player HUD
        player_hud = gfx.render_player_hud(self.state)
        
        # Combat Log Box
        log_lines = [f"{gfx.BRIGHT_BLACK}• {l}{gfx.RESET}" for l in self.combat_log]
        log_box = gfx.draw_box("Battle Log", log_lines, width=w, border_color=gfx.YELLOW)
        
        print(enemy_box)
        print(player_hud)
        print(log_box)

    def player_attack(self) -> bool:
        """Execute player physical attack."""
        gfx.slash_animation()
        roll = random.randint(1, 20)
        is_crit = (roll == 20)
        
        raw_damage = self.state.total_attack + random.randint(1, 6)
        if is_crit:
            raw_damage *= 2
            self.log(f"{gfx.BG_RED}{gfx.BRIGHT_YELLOW}💥 CRITICAL HIT! 💥{gfx.RESET}")
            
        damage = max(1, raw_damage - self.enemy.defense)
        self.enemy.health = max(0, self.enemy.health - damage)
        
        crit_str = " (Critical!)" if is_crit else ""
        self.log(f"You struck {self.enemy.name} for {gfx.BRIGHT_RED}{damage}{gfx.RESET} damage!{crit_str}")
        return self.enemy.health <= 0

    def player_cast_spell(self) -> bool:
        """Let player select and cast a spell."""
        print(f"\n{gfx.BRIGHT_CYAN}{gfx.BOLD}--- SELECT A SPELL ---{gfx.RESET}")
        print(f"Current MP: {self.state.mana}/{self.state.max_mana}")
        spells = [
            {"name": "Fireball", "cost": 15, "min_dmg": 18, "max_dmg": 28, "type": "damage"},
            {"name": "Arcane Strike", "cost": 10, "min_dmg": 12, "max_dmg": 18, "type": "damage"},
            {"name": "Minor Heal", "cost": 20, "heal": 35, "type": "heal"},
            {"name": "Lightning Bolt", "cost": 25, "min_dmg": 30, "max_dmg": 45, "type": "damage"}
        ]
        
        for idx, sp in enumerate(spells, 1):
            if sp["type"] == "damage":
                print(f" [{idx}] {gfx.BRIGHT_WHITE}{sp['name']}{gfx.RESET} (Cost: {gfx.CYAN}{sp['cost']} MP{gfx.RESET}) - Deals {sp['min_dmg']}-{sp['max_dmg']} DMG")
            else:
                print(f" [{idx}] {gfx.BRIGHT_GREEN}{sp['name']}{gfx.RESET} (Cost: {gfx.CYAN}{sp['cost']} MP{gfx.RESET}) - Restores {sp['heal']} HP")
        print(" [0] Cancel")
        
        choice = input(f"{gfx.BRIGHT_YELLOW}Cast spell # > {gfx.RESET}").strip()
        if not choice.isdigit() or choice == "0":
            return False
            
        idx = int(choice) - 1
        if 0 <= idx < len(spells):
            sp = spells[idx]
            if self.state.mana < sp["cost"]:
                self.log(f"{gfx.RED}Not enough Mana to cast {sp['name']}!{gfx.RESET}")
                return False
                
            self.state.mana -= sp["cost"]
            gfx.spell_animation(sp["name"])
            
            if sp["type"] == "damage":
                dmg = random.randint(sp["min_dmg"], sp["max_dmg"])
                self.enemy.health = max(0, self.enemy.health - dmg)
                self.log(f"Your {sp['name']} blasted {self.enemy.name} for {gfx.BRIGHT_MAGENTA}{dmg}{gfx.RESET} magic damage!")
            elif sp["type"] == "heal":
                healed = min(sp["heal"], self.state.max_health - self.state.health)
                self.state.health += healed
                self.log(f"Your {sp['name']} restored {gfx.BRIGHT_GREEN}{healed}{gfx.RESET} HP!")
            return True
        return False

    def player_use_item(self) -> bool:
        """Let player choose an item from inventory."""
        consumables = [item for item in self.state.inventory if any(c in item.lower() for c in ["potion", "flask", "dagger", "scroll", "bomb", "herb"])]
        if not consumables:
            self.log(f"{gfx.YELLOW}No usable combat items in inventory!{gfx.RESET}")
            return False
            
        print(f"\n{gfx.BRIGHT_YELLOW}{gfx.BOLD}--- COMBAT INVENTORY ---{gfx.RESET}")
        for idx, item in enumerate(consumables, 1):
            print(f" [{idx}] {item}")
        print(" [0] Cancel")
        
        choice = input(f"{gfx.BRIGHT_YELLOW}Use item # > {gfx.RESET}").strip()
        if not choice.isdigit() or choice == "0":
            return False
            
        idx = int(choice) - 1
        if 0 <= idx < len(consumables):
            item = consumables[idx]
            self.state.inventory.remove(item)
            item_lower = item.lower()
            
            if "health potion" in item_lower:
                heal_amt = 40
                self.state.health = min(self.state.max_health, self.state.health + heal_amt)
                self.log(f"You drank {item} and restored {gfx.BRIGHT_GREEN}{heal_amt} HP{gfx.RESET}!")
            elif "mana potion" in item_lower:
                mana_amt = 30
                self.state.mana = min(self.state.max_mana, self.state.mana + mana_amt)
                self.log(f"You drank {item} and restored {gfx.BRIGHT_CYAN}{mana_amt} MP{gfx.RESET}!")
            elif "throwing dagger" in item_lower:
                dmg = 18
                self.enemy.health = max(0, self.enemy.health - dmg)
                self.log(f"You hurled {item} dealing {gfx.BRIGHT_RED}{dmg}{gfx.RESET} piercing damage!")
            else:
                dmg = 25
                self.enemy.health = max(0, self.enemy.health - dmg)
                self.log(f"You used {item} dealing {gfx.BRIGHT_RED}{dmg}{gfx.RESET} damage to {self.enemy.name}!")
            return True
        return False

    def enemy_turn(self):
        """Execute enemy attack AI."""
        if self.enemy.health <= 0:
            return
            
        time.sleep(0.5)
        # 25% chance of special move if defined
        uses_special = (self.enemy.special_move and random.random() < 0.3)
        
        if uses_special:
            base_dmg = int(self.enemy.attack * 1.5)
            move_name = self.enemy.special_move
            self.log(f"{gfx.BRIGHT_RED}⚠️  {self.enemy.name} used {move_name}!{gfx.RESET}")
        else:
            base_dmg = self.enemy.attack + random.randint(-2, 2)
            self.log(f"{self.enemy.name} attacks you!")
            
        # Calculate defense reduction
        effective_def = self.state.total_defense * (2 if self.is_defending else 1)
        dmg = max(1, base_dmg - (effective_def // 2))
        
        if self.is_defending:
            self.log(f"You braced your guard! Damage reduced to {gfx.BRIGHT_RED}{dmg}{gfx.RESET}!")
        else:
            self.log(f"You took {gfx.BRIGHT_RED}{dmg}{gfx.RESET} damage!")
            
        self.state.health = max(0, self.state.health - dmg)
        self.is_defending = False

    def check_level_up(self):
        """Check if XP threshold reached and level up player."""
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
            gfx.level_up_animation(self.state.level)

    def run_battle(self) -> str:
        """Main combat loop. Returns a narrative summary of the outcome."""
        while self.state.health > 0 and self.enemy.health > 0:
            gfx.clear_screen()
            self.render_combat_screen()
            
            print(f"\n{gfx.BOLD}Choose your combat action:{gfx.RESET}")
            print(f" [{gfx.BRIGHT_RED}1{gfx.RESET}] ⚔️  Attack (Physical Strike)")
            print(f" [{gfx.BRIGHT_CYAN}2{gfx.RESET}] ✨ Cast Spell (Magic)")
            print(f" [{gfx.BRIGHT_YELLOW}3{gfx.RESET}] 🧪 Use Item (Potions/Daggers)")
            print(f" [{gfx.BRIGHT_BLUE}4{gfx.RESET}] 🛡️  Defend (Half DMG, +5 MP)")
            print(f" [{gfx.BRIGHT_BLACK}5{gfx.RESET}] 🏃 Flee (Escape attempt)")
            
            action_took_place = False
            choice = input(f"\n{gfx.BRIGHT_WHITE}Action [1-5] > {gfx.RESET}").strip().lower()
            
            if choice in ["1", "attack", "strike", "hit"]:
                self.player_attack()
                action_took_place = True
            elif choice in ["2", "spell", "magic", "cast"]:
                action_took_place = self.player_cast_spell()
            elif choice in ["3", "item", "use", "potion", "bag"]:
                action_took_place = self.player_use_item()
            elif choice in ["4", "defend", "guard", "block"]:
                self.is_defending = True
                self.state.mana = min(self.state.max_mana, self.state.mana + 5)
                self.log(f"{gfx.BRIGHT_BLUE}You raise your shield and recover 5 MP!{gfx.RESET}")
                action_took_place = True
            elif choice in ["5", "flee", "run", "escape"]:
                flee_roll = random.randint(1, 20)
                if flee_roll >= 10:
                    self.log(f"{gfx.GREEN}You successfully fled from battle!{gfx.RESET}")
                    time.sleep(1.0)
                    return f"The adventurer tactically retreated from {self.enemy.name}."
                else:
                    self.log(f"{gfx.RED}Failed to escape! {self.enemy.name} cuts off your path!{gfx.RESET}")
                    action_took_place = True
            else:
                # Allow free-form spell or item shorthand
                if "heal" in choice:
                    action_took_place = self.player_cast_spell()
                elif "potion" in choice:
                    action_took_place = self.player_use_item()
                else:
                    self.player_attack()
                    action_took_place = True

            if not action_took_place:
                continue

            # Check if enemy defeated
            if self.enemy.health <= 0:
                break

            # Enemy turn
            self.enemy_turn()

        # Battle Conclusion
        gfx.clear_screen()
        self.render_combat_screen()
        time.sleep(0.8)
        
        if self.enemy.health <= 0:
            print(f"\n{gfx.VICTORY_BANNER}")
            print(f"{gfx.BRIGHT_GREEN}{gfx.BOLD}🎉 VICTORY! You defeated the {self.enemy.name}!{gfx.RESET}")
            print(f"  + Earned {gfx.BRIGHT_YELLOW}{self.enemy.gold_reward} Gold{gfx.RESET}!")
            print(f"  + Gained {gfx.BRIGHT_CYAN}{self.enemy.xp_reward} XP{gfx.RESET}!")
            
            # Rewards
            self.state.gold += self.enemy.gold_reward
            self.state.xp += self.enemy.xp_reward
            
            # 40% chance of random loot drop
            if random.random() < 0.4:
                loot_options = ["Health Potion", "Mana Potion", "Throwing Dagger", "Gleaming Ruby (+50 Gold)"]
                loot = random.choice(loot_options)
                self.state.inventory.append(loot)
                print(f"  + Loot Drop: {gfx.BRIGHT_MAGENTA}🎁 {loot}{gfx.RESET} added to your inventory!")
                
            self.check_level_up()
            input(f"\n{gfx.DIM}Press Enter to continue your adventure...{gfx.RESET}")
            return f"The adventurer triumphed over the {self.enemy.name} in battle, claiming glory, gold, and experience."
            
        elif self.state.health <= 0:
            print(f"\n{gfx.GAME_OVER_BANNER}")
            print(f"\n{gfx.BRIGHT_RED}You collapsed in battle against {self.enemy.name}...{gfx.RESET}")
            print(f"{gfx.BRIGHT_YELLOW}A wandering mystic finds your battered body and drags you back to the Tavern.{gfx.RESET}")
            self.state.health = 30
            self.state.location = "Whispering Oak Tavern"
            self.state.gold = max(0, self.state.gold - 10)
            input(f"\n{gfx.DIM}Press Enter to awaken...{gfx.RESET}")
            return f"The adventurer was defeated by the {self.enemy.name} and barely survived, waking up in the Whispering Oak Tavern."
            
        return "Combat concluded."
