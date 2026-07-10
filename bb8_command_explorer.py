#!/usr/bin/env python3
"""
bb8_command_explorer.py  --  enumerate EVERY BB-8 command we can find (Phase 2 side task).

THREE JOBS (pick with flags; default = interactive catalog):

  1. CATALOG (default) -- an interactive menu of every command decoded from
     thetestgame/pyDroidDepot, each generated from the ONE confirmed framing rule
     (build_command). Fire any of them, watch the droid, log the reaction. This is
     the "all the commands we know" list in runnable form.

  2. --sweep-audio LO-HI -- discovery. The audio controller (multipurpose sub-id 0)
     is a big command space: id 24=play sound, 31=select bank, 14=volume,
     72/73=LED on/off, etc. Most ids are undocumented. This walks the id byte and
     fires audio(id, 01), logging whatever the droid does, to surface functions we
     don't have names for yet. Re-asserts LED-on between ids to keep a known state.

  3. --probe -- telemetry / BATTERY hunt. Subscribes to the notify characteristic,
     enables notifications, then fires a set of candidate "query" commands and logs
     ANY bytes the droid sends back. HONEST EXPECTATION: our own logs show this
     notify char has returned nothing so far (the droid looks write-only), so battery
     may simply not be exposed. This proves it either way and captures anything that
     does come back for decoding.

SAFETY:
  - Drive commands are LOW power + auto-stopped, but still MOVE the droid -- clear floor.
  - --sweep-audio fires unknown ids; it stays inside the audio controller (sound/LED
    space), never the motor space, so nothing should roll away. STOP is always option 'x'.
  - Keep the remote OFF and the Droid Depot app force-closed (see protocol notes).

Requires: pip install bleak
Run:  python bb8_command_explorer.py --address DA:A2:05:2C:0B:26
      python bb8_command_explorer.py --sweep-audio 1-90
      python bb8_command_explorer.py --probe
"""

import argparse
import asyncio
import os
import time

from bleak import BleakClient, BleakScanner
from droid_log import log_event   # shared CSV logger

SCRIPT_NAME = "bb8_command_explorer"

WRITE_UUID  = "09b600b1-3e42-41fc-b474-e9c0c8f0c801"
NOTIFY_UUID = "09b600b0-3e42-41fc-b474-e9c0c8f0c801"
NAME_PREFIX = "DROID"

INIT_SEQUENCE = ["222001", "27420f4444001f00", "27420f4444001802"]
BB_HEAD_LED = 1   # BBUnitHeadLed identifier

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

# ---------------------------------------------------------------------------
# THE FULL KNOWN COMMAND SET  (every command generated from the rule; nothing hardcoded)
# audio-controller ids: 14 SetVolume, 24 PlayAudioFromSelectedGroup, 31 SetSelectedSoundBank,
#   69 FlashHeadLeds, 72 SetLedOn, 73 SetLedOff, 74 DisableHeadLeds, 75 EnableHeadLeds.
# top-level command ids: 15 multipurpose, 5 SetMotorSpeed, 2 SetPairingLedState.
# multipurpose sub-ids: 0 audio, 1 CenterRUnitHead, 4 RotateBUnitHead, 5 DriveBUnit.
# ---------------------------------------------------------------------------

def head_led(on):          return audio(72 if on else 73, int_to_hex(BB_HEAD_LED))
def head_led_flash():      return audio(69, int_to_hex(BB_HEAD_LED))
def head_led_enable(on):   return audio(75 if on else 74, int_to_hex(BB_HEAD_LED))
def play_sound(track=0):   return audio(24, int_to_hex(track))
def select_bank(bank=0):   return audio(31, int_to_hex(bank))
def set_volume(level=50):  return audio(14, int_to_hex(level))
def pairing_led(on):       return build_command(2, "0042" + ("00ff" if on else "0000"))   # SetPairingLedState (cmd 2)
def head_rotate(back=False, speed=120, ramp=300):
    return multi(4, ("ff" if back else "00") + int_to_hex(speed) + int_to_hex(ramp) + "0000")
def center_head():         return multi(1, "00" + int_to_hex(300) + "0000")               # CenterRUnitHead (sub-id 1)
def drive(motor=0, back=False, speed=70, ramp=300):
    return build_command(5, ("%d%d" % (8 if back else 0, motor)) + int_to_hex(speed) + int_to_hex(ramp) + "0000")
def stop_motor(motor=0):   return build_command(5, ("0%d" % motor) + "00" + int_to_hex(300) + "0000")

# Catalog: key -> (label, packet-or-callable, "what to watch for")
CATALOG = {
    "1":  ("Play sound (track 0)",     play_sound(0),        "audible beep (LOUD)"),
    "2":  ("Select sound bank 0",      select_bank(0),       "no sound; sets bank for next play"),
    "3":  ("Set volume ~50",           set_volume(50),       "no effect now; sets level"),
    "4":  ("Head LED ON",              head_led(True),       "head light on"),
    "5":  ("Head LED OFF",             head_led(False),      "head light off"),
    "6":  ("Head LED flash",           head_led_flash(),     "flash (NO reaction on our unit - anomaly)"),
    "7":  ("Head LEDs ENABLE",         head_led_enable(True), "enable head LED channel"),
    "8":  ("Head LEDs DISABLE",        head_led_enable(False),"disable head LED channel"),
    "9":  ("Pairing/body LED ON",      pairing_led(True),    "body pairing LED on (UNCONFIRMED)"),
    "10": ("Pairing/body LED OFF",     pairing_led(False),   "body pairing LED off (UNCONFIRMED)"),
    "11": ("Head rotate LEFT",         head_rotate(False),   "dome turns one way"),
    "12": ("Head rotate RIGHT",        head_rotate(True),    "dome turns the other way"),
    "13": ("Center head",              center_head(),        "dome recenters (UNCONFIRMED)"),
    "14": ("Drive motor0 FWD (low)",   drive(0, False),      "MOVEMENT - floor space"),
    "15": ("Drive motor1 FWD (low)",   drive(1, False),      "MOVEMENT - floor space"),
    "16": ("Drive motor0 REV (low)",   drive(0, True),       "MOVEMENT reverse - UNCONFIRMED dir byte 8"),
    "17": ("Drive motor1 REV (low)",   drive(1, True),       "MOVEMENT reverse - UNCONFIRMED dir byte 8"),
    "18": ("Stop motor 0",             stop_motor(0),        "motor 0 stops"),
    "19": ("Stop motor 1",             stop_motor(1),        "motor 1 stops"),
}

# ---------------------------------------------------------------------------

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


async def do_init(client):
    print("[init] sending confirmed handshake (droid should beep)...")
    for _ in range(3):
        for pkt in INIT_SEQUENCE:
            await client.write_gatt_char(WRITE_UUID, bytes.fromhex(pkt), response=True)
            await asyncio.sleep(0.1)
    await asyncio.sleep(0.5)


async def catalog_loop(client):
    loop = asyncio.get_event_loop()
    while True:
        print("\n" + "-" * 52 + "\n  KNOWN COMMAND CATALOG")
        for k in sorted(CATALOG, key=lambda x: int(x)):
            print(f"  {k:>2}. {CATALOG[k][0]}")
        print("   x. STOP motors    q. quit")
        choice = (await loop.run_in_executor(None, input, "select > ")).strip().lower()
        if choice == "q":
            await send(client, stop_motor(0)); await send(client, stop_motor(1))
            break
        if choice == "x":
            await send(client, stop_motor(0)); await send(client, stop_motor(1))
            print("  stopped."); continue
        if choice not in CATALOG:
            print("  ?"); continue
        label, packet, watch = CATALOG[choice]
        ack = await send(client, packet)
        hx = packet.hex(" ").upper()
        print(f"  [{label}] sent {hx} ({ack:.0f} ms)\n  watch: {watch}")
        # auto-stop any drive so nothing runs away
        if "Drive" in label:
            await asyncio.sleep(0.7)
            await send(client, stop_motor(0)); await send(client, stop_motor(1))
        reacted = (await loop.run_in_executor(None, input, "  did it react? (y/n/skip) ")).strip().lower()
        log_event(SCRIPT_NAME, label, hx, ack, reacted, notes=watch)
        print("  -> logged")


async def sweep_audio(client, lo, hi, auto, delay):
    """Walk the audio-controller command-id byte to find undocumented functions."""
    loop = asyncio.get_event_loop()
    known = {14: "SetVolume", 24: "PlaySound", 31: "SelectBank",
             69: "FlashLED", 72: "LedOn", 73: "LedOff", 74: "LedsDisable", 75: "LedsEnable"}
    await send(client, head_led(True))   # start from a known state (light on)
    print(f"[sweep-audio] ids {lo}..{hi}  ({'AUTO' if auto else 'interactive'}) -- audio controller only")
    for cid in range(lo, hi + 1):
        pkt = audio(cid, "01")
        ack = await send(client, pkt)
        hx = pkt.hex(" ").upper()
        tag = known.get(cid, "?")
        action = f"Audio id {cid} (0x{cid:02X})"
        print(f"  id {cid:>3} 0x{cid:02X} [{tag}]: {hx} ({ack:.0f} ms)")
        if auto:
            log_event(SCRIPT_NAME, action, hx, ack, "?", f"audio_id={cid} known={tag} auto")
            await asyncio.sleep(delay)
        else:
            reacted = (await loop.run_in_executor(None, input, "   reacted? (y/n label/Enter=next q=quit) ")).strip()
            if reacted.lower() == "q":
                break
            r = "y" if reacted and reacted.lower() != "n" else ("n" if reacted.lower() == "n" else "")
            note = f"audio_id={cid} known={tag}" + (f" label={reacted}" if r == "y" and reacted.lower() != "y" else "")
            log_event(SCRIPT_NAME, action, hx, ack, r, note)
        await send(client, head_led(True))   # re-assert known state between ids
    print("[sweep-audio] done. Any 'y' rows in droid_activity_log.csv are candidate new commands.")


async def probe_status(client, seconds):
    """BATTERY/telemetry hunt: subscribe to notify, fire candidate queries, log anything back."""
    got = {"n": 0}
    def on_notify(_char, data: bytearray):
        got["n"] += 1
        hx = data.hex(" ").upper()
        print(f"  [NOTIFY] {hx}")
        log_event(SCRIPT_NAME, "Notify payload", hx, None, "y", f"len={len(data)} telemetry")
    try:
        await client.start_notify(NOTIFY_UUID, on_notify)
        print("[probe] subscribed to notify characteristic.")
    except Exception as e:
        print(f"[probe] could NOT subscribe to notify ({e}). Battery telemetry not available this way.")
        return
    # candidate query commands: audio ids that might return status, plus raw prefixes seen in sources.
    candidates = [audio(c, "00") for c in (0, 1, 2, 3, 16, 32, 33, 48)]
    candidates += [build_command(1, "00"), build_command(3, "00"), bytes.fromhex("2210"), bytes.fromhex("2001")]
    print(f"[probe] firing {len(candidates)} candidate query commands, listening {seconds}s for any reply...")
    for pkt in candidates:
        try:
            await send(client, pkt)
        except Exception:
            pass
        await asyncio.sleep(0.4)
    await asyncio.sleep(seconds)
    try:
        await client.stop_notify(NOTIFY_UUID)
    except Exception:
        pass
    if got["n"]:
        print(f"[probe] RESULT: {got['n']} notification(s) received -- decode them (see logged rows).")
        print("        If any correlates with charge state, THAT's your battery source for the dashboard.")
    else:
        print("[probe] RESULT: no telemetry at all. Consistent with prior runs -- the droid appears")
        print("        write-only over BLE. Battery level is very likely NOT exposed; the dashboard")
        print("        should show connection/uptime/latency instead of a battery figure.")


async def run(args):
    dev = await find_device(args.address)
    print(f"[found] {dev.name} ({dev.address})")
    async with BleakClient(dev) as client:
        print(f"[conn] connected={client.is_connected}")
        await do_init(client)
        if args.sweep_audio:
            lo, hi = (int(x) for x in args.sweep_audio.split("-", 1))
            await sweep_audio(client, lo, hi, args.auto, args.delay)
        elif args.probe:
            await probe_status(client, args.listen)
        else:
            await catalog_loop(client)


def main():
    ap = argparse.ArgumentParser(description="Enumerate/discover BB-8 commands + probe for telemetry.")
    ap.add_argument("--address", default="DA:A2:05:2C:0B:26")
    ap.add_argument("--sweep-audio", metavar="LO-HI", help="sweep audio-controller command ids, e.g. 1-90")
    ap.add_argument("--probe", action="store_true", help="hunt for notify telemetry / battery")
    ap.add_argument("--auto", action="store_true", help="sweep without prompts")
    ap.add_argument("--delay", type=float, default=0.8, help="seconds between commands in --auto sweep")
    ap.add_argument("--listen", type=float, default=6.0, help="seconds to listen for notifications in --probe")
    args = ap.parse_args()
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\n[abort] interrupted.")


if __name__ == "__main__":
    main()
