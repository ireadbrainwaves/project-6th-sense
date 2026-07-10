#!/usr/bin/env python3
"""
bb8_sound_sweep.py  --  discover the BB-8's built-in sound ROM (Phase 2 side task).

WHAT THIS IS:
    A discovery harness. It sweeps the droid's onboard sound library by selecting
    each sound BANK (SetSelectedSoundBank, audio cmd 31 / 0x1F) and then firing each
    TRACK index within it (PlayAudioFromSelectedGroup, audio cmd 24 / 0x18). Every
    sound is generated from the SAME framing rule already confirmed on-unit (our
    init handshake IS SetSelectedSoundBank(0) and our confirmed beep IS
    PlayAudioFromSelectedGroup(0x18)) -- so there are no NEW bytes to trust here.
    We're only enumerating the (bank, track) space to find what's in the ROM.

WHY:
    The voice loop currently fires exactly one confirmed beep. This builds a labeled
    map of real sounds (happy chirp, sad warble, alarm, ...) so BB-8 can react with
    the RIGHT sound. Output: droid_sound_map.csv, plus rows in the shared
    droid_activity_log.csv.

MODES:
    interactive (default) -- plays each sound and waits for you to react:
        [Enter]=next (unlabeled)   y=played   n=nothing
        l=label it (marks played)  r=replay   s=skip rest of this bank   q=quit
    --auto                -- fires every (bank, track) with a fixed --delay and logs
                             them reacted="?"; no prompts. Fast "what's in here" pass;
                             listen and note which indices spoke, then re-run
                             interactive on just those.

SAFETY: sounds can be LOUD. Default --volume is modest; raise if you can't hear it.
        Keep the remote OFF and the Droid Depot app force-closed (see protocol notes).

Requires: pip install bleak
Run:  python bb8_sound_sweep.py --address DA:A2:05:2C:0B:26
      python bb8_sound_sweep.py --banks 0-10 --tracks 0-25 --volume 45
      python bb8_sound_sweep.py --auto --delay 1.2
"""

import argparse
import asyncio
import csv
import os
import time

from bleak import BleakClient, BleakScanner
from droid_log import log_event   # shared CSV logger

SCRIPT_NAME = "bb8_sound_sweep"

WRITE_UUID  = "09b600b1-3e42-41fc-b474-e9c0c8f0c801"
NOTIFY_UUID = "09b600b0-3e42-41fc-b474-e9c0c8f0c801"
NAME_PREFIX = "DROID"

# Confirmed init handshake (droid beeps). Note the 2nd packet == SetSelectedSoundBank(0).
INIT_SEQUENCE = ["222001", "27420f4444001f00", "27420f4444001802"]

SOUND_MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "droid_sound_map.csv")

# ---------------------------------------------------------------------------
# THE FRAMING RULE  (identical to bb8_command_test.py; confirmed on-unit 2026-07-07)
# ---------------------------------------------------------------------------

def int_to_hex(n: int) -> str:
    h = hex(n)[2:]
    return ("0" + h) if len(h) % 2 else h

def build_command(command_id: int, data: str = "") -> bytes:
    dl = len(data) // 2
    return bytes([(dl + 3) | 0x20, 0x42 if command_id == 15 else 0x00, command_id, dl + 0x40]) + bytes.fromhex(data)

def multi(sub_id: int, data: str = "") -> bytes:
    return build_command(15, "44" + "{:02d}".format(sub_id) + data)

def audio(audio_cmd: int, data: str = "00") -> bytes:
    return multi(0, int_to_hex(audio_cmd) + data)

# The two sound commands we sweep. Both are audio-controller sub-commands.
def select_bank(bank: int) -> bytes:
    return audio(31, int_to_hex(bank))     # SetSelectedSoundBank = 31 (0x1F)

def play_sound(track: int) -> bytes:
    return audio(24, int_to_hex(track))    # PlayAudioFromSelectedGroup = 24 (0x18)

def set_volume(level: int) -> bytes:
    return audio(14, int_to_hex(level))    # SetVolume = 14 (0x0E)

# ---------------------------------------------------------------------------

def parse_range(s: str):
    """'0-10' -> [0..10];  '5' -> [5]."""
    s = s.strip()
    if "-" in s:
        a, b = s.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(s)]


async def find_device(address):
    if address:
        print(f"[scan] looking for {address} (20s)... power the droid on NOW.")
        dev = await BleakScanner.find_device_by_address(address, timeout=20.0)
        if dev:
            return dev
        print("[scan] exact address not seen; falling back to a name scan for any DROID...")
    dev = await BleakScanner.find_device_by_filter(
        lambda d, ad: (d.name or "").upper().startswith(NAME_PREFIX), timeout=20.0)
    if dev:
        return dev
    raise RuntimeError(
        "No droid found. Checklist: (1) remote fully OFF, (2) Droid Depot app force-closed, "
        "(3) power the droid OFF then ON and run this within ~5 seconds, (4) keep it within a few feet.")


async def send(client, packet: bytes) -> float:
    t0 = time.perf_counter()
    await client.write_gatt_char(WRITE_UUID, packet, response=True)
    return (time.perf_counter() - t0) * 1000.0


def write_sound_map(discovered):
    """Write the labeled map of sounds that actually played."""
    with open(SOUND_MAP_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bank", "track", "command_hex", "label"])
        for bank, track, hx, label in discovered:
            w.writerow([bank, track, hx, label])
    return SOUND_MAP_PATH


async def run(args):
    banks = parse_range(args.banks)
    tracks = parse_range(args.tracks)
    dev = await find_device(args.address)
    print(f"[found] {dev.name} ({dev.address})")

    discovered = []       # (bank, track, hex, label) for sounds confirmed to play
    quit_all = False

    async with BleakClient(dev) as client:
        print(f"[conn] connected={client.is_connected}")
        try:
            await client.start_notify(NOTIFY_UUID, lambda s, d: print(f"  [notify] {d.hex()}"))
        except Exception:
            pass

        print("[init] sending confirmed handshake (droid should beep)...")
        for _ in range(3):
            for pkt in INIT_SEQUENCE:
                await client.write_gatt_char(WRITE_UUID, bytes.fromhex(pkt), response=True)
                await asyncio.sleep(0.1)
        await asyncio.sleep(0.5)

        await send(client, set_volume(args.volume))
        print(f"[vol] volume set ~{args.volume}")
        print(f"[sweep] banks {banks[0]}..{banks[-1]}  x  tracks {tracks[0]}..{tracks[-1]}"
              f"  ({'AUTO' if args.auto else 'interactive'})")

        loop = asyncio.get_event_loop()

        for bank in banks:
            if quit_all:
                break
            await send(client, select_bank(bank))
            await asyncio.sleep(0.2)
            print(f"\n===== BANK {bank} (0x{bank:02X}) =====")
            skip_bank = False

            for track in tracks:
                if skip_bank or quit_all:
                    break
                pkt = play_sound(track)
                ack = await send(client, pkt)
                hx = pkt.hex(" ").upper()
                action = f"Sound bank{bank} track{track}"
                notes_base = f"bank={bank} track={track}"
                print(f"  bank {bank} track {track:>2}: {hx}  ({ack:.0f} ms ACK)")

                if args.auto:
                    log_event(SCRIPT_NAME, action, hx, ack, "?", notes_base + " auto")
                    await asyncio.sleep(args.delay)
                    continue

                # interactive: react to what you heard
                advanced = False
                while not advanced:
                    choice = (await loop.run_in_executor(
                        None, input, "   [Enter]=next  y=played  n=nothing  l=label  r=replay  s=skip-bank  q=quit > "
                    )).strip().lower()

                    if choice == "r":
                        await send(client, select_bank(bank))
                        await asyncio.sleep(0.1)
                        ack = await send(client, pkt)
                        print("   (replayed)")
                        continue
                    if choice == "l":
                        label = (await loop.run_in_executor(None, input, "   label > ")).strip()
                        log_event(SCRIPT_NAME, action, hx, ack, "y", notes_base + f" label={label}")
                        discovered.append((bank, track, hx, label))
                        print(f"   -> logged as played: {label}")
                        advanced = True
                    elif choice == "y":
                        log_event(SCRIPT_NAME, action, hx, ack, "y", notes_base)
                        discovered.append((bank, track, hx, ""))
                        advanced = True
                    elif choice == "n":
                        log_event(SCRIPT_NAME, action, hx, ack, "n", notes_base + " silent")
                        advanced = True
                    elif choice == "s":
                        print(f"   -> skipping rest of bank {bank}")
                        skip_bank = True
                        advanced = True
                    elif choice == "q":
                        quit_all = True
                        advanced = True
                    else:   # Enter / anything else -> next, unlabeled
                        log_event(SCRIPT_NAME, action, hx, ack, "", notes_base)
                        advanced = True

    # --- summary ---
    print("\n==== SWEEP DONE ====")
    if discovered:
        path = write_sound_map(discovered)
        print(f"[map] {len(discovered)} sound(s) that played -> {os.path.basename(path)}")
        for bank, track, hx, label in discovered:
            print(f"   bank {bank} track {track}: {label or '(unlabeled)'}  [{hx}]")
        print("Wire the good ones into the voice loop's body vocabulary by (bank, track).")
    else:
        print("[map] no sounds marked as played. In --auto? Re-run interactive on the indices you heard.")
    print("All attempts also appended to droid_activity_log.csv.")


def main():
    ap = argparse.ArgumentParser(description="Sweep the BB-8's built-in sound ROM (bank x track).")
    ap.add_argument("--address", default="DA:A2:05:2C:0B:26", help="BLE address of the droid.")
    ap.add_argument("--banks", default="0-10", help="bank range, e.g. '0-10' or '3'. (docs: banks 0-A)")
    ap.add_argument("--tracks", default="0-25", help="track index range per bank, e.g. '0-25' or '7'.")
    ap.add_argument("--volume", type=int, default=45, help="playback volume 0-255 (modest default).")
    ap.add_argument("--auto", action="store_true", help="fire every combo with --delay, no prompts.")
    ap.add_argument("--delay", type=float, default=1.2, help="seconds between sounds in --auto mode.")
    args = ap.parse_args()
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\n[abort] interrupted.")


if __name__ == "__main__":
    main()
