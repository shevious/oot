#!/usr/bin/env python3
"""
Reverse-convert message_data_kor.h back to kanji (SJIS-mapped Japanese chars).
Duplicate kor_char values use the first matched row in code.csv.

Reads:   code.csv
         message_data_kor.h
Writes:  message_data_kanji.h
Checks:  message_data_kanji.h == extracted/ntsc-1.1/text/message_data.h
"""

import csv
import sys
from pathlib import Path

BASE       = Path(__file__).parent
CODE_CSV   = BASE / "code.csv"
INPUT_H    = BASE / "message_data_utf8.h"
OUTPUT_H   = BASE / "message_data_kanji.h"
REFERENCE  = BASE / "extracted/ntsc-1.1/text/message_data.h"

# Build reverse table: kor_char → sjis_char  (first occurrence wins)
table = {}
with open(CODE_CSV, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        src = row["kor_char"]
        dst = row["sjis_char"]
        if src and dst and ord(src) not in table:
            table[ord(src)] = dst

trans = str.maketrans(table)

text = INPUT_H.read_text(encoding="utf-8")
converted = text.translate(trans)

OUTPUT_H.write_text(converted, encoding="utf-8")
replaced = sum(1 for ch in text if ord(ch) in table)
print(f"Replaced {replaced} characters → {OUTPUT_H}")

# Verify against original
ref = REFERENCE.read_text(encoding="utf-8")
if converted == ref:
    print("OK: message_data_kanji.h matches message_data.h exactly.")
else:
    # Find first differing position for diagnosis
    for i, (a, b) in enumerate(zip(converted, ref)):
        if a != b:
            lo = max(0, i - 30)
            print(f"MISMATCH at char {i}:")
            print(f"  got: {repr(converted[lo:i+10])}")
            print(f"  ref: {repr(ref[lo:i+10])}")
            break
    else:
        print(f"MISMATCH: lengths differ ({len(converted)} vs {len(ref)})")
    sys.exit(1)
