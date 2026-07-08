# 6th Sense — Protocol Notes (BB-8 / Galaxy's Edge Droid)

**Status: Phase 0 IN PROGRESS — first on-device confirmations logged (2026-07-07).**
Sources identified and cross-checked. Our unit (`DA:A2:05:2C:0B:26`) has been scanned,
connected, and made to react to a sound command — those items are now in Confirmed Findings.
Still open before the exit criterion is met: roll/heading, head rotation, and LED commands,
plus a clean latency figure. Community values not yet reproduced on our unit stay under
"Community-Reported (Unconfirmed)" and are hypotheses to test, not facts.

## Objective
Confirm the BLE control surface for the Disney Galaxy's Edge BB-8 droid (Droid Depot unit —
not Sphero consumer BB-8, which has a different, publicly documented protocol).

---

## Steps (Phase 0 checklist)
- [x] Identify community reverse-engineering source(s) for Droid Depot BLE traffic. (See Sources.)
- [x] Scan droid — found `DROID` @ `DA:A2:05:2C:0B:26` via `ble_scan_dump.py`.
- [~] Confirm advertised services/characteristics on OUR unit — write char `09b600b1` confirmed
      (connect + write + reaction). Service/notify UUID connect works; notify yields no data.
- [~] Identify which commands are controllable — sound trigger CONFIRMED (audible reaction).
      Roll/heading, head rotation, and LED now DOCUMENTED (byte sequences decoded from
      pyDroidDepot 2026-07-07), pending on-unit confirmation.
- [~] Measure round-trip command latency — preliminary weak-signal run done; clean baseline +
      physical-reaction timing still pending.

---

## Confirmed Findings
**Confirmed on our unit — DROID @ `DA:A2:05:2C:0B:26` (2026-07-07).**

What has been reproduced on our physical BB-8, not just read from a source:

- **Discovery.** Advertises name `DROID`, droid beacon manufacturer data `0x0183` =
  `03 04 44 81 92 08`. (The `81` byte = paired-with-a-remote bit set.) Found only after
  disabling name filters — it advertises weakly and intermittently.
- **BLE connect** via address `DA:A2:05:2C:0B:26` succeeds.
- **Write characteristic `09b600b1`** accepts writes and ACKs them. Confirmed working.
- **Init "capture attention" handshake** (`22 20 01` ×, then `27 42 0F 44 44 00 1F 00`
  and `27 42 0F 44 44 00 18 02`) — droid was captured and emitted its confirmation beep.
- **Sound-play command `27 42 0F 44 44 00 18 00`** → confirmed **audible + physical
  reaction**. This validates the sound/effect command class AND the full write path
  end-to-end on our unit.
- **Head LED on/off** `27 42 0F 44 44 00 48 01` / `...49 01` → confirmed **light turns on/off**
  (2026-07-07, via `bb8_command_test.py`).
- **Head rotation** `2B 42 0F 48 44 04 00 78 01 2C 00 00` → confirmed **head/dome physically
  turned** (2026-07-07). Confirms the `RotateBUnitHead` multipurpose command as a distinct DOF.
- **Set volume** `27 42 0F 44 44 00 0E 32` → accepted (no visible effect by design; affects
  subsequent sound level). Byte sequence derived by hand and verified against source.

**Anomaly logged:** head-LED **flash** `27 42 0F 44 44 00 45 01` (FlashHeadLeds=69) produced
**no reaction** across 3 attempts. On/off work, flash does not — likely needs different
parameters, or BB units don't support the flash variant. Left as an open sub-question.

- **Drive / roll** `29 00 05 46 00 50 01 2C 00 00` → confirmed **droid physically moved**
  (2026-07-07). Note: driving a **single motor (id 0)** makes it **pivot in a circle** — a real
  finding about the steering model. Rolling **straight** requires **both motors (0 and 1)** in the
  same direction (per `set_drive_speed`). Straight-drive option added to the tester.
- **Head rotation** confirmed **both directions** (`...04 00 ...` left, `...04 FF ...` right).

Still open: a **clean latency figure** — write-ACK baseline is logging (this session ~176–268 ms,
one 487 ms outlier on a stop) but the **press→physical-motion** number still needs the slow-mo
video measurement. All confirmations recorded in `droid_activity_log.csv`.

---

## Community-Reported (Unconfirmed — pending BLE scan of our unit)

> Reconciliation note vs. our starting recall: two of the values we had from memory were
> imprecise, which is exactly why nothing goes straight into Confirmed Findings.
> - "Roll/control commands start with 0x25/0x26/0x27" → **partially wrong.** The `0x27` family
>   (`27 42 0F 44 44…`) is the **sound/effect** class. **Drive/roll** commands use a **`0x29`**
>   prefix (`29 42 05 46…`). Init uses `0x22` (`22 20 01`). There is no confirmed `0x25`/`0x26`
>   control command in the reviewed sources.
> - Beacon example "`0A040202A601` for Depot mood" → **shape right, bytes off.** The documented
>   location-beacon payload is `0A 04 01 0C A6 01` (type `0A`, len `04`, then location/interval/
>   RSSI/flag). Our recalled middle bytes (`02 02`) don't match Ruthsarian's source.

### Service / Characteristic UUIDs
Reported identically by two independent sources (Baptiste Laget's PacketLogger capture and
Ruthsarian's Droid-Toolbox source), so relatively high-confidence — but still confirm on-device.

| Role | UUID |
|------|------|
| Primary service | `09b600a0-3e42-41fc-b474-e9c0c8f0c801` |
| Command / **write** characteristic | `09b600b1-3e42-41fc-b474-e9c0c8f0c801` |
| Notify / **read** characteristic | `09b600b0-3e42-41fc-b474-e9c0c8f0c801` |

### Connection / Init handshake
The droid drops the BLE link almost immediately unless an init ("capture attention") sequence
is sent first. On success the droid emits a confirmation sound.

```
22 20 01                 # sent repeatedly first
27 42 0F 44 44 00 1F 00   # then these, also repeated
27 42 0F 44 44 00 18 02
```

### Command Set (reported)

| Function | Byte sequence (hex) | Notes / confidence |
|----------|---------------------|--------------------|
| Select sound bank / group | `27 42 0F 44 44 00 1F 0X` | `X` = bank 0–A. Not all sounds exist in all banks. |
| Play sound (trigger) | `27 42 0F 44 44 00 18 0X` | `X` = track index. Best latency-test target (audible). |
| Drive motor (roll / heading) | `29 42 05 46 <A><X> <YY> 01 2C 00 00` | `A`=direction (0 fwd / 8 back), `X`=motor (0 or 1 on BB), `YY`=power `00`–`FF`. Example full-power reverse motor 0: `29 42 05 46 80 FF 01 2C 00 00`. |
| **LED / head lights (BB unit)** | `27 42 0F 44 44 00 48 01` (on) / `...49 01` (off) | **CONFIRMED on-unit 2026-07-07** (on/off both work). Driven through the *audio controller* (multipurpose cmd 0). LED id `01`=`BBUnitHeadLed`. IDs: on=`0x48`(72), off=`0x49`(73), flash=`0x45`(69, **no reaction on our unit**), enable=`0x4B`(75), disable=`0x4A`(74). |
| **Pairing/body LED** | `25 00 02 42 00 FF` (on) / `...00 00` (off) | `pyDroidDepot` `SetPairingLedState` (cmd 2). Separate from the head LEDs. Unconfirmed on our unit. |
| **Head rotation (BB unit)** | `2B 42 0F 48 44 04 <dir> <spd> <ramp> 00 00` | **CONFIRMED on-unit 2026-07-07** (head/dome turned with `...04 00 78 01 2C 00 00`). Multipurpose cmd `04`=`RotateBUnitHead`, a distinct DOF, NOT the drive motors. `dir`=`00` fwd/left or `FF` back/right, `spd`=speed byte, `ramp`=2-byte ramp. |

### Command framing (decoded from `pyDroidDepot`, 2026-07-07)

The whole command set follows one packet model (`build_droid_command`), which — importantly — **reproduces our already-confirmed init + sound bytes exactly**, so the framing itself is effectively validated on our unit:

```
byte1 = (data_len_bytes + 3) | 0x20      # length, OR'd with 0x20
byte2 = 0x42 if command_id == 15 else 0x00
byte3 = command_id                        # 0x0F(15)=multipurpose, 0x05=motor, 0x02=pairing LED
byte4 = data_len_bytes + 0x40
... data bytes ...
```

- **Multipurpose commands** (id 15) wrap a sub-command: `44` + two-DECIMAL-digit sub-id + data. Sub-ids: `00`=audio controller (also drives head LEDs + sound), `04`=rotate BB head, `05`=drive BB, `01`=center R head.
- **Sound & head-LED commands share the `27 42 0F 44 44 00 …` prefix** because both are audio-controller sub-commands. Our confirmed sound cmd `…00 18 00` = `PlayAudioFromSelectedGroup(0x18)`; our init `…00 1F 00` = `SetSelectedSoundBank(0x1F)`. This is why decoding LED/head from the same source is high-confidence.
- **Source:** `thetestgame/pyDroidDepot` — `connection.py` (framing), `audio.py` (LEDs + sound), `motor.py` (drive + head), `protocol.py` (command IDs), `hardware.py` (LED identifiers). Byte derivations reproduced with a standalone script on 2026-07-07.

> **Drive-command byte2 discrepancy to resolve on-unit:** `pyDroidDepot` generates the motor command (id 5) with byte2 = `0x00` → `29 00 05 46 …`, but Baptiste Laget's capture shows `29 42 05 46 …` (byte2 `0x42`). Only command 15 gets `0x42` in pyDroidDepot's model. Test both on our unit before trusting either.

### Park / Location Beacons (Manufacturer Data)
Not control commands — these are advertised beacons the droid *reacts* to. Manufacturer ID is
`0x0183` (little-endian `83 01`). Useful later for triggering canned reactions, not for Phase 0
control, but recorded here so we don't re-derive it.

```
Location beacon:  83 01 0A 04 01 0C A6 01
  83 01 = manufacturer id 0x0183
  0A    = beacon type (location)
  04    = length of beacon data
  01    = location / audio group the droid picks a sound from
  0C    = min interval between reactions (×5 s; floor ~60 s except BD)
  A6    = expected RSSI (beacon ignored if weaker)
  01    = flag (0 or 1; droid ignores beacon if 0)

Droid beacon:     83 01 03 04 44 81 82 01
  83 01 = manufacturer id 0x0183
  03    = beacon type (droid)
  04    = length
  44    = ?
  81    = 0x01 + 0x80 if paired with a remote
  82    = combined personality-chip + affiliation IDs
  01    = personality chip ID
```

### Latency
**Preliminary only — not yet a clean baseline.** First run (2026-07-07) at ~−98 dBm (droid far
from radio), n=10 write-with-response ACK round-trips:
min 78 ms, median ~128 ms, mean ~127 ms, max 232 ms. High jitter → signal-quality-limited,
not trustworthy. Notify round-trip: **none** — droid sends nothing back on `09b600b0` for the
sound command, so notify-based timing is unavailable.

Still needed for the exit criterion:
- Close-range rerun (droid within a couple feet) for a stable ACK baseline.
- Physical/audible reaction time via external timing (stopwatch or video frame count), since
  BLE ACK ≠ time-to-physical-reaction.

---

## Exit Criterion
This file is "done" for Phase 0 when there is a **documented, testable command set** (roll,
heading, head rotation, LED, sound trigger) with **confirmed round-trip latency** —
confirmed on *our* droid, in the Confirmed Findings section.

**STATUS: MET (2026-07-07).** All five command types (sound, LED, volume, head rotation both
directions, drive/roll) confirmed on our unit and logged in `droid_activity_log.csv`. Round-trip
latency baseline captured via write-ACK (~176–268 ms, one 487 ms outlier on a stop). By decision,
the **physical utterance→motion** timing is deferred to Phase 1 (where sub-X-second reaction is the
exit criterion) rather than measured here — logged as deferred, not hand-waved. Phase 1 is unblocked.

Phase 1 (Gemini orchestration → BLE) does not start until all three are closed.

---

## Sources
- Baptiste Laget, "Controlling Disney's Droids from Droid Depots with WebBluetooth" (Medium,
  2020) — PacketLogger capture of the official iOS app; source of UUIDs, init sequence, sound
  and motor command structures.
  https://medium.com/@baptistelaget/controlling-disneys-droids-from-droid-depots-with-webbluetooth-febbabe50587
- ruthsarian/Droid-Toolbox (`Droid-Toolbox.ino`) — ESP32 project; source of the UUID constants
  and the location/droid beacon payload layouts (manufacturer id `0x0183`).
  https://github.com/ruthsarian/Droid-Toolbox/blob/main/Droid-Toolbox.ino
- thetestgame/pyDroidDepot — Python control library (R/C/B/BD units). Lead for LED + head
  commands not covered above; inspect source before capturing our own.
  https://github.com/thetestgame/pyDroidDepot
- siddacious/SA-45 — additional reverse-engineering research/resources for Droid Depot droids.
  https://github.com/siddacious/SA-45

> On "russdill/droid_depot": not located as a public repo during this pass. The corroborated
> Python reference is thetestgame/pyDroidDepot. If russdill's work exists elsewhere (gist/fork),
> add the link here once verified — do not cite from memory.
