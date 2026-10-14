# Lessons from the first run

What was learned building Thai meeting transcripts (timestamps + speakers) from a Plaud recorder, the Wispr Flow
Mac app and backup audio. Numbers are from that run; the reasons are what to reuse. The pipeline runs
on a CPU worker without a GPU (about 6 h of audio); the Mac only gathers files and shows pages to the owner.

## Sources and which to trust

- Accuracy order for text: Wispr refined > Plaud transcript > Wispr live > Whisper Thai fine-tune >
  Whisper large-v3. Wispr refined was the strongest text source in every spot check. `auto_merge.py` uses
  exactly this order and uses Whisper-th only to fill gaps no other source covers.
- Whisper large-v3 drops much conversational Thai. Keep it only as a secondary hypothesis, mainly for English
  and technical words.
- Plaud `transaction_polish` was identical to `transaction` apart from broken UTF-8 characters: not a separate
  source. A Plaud file can have no transcript at all (only photo marks); keep the marks as markers.
- Plaud photo marks carry an AI caption of the photo. Show them as markers, never as speech.
- A Plaud file may be recorded by the Plaud desktop app instead of the device (different codec, 48 kHz Opus
  instead of 16 kHz MP3, and a byte-identical copy in the app folder). Compare sha256 before counting a
  "second source".
- Wispr audio is stereo: channel 1 = microphone, channel 2 = system audio (silent except when something plays
  on the Mac). Use channel 1 for ASR, alignment and clips. A voice that only exists on channel 2 (a voice
  assistant, a video call) is missed by Whisper/diarization on channel 1; the Wispr text has it.
- Clearest audio per stretch is the Wispr mic channel: median SNR 32-38 dB vs 21-29 dB for the Plaud and about
  11 dB for a screen-recorder backup. Use Plaud/backup only where Wispr is missing or zero-filled.
- Wispr loses audio across pauses and can zero-fill (minutes of digital zero, plus a lost chunk). Plaud
  desktop drops ~0.3 s chunks every few minutes. Neither shows in the file length.
- A recorder on the table (far field) is much worse than a mic worn by the speaker; use it as a witness for
  timing and as a text source only where nothing else exists.

## Clock alignment

- Reference clock = the Mac clock (it is NTP-synced): Wispr `startEpochMs`/`startRecordingMs` in
  `live.ndjson`, backup file names. Shift every other recording onto it by cross-correlation.
- One offset per file is wrong. Use dense probes every 60 s (log-energy envelope cross-correlation +-25 s, refined
  by GCC-PHAT +-60 ms) and a piecewise-linear map between probes. Drop a probe that is a lone outlier against
  both neighbours or has a weak peak (ratio < 2).
- Paused/resumed Wispr recordings (markers in `live.ndjson`) need a piecewise audio->clock map; markers lead the
  audio by ~0.2 s.
- Wispr zero-fill: dense probes show the lost seconds (about 13 s over a long break, then a drift of a few
  hundred ppm). Fix it with a jump plus a rate chosen so the next Wispr recording's own start lines up (`gap_fix`),
  and check that the last real audio maps just before the recording's own pause marker.
- A recording with no overlapping Mac recording borrows offset and average drift from a recording by the same
  device (`borrow_offset`); expect a few seconds of error and say so in coverage.
- Zero-filled stretches: the map is linear there, so real-audio islands inside them can be seconds off. Re-time
  such a stretch by hand against the other recording if it matters.
- Screen-recorder file names (default naming) match the Mac clock to about 2 s; still measure them.

## Whisper Thai settings

- Thai text has a zlib compression ratio of ~2.55, above the default fallback limit 2.4, so default settings
  re-decoded almost every window (>14 min of compute per 3 min of audio). Final: BatchedInferencePipeline,
  Silero VAD chunks <= 15 s, beam 5, temperature 0, no fallback (`compression_ratio_threshold=None`,
  `log_prob_threshold=None`), word timestamps.
- The Thai fine-tune loops ("word word word ...") on 30 s windows. Chunks <= 15 s fix it.
- Models: Systran faster-whisper-large-v3 and biodatlab/whisper-th-large-v3-combined converted to CTranslate2
  float16 (run as int8 on CPU). The Pathumma Thai model is only for re-checking weak spots.
- Parallelism used: 12 worker processes x 8 threads on 96 threads. Cut each stretch into ~5 min chunks at the quietest second within +-20 s; finished chunks are skipped on re-run.
- Run a second Thai pass on a second recording only where every text source came from the same microphone.

## Diarization

- ECAPA (speechbrain/spkrec-ecapa-voxceleb) on Silero-VAD speech, windows 1.5 s with hop 0.75 s. Shorter
  windows are too noisy.
- Per recording: average-linkage cosine clustering with an adaptive cut (clusters >= 25 s covering >= 70-85 % of
  windows), k-means refinement, merge centroids with cosine >= 0.75. On the best recording this gave 4 voices that
  matched Plaud's own speakers at 52-71 %. Wispr's own W1/W2 labels carry no speaker information.
- Cross-recording links, strongest first: same-moment overlap tables (Plaud vs Wispr), then voice similarity
  (mutual best match, cosine >= 0.75). Never join two clusters of one recording (cannot-link). Linking is
  deliberately conservative: one person split into two ids is fixed by naming both the same; two people in one
  id cannot be fixed by naming.
- Global ids S1..Sn by speaking time, pinned in `ids.json` so a re-run never renumbers people.
- Known weak spots: a far-field recorder forms one "hub" cluster similar (cos 0.73-0.81) to every voice, so leave
  it out of diarization; a small in-between cluster close to two or more voices is overlap/mixed speech, so dissolve
  it into the nearest voice; fast question/answer exchanges get one id (sub-second blips); two presenters can look
  alike; Wispr system-audio voices have no turns (use S0 / a fallback clip for the name page).

## Merge: script, not LLM

- An LLM merge of ~6 h of audio (one agent per ~10 min window) cost about USD 270 and also hit rate limits, output
  limits and false safeguard stops. `build_packets.py` + `auto_merge.py` do it in seconds and are repeatable.
- Text priority per window: Wispr refined first, then Plaud, Wispr live, Whisper-th to fill gaps; drop a lower
  source segment when half of it is already covered. Speaker = diarization id with the most time inside the segment.
- Confidence = how closely other sources heard the same words in the same seconds (difflib ratio): >= 0.6 high,
  >= 0.35 medium, else low (the other sources' text is kept in `note`).
- Cut windows (~10 min) in the longest pause near each boundary; check joins for duplicates (`join_check.py`,
  duplicate check in `assemble.py`).
- Keep a word every source agrees on; mark uncertain words `[?]` and unintelligible speech `[ไม่ได้ยิน]` rather than
  guessing. Post-merge fixes go in `corrections` / `aliases` in meeting.json, never as silent edits.

## Owner in the loop (2-3 rounds)

1. Name page: `make_speaker_page.py` cuts the cleanest 6-12 s single-speaker clip per id (plus up to two from other
   meetings) and a name box; `apply_speaker_names.py names.json` writes the names and re-renders. Naming two
   ids the same merges them.
2. Doubt clips: `make_doubts.py` for lines whose speaker label looks wrong and for amounts/numbers; the owner answers
   by ear. Skip filler clips (< 12 characters after Thai fillers, or < 3 s): nothing to decide.
3. Anchor re-match: the owner's confirmed lines are anchors; `relabel_by_anchors.py` re-decides doubtful ids by
   seeded k-means over per-segment ECAPA embeddings (a segment moves only if the new id wins by cosine 0.05) and
   prints a leave-one-out check. `make_group_check.py` samples each group of moves for a final by-ear check.
   Repeat 2-3 rounds until the answers stop changing.
4. Topic split: cut a recording into parts at topic changes (a pause of about a minute, a new group of people
   arriving) and label parts by topic folder.

## Practical

- Everything resumable: decode, ASR chunks, merge windows. Keep decoded WAVs, ASR output and embeddings in the work
  folder, not in the repo; raw audio and scans never leave the owner's machine.
- Log every step with its duration; write DONE or FAILED so a restarted session can resume.
- Output of a first full run is a draft: the by-ear rounds above are part of the method, not an extra.
