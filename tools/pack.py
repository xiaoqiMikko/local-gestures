# -*- coding: utf-8 -*-
"""Build the zip that gets uploaded to an extension store.

Ships only what the browser loads. Development scaffolding (tools/, store/,
tests) has no business inside a package that reviewers read and users install
— and every extra file is one more thing a reviewer has to ask about.

Refuses to write the zip if verify.py fails, because an inconsistent package
is worse than no package: the review queue is measured in days.

Output: store/local-gestures-<version>.zip
"""
import json
import subprocess
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
EXT = HERE.parent

# Allow-list, not a deny-list: a deny-list silently ships whatever gets added
# to the repo next.
INCLUDE_DIRS = ["src", "icons", "_locales"]
INCLUDE_FILES = ["manifest.json"]
SKIP_SUFFIX = {".pyc", ".raw.png"}

print("先跑一致性检查……")
r = subprocess.run([sys.executable, str(HERE / "verify.py")],
                   capture_output=True, text=True, encoding="utf-8")
if r.returncode != 0:
    print(r.stdout, r.stderr)
    sys.exit("verify.py 没过,不打包。")
print("  通过\n")

version = json.loads((EXT / "manifest.json").read_text("utf-8"))["version"]
out = EXT / "store" / f"local-gestures-{version}.zip"
out.parent.mkdir(parents=True, exist_ok=True)

files = [EXT / f for f in INCLUDE_FILES]
for d in INCLUDE_DIRS:
    files += [p for p in (EXT / d).rglob("*")
              if p.is_file() and p.suffix not in SKIP_SUFFIX]

missing = [f for f in files if not f.exists()]
if missing:
    sys.exit(f"缺文件:{missing}")

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(files):
        z.write(f, f.relative_to(EXT).as_posix())

total = sum(f.stat().st_size for f in files)
print(f"版本 {version} | {len(files)} 个文件 | "
      f"原始 {total / 1024:.0f} KB | 压缩后 {out.stat().st_size / 1024:.0f} KB")
print("→", out.relative_to(EXT))
print("\n包里有:")
with zipfile.ZipFile(out) as z:
    tops = sorted({n.split("/")[0] for n in z.namelist()})
    print("  ", ", ".join(tops))
