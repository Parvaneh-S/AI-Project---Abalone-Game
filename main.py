"""
Abalone Game - Main Entry Point

At this point, only the UI for Abalone game has been implemented, and it has no logic yet.
This is the main entry point that initializes and runs the game application.
"""
import asyncio
import traceback

from src.ui.game_app import GameApp


async def main() -> None:
    try:
        app = GameApp()
        await app.run()

    except Exception as e:
        traceback.print_exc()
        print(f"Error running game: {e}")


asyncio.run(main())