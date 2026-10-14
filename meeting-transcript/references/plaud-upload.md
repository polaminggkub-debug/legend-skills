# Putting a transcript back into Plaud

Read this before running `scripts/plaud_upload.py`. The goal is to change what Plaud shows while
leaving Plaud's own raw transcript untouched, and to prove both afterwards.

## What Plaud stores

`GET {api_base}/file/detail/{file_id}` returns `data.content_list`. Two entries matter:

| `data_type` | What it is | Rule |
|---|---|---|
| `transaction` | raw transcript from Plaud's own ASR | **never** changes |
| `transaction_polish` | the transcript the app shows | the only thing we write |

Each has a `data_id` and a signed `data_link` to a JSON array of segments
(`start_time`, `end_time` in ms from the recording start, `content`, `speaker`, sometimes more keys).
A recording that Plaud never transcribed (no paid minutes used on it) has neither entry. There is no
known endpoint that creates one, so such a recording cannot receive a transcript; keep it in the repo.

## The one write path

```text
POST {api_base}/ai/update_source_info
{"file_id": "...", "source_type": "transaction_polish", "source_id": "<its data_id>",
 "source_content": "<JSON.stringify(segments)>"}
```

`PATCH /file/{file_id}` with `trans_result` is unsafe: tested live, it also overwrote the raw source.
Re-transcription endpoints are out of scope.

## Getting a session (the owner does this)

1. The owner signs in at the Plaud web app in their own browser. Never type their password.
2. In DevTools → Network, open any request to `api*.plaud.ai` and copy the `authorization` bearer
   token, the API host, and `x-pld-user` / `x-device-id` / `x-pld-tag` when present.
3. Save them as `auth.json` with mode 0600 outside every repo:
   `{"token": "...", "api_base": "https://api.plaud.ai", "headers": {"x-pld-user": "..."}}`.
   A `-302 user region mismatch` reply is handled by the script (it switches to `data.domains.api`).
4. Delete `auth.json` when the run ends. Never print, log or commit the token or signed links.

## Run

```bash
python scripts/plaud_upload.py snapshot --file-id ID --auth auth.json --out plaud-backup/ID
python scripts/plaud_upload.py speakers --file-id ID --auth auth.json --out plaud-backup/ID --map map.json
#   review plaud-backup/ID/report.json and target.transaction_polish.json, then:
python scripts/plaud_upload.py speakers ... --apply
```

- `speakers` relabels only (`{"Speaker 1": "Name"}`); every other field stays identical. This is the
  path proven live (346 segment relabels, raw unchanged).
- `replace` writes our merged text (same-speaker lines joined into ≤ 60 s paragraphs, times shifted to
  the recording start given by `--plaud-start`). Not yet proven live: try it on one recording first.
- `--apply` refuses to run unless a dry run in the same `--out` was made first and Plaud plus the
  target still hash the same as in that reviewed dry run.

## Done means

The script's read after write shows polished == target and raw == the snapshot (SHA-256 of the
compact JSON, the same bytes as `JSON.stringify`). A successful HTTP reply alone is not done. On any
mismatch it restores polished (and raw if it moved) and reports `ROLLED_BACK` or
`ROLLBACK_UNVERIFIED`; never call a state restored without a matching read. Keep `plaud-backup/ID/`
(before files, target, report) next to the transcripts.
