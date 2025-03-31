# Falliant

A terminal-based block stacking game inspired by classic block stacking games, written in Python using the curses library.

![Falliant Screenshot](https://raw.githubusercontent.com/veteranbv/falliant/main/falliant/images/screenshot.png)

## Quick Start

```bash
pip install falliant
falliant
```

## Game Features

- Classic block-stacking gameplay with a modern twist
- Multiple difficulty levels
- Hold piece functionality
- Next piece preview
- High score system with personal records
- Clean, colorful terminal interface

## How to Play

After installation, simply run `falliant` in your terminal.

### Controls

- **←, ↓, →** or **A, S, D**: Move block
- **↑** or **W**: Rotate block
- **Space**: Drop block
- **C**: Hold current block
- **P**: Pause game
- **Q**: Quit to menu

### Scoring

- Single line: 40 × level
- Double line: 100 × level
- Triple line: 300 × level
- Falliant! (4 lines): 1200 × level

## Requirements

- Python 3.6 or higher
- A terminal that supports curses and colors (most modern terminals do)
- For Windows users: The package automatically installs the required `windows-curses` package

## Troubleshooting

If you encounter display issues:

1. Ensure your terminal window is at least 80×24 characters
2. Check that your terminal supports colors
3. For Windows users: Use Windows Terminal or another modern terminal emulator

## Links

- [GitHub Repository](https://github.com/veteranbv/falliant)
- [Bug Reports](https://github.com/veteranbv/falliant/issues)

## License

Released under the MIT License.
