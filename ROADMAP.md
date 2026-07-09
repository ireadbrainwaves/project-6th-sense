# 6th Sense — Roadmap

Each phase is gated. **Do not spec or design a later phase's hardware/software until the current phase's exit criterion is met.** This file exists specifically to catch scope-creep against a written gate instead of momentum.

## Phase 0 — Protocol Confirmation
**Status:** ✅ COMPLETE — exit criterion met 2026-07-07 (see `6th_sense_protocol_notes.md`, `6TH_SENSE_HUB.md`, `droid_activity_log.csv`)

Confirm the Galaxy's Edge BB-8 BLE protocol. No purchased hardware required.

**Exit criterion:** documented, testable command set (roll, heading, head rotation, LED, sound trigger) with confirmed round-trip latency. — **Met:** all five command types confirmed on our unit; write-ACK round-trip latency measured and logged (~176–268 ms). Physical utterance→motion timing is intentionally deferred to Phase 1, where it is the exit criterion.

## Phase 1 — MVP Software Loop (phone-only)
**Status:** ✅ COMPLETE — closed 2026-07-08 (with caveat, see below)

Pixel 10 Fold runs orchestration directly: mic capture → Gemini → response → BLE command to BB-8. Desktop is dev host only.

**Decisions (2026-07-07):**
- **Runtime:** single HTML page in Chrome on the Pixel — browser mic → Gemini API → Web Bluetooth write. Chosen over Python/bleak-on-Android (experimental, community-only backend) and native Kotlin (toolchain overhead). Requires HTTPS or localhost.
- **Gemini mode:** request-response (simplest). Streaming/Live API deferred; swapping it in later must not touch the BLE layer (feeds Phase 2 modularity).
- **Latency policy:** measure everything, optimize nothing. No target X enforced in Phase 1 — but every run logs utterance→reaction time, because Phase 3's gate needs a Phase 1/2 baseline to exist.

**Deliverable:** droid reacts physically + audibly to a spoken prompt, end to end.

**Exit criterion (amended 2026-07-07):** end-to-end demo works repeatably (spoken prompt → droid physical + audible reaction), with utterance→reaction latency logged on every run. No latency target gated; the log IS the Phase 2/3 baseline.

**How it was met (2026-07-08):** 11 voice→reaction successes across two on-unit sessions (`droid_voice_log.csv`, `droid_voice_log_stale_build_session.csv`); utterance→reaction 2.3–3.9 s, Gemini dominates (~2.2–3.3 s), BLE negligible. All failures (5) were Gemini JSON parse errors — root-caused, fixed in v3 (robust extraction + retry), unit-tested against both observed failure modes. **Caveat:** v3 fix not yet validated on-unit (API quota hit); the first Phase 2 session doubles as that validation. If v3 fails on-unit, this phase reopens per the update rule.

## Phase 2 — Embodiment Hardening
**Status:** ACTIVE — work item 1 (v3 validation) DONE 2026-07-09; next up: body driver seam.

Formalize BLE control as a swappable interface (modularity requirement — body should be replaceable without touching orchestration code). State management: idle animations, mid-command interrupts, BLE reconnect/error handling.

**Design principle (decided 2026-07-08):** use the cheapest system that produces the behavior. Reflexes (idle fidgets, timers, reconnect) = local algorithms, $0, no Gemini. Cognition (interpreting speech) = Gemini. Audio becomes an *interrupt* to an otherwise algorithmic idle loop.

**Work items (in order):**
1. ~~Validate v3 voice loop on-unit~~ **DONE 2026-07-09** — 12/12 voice reactions parse-clean, all attempt=1 (`droid_voice_log_v3_validation.csv`). 3 leading Gemini 503s excluded per agreed criteria (upstream overload, not a v3 failure). NEW LATENCY BASELINE: utterance→reaction 793–1285 ms (Gemini 687–1148 ms, BLE ~100–180 ms) — ~3x better than Phase 1's 2330–3690 ms. Gap: CSV doesn't record which Gemini model ran — stamp model string into rows in next page rev (v4).
2. ~~Body driver seam~~ **DONE 2026-07-09 (v4)** — everything droid-specific lives in one `body` object (`connect()`, `do(word)`, `stopAll()`, `onDrop(cb)`, `actions()`, ACK latency probe). Seam rule: brain sequences BETWEEN actions; body owns execution WITHIN an action (auto-stop = body reflex; timing constants = body config). System prompt now generated from `body.actions()`. v4 stamps model + body into every CSV row. Verified: frames byte-identical to confirmed hexes; on-unit smoke test 3/3 (`droid_voice_log (3).csv` rows, latency 906–1335 ms on baseline). Phase 3 test stands: new body = one new object, zero brain changes.
3. Idle state machine — random fidgets on timers (head turns, blinks, occasional beep), pure algorithm, zero API calls.
4. Reconnect/error handling — detect BLE drops, auto-reconnect + re-init, resume idle; voice interrupts yield mid-fidget.

**Open sub-questions carried in:** head-LED flash anomaly (`...45 01` no reaction); flaky stop commands (Phase 0 log rows 13–14); undecoded notify payload `2F 32 81 45 4B 10 01 44 44 11 11 01 00 00 00 00` (apply framing rule in reverse); Web Speech STT mishearings (improvement, not a gate). For Phase 3: decide which side of the seam the microphone lives on.

**Exit criterion:** droid survives a 30-minute unattended session without a hard crash or BLE desync — proven by the session CSV, not by feel.

## Phase 3 — Custom Embedded Body (first purchased hardware)
**Status:** not started — blocked on Phase 2

First point where MCU selection (e.g. ESP32-C3), mic/camera pipeline design, and power budget become relevant. Decide: replaces BB-8, or runs alongside it as a second familiar form factor.

**Candidate feature — follow mode (parked here 2026-07-09):** following is closed-loop control and needs relative position sensing; BLE RSSI is the only signal available in Phase 2 and it's unusable (noisy, distance-only, no direction, barely exposed by Web Bluetooth). Requires camera/UWB-class sensing → Phase 3. Feeds the mic/camera seam-side decision.

**Exit criterion:** custom unit matches or beats Phase 2 latency/stability baseline before any new feature is added.

## Phase 4 — Flagship Platform (blimp)
**Status:** not started — blocked on Phase 3. Not to be spec'd before then.

Lift/buoyancy budget, motor/prop power draw vs. battery, onboard vs. tethered compute. No code or component selection happens for this phase until Phase 3 is stable. Full concept in `CO-600 Companion Unit 01 - Design Document.md`.

### Design choices (design-space only — recorded, not spec'd)
These are form-factor forks to hold in mind, not decisions that unlock hardware buys. They do not violate the phase gate.

- **A — Desk pet (original CO-600 framing).** 60 cm sphere, minimum envelope that flies a real payload. Tension: the boom footprint is still ~100 cm wide (§11), so it doesn't actually clear a doorway or sit on a desk. Smallest, quietest, shortest endurance.
- **B — Room pet (Austin's preferred direction, 2026-07-09).** Embrace the ~100 cm footprint instead of apologizing for it. The object lives in and moves through a room, not on a desk. Opens the door to a larger or prolate envelope (AR 1.3–1.5, ~80–90 cm long, +~50 g lift for ~8 g film) for more endurance/payload headroom. Changes the station-keeping story: it must hold position against room-scale drafts and doorways, not just a desk-side HVAC breeze — so draft authority and the swing/bob controller (GT-MAB, §13 Q4) matter more. Yaw inertia and where it's allowed to fly (safe zones vs. open windows) become real constraints.

**Consequence to revisit at spec time:** B likely wants the prolate envelope and a firmer answer on the boom-length ↔ draft-authority tradeoff (CO-600 §13 Q5) before any component is chosen.

## Update Rule
Change status fields only when the exit criterion is **actually met**, not when work "feels" close. If a phase is in progress, note it, but don't mark done without the criterion satisfied.
