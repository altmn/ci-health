#!/usr/bin/env python3
"""Validate and build a small, deterministic, allowlisted CI Health package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = "skills/ci-health/"
SKILLS = ("ci-health", "ci-health-preflight", "ci-health-optimize")
SKILL_ROOTS = tuple(f"skills/{name}/" for name in SKILLS)
RUNTIME = (
    "plugin.json", "README.md", "LICENSE", "NOTICE.md", "PRIVACY.md", "TERMS.md",
    "CONTRIBUTING.md", "SECURITY.md", "SUPPORT.md", "CHANGELOG.md",
    "docs/architecture.md", "docs/validation.md", "docs/releasing.md",
    *(f"skills/{name}/{path}" for name in SKILLS for path in ("SKILL.md", "agents/openai.yaml")),
    SKILL + "scripts/ci_health.py",
    *(SKILL + "references/" + name + ".md" for name in (
        "audit", "measurement", "helper-schema", "orchestration", "execution",
        "selection-and-reuse", "experiments", "optimization", "bun-ci", "openclaw-case-study")),
)


class ReleaseError(ValueError):
    pass


def regular(root: Path, relative: str) -> Path:
    path = root / relative
    for part in (path, *path.parents):
        if part == root.parent:
            break
        if part.is_symlink():
            raise ReleaseError(f"symlink is not allowed: {relative}")
    if not path.is_file():
        raise ReleaseError(f"missing regular file: {relative}")
    return path


def privacy_check(content: str, label: str) -> None:
    patterns = (
        r"/(?:Users|home)/[^\s/'\"]+",  # accidental workstation paths
        r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    )
    if any(re.search(pattern, content) for pattern in patterns):
        raise ReleaseError(f"potential private path or credential in {label}; review content")


def local_links(root: Path, path: Path, members: set[str] | None = None) -> None:
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^\s)]+)(?:\s+[^)]*)?\)", text):
        target = unquote(target.strip("<>"))
        if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
            continue
        destination = (path.parent / target.split("#", 1)[0]).resolve()
        if not destination.is_relative_to(root.resolve()) or not destination.exists():
            raise ReleaseError(f"broken or escaping local link in {path.relative_to(root)}: {target}")
        if members is not None:
            relative = destination.relative_to(root.resolve()).as_posix()
            included = relative in members or (destination.is_dir() and any(name.startswith(relative + "/") for name in members))
            if not included:
                raise ReleaseError(f"unpackaged skill link in {path.relative_to(root)}: {target}")


def validate(root: Path = ROOT) -> dict:
    for relative in RUNTIME:
        privacy_check(regular(root, relative).read_text(encoding="utf-8"), relative)
    manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("name") != "ci-health" or not re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", "")):
        raise ReleaseError("invalid canonical name or version")
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise ReleaseError("unexpected portable manifest schema")
    if manifest.get("license") != "MIT" or "email" in manifest.get("author", {}):
        raise ReleaseError("review license and author metadata")
    openai = manifest["extensions"]["com.openai"]["interface"]
    if openai.get("displayName") != "CI Health":
        raise ReleaseError("inconsistent plugin interface")
    subtitle = openai.get("shortDescription")
    if not isinstance(subtitle, str) or not 1 <= len(subtitle) <= 30:
        raise ReleaseError("plugin listing subtitle must be 1–30 characters")
    for name, skill_root in zip(SKILLS, SKILL_ROOTS):
        skill = (root / skill_root / "SKILL.md").read_text(encoding="utf-8")
        if (not re.match(rf"\A---\nname: {re.escape(name)}\ndescription: [^\n]+\n", skill)
                or "\n---\n" not in skill or "[TODO" in skill):
            raise ReleaseError(f"invalid or unfinished skill frontmatter: {name}")
        ui = (root / skill_root / "agents/openai.yaml").read_text(encoding="utf-8")
        invocation = rf"\${re.escape(name)}(?![A-Za-z0-9_-])"
        if not re.search(invocation, ui) or "allow_implicit_invocation: true" not in ui:
            raise ReleaseError(f"inconsistent skill invocation metadata: {name}")
    catalog = json.loads((root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    plugin = catalog["plugins"][0]
    if catalog["name"] != "ci-health-dev" or plugin["name"] != manifest["name"] or plugin["source"] != {"source": "local", "path": "./dist/local-plugin"}:
        raise ReleaseError("inconsistent local marketplace")
    # Source documentation gets link/privacy checks; generated or private evidence is excluded.
    sources = [p for p in root.glob("*.md") if p.is_file()]
    sources += list((root / "docs").glob("*.md"))
    sources += [path for skill_root in SKILL_ROOTS for path in (root / skill_root).rglob("*.md")]
    for path in sources:
        regular(root, path.relative_to(root).as_posix())
        privacy_check(path.read_text(encoding="utf-8"), path.relative_to(root).as_posix())
        members = set(RUNTIME) if path.relative_to(root).as_posix().startswith(SKILL_ROOTS) else None
        local_links(root, path, members)
    return manifest


def runtime_bytes(root: Path, manifest: dict, compatibility: bool = False) -> dict[str, bytes]:
    result = {name: regular(root, name).read_bytes() for name in sorted(RUNTIME)}
    if compatibility:
        legacy = {key: manifest[key] for key in (
            "name", "version", "description", "author", "license", "keywords", "homepage", "repository")}
        legacy.update(skills="./skills/", interface=manifest["extensions"]["com.openai"]["interface"])
        result[".codex-plugin/plugin.json"] = (json.dumps(legacy, indent=2) + "\n").encode()
    return result


def write_zip(destination: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() or archive.namelist() != sorted(files):
            raise ReleaseError("archive integrity or member mismatch")
        for name, data in files.items():
            if archive.read(name) != data:
                raise ReleaseError("archive content mismatch")


def preflight_output(dist: Path, stage_files: dict[str, bytes]) -> None:
    if dist.is_symlink() or (dist.exists() and not dist.is_dir()):
        raise ReleaseError("dist must be a regular directory")
    stage = dist / "local-plugin"
    if stage.is_symlink() or (stage.exists() and not stage.is_dir()):
        raise ReleaseError("local staging must be a regular directory")
    allowed_dirs = {p.as_posix() for name in stage_files for p in Path(name).parents if str(p) != "."}
    if stage.exists():
        for path in stage.rglob("*"):
            relative = path.relative_to(stage).as_posix()
            if path.is_symlink() or (path.is_file() and relative not in stage_files) or (path.is_dir() and relative not in allowed_dirs) or (not path.is_file() and not path.is_dir()):
                raise ReleaseError("unexpected staging entry; refusing to overwrite local content")


def git_info(root: Path) -> tuple[str | None, bool | None]:
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True).stdout.strip())
        return commit, dirty
    except (OSError, subprocess.CalledProcessError):
        return None, None


def build(root: Path = ROOT, require_clean: bool = False) -> Path:
    manifest = validate(root)
    commit, dirty = git_info(root)
    if require_clean and (commit is None or dirty is not False):
        raise ReleaseError("release build requires a clean Git revision")
    files = runtime_bytes(root, manifest)
    stage_files = runtime_bytes(root, manifest, compatibility=True)
    dist = root / "dist"
    preflight_output(dist, stage_files)
    dist.mkdir(exist_ok=True)
    output = dist / f"ci-health-{manifest['version']}.zip"
    companions = [output, output.with_suffix(".sha256"), dist / "build-info.json"]
    if any(p.is_symlink() or (p.exists() and not p.is_file()) for p in companions):
        raise ReleaseError("release output must be a regular file")
    with tempfile.TemporaryDirectory(prefix=".build-", dir=dist) as scratch:
        scratch = Path(scratch)
        archive = scratch / output.name
        write_zip(archive, files)
        stage = scratch / "local-plugin"
        for name, data in stage_files.items():
            destination = stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        # Only verified generated content can be replaced, after all preparation succeeds.
        if (dist / "local-plugin").exists():
            shutil.rmtree(dist / "local-plugin")
        os.replace(stage, dist / "local-plugin")
        os.replace(archive, output)
        output.with_suffix(".sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
        info = {"schema_version": 1, "version": manifest["version"], "source_commit": commit,
                "source_dirty": dirty, "archive": output.name, "sha256": digest,
                "runtime_files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
        (dist / "build-info.json").write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build"))
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            validate()
            print(f"Validated {len(RUNTIME)} allowlisted runtime files and source documentation.")
        else:
            output = build(require_clean=args.require_clean)
            print(f"Built {output.relative_to(ROOT)} and dist/local-plugin; see checksum and build-info.json.")
    except (ReleaseError, OSError, ValueError, KeyError) as exc:
        print(f"release: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
