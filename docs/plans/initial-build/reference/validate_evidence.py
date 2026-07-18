#!/usr/bin/env python3
"""Validate release metadata: SemVer/CHANGELOG coupling and plugin-mirror byte-identity.

Slimmed for the docs-DB (v1.2.0) knowledge substrate. The old deltas-only
justification — pinning SKILL.md's hash to the probe records under
docs/plans/research/ — was retired (see docs/plans/docs-db/00 D9): SKILL.md is
now rewritten on every DB refresh, so a pinned hash models nothing. Those probe
records are preserved on disk as historical measurement, no longer asserted here.

Remaining checks (both from docs/plans/docs-db/06):
  1. plugin.json version has a matching `## [x.y.z]` CHANGELOG heading;
  2. the plugin skill mirror is byte-identical to the canonical skill tree
     (every skill file AND the committed docs_official.db).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def rel_files(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


def main() -> None:
    errors: list[str] = []

    plugin_root = ROOT / "plugins" / "skills-for-langchain"
    plugin = load_json(plugin_root / ".claude-plugin" / "plugin.json")
    marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    version = plugin["version"]

    require(plugin["name"] == "skills-for-langchain", "Unexpected plugin name", errors)
    require(marketplace["name"] == "skills-for-langchain", "Unexpected marketplace name", errors)
    require(marketplace["plugins"][0]["name"] == plugin["name"],
            "Marketplace and plugin names must match", errors)
    require(marketplace["plugins"][0]["source"] == "./plugins/skills-for-langchain",
            "Unexpected marketplace plugin source", errors)
    require(f"## [{version}]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
            f"Plugin version {version} must have a matching '## [{version}]' CHANGELOG heading", errors)

    # Plugin mirror must be byte-identical to the canonical skill tree.
    canonical = ROOT / ".claude" / "skills" / "langchain"
    packaged = plugin_root / "skills" / "langchain"
    canonical_files = rel_files(canonical)
    packaged_files = rel_files(packaged)
    for missing in sorted(canonical_files - packaged_files):
        errors.append(f"Missing from plugin mirror: {missing}")
    for extra in sorted(packaged_files - canonical_files):
        errors.append(f"Stale file in plugin mirror: {extra}")
    for rel in sorted(canonical_files & packaged_files):
        require(sha256(canonical / rel) == sha256(packaged / rel),
                f"Packaged skill drift: {rel}", errors)

    if errors:
        print("Release validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"Release metadata passed: {plugin['name']} v{version}")
    print(f"Plugin mirror byte-identical: {len(canonical_files)} files")


if __name__ == "__main__":
    main()
