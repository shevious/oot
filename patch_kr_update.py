#!/usr/bin/env python3
"""
Create a Korean-patched version of NTSC 1.2 message_data.h.

file1: oot/extracted/ntsc-1.1/text/message_data.h   (original English 1.1)
file2: ootkr/extracted/ntsc-1.1/text/message_data.h  (Korean 1.1, patched from file1)
file3: oot/extracted/ntsc-1.2/text/message_data.h    (English 1.2, updated from file1)

file12.diff: diff file1 file2  (shows Korean translation changes)
file13.diff: diff file1 file3  (shows 1.1→1.2 updates)

Strategy:
  1. From file13.diff, find (f1_lineno, f3_lineno) pairs for lines identical
     between file1 and file3.
  2. From file12.diff, process all 'c' hunks:
     - Equal line counts: 1-to-1 line replacement in file3.
     - Unequal line counts: range replacement — the N file3 lines are replaced
       by the M file2 lines (Korean translation changed the line structure).
  3. Hunks whose file1 lines have no file3 mapping (changed in 1.2) are skipped.

Output: ootkr/message_data_kor.h
"""

import re
from pathlib import Path

BASE   = Path(__file__).parent
FILE1  = BASE / "message_data_rev1.h"
FILE2  = BASE / "extracted/ntsc-1.1/text/message_data.h"
FILE3  = BASE / "extracted/ntsc-1.2/text/message_data.h"
DIFF12 = BASE / "file12.diff"
DIFF13 = BASE / "file13.diff"
OUTPUT = BASE / "message_data_kor.h"

HUNK_RE = re.compile(r'^(\d+)(?:,(\d+))?([acd])(\d+)(?:,(\d+))?')


def parse_hunks(diff_path: Path):
    hunks = []
    for line in diff_path.read_text(encoding='utf-8', errors='replace').splitlines():
        m = HUNK_RE.match(line)
        if m:
            l1 = int(m.group(1)); l2 = int(m.group(2)) if m.group(2) else l1
            op = m.group(3)
            r1 = int(m.group(4)); r2 = int(m.group(5)) if m.group(5) else r1
            hunks.append((l1, l2, op, r1, r2))
    return hunks


def identical_pairs(diff_path: Path, left_total: int):
    """Return {f1_lineno: f3_lineno} for lines identical in both files."""
    pairs = {}
    left_cur = 1; right_cur = 1
    for l1, l2, op, r1, r2 in parse_hunks(diff_path):
        if op == 'a':
            for i in range(l1 - left_cur + 1):
                pairs[left_cur + i] = right_cur + i
            left_cur = l1 + 1; right_cur = r2 + 1
        elif op == 'd':
            for i in range(l1 - left_cur):
                pairs[left_cur + i] = right_cur + i
            left_cur = l2 + 1; right_cur = r1 + 1
        elif op == 'c':
            for i in range(l1 - left_cur):
                pairs[left_cur + i] = right_cur + i
            left_cur = l2 + 1; right_cur = r2 + 1
    if left_total > 0 and left_cur <= left_total:
        offset = right_cur - left_cur
        for ln in range(left_cur, left_total + 1):
            pairs[ln] = ln + offset
    return pairs


def build_replacements(diff_path: Path, f1_to_f3: dict, f2_lines: list):
    """
    Process all 'c' hunks in diff_path (file12.diff).

    Returns:
      replace_1to1  : {f3_0idx: line}            — equal-count hunks
      range_reps    : [(f3_start_0, f3_end_0_excl, [lines])]  — unequal-count hunks
    """
    replace_1to1 = {}
    range_reps   = []
    skipped      = 0

    for l1, l2, op, r1, r2 in parse_hunks(diff_path):
        if op != 'c':
            continue

        lc = l2 - l1 + 1
        rc = r2 - r1 + 1

        # Map each file1 line in this hunk to its file3 counterpart
        f3_lns = [f1_to_f3.get(l1 + i) for i in range(lc)]
        if any(f3_ln is None for f3_ln in f3_lns):
            skipped += 1
            continue

        f2_replacement = f2_lines[r1 - 1 : r2]

        if lc == rc:
            for i, f3_ln in enumerate(f3_lns):
                if f3_ln <= len(f2_lines):
                    replace_1to1[f3_ln - 1] = f2_replacement[i]
        else:
            # Replace the block f3_lns[0]..f3_lns[-1] with f2_replacement
            f3_start_0      = f3_lns[0] - 1
            f3_end_0_excl   = f3_lns[-1]      # == f3_lns[-1] - 1 + 1
            range_reps.append((f3_start_0, f3_end_0_excl, f2_replacement))

    if skipped:
        print(f"  Skipped {skipped} hunks (file1 lines not present in file3)")
    print(f"  1-to-1 replacements:  {len(replace_1to1)}")
    print(f"  Range replacements:   {len(range_reps)}")
    return replace_1to1, range_reps


def apply_replacements(f3_lines: list, replace_1to1: dict, range_reps: list):
    """
    Build output by walking file3 lines and applying both replacement types.
    Range replacements take priority and consume multiple lines at once.
    """
    range_reps_sorted = sorted(range_reps, key=lambda x: x[0])
    rr_idx = 0
    output = []
    i = 0
    while i < len(f3_lines):
        if rr_idx < len(range_reps_sorted) and i == range_reps_sorted[rr_idx][0]:
            start, end, new_lines = range_reps_sorted[rr_idx]
            output.extend(new_lines)
            i = end
            rr_idx += 1
        elif i in replace_1to1:
            output.append(replace_1to1[i])
            i += 1
        else:
            output.append(f3_lines[i])
            i += 1
    return output


def main():
    f1_lines = FILE1.read_text(encoding='utf-8').splitlines(keepends=True)
    f2_lines = FILE2.read_text(encoding='utf-8').splitlines(keepends=True)
    f3_lines = FILE3.read_text(encoding='utf-8').splitlines(keepends=True)

    print(f"file1: {len(f1_lines)} lines")
    print(f"file2: {len(f2_lines)} lines (Korean 1.1)")
    print(f"file3: {len(f3_lines)} lines (English 1.2)")

    f1_to_f3 = identical_pairs(DIFF13, len(f1_lines))
    print(f"  file1↔file3 identical lines: {len(f1_to_f3)}")

    replace_1to1, range_reps = build_replacements(DIFF12, f1_to_f3, f2_lines)

    output = apply_replacements(f3_lines, replace_1to1, range_reps)
    OUTPUT.write_text(''.join(output), encoding='utf-8')
    print(f"Output: {len(output)} lines → {OUTPUT}")


if __name__ == "__main__":
    main()
