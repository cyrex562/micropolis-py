from pathlib import Path
text=Path('src/micropolis/graphs.py').read_text().splitlines()
for i in range(340,420):
    print(f"{i}: {text[i-1]}")
