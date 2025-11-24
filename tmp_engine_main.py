from pathlib import Path
lines=Path('src/micropolis/engine.py').read_text().splitlines()
for i in range(1410, 1460):
    print(f'{i+1}: {lines[i]}')
