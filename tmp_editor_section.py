from pathlib import Path
lines=Path('src/micropolis/editor.py').read_text().splitlines()
for i in range(700, 840):
    print(f'{i+1}: {lines[i]}')
