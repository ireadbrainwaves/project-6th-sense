#!/usr/bin/env python3
"""
bb8_latency_test.py  --  Phase 0 latency baseline for Project "6th Sense".

PURPOSE (and ONLY purpose):
    Connect to the Droid Depot BB-8 over BLE, send ONE test command, and measure
    round-trip latency. This is a throwaway measurement harness, NOT the start of
    the orchestration layer. No Gemini, no state machine, no swappable interface,
    no abstraction. Phase 0 only. Delete or ignore once latency is recorded.

WHAT IT MEASURES:
    (a) GATT write-with-response ACK round-trip  -> software lower bound.
    (b) Notify round-trip, IF the droid emits a notification on the read char.
    NOTE: neither equals "time to physical/audible reaction". True utterance->motion
    timing (Phase 1's exit criterion) needs external timing (mic/video). For Phase 0
    we just want a repeatable BLE baseline. Use the audible sound command below and
    you can also stopwatch/video the beep to cross-check physical latency by hand.

ALL byte values here are COMMUNITY-REPORTED and UNCONFIRMED against our unit.
See 6th_sense_protocol_notes.md. If the connect/handshake fails, that is expected
until we verify UUIDs and the init sequence with an on-device BLE scan.

Requires: Python 3.9+, bleak  ->  pip install bleak
Run:      python bb8_latency_test.py            (auto-discovers by name)
          python bb8_latency_test.py --address AA:BB:CC:DD:EE:FF
"""

import argparse
import asyncio
import statistics
import time

from bleak import BleakClient, BleakScanner

# --- Community-reported identifiers (UNCONFIRMED). See protocol notes. ---------
SERVICE_UUID = "09b600a0-3e42-41fc-b474-e9c0c8f0c801"
WRITE_UUID   = "09b600b1-3e42-41fc-b474-e9c0c8f0c801"  # command / write
NOTIFY_UUID  = "09b600b0-3e42-41fc-b474-e9c0c8f0c801"  # read / notify

# Droid Depot units typically advertise a name starting with "DROID".
NAME_PREFIX = "DROID"

# Init "capture attention" handshake. Link drops without it.
INIT_SEQUENCE = [
    bytes.fromhex("222001"),
    bytes.fromhex("27420f4444001f00"),
    bytes.fromhex("27420f4444001802"),
]
INIT_REPEATS = 3          # sources say "repeated multiple times"
INIT_GAP_S   = 0.10       # small gap between init writes

# The single test command whose latency we measure.
# Default = play a sound (audible => easy to cross-check by ear/video).
# Confirmed-structure command from the sources (sound track index 0x00):
TEST_COMMAND = bytes.fromhex("27420f4444001800")

# Alternative test payloads (uncomment ONE to swap the measured command):
#   Drive motor 0, forward, low power (a small physical nudge). Verify bytes before use:
# TEST_COMMAND = bytes.fromhex("29420546002001 2c0000".replace(" ", ""))  # 29 42 05 46 00 20 01 2C 00 00
#   NOTE: LED and dedicated head-rotation commands are UNKNOWN (see notes) --
#   do not invent them here; capture them first.

TRIALS = 10               # how many timed sends to average
INTER_TRIAL_S = 0.5       # spacing between trials


async def find_device(address: str | None):
    if address:
        print(f"[scan] looking for {address} ...")
        dev = await BleakScanner.find_device_by_address(address, timeout=15.0)
        if dev is None:
            raise RuntimeError(f"Device {address} not found. Is the droid on and unpaired?")
        return dev

    print(f"[scan] scanning for a device whose name starts with '{NAME_PREFIX}' ...")
    dev = await BleakScanner.find_device_by_filter(
        lambda d, ad: (d.name or "").upper().startswith(NAME_PREFIX),
        timeout=15.0,
    )
    if dev is None:
        raise RuntimeError(
            "No 'DROID*' device found. Turn the droid on, make sure it is NOT paired "
            "to the remote or the Droid Depot app, and pass --address if the name differs."
        )
    return dev


async def run(address: str | None):
    dev = await find_device(address)
    print(f"[scan] found: {dev.name} ({dev.address})")

    # Timestamp of the most recent notification, set by the callback.
    last_notify = {"t": None}

    def on_notify(_char, data: bytearray):
        last_notify["t"] = time.perf_counter()
        print(f"[notify] {data.hex()}")

    async with BleakClient(dev) as client:
        print(f"[conn] connected={client.is_connected}")

        # Subscribe to notifications if the characteristic supports it.
        notify_ok = False
        try:
            await client.start_notify(NOTIFY_UUID, on_notify)
            notify_ok = True
            print("[conn] subscribed to notify characteristic")
        except Exception as e:  # noqa: BLE001 - Phase 0 throwaway
            print(f"[conn] notify subscribe failed ({e}); will measure write-ACK only")

        # Send init handshake.
        print("[init] sending capture-attention handshake ...")
        for _ in range(INIT_REPEATS):
            for pkt in INIT_SEQUENCE:
                await client.write_gatt_char(WRITE_UUID, pkt, response=True)
                await asyncio.sleep(INIT_GAP_S)
        await asyncio.sleep(0.5)  # let the droid settle / beep

        ack_ms, notify_ms = [], []
        print(f"[test] sending test command x{TRIALS}: {TEST_COMMAND.hex()}")
        for i in range(TRIALS):
            last_notify["t"] = None
            t0 = time.perf_counter()
            await client.write_gatt_char(WRITE_UUID, TEST_COMMAND, response=True)
            t_ack = time.perf_counter()
            ack = (t_ack - t0) * 1000.0
            ack_ms.append(ack)

            line = f"  trial {i+1:2d}: write-ACK {ack:7.2f} ms"
            if notify_ok:
                # Give the droid a moment to notify back.
                await asyncio.sleep(0.3)
                if last_notify["t"] is not None:
                    nms = (last_notify["t"] - t0) * 1000.0
                    notify_ms.append(nms)
                    line += f" | notify {nms:7.2f} ms"
                else:
                    line += " | notify   (none)"
            print(line)
            await asyncio.sleep(INTER_TRIAL_S)

        if notify_ok:
            try:
                await client.stop_notify(NOTIFY_UUID)
            except Exception:  # noqa: BLE001
                pass

    # --- Summary ---
    def summarize(label, xs):
        if not xs:
            print(f"[result] {label}: no samples")
            return
        print(
            f"[result] {label}: n={len(xs)} "
            f"min={min(xs):.2f} med={statistics.median(xs):.2f} "
            f"mean={statistics.fmean(xs):.2f} max={max(xs):.2f} ms"
        )

    print("\n==== LATENCY BASELINE ====")
    summarize("write-ACK round-trip", ack_ms)
    summarize("notify round-trip", notify_ms)
    print("Copy the numbers into 6th_sense_protocol_notes.md -> Latency.")
    print("Reminder: BLE ACK != physical reaction time. Cross-check the beep with a stopwatch/video.")


def main():
    ap = argparse.ArgumentParser(description="Phase 0 BB-8 BLE latency baseline (throwaway).")
    ap.add_argument("--address", help="BLE MAC/UUID of the droid (skip name scan).")
    args = ap.parse_args()
    asyncio.run(run(args.address))


if __name__ == "__main__":
    main()
