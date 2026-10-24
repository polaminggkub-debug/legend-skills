---
name: artifact-sketch
description: >
  Build a step-by-step visual explainer as an Artifact page: one press = one action, a clear
  picture for every step, real colours and real photos. Use whenever the user asks to
  "sketch it in an Artifact", "อธิบายเป็นภาพ", "ทำ step by step", "วิธีต่อ", "วิธีประกอบ",
  or wants something explained or taught visually: wiring, electronics, assembly, hardware
  setup, installing or configuring software, a process, a workflow, a concept. Use it even
  when the user only says "explain this to me" and a picture would make it clearer. Not for
  sketches of ERP demo chapters (those follow docs/demos/demo-rules.md).
---

# Artifact sketch

An artifact sketch is a page the user follows with their hands or their eyes, one step at a
time. Its reader is not an engineer reading a spec. The reader is a person at a desk with the
real parts, who looks up from the work, glances at the screen, and must know at once what to
do next. Every rule below comes from that one glance.

Load `artifact-design` before writing the page. For UI work in this setup, also load
`steve` and `ui-ux-pro-max` first.

## 1. Shape: a stepper, not a long page

- **One press = one action.** "Screw the red wire into a1" is one step. "Wire T1" is not:
  split it into one step per wire, part or hole. 50+ steps is normal and fine.
- Big **‹ ย้อน / ถัดไป ›** buttons fixed at the bottom, plus arrow keys. Group chips at the
  top jump to a group (e.g. "3 · จัมเปอร์").
- **One counter only:** "ข้อ 12 จาก 54", with the group name beside it. Never show two
  number pairs (group X/Y and step X/Y) at once: the reader cannot tell which is which.
- **Merge steps that do nothing.** "Prepare the parts" and "get the clock ready" are not
  steps. Put all parts on one first page: photo card + name + count for each, plus a few
  short prep lines (solder pins, set switches, insert battery, tools).
- Say up front anything that changes how the reader prepares. Example: if two wires must
  share one screw slot, say so in step 1, because one ferrule cannot take two wires and the
  reader has to crimp them together before starting. Better: design so every slot takes
  exactly one wire, and say that.

## 2. Pictures: one clear picture per step

- Every step has a picture. The picture **zooms to where the hands are** and marks the exact
  spot (hole, port, button) with a ring and a readable tag ("a21"). A "ทั้งบอร์ด / whole
  view" toggle shows the full picture.
- Parts done in earlier steps are faded; this step's part is full colour. The **final step
  and the check steps show everything in full colour**, nothing faded.
- **No blinking, no dashed lines, no animation** that the reader must wait for or decode.
  Solid lines and solid rings only.
- **Never collapse many wires into one line.** A 4-wire cable is drawn as 4 wires, each in
  its own colour, each ending in its own hole or slot. A "summary line" makes the reader
  guess, and guessing is what the sketch exists to prevent.
- Show *how* each end attaches. A wire into a screw terminal ends with an arrow at the
  terminal; a jumper pin into a hole ends with a pin in that hole. Say the legend under the
  picture. Never draw it so that several wires appear to enter one slot.
- **Use a real photo** of the device for ports and connectors (from the official manual or
  shop page). Circle only the ports this build uses, each with a label: name, where it is on
  the board ("left edge, between RESET and BOOT"), and what plugs in. Remove every mark that
  is not ours (the manual's red boxes, arrows, unused ports): unused highlights confuse.
- **One overview picture** shows every connection end to end: source, cable, destination
  port. Put it at the start of the "connect" group and again at the last step.
- Always name the far end: "JST cable → IIC port **of the ESP32 screen**", not "→ IIC".

## 3. Colour: real colours, everywhere, in text too

- **Every wire is drawn in its real colour** (the colour of the cable the user bought), in
  every picture. Never use "function colours" (orange = power) that differ from the real
  wire: the reader matches the screen to the wire in their hand.
- **Every step that touches a wire states its colour in the text**: "แดง → a21 (3.3V)".
- **Colour words in text are colour chips**, not plain monotone words: a small rounded chip
  filled with the real colour and contrasting text (red chip with white text, white chip with
  dark text and a border, black chip with white text, yellow chip with dark text). Apply it
  to every text area (step title, details, warnings, checks) by post-processing the step
  data, so no step is missed. Plain text "แดง ดำ เขียว" in one grey is a fail.
- **Every reference in text carries its colour too, not only colour words.** Hole names
  (a21), column numbers (1 3 5 7…), pins and signals (5V, GND, SDA, SCL, D+), and any other
  identifier the reader must find in the picture are chips with a dot in the colour of the
  real wire that lands there. Identifiers with no wire get a hollow dot. A list like
  "แดง a1 j1 a11" where only "แดง" is coloured and the holes are plain grey is a fail: the
  reader scans for the hole, not the colour word. Build one map (column/pin → wire colour)
  from the circuit data and use it for both picture and text, so they cannot disagree.
- Where the colour is unknown or does not matter, say it plainly: "2 wires, any colour, either
  way round", or "colour of the U-jumper depends on its length, not the picture". If the
  colour order is not standardised (e.g. JST cables), find it with a meter step, not by
  guessing, and give both outcomes.
- Components with colour codes get them too (resistor 5.1k = green brown red gold).

## 4. Facts: check before you say done

- Take every pin, hole and port name from a source: the circuit plan, the datasheet, the
  print on the board. When a source corrects an assumption (e.g. pin 3 is SCL, not SDA),
  update every step and picture that uses it.
- Before reporting, walk **every step** and check: wire colour stated, picture shows each wire
  separately, holes match the circuit, nothing on the 3.3V side touches 5V, final picture
  complete. Run a small script over the built step data that lists (a) steps that touch a
  wire but name no colour and (b) any identifier (hole, column, pin) left as plain text
  outside a colour chip. Both lists must be empty before "done".
- Render it and look (local server + screenshot; add `<meta charset="utf-8">` to the local
  copy, or Thai shows as mojibake). Report what was not visually checked.
- Add stop rules where a mistake can damage something: "meter shows 5V → stop, send a photo".

## 5. Language

Write in the user's language (Thai for this owner), short lines, one fact per line. When the
user says they don't understand a picture, the picture is wrong: fix the picture, then explain
in plain words what each mark means.

## 6. Beyond hardware

The same shape works for any explainer: a software setup (one click per step, real
screenshot with the button circled), a process (one actor action per step, overview diagram
first and last), a concept (one idea per step, the same diagram growing step by step). Keep:
one action per press, one clear picture per step, real visuals over abstract ones, colour
references in text match the picture, an overview, and a full check before "done".

## Build pattern

Keep content as data and the page as a renderer: a Python (or JS) list of steps
`{group, text, details[], picture-state, rings[], photo, warning}` and one HTML template that
draws the picture for the current step. Post-process all text fields once (colour-word chips,
plus dot chips for every hole, column, pin and signal from the colour map) and run the
"missing colour" and "bare identifier" checks over the same list. Publish to the same Artifact URL on every
revision so the user's link stays the same.
