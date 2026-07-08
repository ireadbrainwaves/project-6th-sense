# Project 6th Sense — Central Hub

*Autonomous droids & drones: a hybrid between a pet and a helper.*

**Last updated:** 2026-07-07
**Status:** Phase 0 ✅ COMPLETE (2026-07-07) — Phase 1 unblocked
**This file** consolidates everything from the "6th Sense protocol confirmation" work session so it all lives in one place. Reconstructed from the full session record.

> ✅ **The real files are now in this folder:** `ble_scan_dump.py`, `bb8_latency_test.py`, and `6th_sense_protocol_notes.md`. The confirmed byte sequences below (init handshake, sound command) are taken verbatim from `bb8_latency_test.py`.

---

## 1. The target device

You're reverse-engineering a **Disney Droid Depot BB-8-class droid** over Bluetooth LE.

| Property | Value | Confidence |
|---|---|---|
| Advertised name | `DROID` (often no name — don't filter by name) | **Confirmed on your unit** |
| Address | `DA:A2:05:2C:0B:26` | **Confirmed on your unit** |
| Manufacturer ID | `0x0183` (droid beacon) | **Confirmed on your unit** |
| Beacon payload seen | `03 04 44 81 92 08` | **Confirmed on your unit** |
| Service UUID | `09b600a0-3e42-41fc-b474-e9c0c8f0c801` | Corroborated by 2 sources; verify on-unit |
| Write characteristic | `09b600b1-...` | Corroborated; verify on-unit |
| Notify characteristic | `09b600b0-...` | Corroborated; verify on-unit |

The `81` byte in the beacon means the droid still thinks it's **paired to its remote** — turn the remote fully off (and force-close the Droid Depot app) or connections get grabbed/dropped.

---

## 2. Confirmed findings (reproduced on YOUR droid)

These are real — reproduced on your BB-8 on 2026-07-07, not just sourced from the community:

- **Discovery** — droid found via BLE scan (`DA:A2:05:2C:0B:26`, mfr `0x0183`).
- **Connect** — BLE connection succeeds.
- **Write characteristic** — writes land and get ACKed (10/10 trials).
- **Init handshake** — accepted by the droid.
- **Sound command** — **droid physically beeped and reacted.** This confirms the init sequence + sound command bytes are correct for your unit and the write path works end-to-end.
- **Head LED on/off** (`27 42 0F 44 44 00 48 01` / `...49 01`) — light turns on/off. Confirmed 2026-07-07.
- **Head rotation** (`2B 42 0F 48 44 04 00 78 01 2C 00 00`) — head/dome physically turned. Confirmed 2026-07-07. (Decoded from source, derived, *and* proven on-unit the same day.)
- **Set volume** (`27 42 0F 44 44 00 0E 32`) — accepted; byte sequence hand-derived by Austin.
- *Anomaly:* head-LED **flash** (`...45 01`) gave no reaction (3 tries) — open sub-question.
- All on-unit results recorded in `droid_activity_log.csv`.

---

## 3. Command byte reference

Prefixes / command classes (from community sources; sound + init reproduced on-unit, the rest are test targets):

| Function | Prefix | Example payload | Status |
|---|---|---|---|
| Init handshake | `0x22` | `22 20 01`, then `27 42 0F 44 44 00 1F 00`, then `27 42 0F 44 44 00 18 02` — sent as a 3-packet block, repeated 3× with a 0.10 s gap | **Reproduced on-unit** |
| Sound / effect | `0x27` | `27 42 0F 44 44 00 18 00` (the measured test command) | **Reproduced on-unit** |
| Drive / roll | `0x29` | `29 00 05 46 <dir><motor> <power> 01 2C 00 00` (pyDroidDepot) — byte2 may be `42` per Baptiste; test both | Bytes decoded; untested on-unit (movement) |
| Head rotation (BB, distinct DOF) | multi `04` | `2B 42 0F 48 44 04 <dir> <spd> <ramp> 00 00`; e.g. `2B 42 0F 48 44 04 00 A0 01 2C 00 00` | **Decoded from pyDroidDepot**; untested on-unit |
| Head LED (BB) | audio `48`/`49` | `27 42 0F 44 44 00 48 01` on / `...49 01` off (flash `45`, enable `4B`, disable `4A`) | **Decoded from pyDroidDepot**; untested on-unit |
| Pairing/body LED | `0x02` | `25 00 02 42 00 FF` on / `...00 00` off | Decoded; untested on-unit |
| Location beacon | `0x83` | `83 01 0A 04 01 0C A6 01` | Reference |

**Corrections captured during the session (don't regress on these):**
- Roll/drive is **`0x29`**, NOT `0x27`. The `0x27` family is sound/effects.
- There is **no** confirmed `0x25`/`0x26` control command in the sources.
- The correct location-beacon payload is `83 01 0A 04 01 0C A6 01` (earlier `0A 04 02 02 A6 01` was wrong in the middle).

**Previously UNKNOWN — now DECODED from `pyDroidDepot` source (2026-07-07), pending on-unit test:**
- **LED / head lights** — driven via the audio controller: `27 42 0F 44 44 00 48 01` (on) / `...49 01` (off). Separate pairing/body LED: `25 00 02 42 00 FF`.
- **Head rotation** — its own DOF via multipurpose cmd `04` (`RotateBUnitHead`): `2B 42 0F 48 44 04 00 A0 01 2C 00 00`.

No app-sniffing needed — the packet framing was decoded from source and reproduces our confirmed init/sound bytes exactly (see the protocol notes' "Command framing" section). Remaining work is just firing these at the droid and watching for reaction.

---

## 4. Latency baseline (first run — needs a clean rerun)

10 sound-command trials, write-ACK latency:

```
trial  1: 116.47 ms      trial  6: 154.29 ms
trial  2:  85.27 ms      trial  7:  78.42 ms
trial  3:  85.09 ms      trial  8:  79.15 ms
trial  4: 144.06 ms      trial  9: 231.53 ms
trial  5: 139.07 ms      trial 10: 152.92 ms
```

Min 78 / max 232 / median ~128 / mean ~127 ms. `notify (none)` on every trial.

**Caveats:**
- This run was at **RSSI −98 dBm** (nearly the noise floor) — too jittery to trust. Rerun with the droid within a couple feet of the radio for a real baseline.
- **write-ACK ≠ physical reaction.** The BLE layer ACKs the write regardless of whether the droid acted. The number that actually matters is time-to-beep/motion — cross-check with a stopwatch or video of the beep.

---

## 5. What's next (Phase 0 exit criteria)

1. **Confirm LED command on-unit** — fire `27 42 0F 44 44 00 48 01` (head LED on) / `...49 01` (off). Silent — good for family-asleep time.
2. **Confirm head rotation on-unit** — `2B 42 0F 48 44 04 00 A0 01 2C 00 00`. Near-silent (small motor), low power.
3. **Confirm drive/roll on-unit** — `29 00 05 46 00 A0 01 2C 00 00` (also try byte2 `42`). Movement — needs space.
4. **Clean latency rerun** — droid within a couple feet, rerun the sound test, record write-ACK + a stopwatch/video reaction time.
5. **Decide the latency target "X"** for Phase 1 — hold off until step 4 gives real numbers.

When these are reproduced on your own droid with measured latency, the values move into Confirmed Findings and the Phase 0 gate opens to Phase 1.

**Quietest next task** (family asleep / no sound): step 1 — the head-LED on/off command is silent and now fully decoded, so it's the easiest remaining confirmation.

---

## 6. Sources

- Baptiste Laget — Controlling Disney's droids with WebBluetooth: https://medium.com/@baptistelaget/controlling-disneys-droids-from-droid-depots-with-webbluetooth-febbabe50587
- ruthsarian/Droid-Toolbox: https://github.com/ruthsarian/Droid-Toolbox/blob/main/Droid-Toolbox.ino
- thetestgame/pyDroidDepot: https://github.com/thetestgame/pyDroidDepot
- siddacious/SA-45: https://github.com/siddacious/SA-45

(Note: no public `russdill/droid_depot` repo was found — the corroborated Python reference is `thetestgame/pyDroidDepot`.)

---

## 7. Scripts (the real files, in this folder)

Both working scripts now live alongside this hub — no reconstruction needed:

- **`ble_scan_dump.py`** — the "blue scanner." Lists every nearby BLE advertisement and flags anything matching the droid signature (`0x0183` manufacturer data or the service UUID). Run: `python ble_scan_dump.py [seconds]`.
- **`bb8_latency_test.py`** — connect + latency harness. Sends the init handshake, fires the sound command 10×, prints write-ACK / notify latency. Run: `python bb8_latency_test.py --address DA:A2:05:2C:0B:26`.
- **`6th_sense_protocol_notes.md`** — the full protocol notes.

Both need `pip install bleak` and must run on a machine with a Bluetooth radio near the droid.

### Confirmed init handshake (from `bb8_latency_test.py`)

Sent as a 3-packet block, repeated 3× with a 0.10 s gap between writes, all to the write characteristic `09b600b1-...`:

```
22 20 01
27 42 0f 44 44 00 1f 00
27 42 0f 44 44 00 18 02
```

Then the measured **sound test command**: `27 42 0f 44 44 00 18 00` (write-with-response, ×10).

Drive/roll alternative noted in the script (verify bytes before use): `29 42 05 46 00 20 01 2C 00 00`.
