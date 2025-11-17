path = "src/micropolis/generation.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
print("total triple quotes:", text.count('"""'))
for i, line in enumerate(text.splitlines(), start=1):
    if '"""' in line:
        print(i, line.strip())
