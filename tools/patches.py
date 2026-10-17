#!/usr/bin/env python3
"""Check, export and apply only the custom commits after a fixed Chromium base."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "chromium.json"


def git(src, *args):
    return subprocess.check_output(["git", "-C", str(src), *args])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check():
    manifest = json.loads(MANIFEST.read_text())
    require(manifest["schema_version"] == 1, "Unsupported manifest schema")
    for key in ("base_commit", "source_head", "source_tree"):
        require(re.fullmatch(r"[0-9a-f]{40}", manifest[key]), f"Invalid {key}")
    records = manifest["patches"]
    require(records, "Patch series is empty")
    names = []
    for index, record in enumerate(records, 1):
        commit = record["source_commit"]
        require(re.fullmatch(r"[0-9a-f]{40}", commit), "Invalid source commit")
        expected = f"patches/{index:04d}-{commit[:10]}.patch"
        require(record["file"] == expected, f"Invalid patch path: {record['file']}")
        path = ROOT / expected
        require(not path.is_symlink(), f"Symlink patch is unsupported: {expected}")
        data = path.read_bytes()
        require(digest(data) == record["sha256"], f"Checksum mismatch: {expected}")
        require(data.startswith(f"From {commit} ".encode()), f"Commit mismatch: {expected}")
        names.append(path.name)
    require(records[-1]["source_commit"] == manifest["source_head"], "HEAD mismatch")
    require((ROOT / "patches/series").read_text() == "".join(n + "\n" for n in names),
            "patches/series does not match manifest order")
    require({p.name for p in (ROOT / "patches").glob("*.patch")} == set(names),
            "Unexpected or missing patch file")
    return manifest


def source_root(path):
    src = Path(path).resolve()
    require(Path(git(src, "rev-parse", "--show-toplevel").decode().strip()).resolve() == src,
            "Pass the Chromium src repository root")
    require(not git(src, "status", "--porcelain", "--untracked-files=normal").strip(),
            "Chromium worktree must be clean; commit or save changes first")
    git_dir = Path(git(src, "rev-parse", "--absolute-git-dir").decode().strip())
    require(not (git_dir / "rebase-apply").exists() and
            not (git_dir / "rebase-merge").exists(), "Finish the existing am/rebase first")
    return src


def export(path):
    manifest = check()
    src = source_root(path)
    base = manifest["base_commit"]
    git(src, "merge-base", "--is-ancestor", base, "HEAD")
    require(not git(src, "rev-list", "--min-parents=2", base + "..HEAD").strip(),
            "Merge commits are unsupported; keep custom commits linear")
    parts = dict(line.split("=", 1) for line in (src / "chrome/VERSION").read_text().splitlines())
    version = ".".join(parts[k] for k in ("MAJOR", "MINOR", "BUILD", "PATCH"))
    require(version == manifest["chromium_version"], "Chromium version differs from fixed base")
    commits = git(src, "rev-list", "--reverse", base + "..HEAD").decode().splitlines()
    require(commits, "No custom commits to export")
    records, contents = [], {}
    for index, commit in enumerate(commits, 1):
        name = f"patches/{index:04d}-{commit[:10]}.patch"
        data = git(src, "format-patch", "-1", commit, "--stdout", "--binary", "--full-index",
                   "--no-signature", "--no-stat", "--no-numbered")
        records.append({"file": name, "source_commit": commit,
                        "subject": git(src, "show", "-s", "--format=%s", commit).decode().strip(),
                        "sha256": digest(data)})
        contents[name] = data
    for name, data in contents.items():
        (ROOT / name).write_bytes(data)
    for record in manifest["patches"]:
        if record["file"] not in contents:
            (ROOT / record["file"]).unlink()
    manifest.update(source_head=commits[-1], source_tree=git(src, "rev-parse", "HEAD^{tree}").decode().strip(),
                    patches=records)
    (ROOT / "patches/series").write_text("".join(Path(r["file"]).name + "\n" for r in records))
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    check()
    print(f"Exported {len(records)} custom commits; review the repository diff before committing.")


def apply(path):
    manifest = check()
    src = source_root(path)
    require(git(src, "rev-parse", "HEAD").decode().strip() == manifest["base_commit"],
            "Chromium HEAD must equal the exact base_commit in chromium.json")
    for key in ("user.name", "user.email"):
        require(git(src, "config", "--get", key).strip(), f"Configure Git {key} before applying")
    patches = [str(ROOT / r["file"]) for r in manifest["patches"]]
    try:
        subprocess.run(["git", "-C", str(src), "am", *patches], check=True)
    except subprocess.CalledProcessError:
        print("Patch application failed. Inspect src, then use git am --continue or git am --abort.",
              file=sys.stderr)
        raise
    tree = git(src, "rev-parse", "HEAD^{tree}").decode().strip()
    require(tree == manifest["source_tree"], "Applied tree differs from recorded source tree")
    print(f"Applied {len(patches)} patches; verified source tree {tree}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Verify series order, commit identifiers and SHA-256")
    for name in ("export", "apply"):
        sub.add_parser(name).add_argument("src", help="Chromium src repository root")
    args = parser.parse_args()
    try:
        if args.command == "check":
            manifest = check()
            print(f"Verified {len(manifest['patches'])} patches for Chromium {manifest['chromium_version']}.")
        elif args.command == "export":
            export(args.src)
        else:
            apply(args.src)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
