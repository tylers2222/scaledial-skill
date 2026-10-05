"""Keep the skills lean, linked, and free of example-shaped bias.

Checks every skills/*/SKILL.md:
  - frontmatter has name and description
  - body word count (warn > 2000, fail > 3000)
  - every references/, examples/, scripts/ path it mentions exists
  - no product names from product_blocklist.txt (they belong in references and examples, not the method)
Checks every reference file: warn above 5000 words (split it or promote it to its own skill).
Checks all markdown: no paragraph of 25+ words appears in two files.
"""

import hashlib
import re
from collections import defaultdict
from pathlib import Path

from . import PACKAGE_DIR

WARN_WORDS, FAIL_WORDS, REF_WARN_WORDS = 2000, 3000, 5000
PATH_RE = re.compile(r"`((?:references|examples|scripts)/[^`\s]+)`")


def default_root() -> Path:
    return PACKAGE_DIR.parents[1] / "skills"


def blocklist() -> list[str]:
    lines = (PACKAGE_DIR / "product_blocklist.txt").read_text().splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def lint(root: Path) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    products = blocklist()
    paragraphs: dict[str, list[str]] = defaultdict(list)

    skill_files = sorted(root.glob("*/SKILL.md"))
    if not skill_files:
        raise SystemExit(f"no skills found under {root}")
    for skill in skill_files:
        rel = skill.relative_to(root)
        text = skill.read_text()
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
        if not match:
            errors.append(f"{rel}: missing YAML frontmatter")
            continue
        front, body = match.groups()
        for field in ("name", "description"):
            if not re.search(rf"^{field}:\s*\S", front, re.M):
                errors.append(f"{rel}: frontmatter has no {field}")
        words = len(body.split())
        if words > FAIL_WORDS:
            errors.append(f"{rel}: body is {words} words (limit {FAIL_WORDS}); move detail to references/")
        elif words > WARN_WORDS:
            warnings.append(f"{rel}: body is {words} words (target <= {WARN_WORDS})")
        for ref in PATH_RE.findall(body):
            found = any(skill.parent.glob(ref)) if "*" in ref else (skill.parent / ref).exists()
            if not found:
                errors.append(f"{rel}: mentions {ref}, which does not exist")
        for product in products:
            if re.search(rf"(?<![\w-]){re.escape(product)}(?![\w-])", body, re.I):
                errors.append(f"{rel}: names product {product!r}; keep SKILL.md product-free (use references/ or examples/)")

    for md in sorted(root.rglob("*.md")):
        rel = str(md.relative_to(root))
        text = md.read_text()
        if md.name != "SKILL.md" and len(text.split()) > REF_WARN_WORDS:
            warnings.append(f"{rel}: {len(text.split())} words; split it or promote it to its own skill")
        for para in re.split(r"\n\s*\n", text):
            flat = " ".join(para.split())
            if len(flat.split()) >= 25 and not flat.startswith(("|", "```")):
                paragraphs[hashlib.sha1(flat.lower().encode()).hexdigest()].append(rel)
    for files in paragraphs.values():
        if len(set(files)) > 1:
            warnings.append(f"same paragraph in {sorted(set(files))}; keep one copy")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{len(skill_files)} skills checked: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0
