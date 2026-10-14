#!/usr/bin/env bash
# One-time (idempotent) setup of the transcript worker: venv, Python packages, models, ffmpeg.
#
# Usage: bash setup_worker.sh        (re-running skips whatever is already in place)
#   MEETING_VENV     venv folder (default ~/work/tools/meetings-venv), Python 3.11 made by uv
#   MEETING_MODELS   model folder (default ~/work/tools/models)
#   MEETING_WORK     scratch folder (default ~/work/tools/meetings-work); the speaker model is cached in sb-ecapa/
#   WITH_PATHUMMA=1  also convert the Pathumma Thai model (only used to re-check weak spots: run_asr.py --only pt)
# Installs: torch + torchaudio (CPU), faster-whisper, ctranslate2, speechbrain, soundfile, pythainlp, numpy, scipy,
#   transformers (for the model converter). scikit-learn is not needed (no script imports it).
# Models: Systran/faster-whisper-large-v3 -> large-v3-ct2; biodatlab/whisper-th-large-v3-combined converted to
#   CTranslate2 float16 -> biodatlab-th-combined-ct2 (run as int8); speechbrain/spkrec-ecapa-voxceleb -> WORK/sb-ecapa.
# ffmpeg/ffprobe: if missing, installed with apt when sudo works without a password, else a static build
#   goes to ~/tools/bin (run_worker.sh puts that folder on PATH).
set -euo pipefail

VENV="${MEETING_VENV:-$HOME/work/tools/meetings-venv}"
MODELS="${MEETING_MODELS:-$HOME/work/tools/models}"
WORK="${MEETING_WORK:-$HOME/work/tools/meetings-work}"
BIN="$HOME/tools/bin"
export PATH="$BIN:$HOME/.local/bin:$PATH"
mkdir -p "$MODELS" "$WORK" "$BIN"
log() { echo "[setup] $*"; }

# --- uv ---
if ! command -v uv > /dev/null; then
  log "installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# --- ffmpeg / ffprobe ---
if ! command -v ffmpeg > /dev/null || ! command -v ffprobe > /dev/null; then
  if sudo -n true 2> /dev/null; then
    log "installing ffmpeg with apt"
    sudo apt-get update -y && sudo apt-get install -y ffmpeg
  else
    case "$(uname -m)" in
      x86_64) arch=amd64 ;;
      aarch64 | arm64) arch=arm64 ;;
      *) echo "no static ffmpeg for $(uname -m)" >&2; exit 1 ;;
    esac
    log "no sudo: installing a static ffmpeg into $BIN"
    tmp="$(mktemp -d)"
    curl -L --fail -o "$tmp/ffmpeg.tar.xz" "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-${arch}-static.tar.xz"
    tar -xf "$tmp/ffmpeg.tar.xz" -C "$tmp"
    cp "$tmp"/ffmpeg-*-static/ffmpeg "$tmp"/ffmpeg-*-static/ffprobe "$BIN/"
    rm -rf "$tmp"
  fi
fi
log "ffmpeg: $(ffmpeg -version | head -1)"

# --- venv + packages ---
if [ ! -x "$VENV/bin/python" ]; then
  log "creating venv $VENV (Python 3.11)"
  mkdir -p "$(dirname "$VENV")"
  uv venv --python 3.11 "$VENV"
fi
PY="$VENV/bin/python"
uv pip install --python "$PY" torch torchaudio --index-url https://download.pytorch.org/whl/cpu
uv pip install --python "$PY" faster-whisper ctranslate2 speechbrain soundfile pythainlp numpy scipy transformers

# --- models ---
if [ ! -f "$MODELS/large-v3-ct2/model.bin" ]; then
  log "downloading Systran/faster-whisper-large-v3"
  "$PY" -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-large-v3', local_dir='$MODELS/large-v3-ct2')"
fi

convert() {  # convert <hf repo> <folder name>: CTranslate2 float16 conversion
  local repo="$1" dir="$MODELS/$2"
  [ -f "$dir/model.bin" ] && return 0
  log "converting $repo -> $dir"
  rm -rf "$dir"
  "$VENV/bin/ct2-transformers-converter" --model "$repo" --output_dir "$dir" \
    --copy_files tokenizer.json preprocessor_config.json --quantization float16 \
    || { rm -rf "$dir"; "$VENV/bin/ct2-transformers-converter" --model "$repo" --output_dir "$dir" --quantization float16; }
}
convert biodatlab/whisper-th-large-v3-combined biodatlab-th-combined-ct2
[ "${WITH_PATHUMMA:-0}" = 1 ] && convert nectec/Pathumma-whisper-th-large-v3 pathumma-th-ct2

if [ ! -f "$WORK/sb-ecapa/hyperparams.yaml" ]; then
  log "downloading speechbrain/spkrec-ecapa-voxceleb"
  "$PY" -c "
from speechbrain.inference.speaker import EncoderClassifier
EncoderClassifier.from_hparams(source='speechbrain/spkrec-ecapa-voxceleb', savedir='$WORK/sb-ecapa', run_opts={'device': 'cpu'})"
fi

log "done: venv $VENV, models $MODELS"
