# Abalone State Space Generator

This program generates all legal move notations and their resulting board configurations for any given Abalone board state.

---

## Requirements

- Python 3.10 or higher (no third-party packages required)

---


## How to Run

Place move_engine.py in the same directory with your input file, then run from a terminal:

```bash
python move_engine.py <path/to/TestX.input>
```

### Examples

**Windows (PowerShell / Command Prompt):**
```powershell
python move_engine.py Test1.input
```
```powershell
python move_engine.py C:\Users\you\inputs\Test2.input
```

**macOS / Linux:**
```bash
python3 move_engine.py Test1.input
```
```bash
python3 move_engine.py /home/you/inputs/Test2.input
```

The program prints a short summary to the console and writes the two output files:
```
Player to move : b
Moves generated: 44
Move file      : C:\path\to\Test1.move
Board file     : C:\path\to\Test1.board
```


