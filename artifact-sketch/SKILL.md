---
name: artifact-sketch
description: >
  Build a step-by-step visual explainer as an Artifact page: one press = one action, a clear
  picture for every step, real colours and real photos, colour-coded text that lights up
  its part of the picture on hover (and back). Use whenever the user asks to
  "sketch it in an Artifact", "อธิบายเป็นภาพ", "ทำ step by step", "วิธีต่อ", "วิธีประกอบ",
  or wants something explained or taught visually: wiring, electronics, assembly, hardware
  setup, installing or configuring software, a process, a workflow, a concept. Use it even
  when the user only says "explain this to me" and a picture would make it clearer. Not for
  sketches of ERP demo chapters (those follow docs/demos/demo-rules.md).
---

# Artifact sketch

The reader has the real parts in hand, glances at the screen, and must know the next move at
once. Every rule serves that glance. Load `artifact-design` first (here also `steve`, `ui-ux-pro-max`).

## Shape
- Stepper, not a long page. One press = one action (one wire, one hole, one click); 50+ steps is fine.
- Big ‹ ย้อน / ถัดไป › fixed at the bottom, arrow keys, group chips at the top to jump.
- One counter only: "ข้อ 12 จาก 54" plus the group name. Never two number pairs.
- First page = every part (photo, name, count) plus short prep lines. No do-nothing prep steps.
- Say up front what changes preparation. Design one wire per screw slot and state it; a ferrule takes one wire.

## Pictures
- Every step has a picture, zoomed to where the hands are, target marked with a solid ring and tag ("a21"); a whole-view toggle.
- Earlier parts faded, this step full colour. Final and check steps: everything full colour.
- No blinking, dashes or animation.
- Never merge wires: a 4-wire cable is 4 lines, each its real colour, each into its own hole.
- Show how each end attaches (arrow at a screw terminal, pin in a hole) with a legend. Never let wires look like they share a slot.
- Ports: real device photo from the manual or shop. Circle only ports we use, label each (name, where on the board, what plugs in). Erase every other mark.
- One overview picture of every connection end to end, at the start of the connect group and at the last step.
- Name the far end: "→ IIC port of the ESP32 screen", not "→ IIC".

## Colour and text
- Real wire colours everywhere (the cable bought), never function colours.
- Every step touching a wire states its colour in text.
- Colour words are filled chips (red/white text, white/border, black, yellow/dark text).
- Every identifier the reader looks for in the picture (hole, column, pin, signal, port) is a chip with a dot in its real wire colour; hollow dot if no wire. Colouring only the colour word is a fail. Build one map (column/pin → colour) and feed picture and text from it.
- Same look in text and picture: a tag in the picture ("a21") uses the same chip as the text (same dot colour, same text colour, no link-blue). Orange means only "do it here" (ring, tag border, hover).
- One colour per line: when a line lists several wires, give each wire its own row ("แดง a21 3.3V" / "ดำ a23 GND" …). Never chain colours with "·" in one line.
- Two-way hover (tap pins on phones): text chip lights its wire, part and ring and dims the rest; a wire lights its text chips. Same key list on both (`data-l="h-a21 c21 w-r"`), wide transparent hit stroke on thin wires, faded layers lifted while highlighted, cleared on step change, one hint line under the picture.
- Unknown or irrelevant colour: say "any colour, either way round". Non-standard order (JST): find it with a meter step and give both outcomes, never guess. Resistor bands too.

## Check before "done"
- Labels follow the real part's print and orientation (e.g. breadboard: where column 1 and row a really are). Ask or check a photo before drawing; if the picture and the part disagree, rename the labels to the print, not the reader's part.
- Every pin, hole and port comes from a source (circuit, datasheet, board print). When a source corrects an assumption, fix every step and picture.
- Script over the step data: steps with a wire but no colour, identifiers outside a chip, lines with 2+ colours, hole colour in text ≠ wire colour in picture. All empty.
- Walk every step: colours, separate wires, holes match the circuit, 3.3V never meets 5V, final picture complete.
- Render and look (local server, `<meta charset="utf-8">` in the local copy). Test hover both ways on a board step and a port step. Report what was not seen.
- Stop rules where damage is possible: "meter shows 5V → stop, send a photo".

## Language and scope
- User's language (Thai here), short lines, one fact per line. If the user does not understand a picture, the picture is wrong: fix it, then explain each mark.
- Works beyond hardware: software (real screenshot, button circled), process (one actor action per step), concept (one diagram growing step by step). Same rules.

## Build
Steps as data (`{group, text, details[], picture-state, rings[], photo, warning}`) plus one HTML renderer. Post-process all text once (chips, dots, rows) and run the checks on the same list. Wrap each drawn wire, part, terminal and port in `<g class="lk" data-l="…">` at generation; one delegated pointer handler drives the highlight. Republish to the same Artifact URL.
