"""Create, verify or restore a checksummed local Chroma backup.

Create: python scripts/chroma_archive.py create --archive tmp/chroma-backup.zip
Verify: python scripts/chroma_archive.py verify --archive tmp/chroma-backup.zip
Restore: python scripts/chroma_archive.py restore --archive tmp/chroma-backup.zip --destination tmp/chroma-restore
The archive is local until copied to durable storage by the owner.
"""

import argparse
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "chroma_store"
MANIFEST = ROOT / "data" / "report_manifest.json"


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def create(archive: Path) -> None:
    if archive.exists():
        raise SystemExit(f"Archive already exists: {archive}")
    archive.parent.mkdir(parents=True, exist_ok=True)
    staging = ROOT / "tmp"
    staging.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=staging) as staging_name:
        snapshot = Path(staging_name) / "chroma.sqlite3"
        source = sqlite3.connect(f"file:{STORE / 'chroma.sqlite3'}?mode=ro", uri=True)
        target = sqlite3.connect(snapshot)
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
        files = [("chroma_store/chroma.sqlite3", snapshot), ("data/report_manifest.json", MANIFEST)]
        files += [(path.relative_to(ROOT).as_posix(), path) for path in STORE.rglob("*") if path.is_file() and path.name != "chroma.sqlite3"]
        checksums = {}
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
            for name, path in files:
                data = path.read_bytes()
                checksums[name] = {"sha256": digest(data), "bytes": len(data)}
                output.writestr(name, data)
            output.writestr("backup-manifest.json", json.dumps({"version": 1, "files": checksums}, indent=2) + "\n")
    verify(archive)
    print(f"Created {archive} ({archive.stat().st_size:,} bytes)")


def verify(archive: Path) -> dict:
    with zipfile.ZipFile(archive) as source:
        record = json.loads(source.read("backup-manifest.json"))
        files = record["files"]
        if record.get("version") != 1 or set(source.namelist()) != set(files) | {"backup-manifest.json"}:
            raise SystemExit("Backup manifest does not match archive contents")
        for name, expected in files.items():
            if Path(name).is_absolute() or ".." in Path(name).parts or not name.startswith(("chroma_store/", "data/")):
                raise SystemExit(f"Unsafe archive path: {name}")
            data = source.read(name)
            if len(data) != expected["bytes"] or digest(data) != expected["sha256"]:
                raise SystemExit(f"Backup checksum mismatch: {name}")
    print(f"Verified {len(files)} files in {archive}; SHA-256 {digest(archive.read_bytes())}")
    return files


def restore(archive: Path, destination: Path) -> None:
    files = verify(archive)
    if destination.exists():
        raise SystemExit(f"Restore destination already exists: {destination}")
    destination.mkdir(parents=True)
    with zipfile.ZipFile(archive) as source:
        for name in files:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read(name))
    print(f"Restored to {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["create", "verify", "restore"])
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.action == "create":
        create(args.archive)
    elif args.action == "verify":
        verify(args.archive)
    elif args.destination:
        restore(args.archive, args.destination)
    else:
        parser.error("restore requires --destination")
