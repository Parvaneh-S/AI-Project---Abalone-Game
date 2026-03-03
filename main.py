"""
Abalone Game - Main Entry Point

At this point, only the UI for Abalone game has been implemented, and it has no logic yet.
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
