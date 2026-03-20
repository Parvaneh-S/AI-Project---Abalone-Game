"""
Test script to run the AI with Minimax and Alpha-Beta Pruning.

This script demonstrates how to use the AI module with the heuristic
to find the best move in an Abalone game.
"""

from move_engine import parse_input_file
from src.ai import get_ai_move


def main():
    """Main function to run AI and display results."""
    print("\n" + "=" * 70)
    print("ABALONE AI - MINIMAX WITH ALPHA-BETA PRUNING".center(70))
    print("=" * 70 + "\n")

    # Load board from input file
    try:
        player, board = parse_input_file("../inputs/Test1.input")
        print(f"✓ Loaded board from Test1.input")
        print(f"  Player to move: {player}")
        print(f"  Marbles on board: {len(board)}")
        print()
    except FileNotFoundError:
        print("✗ Error: Test1.input not found")
        print("  Make sure Test1.input exists in the project root")
        return False
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return False

    # Run AI to find best move
    try:
        print("Running Minimax search with Alpha-Beta Pruning...")
        print("(Depth = 4, this may take a moment)\n")

        best_move = get_ai_move(board, player, depth=4)

        if best_move:
            move, resulting_board, score = best_move
            print("\n" + "-" * 70)
            print("RESULTS:")
            print("-" * 70)
            print(f"Best move: {move.notation()}")
            print(f"Move type: {'Inline' if move.kind == 'i' else 'Side-step'}")
            print(f"From marble(s): {move.a}" + (f", {move.b}" if move.b else ""))
            print(f"Direction: {move.d}")
            print(f"Heuristic score: {score}")
            print("-" * 70)
            return True
        else:
            print("✗ No legal moves available for player " + player)
            return False

    except Exception as e:
        print(f"✗ Error during AI search: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

