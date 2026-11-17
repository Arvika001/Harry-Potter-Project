"""Select new, non-repeating Harry Potter dialogue validation batches.

Usage (first run):
    python validate_dialogues_batches.py --input dialogue_review.csv --previous validation_review.xlsx

Later runs (same command is safe):
    python validate_dialogues_batches.py --input dialogue_review.csv --previous validation_review.xlsx

Requires openpyxl only when reading .xlsx: pip install openpyxl
Keep this script, the original CSV and the reviewed workbook in the same folder,
or supply their paths. Outputs go into validation_batches/ by default.
"""
import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

FIELDS = ["id", "chapter", "pdf_page", "speaker", "candidate_listener",
          "dialogue_excerpt", "confidence", "reviewed"]
EXTRA = ["verified_speaker", "verified_listener", "interaction_type",
         "manual_status", "verification_notes"]


def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_previous_ids(path):
    """Read IDs from an earlier reviewed CSV or XLSX; never modify the source."""
    if path.suffix.lower() == ".csv":
        rows = load_csv(path)
    elif path.suffix.lower() == ".xlsx":
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise SystemExit("Install Excel support: pip install openpyxl") from exc
        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        values = ws.iter_rows(values_only=True)
        headers = [str(v).strip() if v is not None else "" for v in next(values)]
        rows = [dict(zip(headers, values_row)) for values_row in values]
        wb.close()
    else:
        raise ValueError(f"Unsupported previous-file type: {path}")
    if rows and "id" not in rows[0]:
        raise ValueError(f"Previous file lacks an 'id' column: {path}")
    return {str(r["id"]).strip() for r in rows if r.get("id") is not None and str(r["id"]).strip()}


def choose(rows, used_ids, batch_number, per_chapter, seed):
    by_chapter = defaultdict(list)
    for row in rows:
        if row["id"].strip() not in used_ids:
            by_chapter[row["chapter"].strip()].append(row)

    rng = random.Random(seed + batch_number)
    selected = []
    counts = {}
    for chapter in sorted(by_chapter, key=lambda x: (0, int(x)) if x.isdigit() else (1, x)):
        available = by_chapter[chapter]
        attributed = [r for r in available if r["speaker"].strip()]
        unattributed = [r for r in available if not r["speaker"].strip()]
        chosen = []
        if attributed:
            chosen.append(rng.choice(attributed))
        if unattributed and len(chosen) < per_chapter:
            chosen.append(rng.choice(unattributed))
        remaining = [r for r in available if r not in chosen]
        chosen.extend(rng.sample(remaining, min(per_chapter - len(chosen), len(remaining))))
        selected.extend(chosen)
        counts[chapter] = len(chosen)
    return selected, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=Path("dialogue_review.csv"), help="Original dialogue CSV")
    parser.add_argument("--previous", type=Path, action="append", default=[], help="Earlier reviewed CSV/XLSX, repeat option for multiple files")
    parser.add_argument("--output-dir", type=Path, default=Path("validation_batches"))
    parser.add_argument("--per-chapter", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.per_chapter < 1:
        parser.error("--per-chapter must be at least 1")
    if not args.input.is_file():
        parser.error(f"Input not found: {args.input}")
    for p in args.previous:
        if not p.is_file():
            parser.error(f"Previous file not found: {p}")
    rows = load_csv(args.input)
    if not rows or not set(FIELDS).issubset(rows[0]):
        parser.error("Input must contain all original dialogue_review.csv columns")
    ids = [r["id"].strip() for r in rows]
    if not all(ids) or len(ids) != len(set(ids)):
        parser.error("Input IDs must be nonempty and unique")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    # Existing batch CSVs are the history: do not depend on a separate fragile state file.
    existing = sorted(args.output_dir.glob("validation_batch_*.csv"))
    used = set()
    for p in args.previous:
        used.update(read_previous_ids(p))
    for p in existing:
        used.update(read_previous_ids(p))
    # Batch 1 is the original reviewed sample, supplied via --previous.
    if not args.previous and not existing:
        parser.error("Supply --previous validation_review.xlsx (or the original validation_sample.csv) "
                     "on the first run, so Batch 2 cannot repeat Batch 1")
    batch_numbers = []
    for p in existing:
        suffix = p.stem.removeprefix("validation_batch_")
        if suffix.isdigit():
            batch_numbers.append(int(suffix))
    number = max([1, *batch_numbers]) + 1
    selected, counts = choose(rows, used, number, args.per_chapter, args.seed)
    selected_ids = {r["id"].strip() for r in selected}
    totals = defaultdict(int)
    used_by_chapter = defaultdict(int)
    remaining_by_chapter = defaultdict(int)
    for row in rows:
        chapter = row["chapter"].strip()
        totals[chapter] += 1
        if row["id"].strip() in used:
            used_by_chapter[chapter] += 1
        elif row["id"].strip() not in selected_ids:
            remaining_by_chapter[chapter] += 1

    def chapter_key(chapter):
        return (0, int(chapter)) if chapter.isdigit() else (1, chapter)

    def print_progress():
        print("\nDialogue sampling progress (after this run):")
        print(f"{'Chapter':<10} {'Total':>7} {'Previously':>11} {'New':>7} {'Remaining':>11}")
        print("-" * 51)
        for chapter in sorted(totals, key=chapter_key):
            print(f"{chapter:<10} {totals[chapter]:>7} {used_by_chapter[chapter]:>11} "
                  f"{counts.get(chapter, 0):>7} {remaining_by_chapter[chapter]:>11}")
        print("-" * 51)
        print(f"{'TOTAL':<10} {sum(totals.values()):>7} {sum(used_by_chapter.values()):>11} "
              f"{len(selected):>7} {sum(remaining_by_chapter.values()):>11}")
        print("Previously = selected in earlier batches (not necessarily reviewed).")
        print("Remaining = dialogue records not yet selected for manual checking.")

    if not selected:
        print("No new records remain. No file created.")
        print_progress()
        return
    output = args.output_dir / f"validation_batch_{number:02d}.csv"
    # Exclusive creation avoids overwriting previous manual work.
    with output.open("x", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS + EXTRA)
        writer.writeheader()
        for row in selected:
            new = {col: row.get(col, "") for col in FIELDS}
            new.update({"verified_speaker": "", "verified_listener": "",
                        "interaction_type": "", "manual_status": "pending",
                        "verification_notes": ""})
            writer.writerow(new)
    print(f"Created: {output} ({len(selected)} NEW dialogue records)")
    print(f"Previously selected IDs excluded: {len(used)}")
    print("Selected per chapter:", ", ".join(f"{c}: {n}" for c, n in counts.items()))
    print_progress()
    print("Review this batch in Excel. Keep the file for future runs.")
    print("IMPORTANT: Always pass --previous for original Batch 1, and keep older batch CSVs in output-dir.")


if __name__ == "__main__":
    main()
