"""
Abalone Game - Main Entry Point

A strategic board game with AI opponents.
This is the main entry point that initializes and runs the game application.
"""
import sys
from src.ui.game_app import GameApp


def main() -> None:
    """Main entry point for the Abalone game."""
    try:
        app = GameApp()
        app.run()
    except Exception as e:
        print(f"Error running game: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)



if __name__ == "__main__":
    main()
