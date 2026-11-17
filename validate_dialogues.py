
import csv
import random
from collections import defaultdict
from pathlib import Path

# ============================================
# HARRY POTTER DIALOGUE VALIDATION SAMPLER
# ============================================

# Folder containing this Python script
FOLDER = Path(__file__).resolve().parent

# Original dataset
INPUT_FILE = FOLDER / "dialogue_review.csv"

# Files that will be created
OUTPUT_FILE = FOLDER / "validation_sample.csv"
SUMMARY_FILE = FOLDER / "validation_summary.txt"

# Number of dialogue records to sample per chapter
SAMPLE_PER_CHAPTER = 3

# Fixed seed makes the sample reproducible
RANDOM_SEED = 42

random.seed(RANDOM_SEED)


def read_dialogues():
    """Read the original CSV without modifying it."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Cannot find {INPUT_FILE.name}. "
            "Place the CSV in the same folder as this script."
        )

    with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    required_columns = {
        "id",
        "chapter",
        "pdf_page",
        "speaker",
        "candidate_listener",
        "dialogue_excerpt",
        "confidence",
        "reviewed",
    }

    if not rows:
        raise ValueError("The input CSV contains no dialogue records.")

    missing = required_columns - set(rows[0].keys())

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    return rows


def select_sample(rows):
    """
    Select three records per chapter where possible.

    Prefer a mixture of:
    - Records with an attributed speaker
    - Records without an attributed speaker
    - Other randomly selected records

    This is a diagnostic sample, not a statistically
    representative random sample of all dialogues.
    """

    chapters = defaultdict(list)

    for row in rows:
        chapter = row["chapter"].strip()
        chapters[chapter].append(row)

    selected = []

    for chapter in sorted(
        chapters,
        key=lambda x: int(x) if x.isdigit() else x
    ):
        chapter_rows = chapters[chapter]

        attributed = [
            row for row in chapter_rows
            if row["speaker"].strip()
        ]

        unattributed = [
            row for row in chapter_rows
            if not row["speaker"].strip()
        ]

        chosen = []

        # Pick one dialogue with a speaker
        if attributed:
            chosen.append(random.choice(attributed))

        # Pick one dialogue without a speaker
        if unattributed:
            chosen.append(random.choice(unattributed))

        # Fill remaining sample slots
        remaining = [
            row for row in chapter_rows
            if row not in chosen
        ]

        slots = SAMPLE_PER_CHAPTER - len(chosen)

        if slots > 0:
            chosen.extend(
                random.sample(
                    remaining,
                    min(slots, len(remaining))
                )
            )

        selected.extend(chosen)

    return selected, chapters


def save_sample(selected):
    """Create a CSV for manual validation."""

    original_columns = [
        "id",
        "chapter",
        "pdf_page",
        "speaker",
        "candidate_listener",
        "dialogue_excerpt",
        "confidence",
        "reviewed",
    ]

    additional_columns = [
        "verified_speaker",
        "verified_listener",
        "interaction_type",
        "manual_status",
        "verification_notes",
    ]

    columns = original_columns + additional_columns

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        writer.writeheader()

        for row in selected:
            new_row = {
                col: row.get(col, "")
                for col in original_columns
            }

            # These fields must be filled manually
            new_row["verified_speaker"] = ""
            new_row["verified_listener"] = ""
            new_row["interaction_type"] = ""
            new_row["manual_status"] = "pending"
            new_row["verification_notes"] = ""

            writer.writerow(new_row)


def save_summary(rows, selected, chapters):
    """Save a description of the sampling method."""

    lines = [
        "HARRY POTTER DIALOGUE VALIDATION",
        "=" * 40,
        "",
        f"Total original records: {len(rows)}",
        f"Chapters found: {len(chapters)}",
        f"Records selected: {len(selected)}",
        f"Target per chapter: {SAMPLE_PER_CHAPTER}",
        f"Random seed: {RANDOM_SEED}",
        "",
        "SAMPLING METHOD",
        "-" * 40,
        "Up to three dialogue records were selected",
        "from each chapter.",
        "",
        "Where available, the sample includes:",
        "1. One attributed dialogue",
        "2. One unattributed dialogue",
        "3. One additional randomly chosen dialogue",
        "",
        "This is a stratified diagnostic sample.",
        "It is not a statistically representative",
        "sample of all dialogue interactions.",
        "",
        "IMPORTANT LIMITATIONS",
        "-" * 40,
        "No records were automatically verified.",
        "Speaker names require manual checking.",
        "Listeners require contextual verification.",
        "Adjacent dialogue does not always imply",
        "direct character interaction.",
        "",
        "CHAPTER COUNTS",
        "-" * 40,
    ]

    for chapter in sorted(
        chapters,
        key=lambda x: int(x) if x.isdigit() else x
    ):
        count = sum(
            1 for row in selected
            if row["chapter"].strip() == chapter
        )

        lines.append(
            f"Chapter {chapter}: "
            f"{len(chapters[chapter])} original, "
            f"{count} selected"
        )

    SUMMARY_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


def main():
    print("Starting dialogue validation sampler...")

    rows = read_dialogues()

    selected, chapters = select_sample(rows)

    save_sample(selected)

    save_summary(rows, selected, chapters)

    print(f"Loaded {len(rows)} original dialogue records.")
    print(
        f"Selected {len(selected)} records "
        f"across {len(chapters)} chapters."
    )
    print(f"Created: {OUTPUT_FILE.name}")
    print(f"Created: {SUMMARY_FILE.name}")
    print(
        "IMPORTANT: No records have been "
        "automatically verified."
    )


if __name__ == "__main__":
    main()
