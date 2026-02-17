# Quick Start Guide - Abalone AI

## Installation (1 minute)

```bash
# 1. Install Python dependency
pip install pygame>=2.5

# 2. Run the application
python main.py
```

## First Game (2 minutes)

### Step 1: Configure
On the left panel, you'll see:
- **Board Layout**: Keep "Standard" (or try German/Belgian Daisy)
- **Game Mode**: Keep "Human vs Computer"
- **Your Color**: Choose BLACK or WHITE

### Step 2: Start
Click the big **"Start"** button

### Step 3: Play
**To move your marble:**
- **Option A**: Click your marble → Click destination
- **Option B**: Drag your marble to destination

**Rules (simplified version):**
- You can only move to adjacent empty cells
- Take turns with the AI
- Watch the right panel for game info

### Step 4: Observe
**Right panel shows:**
- Current score (marbles off board)
- Number of moves made
- AI thinking time
- Complete move history

## Quick Controls

| Button | What It Does |
|--------|--------------|
| Start | Begin new game |
| Pause/Resume | Freeze/unfreeze game |
| Reset | Start over with same settings |
| Undo | Take back last move |
| Stop | End game, change settings |

## Try These Features

### 1. Different Layouts
- Click "Board Layout" dropdown
- Select "German Daisy" or "Belgian Daisy"
- Click "Reset" to see new layout

### 2. Set Move Limit
- Check "Enable Move Limit"
- Type "20" in the box
- Game ends after 20 moves per player

### 3. Set Time Limit
- Check "BLACK Time Limit"
- Type "5.0" (5 seconds per move)
- AI must think faster!

### 4. Drag and Drop
- Click and hold your marble
- Drag to empty cell
- Release to move
- Watch it follow your cursor!

## Visual Guide

```
[Configuration]     [Game Board]      [Information]
  Dropdowns         Hexagonal Grid    Status & Score
  Checkboxes        Black/White       Move History
  Text Inputs       Marbles           AI Timing
                    
[Controls]
  5 Buttons
```

## Tips

💡 **Click anywhere on the board** to see hover highlight

💡 **Yellow ring** = Selected marble

💡 **Right panel** updates in real-time

💡 **Change configuration** only when game is stopped

💡 **Undo multiple times** to review your strategy

## Keyboard Shortcuts

Currently none - all mouse-based interaction

## Troubleshooting

**Game won't start?**
- Make sure status says "STOPPED" before clicking Start

**Can't move marble?**
- Check if it's your turn (see "To move:" on right)
- Only your color marbles can be moved

**AI not moving?**
- It thinks for a brief moment - watch "Next AI Move"

**Drag not working?**
- Make sure you're dragging your own marble
- Make sure destination is adjacent and empty

## Next Steps

Once you're comfortable:
1. Try different board layouts
2. Experiment with time limits
3. Set challenging move limits
4. Watch Computer vs Computer mode
5. Check the complete move history

## Full Documentation

- **README.md** - Complete feature overview
- **GUI_FEATURES.md** - Detailed component documentation
- **GUI_LAYOUT.md** - Visual layout reference
- **IMPLEMENTATION_SUMMARY.md** - Technical details

## Need Help?

Check the right panel - it shows:
- Current game status
- Whose turn it is
- Recent moves
- Everything you need to know!

---

**Enjoy playing Abalone! 🎮**

