# COMPANION UNIT 01 — Design Document
### CO-600 · Indoor Hybrid Airship Companion
*A buoyancy-assisted VTOL companion robot. Soft body, hard hardware, mortal.*

> Source: Notes from engineer meeting. Stored 2026-07-09.

---
## 0. Thesis
A pet that isn't biological, gives the emotional weight of one, has real utility, and can genuinely die.

The physical form is a **hybrid airship**: a helium envelope carries the static weight, two tilting rotors provide steering and trim. This is not a stylistic choice. It is the only configuration that delivers all four of the things a companion in a home requires:

| Requirement | Why buoyancy delivers it |
|---|---|
| **Quiet** | Rotors carry ~3% of weight, not 100%. Tip speed collapses; noise follows. |
| **Long endurance** | Hover power drops from watts to milliwatts. Hours, not minutes. |
| **Safe** | Soft, slow, near-neutral mass. Bumping it is nothing. |
| **Soft failure** | Power loss → gentle sink. Puncture → slow sag. Nothing falls. |

A quadcopter of this size is loud, flies for 8 minutes, has spinning blades at face height, and drops out of the air when the battery dies. Every one of those is disqualifying for a thing that lives with you.

**The governing physical insight:** buoyancy is a *volume* game. You are not lifting with helium — you are displacing air and paying back the small mass of the gas that fills the hole. Lift ≈ **1.0 g per liter displaced** (realistic, with consumer-grade helium). Everything below follows from that one number.

---
## 1. Constraint
**Envelope diameter: 60 cm** — the width of a 27" monitor.

This constraint was tested and it holds, but only just barely on the right side of the line. For context, on the same curve:

| Diameter | Displaced volume | Gross lift | Verdict |
|---|---|---|---|
| 30 cm (laptop width) | 14 L | **~15 g** | Dead. Envelope is cargo, not lift. |
| **60 cm (monitor width)** | **113 L** | **~113 g** | **Closes, comfortably.** |
| 100 cm | 524 L | ~550 g | Overkill for a desk pet. |

Lift scales with r³. Halving the diameter cut lift ~8×. There is no clever material or gas that recovers that — hydrogen buys 8% and isn't safe indoors. **60 cm is near the smallest envelope that flies a real payload.**

---
## 2. Lift Budget
Sea level, ρ_air = 1.225 kg/m³, ρ_He = 0.1786 kg/m³ → theoretical 1.046 g/L; **use 1.0 g/L** for real helium purity and superpressure.

**60 cm sphere:** V = 113.1 L · S = 1.131 m² · gross lift ≈ **113 g**

| Item | Mass |
|---|---|
| Envelope (17 g/m² metallized PET + 20% seams/valve) | 24 g |
| Gondola, full companion payload | ~40 g |
| **Subtotal** | **64 g** |
| **Spare lift** | **~49 g** |

**You are too buoyant.** That is the correct problem to have. The spare 49 g gets spent on a deliberately oversized battery and ballast to reach trim.

### Trim: buoyancy fraction (f)
f = buoyant lift ÷ total weight. This is the master variable — it sets power, endurance, noise, and failure mode all at once.

| f | Rotors carry | Continuous power | Character |
|---|---|---|---|
| 0.85 | ~18 g | 4.5–7 W | Working hard. Loud-ish. ~15 min. |
| 0.90 | ~12 g | 3–5 W | Still paying too much. |
| **0.97** | **~3 g** | **~1 W** | **Target. Quiet, hours, sinks gently.** |
| 0.99 | ~1 g | ~0.4 W | Nearly silent, but no draft authority. |
| >1.0 | — | — | Pinned to ceiling. Failure. |

**Target f ≈ 0.96–0.98.** Slightly heavy. Rotors do almost nothing except steer and trim; on power loss it settles to the floor over several seconds.

*Trim is set by adding battery, not by removing it.* Buy 1000 / 1500 / 2000 mAh cells and fit whichever lands you slightly heavy. Excess lift converts directly into endurance for free.

---
## 3. Prior Art — This Has Been Built
Three research platforms bracket this design. They are the reason to trust the numbers.

**ETH Zurich nano-blimp** (Palossi et al., *J. Signal Processing Systems* 91, 2019)
Ellipsoidal 60 × 65 × 40 cm mylar balloon (~82 L). A 68 g prototype hovering on **under 200 mW**. Max lift measured ~69 g. Nearly a drop-in match for this design.

**Georgia Tech GT-MAB** (Cho et al., CCTA 2017; Tao thesis 2020)
0.72 × 0.46 m saucer envelope (~120 L). Payload capacity <80 g. **Flight endurance >2 hours.** Also developed a swing-reducing controller for exactly the pendulum oscillation this airframe has — worth replicating.

**TU Delft BEAVIS** (Sharma et al., MobiCom '23)
**55 cm diameter balloon.** Coreless motors with only 15 g max thrust. Flies indoors reliably; blows away outdoors. Confirms both the feasibility and the boundary.

*The design is not novel physics. It is a known airframe class, customized.*

---
## 4. Airframe
**Configuration:** semi-rigid bicopter airship.

- **Envelope above, gondola below.** The offset between center of buoyancy and center of gravity makes it **pendulum-stable in pitch and roll — it self-levels for free.** Rotors never waste authority holding attitude.
- **Two tilting rotors** on booms at the equator, opposite sides. A free bicopter is famously hard to fly; a *buoyant* bicopter is easy, because the body handles attitude and the rotors only do the fun parts:
  - Both tilt forward → translate toward you
  - Differential tilt → clean yaw (turn to face you)
  - Both toward vertical → climb
- **Counter-rotate the props.** Otherwise reaction torque slowly spins the whole ship. Cheap fix, easy to forget.
- **Mount rotors near the CG's vertical level** to minimize thrust-induced pitch coupling.
- **Stiff harness** from envelope to gondola to suppress swing (per ETH's note).

### Shape
Sphere (AR 1.0) is recommended. A gentle prolate (AR 1.3–1.5, ~80–90 cm long) adds ~50 g of lift for ~8 g more film — lift-efficient, space-inefficient. **AR ≥ 2 is a small airship, not a desk pet:** 1.2 m long, high yaw inertia.

### Gas cells
**One cell.** Subdividing is tempting (puncture redundancy, creature shapes) but costs real money:
- Splitting one bag into 8 of equal total volume keeps **lift identical** (volume preserved)…
- …but roughly **doubles surface area** (S ∝ V^⅔), which doubles film mass *and* doubles permeation area.

Two or three cells is a defensible price for redundancy. Ten is paying the tax repeatedly for redundancy you'll never use.

---
## 5. Bill of Materials
Flying mass target ~64 g + ballast/battery to trim.

| Part | Spec | Mass | ~USD |
|---|---|---|---|
| Envelope | 60 cm metallized-PET sphere, self-sealing valve | 24 g | $8–15 |
| Helium | ~115 L, balloon grade (small tank ≈ 400 L) | — | $40–60/tank |
| FC / SoC / camera / mic | **Seeed XIAO ESP32-S3 Sense** | 4.5 g | $15 |
| Optical flow | PMW3901 (drift kill) | 1 g | $18 |
| Rangefinder | VL53L1X ToF (altitude) | 0.5 g | $8 |
| IMU | ICM-42688 / MPU-6050 | 1 g | $5–12 |
| Motors ×2 | 8520 coreless, ~40 g thrust each | 9.8 g | $8/pr |
| Props ×2 | 55–65 mm, counter-rotating | 2 g | $4 |
| Tilt servos ×2 | 1.7–2 g micro | 3.5 g | $12 |
| Motor driver | DRV8833 / dual MOSFET | 1 g | $5 |
| Battery | 1S LiPo 1500–2000 mAh *(trim knob)* | 28–36 g | $12 |
| Gondola + booms | 3D-printed shells, carbon rod | 5–8 g | $5 |
| Wiring, connectors | — | 3 g | $10 |

**≈ $150–200** plus helium.

**Notes:**
- The **XIAO ESP32-S3 Sense is the keystone part** — camera, mic, Wi-Fi, and flight controller in 4.5 g. The entire "sensory organ" in one component.
- **Skip tilt servos on v1.** Fixed rotors + differential thrust hovers and yaws. Add tilt after the reflex loop works.
- **Buy two envelopes.** You will overinflate or tear the first.
- **Not in the BOM, mandatory:** a 0.1 g scale (~$15). Every number here is a weighing problem. Guessing masses is how these projects die.

---
## 6. Control Architecture
**The slow dynamics of a blimp are what make phone-offloaded cognition possible.** A quad needs millisecond reflexes. This drifts at 0.5 m/s with huge drag damping and passive self-leveling, so a 100–300 ms perception loop through a phone is fine.

Two loops, cleanly separated:

### Spinal cord — onboard, 50–100 Hz
Runs on the XIAO. Never depends on the phone.
- Attitude/heading hold (IMU)
- Altitude hold (VL53L1X)
- **Drift kill / station-keeping (PMW3901 optical flow)** — the single most important onboard function
- Consumes setpoints: *bearing, range, height*

### Cortex — on the Pixel, 5–15 Hz
- Ship streams camera frames over Wi-Fi (~10–25 fps MJPEG, ~1.3 W)
- Phone runs person detection / pose tracking on the NPU (ML Kit, MediaPipe)
- Phone returns **setpoints only** — never raw actuator commands
- Personality state, LLM cognition, memory all live here

**The ship never needs to know what a person is.** It chases setpoints.

### Failsafe state machine
```
LINK OK        → follow setpoints
LINK LOST      → hold position (onboard flow + ToF)
HOLD > 30 s    → gentle descent to floor
BATTERY LOW    → return-to-pad, or descend
POWER LOSS     → passive sink (physics, not firmware)
```
Because it's buoyant, "link lost" means it parks in midair and settles softly. **The failure mode is a pet that stops and waits for you.** That is nearly in character.

### Follow-me: you may not need vision for navigation
The phone in your pocket can be the beacon. **UWB** (present on recent Pixels) gives range + bearing directly — works in the dark, through light occlusion, no inference required. BLE RSSI is the coarse fallback. A UWB module is ~2 g.

That frees vision to be what it should be for a pet: recognizing *who* you are, reading gestures, looking where you point. **Perception becomes personality, not navigation.**

### Build tiers
1. **Hover + hold** — onboard only, no phone. *(Stage 1 milestone)*
2. **Follow the beacon** — UWB/BLE pursuit. Still no vision.
3. **See you** — camera → Pixel → person detection → approach & orient. *The "it looks at you" moment.*
4. **Understand you** — perception summaries feed the personality brain; behaviors come back down.

Each tier demos independently. Tiers 1–2 need no vision pipeline at all.

---
## 7. Station-Keeping and Noise
### Drafts — the #1 indoor enemy
60 cm sphere, frontal area 0.283 m². Re ≈ 1×10⁴ to 4×10⁴ → subcritical, Cd ≈ 0.47–0.5.

| Draft | Speed | Drag | Lateral thrust needed |
|---|---|---|---|
| HVAC background | 0.25 m/s | ~5 mN | **~0.5 g** |
| Room draft | 0.5 m/s | ~20 mN | **~2 g** |
| Doorway | 1.0 m/s | ~87 mN | **~8.8 g** |

Two 8520s (~40 g thrust each) have ample authority. **It can hold station in a normal house.** Sustained gusts >1.5–2 m/s (open window, direct HVAC blast) will win — the same limit BEAVIS documented.

*Budget ~1.5× thrust margin over these figures: a seamed, gondola-laden envelope has higher drag than a smooth sphere.*

### Noise
Rotors carry ~3 g instead of a quad's ~300 g — roughly 20–30× less thrust per disc. Thrust ∝ RPM², tonal sound power ∝ tip speed⁵. Net: tip speed down ~5×, radiated power down **~20–30 dB**.

A micro-quad hovers at 64–77 dB at 1 m. This should sit **below 50 dB** — under conversational level. Research blimps are universally described as near-silent.

Levers, in order of effect: **lower tip speed** (dominant) → larger, slower discs → more blades → uneven blade spacing (smears the tone into noise, which the ear forgives) → swept/serrated tips.

---
## 8. Helium: Leak, Trim Drift, and Mortality
Metallized PET holds visible fill 3–7 days and useful lift 1–2 weeks. Helium diffuses through the film and, more so, through seams and the valve. **Expect a few grams of lift lost per day.**

This is unavoidable, and it is the most interesting fact in the whole design.

**Engineering consequences:**
- Size motors for the *heavy* end of the range, not the fresh-fill end
- Firmware **auto-trim**: raise baseline rotor lift as buoyancy decays
- Self-sealing valve for weekly top-ups
- A PET/EVOH or nylon barrier laminate stretches refills to weeks, at a small areal-density cost

**Design consequence:** the pet gets heavier every day until it can't hold altitude. It must be fed helium to stay alive. Not as a metaphor — as a fact of the physics.

The mortality that was supposed to be a designed mechanic is *already in the material.* You didn't have to build it. You have to decide whether to fight it.

> **A note on the death mechanic.** Choosing, for yourself, that your companion has real stakes is legitimate and interesting — a bond without loss on the table is a subscription. But that defense is personal. Selling "pay or it dies" to lonely or elderly strangers is a dark pattern, and this is a category whose buyers are exactly those people. Keep the wall clean: for a unit built for someone else, neglect should make it **sleepy and sad, never dead.** Reversible dormancy builds attachment. Irreversible death on a $5,000 device is a refund queue and a headline.

---
## 9. The Resource Model
The unit runs on **three separate resources with three separate depletion states.** Conflating them is the single most likely way to ruin this design.

| Resource | Buys | Refilled by | Depletion state |
|---|---|---|---|
| **Helium** | *Being alive.* Flight itself. | Dock reservoir / cartridge | Sinks. Cannot fly. **Dead.** |
| **Battery** | *Being awake.* Motion, sensing. | Landing pad | Returns to pad. **Asleep.** |
| **API credit** | *Thinking.* Language, personality. | Physical cards | Goes quiet. **Mute.** |

### The hard line
**Credit gates the cortex. It never gates the spinal cord.**

Look at where the work actually lives in §6. Tiers 1–3 — hover, station-keeping, beacon-follow, on-device person detection — run entirely on the XIAO and the Pixel's NPU. **None of them cost a token.** Only tier 4, the language and personality layer, meters.

So an out-of-credit unit is not a broken unit. It still flies. It still follows you. It still recognizes your face and turns toward you when you enter a room. It just can't *talk*.

That is an emotionally coherent state — a dog doesn't stop being a dog when it can't speak — and an honest one, because it maps exactly onto what is actually being paid for.

```
NEVER FOR SALE          ALWAYS METERED
─────────────────       ──────────────────
locomotion              conversation
station-keeping         personality state
altitude hold           LLM reasoning
collision avoidance     open-ended vision Q&A
following you           
recognizing you         
gentle descent          
```
If low credit ever degrades **movement, safety, or recognition**, pay-or-it-dies has been rebuilt through the back door. Hold this line.

### Legibility
A prepaid meter is only acceptable when it is *visible*. People accept prepaid minutes; they revolt when the balance vanishes silently.
- The status ring should shift color as credit runs low — days of warning, not minutes.
- Behavior should telegraph the state: growing verbal sluggishness, shorter responses, longer pauses before it "finds the words."
- Going mute should feel like the pet getting tired, not like a paywall slamming shut.

### Three failure states, three characters
- **Low battery** → seeks the pad, settles, sleeps. *Tired.*
- **Low credit** → still present and affectionate, but quiet. *Wordless.*
- **Low helium** → heavier each day, struggles to hold altitude, finally rests on the floor. *Dying.*

Only the third is mortality, and it is a property of the material (§8), not a business decision. That is what makes it defensible.

---
## 10. The Dock
Constraint: it must stow flat, and helium must get back in.

**The ship cannot recover its own helium.** A pressure vessel and compressor capable of storing 113 L weigh well over a kilogram. Total lift is 113 g. The recovery hardware outweighs the ship by 10×.

**Therefore the dock does it.** The pet carries only a valve and film. The pad holds the compressor and reservoir. Docking:
1. Clamp onto the valve
2. Pump helium out of the envelope into the pad's tank → body collapses flat
3. Charge the battery
4. To wake: pump the gas back in

All the mass that made this impossible lives in a stationary base where mass is irrelevant. **Docking becomes one gesture that feeds it both power and breath.**

**Remaining hard parts:**
- Permeation still bleeds gas from the closed loop → the pad's reservoir needs occasional top-up from a cartridge. *This is the feeding ritual, made literal.*
- **Film fatigue.** Repeated collapse/reinflation work-hardens the film and cracks it at fold lines. Use a fold-tolerant film (TPU-coated fabric over bare mylar) and a *controlled* collapse so it packs the same way every time.
- Reinflation takes minutes and the compressor is audible. It happens while asleep. Call it a wake-up ritual.

---
## 11. Visual Direction
**Soft body, hard hardware.** The envelope is a balloon and must look like one. All density concentrates where real machinery lives.

- **Envelope:** charcoal technical fabric, **quilted** — deep stitched seam channels dividing it into faceted panels that catch light and cast real shadow. Like a Zeppelin's fabric skin or a bomber jacket. Not printed decals; relief. Not rigid; inflated.
- **Markings:** white stencil. Functional labeling only. `SER NO. CO-600` · `COMPANION UNIT 01` · `LIFT GAS HE` · `VENT`
- **Booms:** thick, tapered carbon fiber, meeting the sphere at machined shouldered collars with visible fasteners.
- **Nacelles:** chunky tilting pods with cooling fins and exposed hardware, inside thin ring guards. *(The rings are safety and styling, not aerodynamics — ducts earn nothing at this disc loading.)*
- **Sensor head:** dense gimballed multi-lens cluster slung below. Main camera, secondary lens, mic ports, soft amber status ring.
- **Language:** reconnaissance aircraft meets Teenage Engineering. **Osprey, not gunship.** Transport. No weapons — a creature in gear, not a machine of war.
- **Lighting that sells it:** dramatic side light raking across the quilted surface to reveal depth.

**What the renders lie about:** those nacelles must be hollow printed shells (~5 g each), not machined billet. The gondola will be chunkier than drawn — a 2000 mAh battery is a real object. And the booms push the true footprint to ~100 cm wide, which matters for doorways.

*Industrial design here is the art of making 40 grams look like it means business.*

---
## 12. Build Plan
### Stage 1 — Prove the physics
Commercial 60 cm foil sphere. XIAO ESP32-S3, two fixed 8520 rotors, 500 mAh, phone Wi-Fi link. Ballast to f ≈ 0.95.
- **Pass:** hovers on <3 W; holds station against a 0.25 m/s HVAC draft
- **Fail → act:** hover >5 W → lower-Kv motors or bigger props. Can't hold 0.5 m/s → trim closer to neutral, or more thrust.

### Stage 2 — The companion
Custom envelope (sphere, or AR 1.3–1.5), quilted skin, self-sealing valve. Add tilt servos, camera + mic (XIAO Sense), 1500–2000 mAh, trim to f ≈ 0.97.
- **Expect:** 1.5–3 h endurance, <50 dB, reliable indoor station-keeping
- **Fail → act:** lift loss >3 g/day → move to PET/EVOH barrier laminate

### Stage 3 — Alive
Docking pad (charge + helium recovery). Firmware auto-trim for leak. UWB follow-me. Vision → personality. Swing-reducing controller per GT-MAB.

### Thresholds that change the design
- Need >3 h continuous streaming → AR 2 envelope (accept 1.2 m length)
- Operating near open windows / direct HVAC → sphere insufficient; restrict to safe zones
- Need weeks between refills → barrier laminate (heavier film, less net lift)

---
## 13. Open Questions
1. **Trim authority vs. quiet.** f = 0.97 is the recommendation, but the real optimum depends on your house's draft profile. Measure it.
2. **Coreless motor efficiency (3–5 g/W) is the dominant endurance uncertainty.** Momentum theory says milliwatts; real electrical draw at these tiny thrusts is poorly characterized. **Put the motors on a test stand before trusting any endurance number.**
3. **Quilted skin areal density** is unmeasured. It costs more than bare 17 g/m² film. How much?
4. **Pendulum swing during follow-me acceleration.** Passive stability is free but it *bobs*. GT-MAB solved this in firmware; budget for that work.
5. **Boom footprint.** ~100 cm wide is a lot of room. Shorter booms = less authority. Where's the line?

---
## Appendix: The Math, Standalone
```
Net lift per liter    = ρ_air − ρ_He = 1.225 − 0.1786 = 1.046 g/L
                        (use 1.0 g/L realistic)
Sphere volume         V = (4/3)πr³
Sphere surface        S = 4πr²
Prolate volume        V = (4/3)π·a·b²      (a = semi-major, b = semi-minor)
Buoyancy fraction     f = lift / total_weight
Rotor deficit         W_def = total_weight − lift
Induced power         P = T^1.5 / √(2ρA)        [ideal]
Real electrical       P_elec ≈ T / 4 g/W        [8520-class coreless]
Drag                  F = ½ ρ Cd A v²
Reynolds              Re = ρvD/µ                 (µ = 1.81e−5 Pa·s)
  → 60 cm sphere, 0.25–1.0 m/s: Re = 1e4 – 4e4, Cd ≈ 0.47–0.5
Noise scaling         P_acoustic ∝ v_tip⁵ ;  T ∝ RPM²
  → thrust ÷20  ⇒  tip speed ÷4.5  ⇒  ~20–30 dB quieter
```
---
*Displaced volume buys free lift. The rotors just steer the bubble.*
