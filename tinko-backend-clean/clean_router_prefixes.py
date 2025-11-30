import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROUTERS_DIR = os.path.join(BASE_DIR, "app", "routers")

print(f"Scanning routers in: {ROUTERS_DIR}")

router_files = []
for root, dirs, files in os.walk(ROUTERS_DIR):
    for f in files:
        if f.endswith(".py"):
            router_files.append(os.path.join(root, f))

prefix_pattern_leading = re.compile(r'prefix\s*=\s*"[^"]*"\s*,\s*')
prefix_pattern_trailing = re.compile(r',\s*prefix\s*=\s*"[^"]*"')

for path in router_files:
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()

    if "APIRouter(" not in original:
        continue

    new_content = original

    # 1) Remove prefix=... when it's the first arg
    new_content, n1 = prefix_pattern_leading.subn("", new_content)

    # 2) Remove prefix=... when it's a trailing arg
    new_content, n2 = prefix_pattern_trailing.subn("", new_content)

    total = n1 + n2
    if total > 0:
        print(f"[UPDATED] {path} (removed {total} prefix argument(s))")
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
    else:
        print(f"[SKIPPED] {path} (no prefix= found)")

print("Done. Restart your server and refresh Swagger to verify paths.")
