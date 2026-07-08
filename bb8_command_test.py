#!/usr/bin/env python3
"""
bb8_command_test.py  --  Phase 0 on-unit command confirmation for Project "6th Sense".

WHAT THIS IS:
    An interactive tester. It connects to the droid, runs the confirmed init handshake,
    then lets you fire each DECODED command (LED, head rotation, drive, volume, sound)
    one at a time so you can watch the droid physically react and confirm the bytes.

THE POINT (why this isn't 50 hardcoded byte-strings):
    Every command is generated from ONE framing rule (build_droid_command), the same rule
    we decoded from pyDroidDepot and verified reproduces our confirmed sound/init bytes.
    Understand the rule once -> generate the whole command set. That's the whole game.

Requires: pip install bleak
Run:      python bb8_command_test.py --address DA:A2:05:2C:0B:26
"""

import argparse
import asyncio
import os
import threading
import time
from bleak import BleakClient, BleakScanner
from droid_log import log_event   # shared CSV logger

SCRIPT_NAME = "bb8_command_test"

def latency_beep():
    """Short audible marker at send-time. In a slow-mo video with sound, the beep
    is your t=0; the first frame the droid moves is t=1. Non-blocking (own thread)."""
    def _beep():
        try:
            import winsound          # Windows
            winsound.Beep(2500, 90)
        except Exception:
            print("\a", end="", flush=True)   # fallback: terminal bell
    threading.Thread(target=_beep, daemon=True).start()

WRITE_UUID  = "09b600b1-3e42-41fc-b474-e9c0c8f0c801"
NOTIFY_UUID = "09b600b0-3e42-41fc-b474-e9c0c8f0c801"
NAME_PREFIX = "DROID"

# ---------------------------------------------------------------------------
# THE FRAMING RULE  (decoded from thetestgame/pyDroidDepot, verified 2026-07-07)
# ---------------------------------------------------------------------------

def int_to_hex(n: int) -> str:
    """Decimal -> even-length hex string. 50 -> '32', 14 -> '0e'."""
    h = hex(n)[2:]
    return ("0" + h) if len(h) % 2 else h

def build_command(command_id: int, data: str = "") -> bytes:
    """The one rule that frames every droid command.
        byte1 = (data_len + 3) | 0x20
        byte2 = 0x42 if command_id == 15 else 0x00
        byte3 = command_id
        byte4 = data_len + 0x40
    """
    dl = len(data) // 2
    b1 = (dl + 3) | 0x20
    b2 = 0x42 if command_id == 15 else 0x00
    return bytes([b1, b2, command_id, dl + 0x40]) + bytes.fromhex(data)

def multi(sub_id: int, data: str = "") -> bytes:
    """Multipurpose (id 15) wrapper: '44' + 2-decimal-digit sub-id + data."""
    return build_command(15, "44" + "{:02d}".format(sub_id) + data)

def audio(audio_cmd: int, data: str = "00") -> bytes:
    """Audio-controller command (multipurpose sub-id 0). Sound + head LEDs live here."""
    return multi(0, int_to_hex(audio_cmd) + data)

# ---------------------------------------------------------------------------
# THE COMMAND SET  (all generated from the rule above -- nothing hardcoded)
# ---------------------------------------------------------------------------

# Confirmed init handshake (proven on our unit: droid beeps).
INIT_SEQUENCE = ["222001", "27420f4444001f00", "27420f4444001802"]
BB_HEAD_LED = 1  # BBUnitHeadLed identifier

def head_led(on: bool) -> bytes:
    # SetLedOn=72(0x48), SetLedOff=73(0x49)
    return audio(72 if on else 73, int_to_hex(BB_HEAD_LED))

def head_led_flash() -> bytes:
    return audio(69, int_to_hex(BB_HEAD_LED))          # FlashHeadLeds=69

def play_sound(track: int = 0) -> bytes:
    return audio(24, int_to_hex(track))                # PlayAudioFromSelectedGroup=24

def set_volume(level: int = 50) -> bytes:
    return audio(14, int_to_hex(level))                # SetVolume=14  (you derived this one!)

def head_rotate(back: bool = False, speed: int = 120, ramp: int = 300) -> bytes:
    dir_hex = "ff" if back else "00"
    return multi(4, dir_hex + int_to_hex(speed) + int_to_hex(ramp) + "0000")  # RotateBUnitHead=4

def drive(motor: int = 0, back: bool = False, speed: int = 80, ramp: int = 300) -> bytes:
    direction = 8 if back else 0
    delay = "0000"
    motor_select = "%s%d" % (direction, motor)         # SetMotorSpeed=5
    return build_command(5, motor_select + int_to_hex(speed) + int_to_hex(ramp) + delay)

def stop_motor(motor: int) -> bytes:
    return build_command(5, "0%d" % motor + int_to_hex(0) + int_to_hex(300) + "0000")

# Menu: label -> (builder, "what to watch for")
MENU = {
    "1": ("Head LED ON",        head_led(True),   "head light should turn on"),
    "2": ("Head LED OFF",       head_led(False),  "head light should turn off"),
    "3": ("Head LED flash",     head_led_flash(), "head light should flash"),
    "4": ("Play sound",         play_sound(0),    "audible beep (LOUD - mind sleepers)"),
    "5": ("Set volume ~50",     set_volume(50),   "no visible effect; sets level for next sound"),
    "6": ("Head rotate LEFT",   head_rotate(False), "head/dome should turn one way"),
    "7": ("Head rotate RIGHT",  head_rotate(True),  "head/dome should turn the other way"),
    "8": ("Drive fwd (low)",    drive(0, False),  "MOVEMENT - give it floor space"),
    "9": ("Stop drive motor 0", stop_motor(0),    "movement should stop"),
}

# ---------------------------------------------------------------------------

async def find_device(address):
    # Try the exact address first (fast path).
    if address:
        print(f"[scan] looking for {address} (20s)... power the droid on NOW.")
        dev = await BleakScanner.find_device_by_address(address, timeout=20.0)
        if dev:
            return dev
        print("[scan] exact address not seen; falling back to a name scan for any DROID...")

    # Fallback: any device advertising as DROID.
    dev = await BleakScanner.find_device_by_filter(
        lambda d, ad: (d.name or "").upper().startswith(NAME_PREFIX), timeout=20.0)
    if dev:
        return dev

    raise RuntimeError(
        "No droid found. Checklist: (1) remote fully OFF, (2) Droid Depot app force-closed, "
        "(3) power the droid OFF then ON and run this within ~5 seconds, (4) keep it within a few feet.")

async def send(client, label, packet, watch):
    t0 = time.perf_counter()
    await client.write_gatt_char(WRITE_UUID, packet, response=True)
    ack = (time.perf_counter() - t0) * 1000
    hx = packet.hex(" ").upper()
    print(f"  sent {hx}  ({ack:.1f} ms ACK)")
    print(f"  watch for: {watch}")
    return ack

async def run(address):
    dev = await find_device(address)
    print(f"[found] {dev.name} ({dev.address})")
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

        loop = asyncio.get_event_loop()
        while True:
            print("\n" + "-" * 48)
            for k, (label, _, _) in MENU.items():
                print(f"  {k}. {label}")
            print("  0. Drive fwd + LATENCY beep (film in slow-mo: beep=t0, first motion=t1)")
            print("  d. Drive STRAIGHT (both motors) + auto-stop")
            print("  q. quit (stops motors first)")
            choice = (await loop.run_in_executor(None, input, "select > ")).strip().lower()
            if choice == "0":
                print("[LATENCY DRIVE] Point your phone (slow-mo, sound ON) at the droid.")
                await loop.run_in_executor(None, input, "  press Enter when you're filming... ")
                pkt = drive(0, False, speed=90)
                latency_beep()                       # audible t=0 marker
                ack = await send(client, "Drive latency", pkt, "watch beep -> first motion")
                await send(client, "Drive latency (motor1)", drive(1, False, speed=90), "")  # both motors = straight
                await asyncio.sleep(0.7)
                await send(client, "stop", stop_motor(0), "stopping")
                await send(client, "stop", stop_motor(1), "stopping")
                moved = (await loop.run_in_executor(None, input, "  did it move? (y/n) ")).strip().lower()
                ms = (await loop.run_in_executor(None, input, "  beep->motion from video (ms, or blank) ")).strip()
                log_event(SCRIPT_NAME, "Drive latency (video)", pkt.hex(" ").upper(), ack,
                          moved, notes=f"press->move ~{ms}ms (slow-mo); both motors" if ms else "both motors; measure video")
                print("  -> logged")
                continue
            if choice == "d":
                print("[DRIVE STRAIGHT] both motors together - give it floor room")
                ack = await send(client, "Drive straight", drive(0, False, 90), "should roll ~straight")
                await send(client, "Drive straight (motor1)", drive(1, False, 90), "")
                await asyncio.sleep(0.8)
                await send(client, "stop", stop_motor(0), "stop")
                await send(client, "stop", stop_motor(1), "stop")
                moved = (await loop.run_in_executor(None, input, "  did it roll straighter? (y/n) ")).strip().lower()
                log_event(SCRIPT_NAME, "Drive straight (both motors)", drive(0, False, 90).hex(" ").upper(),
                          ack, moved, notes="motors 0+1 same direction")
                print("  -> logged")
                continue
            if choice == "q":
                ack0 = await send(client, "stop", stop_motor(0), "stop")
                ack1 = await send(client, "stop", stop_motor(1), "stop")
                log_event(SCRIPT_NAME, "Stop motors (quit)", stop_motor(0).hex(' ').upper(), ack0, notes="session end")
                break
            if choice in MENU:
                label, packet, watch = MENU[choice]
                print(f"[{label}]")
                ack = await send(client, label, packet, watch)
                # log whether it worked so you can fill Confirmed Findings
                reacted = (await loop.run_in_executor(None, input, "  did it react? (y/n/skip) ")).strip().lower()
                path = log_event(SCRIPT_NAME, label, packet.hex(' ').upper(), ack, reacted, notes=watch)
                print(f"  -> saved to {os.path.basename(path)}: {label} = {reacted}")
            else:
                print("  ?")

def main():
    ap = argparse.ArgumentParser(description="Phase 0 on-unit command tester.")
    ap.add_argument("--address", default="DA:A2:05:2C:0B:26")
    args = ap.parse_args()
    asyncio.run(run(args.address))

if __name__ == "__main__":
    main()
