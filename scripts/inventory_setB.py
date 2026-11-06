#!/usr/bin/env python3
"""Offline, read-only Set B audio inventory. Does not play, transcribe, copy, or rename audio."""
from pathlib import Path
import argparse
import csv
import hashlib
import re
import shutil
import subprocess

AUDIO_EXTENSIONS = {".m4a"}
STANDARD_RE = re.compile(r"^B_(S\d{2})_(P\d+)$", re.IGNORECASE)
SESSION_RE = re.compile(r"^S(\d{2})$", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def duration_seconds(path: Path):
    """Try optional mutagen, then ffprobe. Return blank if neither is available."""
    try:
        from mutagen.mp4 import MP4  # optional dependency
        audio = MP4(str(path))
        if audio.info and audio.info.length:
            return round(float(audio.info.length), 3), "mutagen"
    except Exception:
        pass

    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            result = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                capture_output=True, text=True, timeout=20, check=True
            )
            value = float(result.stdout.strip())
            return round(value, 3), "ffprobe"
        except Exception:
            pass
    return "", "unavailable (install mutagen or ffprobe for durations)"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Path to Gnani_Hackathon repository root (default: current directory)")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    source_root = repo / "raw" / "setB_tm"
    if not source_root.is_dir():
        raise SystemExit(f"ERROR: folder not found: {source_root}\nRun this script from the repository root or pass --repo PATH.")

    files = sorted(p for p in source_root.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS)
    if not files:
        raise SystemExit(f"No .m4a files found recursively under {source_root}")

    rows = []
    hash_to_paths = {}
    for path in files:
        rel = path.relative_to(repo).as_posix()
        session = ""
        for part in path.relative_to(source_root).parts[:-1]:
            if SESSION_RE.match(part):
                session = part.upper()
                break

        stem = path.stem
        match = STANDARD_RE.match(stem)
        question_id = ""
        recording_type = "Follow-up / needs review"
        proposed = ""
        mapping_status = "Needs review"
        if match:
            filename_session, question_id = match.groups()
            filename_session = filename_session.upper()
            if session and session != filename_session:
                mapping_status = "Needs review: folder/filename session mismatch"
            else:
                session = filename_session
                recording_type = "Standard question"
                proposed = f"recordings/tm_{session}_{question_id}.m4a"
                mapping_status = "Proposed; approval required"
        else:
            # Preserve follow-up identity as written; do not infer which branch/question it answers.
            follow_match = re.match(r"^B_(S\d{2})_(F.+)$", stem, re.IGNORECASE)
            if follow_match:
                filename_session, _ = follow_match.groups()
                if not session:
                    session = filename_session.upper()
                if session != filename_session.upper():
                    mapping_status = "Needs review: folder/filename session mismatch"

        duration, duration_method = duration_seconds(path)
        digest = sha256_file(path)
        hash_to_paths.setdefault(digest, []).append(rel)
        rows.append({
            "session": session,
            "original_relative_path": rel,
            "filename": path.name,
            "question_id": question_id,
            "recording_type": recording_type,
            "duration_seconds": duration,
            "duration_method": duration_method,
            "size_mb": round(path.stat().st_size / (1024 * 1024), 3),
            "sha256": digest,
            "proposed_destination": proposed,
            "mapping_status": mapping_status,
            "duplicate_sha256": "yes" if len(hash_to_paths[digest]) > 1 else "",
        })

    # Mark every copy of a duplicate hash, including earlier rows.
    duplicate_hashes = {h for h, paths in hash_to_paths.items() if len(paths) > 1}
    for row in rows:
        if row["sha256"] in duplicate_hashes:
            row["duplicate_sha256"] = "yes"
            row["mapping_status"] = (row["mapping_status"] + "; duplicate content: review")

    out_dir = repo / "eval" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = out_dir / "setB_inventory.csv"
    mapping_path = out_dir / "setB_mapping_review.csv"

    fields = list(rows[0].keys())
    with inventory_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    with mapping_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    session_counts = {f"S{i:02d}": 0 for i in range(1, 11)}
    for row in rows:
        if row["session"] in session_counts:
            session_counts[row["session"]] += 1

    print("SET B OFFLINE INVENTORY COMPLETE")
    print(f"Source: {source_root}")
    print(f"Total .m4a files: {len(rows)}")
    print("Counts by session:")
    for session, count in session_counts.items():
        print(f"  {session}: {count}")
    unknown = sum(1 for row in rows if not row["session"])
    followups = sum(1 for row in rows if row["recording_type"].startswith("Follow-up"))
    duplicates = sum(1 for row in rows if row["duplicate_sha256"] == "yes")
    no_duration = sum(1 for row in rows if row["duration_seconds"] == "")
    print(f"Follow-up/unclassified files: {followups}")
    print(f"Files with unknown session: {unknown}")
    print(f"Files flagged as duplicate content: {duplicates}")
    print(f"Durations unavailable: {no_duration}")
    print(f"\nCreated: {inventory_path}")
    print(f"Created: {mapping_path}")
    print("No audio was played, uploaded, transcribed, copied, or renamed. No API calls were made.")
    print("NOTE: proposed destinations are suggestions only; do not copy until mapping is reviewed and approved.")


if __name__ == "__main__":
    main()
