#!/usr/bin/env python3
"""
ble_scan_dump.py  --  Phase 0 diagnostic. List EVERY nearby BLE advertisement.

Use this when the droid doesn't show up as "DROID". It doesn't filter by name --
it dumps name, address, RSSI, advertised service UUIDs, and manufacturer data for
everything in range, and flags anything that matches the droid's known signature
(service 09b600a0... or manufacturer id 0x0183). That lets you find the droid even
if it advertises with no name.

Requires: Python 3.9+, bleak  ->  pip install bleak
Run:      python ble_scan_dump.py            (10 s scan)
          python ble_scan_dump.py 20         (custom seconds)
"""

import asyncio
import sys

from bleak import BleakScanner

DROID_SERVICE = "09b600a0-3e42-41fc-b474-e9c0c8f0c801"
DROID_MFR_ID = 0x0183  # manufacturer id used in droid/location beacons


async def main(seconds: float):
    print(f"[scan] listening for {seconds:.0f} s ... power the droid on NOW "
          f"(remote OFF, app closed).\n")
    # return_adv=True gives us (device, advertisement_data) per hit.
    found = await BleakScanner.discover(timeout=seconds, return_adv=True)

    if not found:
        print("No BLE advertisements seen at all. That usually means Bluetooth is off, "
              "the OS blocked scan permission, or nothing is advertising nearby.")
        return

    rows = []
    for addr, (dev, adv) in found.items():
        name = adv.local_name or dev.name or "(no name)"
        rssi = adv.rssi
        svcs = [s.lower() for s in (adv.service_uuids or [])]
        mfr = adv.manufacturer_data or {}

        is_droid = DROID_SERVICE in svcs or DROID_MFR_ID in mfr
        rows.append((rssi, name, addr, svcs, mfr, is_droid))

    # Strongest signal first.
    rows.sort(key=lambda r: r[0], reverse=True)

    print(f"{'RSSI':>5}  {'NAME':<22} {'ADDRESS':<18} MATCH")
    print("-" * 70)
    for rssi, name, addr, svcs, mfr, is_droid in rows:
        flag = "  <-- DROID SIGNATURE" if is_droid else ""
        print(f"{rssi:>5}  {name[:22]:<22} {addr:<18}{flag}")
        if svcs:
            print(f"        services: {', '.join(svcs)}")
        if mfr:
            for cid, data in mfr.items():
                tag = "  (0x0183 droid!)" if cid == DROID_MFR_ID else ""
                print(f"        mfr 0x{cid:04x}: {data.hex()}{tag}")

    hits = [r for r in rows if r[5]]
    print("\n" + "=" * 70)
    if hits:
        print(f"Found {len(hits)} device(s) matching the droid signature:")
        for _, name, addr, *_ in hits:
            print(f"  {name}  {addr}")
        print("Use that ADDRESS with:  python bb8_latency_test.py --address <ADDRESS>")
    else:
        print("No device matched the droid signature (service 09b600a0 / mfr 0x0183).")
        print("If the droid is definitely on: it may already be connected to the remote/app,")
        print("or it dropped out of its advertising window. Power-cycle it and re-run.")


if __name__ == "__main__":
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
    asyncio.run(main(secs))
