#!/usr/bin/env python3
"""
droid_log.py  --  shared activity logger for Project "6th Sense".

Every script imports this and calls log_event(...) so all on-unit actions land in
ONE running CSV (droid_activity_log.csv, in this folder). That gives us a permanent,
timestamped record of what we sent and how the droid reacted -- the raw material for
Confirmed Findings and latency analysis, without retyping anything.

Usage from any script:
    from droid_log import log_event
    log_event(script="bb8_command_test", action="Head LED ON",
              command_hex="27 42 0F 44 44 00 48 01", ack_ms=112.1, reacted="y")
"""

import csv
import os
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "droid_activity_log.csv")
FIELDS = ["timestamp", "script", "action", "command_hex", "ack_ms", "reacted", "notes"]

def log_event(script: str, action: str, command_hex: str = "",
              ack_ms=None, reacted: str = "", notes: str = "") -> str:
    """Append one row to the shared CSV. Writes the header if the file is new."""
    is_new = not os.path.isfile(LOG_PATH)
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "script": script,
            "action": action,
            "command_hex": command_hex,
            "ack_ms": f"{ack_ms:.1f}" if isinstance(ack_ms, (int, float)) else (ack_ms or ""),
            "reacted": reacted,
            "notes": notes,
        })
    return LOG_PATH
