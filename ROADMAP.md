# 6th Sense — Roadmap

Each phase is gated. **Do not spec or design a later phase's hardware/software until the current phase's exit criterion is met.** This file exists specifically to catch scope-creep against a written gate instead of momentum.

## Phase 0 — Protocol Confirmation
**Status:** ✅ COMPLETE — exit criterion met 2026-07-07 (see `6th_sense_protocol_notes.md`, `6TH_SENSE_HUB.md`, `droid_activity_log.csv`)

Confirm the Galaxy's Edge BB-8 BLE protocol. No purchased hardware required.

**Exit criterion:** documented, testable command set (roll, heading, head rotation, LED, sound trigger) with confirmed round-trip latency. — **Met:** all five command types confirmed on our unit; write-ACK round-trip latency measured and logged (~176–268 ms). Physical utterance→motion timing is intentionally deferred to Phase 1, where it is the exit criterion.

## Phase 1 — MVP Software Loop (phone-only)
**Status:** 🔨 IN PROGRESS — started 2026-07-07

Pixel 10 Fold runs orchestration directly: mic capture → Gemini → response → BLE command to BB-8. Desktop is dev host only.

**Decisions (2026-07-07):**
- **Runtime:** single HTML page in Chrome on the Pixel — browser mic → Gemini API → Web Bluetooth write. Chosen over Python/bleak-on-Android (experimental, community-only backend) and native Kotlin (toolchain overhead). Requires HTTPS or localhost.
- **Gemini mode:** request-response (simplest). Streaming/Live API deferred; swapping it in later must not touch the BLE layer (feeds Phase 2 modularity).
- **Latency policy:** measure everything, optimize nothing. No target X enforced in Phase 1 — but every run logs utterance→reaction time, because Phase 3's gate needs a Phase 1/2 baseline to exist.

**Deliverable:** droid reacts physically + audibly to a spoken prompt, end to end.

**Exit criterion (amended 2026-07-07):** end-to-end demo works repeatably (spoken prompt → droid physical + audible reaction), with utterance→reaction latency logged on every run. No latency target gated; the log IS the Phase 2/3 baseline.

## Phase 2 — Embodiment Hardening
**Status:** not started — blocked on Phase 1

Formalize BLE control as a swappable interface (modularity requirement — body should be replaceable without touching orchestration code). State management: idle animations, mid-command interrupts, BLE reconnect/error handling.

**Exit criterion:** droid survives a 30-minute unattended session without a hard crash or BLE desync.

## Phase 3 — Custom Embedded Body (first purchased hardware)
**Status:** not started — blocked on Phase 2

First point where MCU selection (e.g. ESP32-C3), mic/camera pipeline design, and power budget become relevant. Decide: replaces BB-8, or runs alongside it as a second familiar form factor.

**Exit criterion:** custom unit matches or beats Phase 2 latency/stability baseline before any new feature is added.

## Phase 4 — Flagship Platform (blimp)
**Status:** not started — blocked on Phase 3. Not to be spec'd before then.

Lift/buoyancy budget, motor/prop power draw vs. battery, onboard vs. tethered compute. No code or component selection happens for this phase until Phase 3 is stable.

## Update Rule
Change status fields only when the exit criterion is **actually met**, not when work "feels" close. If a phase is in progress, note it, but don't mark done without the criterion satisfied.
