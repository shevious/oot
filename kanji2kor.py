#!/usr/bin/env python3
"""
Convert message_data.h: replace SJIS-mapped Japanese kanji with Korean chars.

Reads:   code.csv                                  (sjis_char → kor_char table)
         extracted/ntsc-1.1/text/message_data.h    (input)
Writes:  message_data_kor.h                        (output, same directory as this script)
"""

import csv
import sys
from pathlib import Path

BASE      = Path(__file__).parent
CODE_CSV  = BASE / "code.csv"
INPUT_H   = BASE / "extracted/ntsc-1.1/text/message_data.h"
OUTPUT_H  = BASE / "message_data_utf8.h"

# Build translation table: sjis_char (one Unicode codepoint) → kor_char
table = {}
with open(CODE_CSV, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        src = row["sjis_char"]
        dst = row["kor_char"]
        if src and dst:
            table[ord(src)] = dst

trans = str.maketrans(table)

text = INPUT_H.read_text(encoding="utf-8")
converted = text.translate(trans)

OUTPUT_H.write_text(converted, encoding="utf-8")

replaced = sum(1 for ch in text if ord(ch) in table)
print(f"Replaced {replaced} characters → {OUTPUT_H}")
