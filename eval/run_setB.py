#!/usr/bin/env python3
"""Set B local Gnani evaluation. Dry plan by default; --real requires confirmation.

Reads the teammate's original audio directly from raw/setB_tm. It never moves,
renames, uploads, or modifies recordings.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml
import extract
import gnani
import llm
import redflags

ROOT = gnani.ROOT
AUDIO_EXTENSIONS = {".m4a", ".wav", ".mp3"}
EXPECTED_TOTAL = 106
EXPECTED_STANDARD = 80
EXPECTED_FOLLOWUPS = 26
FOLLOWUP_SOURCE_IDS = {}

FOLLOWUP_PROMPTS = {
    "F(chills)": "Thand lag ke aata hai?",
    "F(measured)": "Bukhaar naapa tha? Kitna tha?",
    "F(last BP)": "Pichhli baar BP kitna aaya tha?",
    "F(last)": "Pichhli baar sugar kitni aayi thi?",
    "F(pain)": "Ek se das mein dard kitna tez hai?",
    "F(where)": "Dard theek kahan hai?",
    "F(breathless)": "Saans phoolti hai?",
    "F(phlegm)": "Balgam aata hai? Kis rang ka?",
    "F(how)": "Din mein kitni baar ulti ya dast ho rahe hain?",
    "R1": "Maine jo dawaiyon ke naam dohraye hain, kya woh sahi hain?",
}

def classify(path):
    m = re.fullmatch(r"B_(S\d{2})_(P[0-7]|R1|F.+)\.([^.]+)", path.name, re.I)
    if not m:
        raise ValueError(f"Unexpected Set B filename: {path.name}")
    session, label = m.group(1).upper(), m.group(2)
    label = "R1" if label.upper() == "R1" else label
    question = label if re.fullmatch(r"P[0-7]", label, re.I) else "FOLLOWUP"
    return session, label, question

def prompt_for(label, prompts):
    if label in prompts:
        return prompts[label]
    if label in FOLLOWUP_PROMPTS:
        return FOLLOWUP_PROMPTS[label]
    raise ValueError(f"No STT question context defined for {label}")

def source_followup_label(session, label):
    """Restore the original semantic label for context using the rename map."""
    return FOLLOWUP_SOURCE_IDS.get((session, label), label)

def duration_seconds(path):
    try:
        from mutagen import File as MutagenFile
        media = MutagenFile(str(path))
        if media is not None and media.info is not None:
            return float(media.info.length)
    except Exception:
        pass
    return gnani._file_seconds(path, path.read_bytes())

def load_inputs():
    global FOLLOWUP_SOURCE_IDS
    source = ROOT / "raw" / "setB_tm"
    if not source.is_dir():
        raise SystemExit(f"Set B audio folder not found: {source}")
    paths = sorted(p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS)
    if len(paths) != EXPECTED_TOTAL:
        raise SystemExit(f"Expected {EXPECTED_TOTAL} Set B audio files under {source}, found {len(paths)}.")
    seen = set()
    standard = followups = 0
    for path in paths:
        session, label, question = classify(path)
        key = (session, label)
        if key in seen:
            raise SystemExit(f"Duplicate session/question recording: {key}")
        seen.add(key)
        if question == "FOLLOWUP":
            followups += 1
        else:
            standard += 1
        if not path.stat().st_size:
            raise SystemExit(f"Empty audio file: {path}")
        seconds = duration_seconds(path)
        if seconds == "" or not 0 < seconds < 30:
            raise SystemExit(f"Duration unavailable or not between 0 and 30 seconds: {path}")
    if (standard, followups) != (EXPECTED_STANDARD, EXPECTED_FOLLOWUPS):
        raise SystemExit(f"Expected 80 standard + 26 follow-ups; found {standard} + {followups}.")
    mapping_path = ROOT / "eval" / "setB_recording_name_map.csv"
    if not mapping_path.is_file():
        raise SystemExit(f"Set B follow-up name map not found: {mapping_path}")
    with mapping_path.open(newline="", encoding="utf-8-sig") as stream:
        mapping = list(csv.DictReader(stream))
    FOLLOWUP_SOURCE_IDS = {
        (row["session"], row["recording_id"]): row["original_recording_id"]
        for row in mapping
        if row["speaker"] == "tm" and row["original_recording_id"].startswith("F(")
    }
    tm_followups = {
        (session, label)
        for path in paths
        for session, label, question in (classify(path),)
        if question == "FOLLOWUP" and re.fullmatch(r"F\d{2}", label)
    }
    if tm_followups != set(FOLLOWUP_SOURCE_IDS):
        raise SystemExit("Set B tm follow-up filenames and eval/setB_recording_name_map.csv do not match.")
    unknown_followups = sorted(set(FOLLOWUP_SOURCE_IDS.values()) - set(FOLLOWUP_PROMPTS))
    if unknown_followups:
        raise SystemExit(f"No prompt context defined for mapped Set B follow-ups: {unknown_followups}")
    prompts = yaml.safe_load((ROOT / "prompts.yaml").read_text(encoding="utf-8"))
    for q in ("P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"):
        if not isinstance(prompts.get(q), str) or not prompts[q].strip():
            raise SystemExit(f"Missing prompt {q} in prompts.yaml")
    medicines = [x.strip() for x in (ROOT / "data/medicines.txt").read_text(encoding="utf-8").splitlines() if x.strip()]
    symptoms = [x.strip() for x in (ROOT / "data/symptoms.txt").read_text(encoding="utf-8").splitlines() if x.strip()]
    if not 1 <= len(medicines) <= 200 or not 1 <= len(symptoms) <= 200:
        raise SystemExit("Gnani keyterm lists must each contain 1–200 entries.")
    return paths, prompts, medicines, symptoms

def request_terms(question, medicines, symptoms):
    if question == "P5":
        return medicines
    if question in ("P2", "P4"):
        return symptoms
    return None

def build_plan(paths, prompts, medicines, symptoms):
    stt_seen = set()
    llm_seen = set()
    prisma_calls = prisma_hits = groq_known = groq_hits = groq_pending = 0
    extraction_count = 0
    for path in paths:
        session, label, question = classify(path)
        context = prompt_for(source_followup_label(session, label), prompts)
        terms = request_terms(question, medicines, symptoms)
        cache = gnani.stt_cache_path(path, terms, context=context, mock=False)
        if cache.exists():
            prisma_hits += 1
            payload = json.loads(cache.read_text(encoding="utf-8"))
            transcript = payload.get("transcript")
            if question in extract.FIELDS and isinstance(transcript, str):
                key = str(extract.cache_path(question, transcript))
                if extract.cached_available(question, transcript) or key in llm_seen:
                    groq_hits += 1
                else:
                    groq_known += 1
                llm_seen.add(key)
        elif str(cache) not in stt_seen:
            prisma_calls += 1
            if question in extract.FIELDS:
                groq_pending += 1
        else:
            prisma_hits += 1
            if question in extract.FIELDS:
                groq_pending += 1
        stt_seen.add(str(cache))
        extraction_count += int(question in extract.FIELDS)
    print("SET B PREFLIGHT — NO API CALLS MADE")
    print(f"Audio files: {len(paths)} (80 standard + 26 follow-ups)")
    print(f"Prisma: {prisma_calls} uncached requests; {prisma_hits} cache hits")
    print(f"Groq extraction: {groq_known} known uncached; {groq_hits} cache hits; up to {groq_pending} depend on new transcripts")
    print(f"Maximum new Groq requests before retries: {groq_known + groq_pending}")
    print(f"Retry ceiling: up to 3 HTTP attempts per uncached request for 429/5xx responses.")
    print("Existing extraction is used only for P1–P5. P0, P6, P7, follow-ups and R1 are transcribed and saved,")
    print("but are not scored as structured extraction because the current extractor has no schemas for them.")
    print("This is per-recording replay, not a live conversation/flow test; all supplied recordings are processed.")
    return {"prisma_calls": prisma_calls, "prisma_cache_hits": prisma_hits,
            "groq_known_calls": groq_known, "groq_cache_hits": groq_hits,
            "groq_pending_transcripts": groq_pending,
            "groq_max_before_retries": groq_known + groq_pending,
            "extractable_recordings": extraction_count}

FIELDS = ["session", "recording_id", "question_type", "file", "context",
          "transcript", "extracted_json", "validation_errors", "red_flag",
          "red_flag_status", "keyword_flags", "llm_flags", "error", "processed_at"]

def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with temp.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)

def run(paths, prompts, medicines, symptoms):
    old_mock = os.environ.get("GNANI_MOCK")
    old_real = gnani._REAL_SCRIPT
    os.environ["GNANI_MOCK"] = "0"
    gnani._REAL_SCRIPT = True
    gnani.STATS.update(real_calls=0, cache_hits=0)
    log = ROOT / "logs" / "llm_calls.csv"
    before_llm = sum(1 for _ in log.open(encoding="utf-8")) - 1 if log.exists() and log.stat().st_size else 0
    rows = []
    output = ROOT / "eval" / "results" / "setB_per_recording.csv"
    try:
        for index, path in enumerate(paths, 1):
            session, label, question = classify(path)
            context = prompt_for(source_followup_label(session, label), prompts)
            terms = request_terms(question, medicines, symptoms)
            row = dict(session=session, recording_id=label, question_type=question,
                       file=path.relative_to(ROOT).as_posix(), context=context,
                       transcript="", extracted_json="", validation_errors="",
                       red_flag="", red_flag_status="", keyword_flags="", llm_flags="",
                       error="", processed_at=datetime.now(timezone.utc).isoformat())
            try:
                response = gnani.stt(path, keyterms=terms, context=context)
                transcript = response.get("transcript")
                if not isinstance(transcript, str):
                    raise ValueError("Gnani STT response did not contain a text transcript.")
                row["transcript"] = transcript
                if question in extract.FIELDS:
                    details = {}
                    result = extract.extract(question, transcript, allow_real=True, details=details)
                    row["extracted_json"] = json.dumps(result, ensure_ascii=False)
                    row["validation_errors"] = json.dumps(details.get("validation_errors", []), ensure_ascii=False)
                    if question == "P4":
                        flags = redflags.detect(transcript, result, question="P4",
                                                validation_errors=details.get("validation_errors", []))
                        row["red_flag"] = "yes" if flags["alert"] else "no"
                        row["red_flag_status"] = flags["status"]
                        row["keyword_flags"] = json.dumps(flags["keyword_flags"], ensure_ascii=False)
                        row["llm_flags"] = json.dumps(flags["llm_flags"], ensure_ascii=False)
                rows.append(row)
                write_rows(output, rows)
                print(f"Processed {index}/{len(paths)}: {session} {label}", flush=True)
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
                rows.append(row)
                write_rows(output, rows)
                raise
    finally:
        if old_mock is None:
            os.environ.pop("GNANI_MOCK", None)
        else:
            os.environ["GNANI_MOCK"] = old_mock
        gnani._REAL_SCRIPT = old_real
        after_llm = sum(1 for _ in log.open(encoding="utf-8")) - 1 if log.exists() and log.stat().st_size else 0
        print(f"Actual HTTP attempts — Prisma: {gnani.STATS['real_calls']}; Groq: {max(0, after_llm-before_llm)}")
        print(f"Prisma cache hits: {gnani.STATS['cache_hits']}")
    print(f"Saved: {output}")
    print("Note: P0/P6/P7 and follow-up/R1 transcripts are present in the CSV; current structured extraction does not support those types.")
    return rows

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", action="store_true",
                        help="Enable paid calls after typed confirmation")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit the number of recordings")
    parser.add_argument("--question", default=None,
                        help="Only process a question type, e.g. P1")
    args = parser.parse_args()

    paths, prompts, medicines, symptoms = load_inputs()

    if args.question:
        paths = [p for p in paths if classify(p)[2] == args.question.upper()]

    if args.limit:
        paths = paths[:args.limit]

    if not paths:
        raise SystemExit("No recordings match the selected filter.")

    plan = build_plan(paths, prompts, medicines, symptoms)

    if not args.real:
        print("STOP: preflight only. No API calls were made.")
        return

    phrase = input("To authorize the exact preflight above, type RUN SET B: ")
    if phrase != "RUN SET B":
        raise SystemExit("Cancelled. No API calls were made.")

    run(paths, prompts, medicines, symptoms)


if __name__ == "__main__":
    main()
