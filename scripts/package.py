"""Build per-corpus tar.gz archives from ``data/`` and emit a SHA256 registry.

Run from the repo root::

    python scripts/package.py [--only NAME ...]

Produces ``dist/<name>.tar.gz`` for each top-level subdirectory of ``data/``
and prints a ``REGISTRY = {...}`` block ready to paste into
``timetoalign/testdata/__init__.py`` in the consuming repository.

This script is also invoked by ``.github/workflows/release.yml`` on a push of
a ``testdata-v*`` tag, which uploads the resulting tarballs as release assets.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import tarfile
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def build_archive(source_dir: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = archive_path.with_suffix(archive_path.suffix + ".part")
    with tarfile.open(tmp, "w:gz", compresslevel=6) as tar:
        tar.add(source_dir, arcname=source_dir.name)
    tmp.replace(archive_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    repo_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=repo_root / "data",
        help="Directory containing top-level corpus subdirectories.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=repo_root / "dist",
        help="Output directory for the produced tarballs.",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Restrict packaging to these corpus names.",
    )
    args = parser.parse_args()

    data_dir: Path = args.data_dir
    out_dir: Path = args.out_dir

    if not data_dir.is_dir():
        print(f"ERROR: data directory not found: {data_dir}", file=sys.stderr)
        return 2

    subdirs = sorted(p for p in data_dir.iterdir() if p.is_dir())
    if args.only:
        wanted = set(args.only)
        subdirs = [p for p in subdirs if p.name in wanted]
        missing = wanted - {p.name for p in subdirs}
        if missing:
            print(f"ERROR: unknown corpus names: {sorted(missing)}", file=sys.stderr)
            return 2

    if not subdirs:
        print(f"No subdirectories found under {data_dir}.", file=sys.stderr)
        return 1

    registry: dict[str, str] = {}
    for sub in subdirs:
        archive_path = out_dir / f"{sub.name}.tar.gz"
        print(f"Packaging {sub.name}/ -> {archive_path}", flush=True)
        build_archive(sub, archive_path)
        digest = sha256_file(archive_path)
        size_mb = archive_path.stat().st_size / (1024 * 1024)
        print(f"  size: {size_mb:8.2f} MB  sha256: {digest}", flush=True)
        registry[archive_path.name] = digest

    print()
    print("# Paste into REGISTRY in timetoalign/testdata/__init__.py:")
    print("REGISTRY = {")
    for name, digest in registry.items():
        print(f'    "{name}": "sha256:{digest}",')
    print("}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
