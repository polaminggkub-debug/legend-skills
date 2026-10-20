---
name: meeting-transcript
description: >
  Turn meeting recordings (Plaud recorder, Wispr Flow, any backup audio) into accurate Thai or
  mixed-language transcripts with timestamps and named speakers, cheaply: free local models on a
  worker machine, no LLM rewriting of the text. Use when the user wants meeting transcripts made,
  merged from several recorders, speakers identified or fixed, meetings split by topic, recordings
  backed up, or a corrected transcript put back into Plaud.
---

# Meeting transcript

Who said what, when, from every recorder of a meeting, for almost no tokens. The text already exists:
Plaud and Wispr Flow transcribe, Whisper fills gaps. The work is lining the sources up, choosing the
clearest wording per stretch by **script merge**, finding speakers by voice, and letting the owner
settle doubts **by ear**. An LLM reading and rewriting every window cost about USD 270 for six hours
of audio once; the script merge does the same in seconds. Keep LLMs to the one cheap reading step.

Scripts are in `scripts/` (each has a Usage docstring: read it, do not guess flags). Why each setting
is what it is: [references/lessons.md](references/lessons.md).

## 1. Gather (on the user's Mac)

- **Plaud:** pick recordings by date with the Plaud MCP `list_files`. `scripts/plaud-dump.mjs` saves
  file detail, transcript, notes and photo marks JSON per recording. Download each recording's audio
  with `curl` from the `presigned_url` in its `get_file.json` (the link expires; never commit it).
- **Plaud photos:** the marks JSON holds each photo's time, Plaud's caption and an OCR link, but not the
  image file. Ask the owner to save the photos from the Plaud app (e.g. to Downloads), then
  `scripts/match_photos.py` copies them into `photos/` paired with their marks by capture time.
- **Wispr Flow:** `scripts/gather_wispr.py` copies each meeting folder (audio + live + refined
  transcript) in the date range, read-only.
- **Backups:** search the Mac for other audio/video from those days (screen recordings, Voice Memos,
  Downloads). Extract audio with `ffmpeg -c:a copy`; never re-encode the originals.
- Never read transcript text into context here; the scripts move it.

Done when every recording of the date range is on disk with a manifest entry (source, path, sha256,
duration, start time with offset).

## 2. Store

Audio goes to a private audio repo (`scripts/build_audio_repo.py` splits files over 95 MB with
`ffmpeg -c copy -f segment` and writes `manifest.json`). Transcripts and raw source JSON go into the
project repo as `README.md, manifest.json, sources/, transcript/, notes/`. The project's `AGENTS.md`
or evidence README names both repos; when it names an evidence repo, transcripts go there, not into the
code repo. Write `meeting.json` from
`scripts/meeting.example.json`: sources, meetings (one wall-clock timeline each), and parts.

Done when both repos are pushed and the worker has a clone of each.

## 3. Run the pipeline on the worker

A Linux box with many cores, reached by ssh. First time: `scripts/setup_worker.sh`. Then start
`scripts/run_worker.sh` in tmux over ssh and watch for `WORK/DONE` or `WORK/FAILED` from a background
loop. Do not drive it through an LLM session on the worker; it needs none.

The run decodes, aligns every source to one clock, runs Whisper, embeds and clusters voices, script-
merges each window, assembles parts, and builds the speaker naming page plus coverage and weak-spot
notes. Copy results back, commit, push.

Done when `WORK/DONE` exists and every part has JSON + Markdown with `[HH:MM:SS]` stamps.

## 4. Names and doubts (the owner's ear)

1. Open the naming page (one clean clip per voice S1..Sn). The owner types names; apply them with
   `scripts/apply_speaker_names.py`. Two ids for one person: give both the same name.
2. Split topics: a cheap model (Haiku) reads the parts and writes `notes/topic-map-*.md` (time-ordered
   blocks, decisions, lines whose label looks wrong). Ask it for `HH:MM` blocks, not prose.
3. Doubt round: `scripts/make_doubts.py` builds a local page of short clips for the suspicious lines
   and unclear numbers. Clips carry content; skip fillers (อ๋อ, อืม, ครับ). Apply the answers.
4. Voice re-match: `scripts/relabel_by_anchors.py` on the worker, seeded with every line the owner
   confirmed. Check it with `scripts/make_group_check.py` (3 clips per moved group). Apply a group only
   when the owner's clips agree with it; mark the rest `speaker_unsure` (shown as `?`). Two or three
   rounds is enough.

Done when the owner has named every voice and each moved group was confirmed by ear.

## 5. Plaud upload (only when asked)

Read [references/plaud-upload.md](references/plaud-upload.md) first. `scripts/plaud_upload.py`: dry run,
owner reviews, then `--apply`. The owner signs in and supplies the token file; never type a password.

## Report

Lead with what is done and where (PR link, naming page, topic map). Then coverage (minutes covered by
1/2/3 sources), the weak spots worth listening to, and what is still `?`.
