# Chronicles of the Realm

A terminal-based dark fantasy text adventure powered by a local Ollama language model. Explore locations, make free-form choices, fight enemies, manage equipment and spells, complete quests, and save your progress.

## Requirements

- macOS, Linux, or Windows
- Python 3.10+
- Ollama
- The `llama3` Ollama model

## Setup

1. Install Ollama from [ollama.com/download](https://ollama.com/download).
2. Start Ollama, then download the model:

```bash
ollama pull llama3
```

3. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, use `.venv\\Scripts\\Activate.ps1` instead.

4. Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run

From the project directory:

```bash
python main.py
```

If Ollama is not already running, start it separately with:

```bash
ollama serve
```

The configured model is `llama3` in `config.py`.

## Controls

- Enter `1`, `2`, or `3` to choose a suggested action.
- Enter a free-form action such as `search the altar` or `talk to the merchant`.
- `C` or `status`: view character stats.
- `I` or `inventory`: manage equipment and consumables.
- `S` or `spells`: view available spells.
- `Q` or `quests`: view the quest journal.
- `R` or `roll`: roll a D20.
- `save` / `load`: save or restore `save_game.json`.
- `H` or `help`: show the in-game help screen.
- `quit` or `exit`: leave the game.

During combat, choose an attack, spell, item, defend, or flee action when prompted.

## Project Layout

- `main.py`: terminal interface, menus, save/load, and game loop
- `engine.py`: LLM interaction, fallback turns, memory, and state updates
- `schema.py`: game, enemy, and turn-action models
- `combat.py`: turn-based combat system
- `graphics.py`: terminal colors, panels, animations, and location art
- `memory.py`: ChromaDB-backed narrative memory
- `config.py`: model, memory, and save-file settings
- `requirements.txt`: Python dependencies

## Troubleshooting

Check that the model is installed and available:

```bash
ollama list
ollama run llama3
```

If Python reports missing packages, activate `.venv` and run the dependency installation command again.
