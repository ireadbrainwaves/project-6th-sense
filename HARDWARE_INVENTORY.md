# 6th Sense — Hardware Inventory

**Status as of 2026-07-06.** One line per confirmed asset. No speculative or planned hardware listed here — that belongs in the roadmap, not the inventory.

## Confirmed Assets

| Item | Role | Notes |
|---|---|---|
| **Pixel 10 Fold** | Primary compute / sensor host | Camera(s), mic array, speaker, battery, network all native. Candidate for running orchestration directly (on-device or API-calling Gemini client) without any embedded firmware. |
| **Home desktop** | Dev host | Spec (CPU/GPU/RAM/OS) TBD — fill in before Phase 1 starts, since it determines whether this machine can also serve as a local relay/orchestration server vs. dev-only. |
| **BB-8 droid** (Disney Galaxy's Edge / Droid Depot) | Physical body | Not the Sphero consumer BB-8 — different hardware, different BLE protocol. No official public SDK. Protocol confirmed via reverse-engineered community work + direct BLE scan. See `6th_sense_protocol_notes.md`. Address: `DA:A2:05:2C:0B:26`. |

## Not Yet Purchased
Nothing. No MCU, no external mic/camera modules, no custom body, no blimp platform. Do not spec components for these here — that's roadmap Phase 3/4 territory and is gated on earlier phases.

## Update Rule
Add a row only when hardware is physically in hand. "Considering buying X" goes in the roadmap as a phase note, not here.
