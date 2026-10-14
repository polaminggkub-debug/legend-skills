#!/usr/bin/env bash
# Run the whole LLM-free transcript pipeline on the worker, stopping at the first error.
#
# Usage: MEETING_AUDIO=<audio folder> [MEETING_OUT=<project folder>] [MEETING_WORK=<scratch>] bash run_worker.sh
#   needs meeting.json (MEETING_CONFIG, default $MEETING_OUT/meeting.json), $MEETING_OUT/sources/ (plaud-dump.mjs and
#   gather_wispr.py output) and the audio + manifest.json in $MEETING_AUDIO; run setup_worker.sh once first.
#   Optional: ASR_WORKERS (default 12) x ASR_THREADS (default 8) should not exceed the CPU thread count;
#   EMB_THREADS (default 8) for speaker embeddings; MEETING_VENV (default ~/work/tools/meetings-venv).
# Steps: decode_audio levels align parse_sources run_asr [run_asr --alt] diarize_embed diarize_cluster
#        build_packets auto_merge assemble make_speaker_page coverage weak_spots
#   (timeline.py is a library imported by the later steps, not a step.)
# Log: $WORK/run.log (one line per step with its duration), per-step output in $WORK/logs/<step>.log.
# Ends with $WORK/DONE, or $WORK/FAILED naming the step that failed. Steps whose output exists resume
# (run_asr skips finished chunks, auto_merge skips finished windows).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export MEETING_OUT="${MEETING_OUT:-$PWD}"
: "${MEETING_AUDIO:?set MEETING_AUDIO to the folder with the original audio and manifest.json}"
export MEETING_WORK="${MEETING_WORK:-$HOME/work/tools/meetings-work}"
export PATH="$HOME/tools/bin:$HOME/.local/bin:$PATH"
VENV="${MEETING_VENV:-$HOME/work/tools/meetings-venv}"
[ -f "$VENV/bin/activate" ] || { echo "venv not found: $VENV (run setup_worker.sh)" >&2; exit 2; }
# shellcheck disable=SC1091
. "$VENV/bin/activate"

WORK="$MEETING_WORK"
mkdir -p "$WORK/logs" "$MEETING_OUT/notes"
rm -f "$WORK/DONE" "$WORK/FAILED"
LOG="$WORK/run.log"
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
trap 'echo "interrupted $(now)" > "$WORK/FAILED"; exit 130' INT TERM

step() {
  local name="$1"; shift
  local t0 rc
  t0=$(date +%s)
  echo "$(now) START $name" >> "$LOG"
  "$@" > "$WORK/logs/$name.log" 2>&1
  rc=$?
  echo "$(now) END   $name rc=$rc in $(( $(date +%s) - t0 )) s" >> "$LOG"
  if [ "$rc" -ne 0 ]; then
    { echo "step: $name"; echo "exit code: $rc"; echo "see: $WORK/logs/$name.log"; echo "time: $(now)"; } > "$WORK/FAILED"
    exit "$rc"
  fi
}

py() { python "$HERE/$1" "${@:2}"; }

step decode_audio py decode_audio.py
step levels py levels.py
step align py align.py
step parse_sources py parse_sources.py
step run_asr py run_asr.py --workers "${ASR_WORKERS:-12}" --threads "${ASR_THREADS:-8}"
# second recording pass only when meeting.json lists "asr.alt" stretches
if [ "$(python -c "import sys; sys.path.insert(0, '$HERE'); import config; print(len(config.CFG.get('asr', {}).get('alt', [])))")" -gt 0 ]; then
  step run_asr_alt py run_asr.py --alt --workers "${ASR_WORKERS:-12}" --threads "${ASR_THREADS:-8}"
fi
step diarize_embed py diarize_embed.py
step diarize_cluster py diarize_cluster.py
step build_packets py build_packets.py
step auto_merge py auto_merge.py
step assemble py assemble.py
step make_speaker_page py make_speaker_page.py
step coverage py coverage.py
step weak_spots py weak_spots.py

echo "finished $(now)" > "$WORK/DONE"
echo "$(now) DONE" >> "$LOG"
