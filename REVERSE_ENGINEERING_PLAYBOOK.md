# Reverse Engineering — A Field Guide
### For Project 6th Sense, and the road from "good taste" to embedded engineer

**Who this is for:** you — no formal engineering background, strong design taste, strong at directing AI. This guide turns the BB-8 work into a repeatable method and a learning ladder, so the project doesn't just produce a droid, it produces an engineer.

**The honest premise.** You're not starting from zero; you're starting from a *different* zero than a CS grad. Taste means you can tell when a system feels wrong before you can explain why — that instinct is what senior engineers spend years rebuilding. AI direction means you can navigate unfamiliar terrain faster than someone working alone. What you lack is *low-level fluency*: bytes, protocols, timing, state. That's learnable, and reverse engineering is one of the fastest ways to learn it, because you're always working against ground truth (the real hardware) instead of a textbook.

---

## Part 1 — What reverse engineering actually is

Reverse engineering is figuring out how a system works when nobody will tell you, by combining three things: **public clues** (community docs, source code, captured traffic), **direct observation** (scanning, probing, measuring the real device), and **verification against ground truth** (does the device actually do what your theory predicts?).

For embedded specifically, this is a daily skill. Datasheets are wrong or missing. Vendor libraries are undocumented. You will constantly be asking "what bytes does this chip actually want?" and answering it exactly the way we answered "what bytes does the BB-8 want?" So this project is not a detour from embedded — it *is* embedded practice.

---

## Part 2 — The core loop (the method)

This is the loop we ran to decode the LED and head-rotation commands. Memorize the shape; you'll reuse it forever.

**1. Locate, don't assume.** When something's "missing" or "broken," separate *where it's shown* from *where it is*. The droid code wasn't gone — it was in Downloads. Half of debugging is discovering the thing you're looking for isn't where you assumed.

**2. Work from the record, not memory.** Pull the actual transcript, the actual log, the actual source file. Your memory (and mine, and any AI's) is confident and lossy. Ground truth isn't.

**3. Search points; source answers.** Web search told us "check the repo." The answer was in the `.py` files. Use search to find *where to look*, then read the primary source.

**4. Extract the rule, not just the answer.** We didn't copy an LED byte string — we pulled out `build_droid_command`, the function that *generates every command*. Understanding the generator beats memorizing outputs, because then you can produce commands nobody documented and spot when sources disagree.

**5. Anchor the unknown to the known.** ← *This is the one that separates guessing from engineering.* We didn't trust the decoded LED bytes because a library said so. We reproduced the packet math and checked it regenerates bytes **we'd already confirmed on the physical droid** (the sound + init commands). When your model reproduces known-true facts, its new predictions inherit that trust. Always find your anchor.

**6. Hold contradictions open.** pyDroidDepot said one byte was `0x00`; another capture said `0x42`. We flagged "test both" instead of guessing. Label everything: *confirmed / reported / conflicting*. Honest ambiguity is cheaper than fake certainty.

**7. Inventory, then triage.** List every gap (we grepped for `TBD`/`UNKNOWN`), then split into *actionable now* vs *blocked*. This is the same discipline as your phase gates — it stops both wheel-spinning and premature work.

**8. Verify cheaply and often.** A 20-line script turned "probably right" into "reproduces confirmed data" for almost no cost. If a check is cheap, always run it. Embedded punishes the unverified assumption harder than almost any field.

**One-sentence version:** *Go to the primary source, extract the generating rule, and validate it against something you already know is true.*

---

## Part 3 — The BB-8 as a learning ladder

Each roadmap phase quietly teaches a pillar of embedded engineering. This is why the gated roadmap is good pedagogy, not just good project management — you can't skip a rung.

| Phase | What it looks like | What you're *actually* learning (embedded) |
|---|---|---|
| **0 — Protocol** | Decode BLE commands | Bytes & hex, packet framing, GATT characteristics, latency measurement, source reading |
| **1 — MVP loop** | mic → AI → BLE command | Event loops, async I/O, the sense→decide→act loop that every robot runs |
| **2 — Hardening** | Survive 30 min unattended | State machines, error handling, reconnection, the difference between "works once" and "reliable" |
| **3 — Custom body** | ESP32, sensors, power | *Actual* embedded: microcontrollers, firmware, GPIO, power budgets, real-time constraints |
| **4 — Blimp** | Lift, motors, batteries | Systems engineering: physics vs. compute vs. battery tradeoffs |

By the time you're specifying an ESP32 in Phase 3, you'll have already handled bytes, protocols, timing, and state — so the microcontroller is "more of the same," not a cliff.

---

## Part 4 — Concepts this project sneaks into you

You don't need to study these upfront. Learn each one *the moment the project forces you to* — that's when it sticks. Rough order of appearance:

- **Bytes, hex, bitwise ops** — already happening (`byte1 = length | 0x20`). The `|` is a bitwise OR; `0x` means hexadecimal. Worth 30 minutes on a good explainer.
- **BLE / GATT** — services, characteristics, write-with-response vs. notify. You've already used all of these.
- **Protocol framing** — length + type + payload. Nearly every protocol on earth is a variation of this.
- **Latency & jitter** — you measured it; next you'll learn why it varies (signal, scheduling, radio).
- **Async / event loops** — the `asyncio` in your scripts. The backbone of responsive embedded code.
- **State machines** — Phase 2. How a device knows "am I idle, connected, mid-command, erroring?"
- **Then real firmware** — C/C++, GPIO, interrupts, power. Phase 3, and not before you're ready.

---

## Part 5 — Your unfair advantage: directing AI well

You already have this skill; here's how to aim it so it builds competence instead of hiding gaps.

- **Ask for the rule, then an example — not just the answer.** "Explain the framing, then show one command" teaches you; "give me the LED bytes" doesn't.
- **Make the AI show its anchor.** Ask "how do we know this is right?" If the answer isn't tied to something confirmed (a datasheet value, a reproduced output, a measurement), treat it as a hypothesis, not a fact.
- **Demand the cheap verification.** "Write a script that proves these bytes match the confirmed ones." Never accept confident prose where a five-line check exists.
- **Have it label confidence.** Confirmed vs. reported vs. guessed. An AI that won't distinguish these will happily invent a plausible byte — the exact failure your project's discipline rule guards against.
- **Learn the vocabulary as you go.** Each time a new term appears (GATT, jitter, GPIO), get a one-paragraph plain explanation before moving on. Vocabulary is most of the gap between "no background" and "engineer."

The trap to avoid: letting AI keep you *productive without getting fluent*. The tell is when you can make it work but can't explain why it works. When that happens, stop and close the gap — that's the difference between directing a tool and becoming an engineer.

---

## Part 6 — Concrete next drills (this project)

1. **Confirm one decoded command yourself.** Fire the head-LED command (`27 42 0F 44 44 00 48 01`) at the droid. Before you run it, predict what happens. Predicting-then-checking is how you build intuition.
2. **Decode one command without help.** Pick a pyDroidDepot command we didn't cover (e.g. `SetVolume`), and hand-derive its bytes using the framing rule. Then verify with a script. This is the whole loop in miniature.
3. **Write down one term a day** that showed up and you couldn't fully explain. Get it to a one-sentence definition.
4. **Keep a "confirmed vs. reported" habit** in every project file. It's the single most engineer-shaping discipline here, and you already have it written into your notes.

---

*This guide pairs with `6TH_SENSE_HUB.md` (project state) and `ROADMAP.md` (phase gates). Update it as your method sharpens — a playbook you revise is a playbook you actually use.*
