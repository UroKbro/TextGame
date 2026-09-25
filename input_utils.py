import re
from collections.abc import Iterable
from typing import Optional, Tuple
import graphics as gfx

# Characters strictly forbidden in story actions and commands
FORBIDDEN_SYMBOLS = set("@&#$%^*~_+|\\<>{}[];:\"=/`")


ALLOWED_PUNCTUATION = set(".,!?' -")

def validate_action_text(text: str) -> Tuple[bool, str]:

    cleaned = text.strip()
    if not cleaned:
        return False, "Input cannot be empty. Please enter an action."

    found_forbidden = [ch for ch in cleaned if ch in FORBIDDEN_SYMBOLS]
    if found_forbidden:
        unique_symbols = "".join(sorted(set(found_forbidden)))
        return False, f"Special symbol(s) '{unique_symbols}' are not allowed. Please use standard words or choose a numbered option."

    invalid_chars = [
        ch for ch in cleaned 
        if not (ch.isalnum() or ch.isspace() or ch in ALLOWED_PUNCTUATION)
    ]
    if invalid_chars:
        unique_invalid = "".join(sorted(set(invalid_chars)))
        return False, f"Character(s) '{unique_invalid}' are not recognized. Please use plain text words."

    if not any(ch.isalnum() for ch in cleaned):
        return False, "Input must contain at least one word or number, not just punctuation."

    return True, ""

def read_valid_input(
    prompt: str,
    valid_options: Iterable[str],
    *,
    numeric_range: Optional[range] = None,
) -> str:

    options = {option.lower().strip() for option in valid_options}

    while True:
        raw = input(prompt).strip()
        value = raw.lower()

        if not value:
            print(f"{gfx.RED}❌ Please make a selection.{gfx.RESET}")
            continue

        if value in options:
            return value

        if numeric_range is not None and value.isascii() and value.isdecimal():
            number = int(value)
            if number in numeric_range:
                return value

        if any(ch in FORBIDDEN_SYMBOLS for ch in raw):
            print(f"{gfx.RED}❌ Special symbols like '@' or '&' are not valid options. Please choose from the list.{gfx.RESET}")
        elif numeric_range is not None and value.isdigit():
            min_val = numeric_range.start
            max_val = numeric_range.stop - 1
            print(f"{gfx.RED}❌ Invalid number [{value}]. Please enter a number between {min_val} and {max_val}.{gfx.RESET}")
        else:
            print(f"{gfx.RED}❌ Invalid input '{raw}'. Please choose one of the listed options.{gfx.RESET}")

def read_action_input(
    prompt: str,
    max_suggestions: int = 3,
) -> str:
    """
    Read a story action or command with strict validation against symbols like @, &, etc.
    Ensures numbers correspond to available suggestions.
    """
    MENU_COMMANDS = {
        "c", "status", "stats", "sheet", "character",
        "i", "inv", "inventory", "bag", "items", "item",
        "s", "spells", "magic", "spellbook", "spell",
        "q", "quests", "quest", "journal", "log",
        "f", "faction", "factions", "rep", "reputation",
        "m", "merchant", "merchants", "shop", "shops", "market", "bazaar", "trade", "buy", "sell",
        "k", "craft", "crafting", "forge", "alchemy", "workshop", "brew",
        "decision", "choice",
        "h", "help", "?",
        "save", "load",
        "roll", "dice", "d20",
        "quit", "exit"
    }

    while True:
        value = input(prompt).strip()
        if not value:
            continue

        if value.isascii() and value.isdecimal():
            number = int(value)
            if 1 <= number <= max_suggestions:
                return value
            else:
                print(f"{gfx.RED}❌ Invalid option number [{number}]. Please choose between 1 and {max_suggestions}, a menu key (C, I, S, Q, H), or type an action.{gfx.RESET}")
                continue


        if value.lower() in MENU_COMMANDS:
            return value

        is_valid, error_msg = validate_action_text(value)
        if is_valid:
            return value

        print(f"{gfx.RED}❌ {error_msg}{gfx.RESET}")