<a id="case-L1"></a>

## L1 — Conduct Guard: PR ที่แก้จาก review หลายรอบจนกลายเป็น integration ที่ทดสอบได้

**ระดับหลักฐาน AI: A** · หลักฐานเฉพาะ contribution ที่เปิดเผยหรือมีร่องรอยลงมือ ไม่ยืนยันทุกบรรทัดหรือทุก commit · [ดูหลักฐาน](https://github.com/BerriAI/litellm/pull/40785#issuecomment-5640336188)

PR: [#40785](https://github.com/BerriAI/litellm/pull/40785), `feat(guardrails): add Conduct Guard integration with validated hooks and forwarded params`

### หลักฐานว่าเป็นงานที่ AI ขับเคลื่อน

GitHub API ระบุ `user.login = devin-ai-integration[bot]` และ opening comment ของ PR ประกาศว่า `Devin AI Engineer` จะช่วย PR นี้โดยอัตโนมัติ ทั้งการ address comments และดู CI failures ([opening comment](https://github.com/BerriAI/litellm/pull/40785#issuecomment-5640336188))

PR body มี [Devin session](https://app.devin.ai/sessions/7b76d7e3c19b4b6bb72e1ea1df5aeee3), ระบุผู้ขอคือ `@yucheng-berri`, และมี Cursor Bugbot summary ที่ผูกกับ final head SHA `0ded7b43d2f7...` ([PR body](https://github.com/BerriAI/litellm/pull/40785))

จาก 27 commit objects มี 9 commit ที่มี trailer `Co-Authored-By: Devin AI <158243242+devin-ai-integration[bot]@users.noreply.github.com>` ได้แก่:

- [`b5f7b58a1ac9`](https://github.com/BerriAI/litellm/commit/b5f7b58a1ac9875f219b17d33ef1b3ef3f0f3362) — validate event hooks, forward `tool_name`, แก้ test skip
- [`747dda483e4b`](https://github.com/BerriAI/litellm/commit/747dda483e4ba9c5eb676100cd56c77221c1d213) — ส่ง Responses API input ผ่าน bridge
- [`0f729bd767d3`](https://github.com/BerriAI/litellm/commit/0f729bd767d3631b056c31fc5460bebe0d94dbe6) — บันทึก decision ของ `apply_guardrail`
- [`9f9ec6871c94`](https://github.com/BerriAI/litellm/commit/9f9ec6871c946448b0344f3a9d23828e2f62d75a) — ย้าย bridge ไปเป็น injectable function
- [`97a45a4f65d9`](https://github.com/BerriAI/litellm/commit/97a45a4f65d9bbfae70d05cd73e83b39995b9011) — ส่ง tool-call-only turns ไป Conduct
- [`7ffde11054ba`](https://github.com/BerriAI/litellm/commit/7ffde11054bab40dcff9f159376896652a1ffd12) — บันทึก verdict ที่ไม่ block ลง standard guardrail information
- [`48c2fe18791e`](https://github.com/BerriAI/litellm/commit/48c2fe18791ec6f4e1f439f3db10c470c4ec8890) — เพิ่ม config model และ Admin UI
- [`ce090d069761`](https://github.com/BerriAI/litellm/commit/ce090d069761956270e212b88bbac6e04a968f78) — ส่ง `unreachable_fallback` ให้ plugin 0.2.5
- [`0ded7b43d2f7`](https://github.com/BerriAI/litellm/commit/0ded7b43d2f7af6be4489e183ee86ddd2ff0b1ce) — ปฏิเสธ plugin รุ่นเก่าที่กลืน kwarg นี้

นี่เป็นหลักฐาน authorship ที่ตรงกว่าการเห็นคำว่า Claude/Codex ในชื่อสาขา เพราะอยู่ใน commit trailer ของ commit ที่ถูก merge จริง แต่ commit author ของ 9 commits ที่มี trailer นี้คือ `yucheng` (บัญชี yucheng-berri) ตาม GitHub object จึงควรเรียกว่า **AI-assisted/agent-driven with human commit identity**, ไม่ใช่ข้อพิสูจน์ว่า Devin เป็นผู้เขียนทุกบรรทัด

### ขอบเขตและ acceptance criteria

ผู้เขียน PR แบ่งงานเป็น integration ที่มีขอบเขตชัดใน TL;DR และ user flow ก่อน/หลัง:

1. ลงทะเบียน `conduct` และ map config ไปยัง plugin kwargs; รองรับเฉพาะ `pre_call`, reject mode ที่ไม่มี hook จริงตอน config load
2. ตั้ง timeout default 8 วินาที และกำหนด `fail_open`/`fail_closed` เมื่อ service ติดต่อไม่ได้
3. แสดง install hint เมื่อ optional package ไม่มี และป้องกัน package 0.2.4 ที่รับ `**kwargs` แล้วทำให้ `fail_open` กลายเป็น `fail_closed`
4. แปลงข้อความของ `/v1/chat/completions`, `/v1/messages` และ `/v1/responses` เข้า Conduct bridge; ต้องไม่ปล่อย Responses `input` ว่าง
5. ส่ง `tool_name`; ตรวจ tool-call-only turns แม้ `texts` ว่าง
6. แปลง warning/advisory เป็น metadata มาตรฐาน (`guardrail_flagged`, verdict และ rule id) โดย request ยังเดินต่อเมื่อ verdict ไม่ block
7. สร้าง behavioral tests ที่รันได้โดยไม่ติดตั้ง package จริง, provider schema และ Admin UI card/preset
8. ทดสอบ before/after ด้วย real Postgres, 4 workers, real provider calls, Conduct service, unreachable endpoints, timeout, streaming, multipart, multi-turn, tool result, long prompt, concurrency และ UI

ตัว checklist ใน PR ระบุให้มี meaningful tests, scope แยกเป็นปัญหาเดียว, required CI/CD ผ่าน และ Greptile confidence อย่างน้อย 4/5 ก่อนขอ maintainer review ([checklist ใน PR](https://github.com/BerriAI/litellm/pull/40785)) ยังไม่ได้ตรวจ branch-protection settings จึงไม่ยืนยันว่าทุกรายการเป็น required gate ของระบบ ส่วนพฤติกรรมที่ถอดได้จาก body เป็น observable behavior: status code, error text, log metadata, startup behavior, provider schema และ UI state ไม่ใช่เพียง “เพิ่ม integration ให้เสร็จ”

### ลำดับ objection → response → code delta

ลำดับที่อ่านได้จาก review comments, commits และ timeline: review มาก่อน commit ที่แก้ประเด็นสอดคล้องกัน การเชื่อมเหตุและผลเป็นข้ออนุมานจากเวลา/เนื้อหา เว้นแต่มี reply ยืนยันโดยตรง; เวลา commit ไม่จำเป็นต้องตรงเวลา push

| เวลา/หลักฐาน | objection หรือการตัดสินใจ | code delta / การตอบ |
|---|---|---|
| 2026-09-11 20:39, [Greptile comment](https://github.com/BerriAI/litellm/pull/40785#discussion_r3993209769) | test ของ production plugin ถูก skip เพราะ package optional; CI อาจไม่เจอ constructor/hook mismatch | agent แย้งว่าการ pin package ที่ release ถี่เกินไปทำให้ baseline CI เปราะ; คง conditional real-package test และใช้ stand-in behavioral tests; Greptile ถอน concern ใน [reply](https://github.com/BerriAI/litellm/pull/40785#discussion_r3993236524) |
| 2026-09-11 20:45, [Devin review](https://github.com/BerriAI/litellm/pull/40785#discussion_r3993251914) | `/v1/responses` ส่ง `input` ไม่ถึง Conduct; plugin อ่านแต่ prompt/messages จึงตรวจเป็น empty prompt | เพิ่ม [`747dda483e4b`](https://github.com/BerriAI/litellm/commit/747dda483e4ba9c5eb676100cd56c77221c1d213) และต่อมา unified injectable bridge; final review reply บอกว่า bridge แปลง translated texts/structured messages เป็น messages payload แล้ว |
| 2026-09-11 21:29, [Greptile P1](https://github.com/BerriAI/litellm/pull/40785#discussion_r3993542362) | tool-call-only request มี structured messages แต่ texts ว่าง จึง return ก่อนตรวจและ bypass policy | เพิ่ม [`97a45a4f65d9`](https://github.com/BerriAI/litellm/commit/97a45a4f65d9bbfae70d05cd73e83b39995b9011) ให้ bridge ส่ง turn เหล่านี้ไป Conduct และเพิ่ม config-load/registry coverage |
| 2026-09-11 21:29, [Greptile P2](https://github.com/BerriAI/litellm/pull/40785#discussion_r3993542370) | test ตรวจ implementation structure แทน behavior | agent ปรับ test wiring ให้ผ่าน config load/behavior path; PR body ระบุว่า tests inject recording check coroutine |
| 2026-09-11 21:29, [Greptile P2](https://github.com/BerriAI/litellm/pull/40785#discussion_r3993542375) | `HTTPException` ใน test ถูกมองว่าละเมิด proxy-only dependency rule | agent ชี้ว่าไฟล์อยู่ใต้ `tests/test_litellm/proxy` และพี่น้อง 35 ไฟล์ทำแบบเดียวกัน; Greptile ถอน concern ใน [reply](https://github.com/BerriAI/litellm/pull/40785#discussion_r3993672253) |
| 2026-09-11 22:14, [Devin review](https://github.com/BerriAI/litellm/pull/40785#discussion_r3993806947) | warning/advisory ถูกทิ้ง ทำให้ log เห็นแค่ allow/success; `only_scan_new_messages` ไม่ถูกส่งต่อ | เพิ่ม [`7ffde11054ba`](https://github.com/BerriAI/litellm/commit/7ffde11054bab40dcff9f159376896652a1ffd12) ให้ warning ลง standard guardrail info; เรื่อง incremental scanning ถูก mark standing down เพราะ hook อื่นยังไม่ใช้ flag นี้ และบันทึกเป็น caveat |
| 2026-09-12 00:49–00:57, package contract | plugin 0.2.5 เปลี่ยนชื่อ `fail_mode` เป็น `unreachable_fallback`; รุ่น 0.2.4 กลืน kwarg ผ่าน `**kwargs` | [`ce090d069761`](https://github.com/BerriAI/litellm/commit/ce090d069761956270e212b88bbac6e04a968f78) ส่ง kwarg ใหม่ และ [`0ded7b43d2f7`](https://github.com/BerriAI/litellm/commit/0ded7b43d2f7af6be4489e183ee86ddd2ff0b1ce) ทำ import-time guard ให้รุ่นเก่าล้มเหลวชัดเจน |

จากหลักฐานนี้ สังเคราะห์วงจรได้เป็น review → ระบุ production scenario → แก้โค้ด/แก้ test → rerun bot review → ค่อยส่ง maintainer review โดยใช้ commit SHA ที่มีในหลักฐานเป็นจุดอ้างอิง

### หลักฐานการพิสูจน์ก่อน merge

- PR body รายงาน final head `0ded7b43d2f7` พร้อม **92 CI checks green**, Greptile confidence 5/5 และ Cursor Bugbot ไม่พบ issue ใหม่; body ระบุชัดว่า Devin Review ครั้งล่าสุดอยู่ที่ `7ffde11054ba` จึงไม่นับเป็น pass บน tip
- GitHub API ที่ดึงจาก final head คืน **94 check-runs หลังเรียกครบ: 93 `completed/success` และ 1 `skipped` (stage-mirror E2E)** ทั้ง 94 รายการเสร็จก่อน merge 17:04:55Z และ commit status context 1 รายการเป็น `success` ก่อน merge ([check-runs API](https://api.github.com/repos/BerriAI/litellm/commits/0ded7b43d2f7af6be4489e183ee86ddd2ff0b1ce/check-runs))
- Codecov comment รายงาน patch coverage 90.10989% ในช่วงแรก; ผู้เขียนทำ fix/review ต่อจน final PR body อ้าง 92 CI checks green
- CodSpeed รายงาน 31 untouched benchmarks และไม่เห็น performance regression ([CodSpeed comment](https://github.com/BerriAI/litellm/pull/40785#issuecomment-5640362052))
- ผู้เขียนอ้าง real-provider matrix: allowed/blocked chat, streaming, Responses string/list input, Messages, warning audit trail, tool calls, timeout/fallback, 4-worker concurrency และ Admin UI; matrix นี้อยู่ใน PR body แต่ไม่มี log artifact ครบให้ตรวจซ้ำจาก GitHub API จึงติดป้าย **claimed by author**
- maintainer review สุดท้ายเป็น `APPROVED` โดย `ryan-crabbe-berri` ที่ commit `0ded7b43d2f7` เวลา 17:04:42Z; merge โดย `yucheng-berri` เวลา 17:04:55Z เป็น merge commit [`e4f59a953cac`](https://github.com/BerriAI/litellm/commit/e4f59a953cac0543515449d8485a94e7393c2636)

### หลักฐานนับได้ของเคส A

| สิ่งที่นับ | จำนวน | ความหมาย |
|---|---:|---|
| commit objects | 27 | มีการแตกงาน/แก้ต่อเนื่องจริง |
| commit ที่มี Devin co-author trailer | 9 | สัญญาณ authorship โดยตรง |
| changed files | 10 | ขอบเขต implementation + tests/UI |
| additions/deletions | 693 / 0 | ขนาด diff ของ integration |
| issue comments | 16 | bot controls, review triggers, coverage, follow-up |
| review records | 17 | Devin Review, Greptile, Cursor Bugbot, human approval |
| inline review comments | 16 | objections, fixes, dismissals/standing-down |
| timeline events | 71 | commit/review/request/merge chronology |
| final head check-runs | 94 | 93 success / 1 skipped ณ snapshot; เรียกครบตาม total_count |
| final merge SHA | `e4f59a953cac0543515449d8485a94e7393c2636` | หลักฐานว่า merge แล้ว |

<a id="case-L2"></a>

## L2 — Post-call spend batching: performance งานใหญ่ที่ถูกแบ่งเป็น stacked scope และ gate หลายชั้น

**ระดับหลักฐาน AI: A** · หลักฐานเฉพาะ contribution ที่เปิดเผยหรือมีร่องรอยลงมือ ไม่ยืนยันทุกบรรทัดหรือทุก commit · [ดูหลักฐาน](https://github.com/BerriAI/litellm/pull/40841#issuecomment-5644537226)

PR: [#40841](https://github.com/BerriAI/litellm/pull/40841), `perf(proxy): one MGET and one pipeline for post-call spend counters, no team/user/org refetch on the response path`

### หลักฐานว่าเป็นงานที่ AI ขับเคลื่อน

PR actor คือ `devin-ai-integration[bot]`; opening comment ระบุ Devin AI Engineer และ auto-monitoring แบบเดียวกับเคส A ([opening comment](https://github.com/BerriAI/litellm/pull/40841#issuecomment-5644537226)) PR body มี [Devin session](https://app.devin.ai/sessions/bbe614d754bf4e779ed46e0d131c407e), requested by `@yassin-berriai`

จาก 20 commits มี **18 commit ที่มี `Co-Authored-By: Devin AI`**; commit author ใน GitHub object คือ `yassin` และ branch มี merge commits จากการ sync staging ดังนั้นจัดเป็น agent-driven pair work ที่มีคนรับผิดชอบ commit identity ชัดเจน

### การแตก scope และ acceptance criteria

PR body ระบุว่าเป็นงานต่อจาก #40834 ซึ่งทำ auth phase โดย API base SHA สอดคล้องกับที่ body อ้าง แต่ไม่ได้ตาม issue/review/merge ของ #40834 แยกต่างหาก; PR นี้รับผิดชอบเฉพาะ post-response path และติดตาม Linear ticket `LIT-7644` ภายใต้ epic `LIT-7478`:

1. ใช้ task-local `SpendCounterBatch` ให้ warm checks, reservation reconcile และ reseed แชร์ MGET เดียว
2. รวม `INCRBYFLOAT` กับ TTL/EXPIRE ใน pipeline เดียว และ record ผลลัพธ์ไว้ใน batch
3. เมื่อ pipeline ล้มเหลว invalidate counter ที่แตะทุกตัวก่อนโยน error
4. carry immutable team/user/org budget snapshots จาก auth ไป request metadata เพื่อไม่ต้อง query Postgres ซ้ำใน Prometheus path
5. เก็บ fallback เดิมเมื่อ snapshot หาย, custom auth, unauthenticated route หรือ Redis error
6. รักษา denied-request status/body และ public signature ของ `RedisCache.async_increment`
7. ห้ามขยาย scope ไป redesign rate limiter; PR body บันทึกงานที่เหลือเป็น PR (c) candidate แทน

มี user flow before/after พร้อมตัวเลข observable: Redis GET/round trips, Postgres SELECTs, p95, status/body และ provider path นอกจากนี้ checklist บังคับ meaningful tests, scope เป็นปัญหาเดียว, required CI/CD และ Greptile confidence >=4/5

### ลำดับ objection → response → code delta

- สาขาเริ่มจาก auth phase แล้วถูก stack/squash เข้ากับ staging; PR body บอกว่า diff ที่ tip `b4f81a7262` byte-identical กับ measurement tip `0626401197` เพื่อป้องกัน base เปลี่ยนแล้วผลวัดไม่ตรงกับโค้ด
- Greptile review ที่ [`6012071b403f`](https://github.com/BerriAI/litellm/commit/6012071b403fb9ef9f2a8f18ad682770f998220f) ชี้ `acme-org` เป็นชื่อ customer ใน test; ต่อมามี commit แก้ด้วย [`f7e03fb90055`](https://github.com/BerriAI/litellm/commit/f7e03fb900554be4318a3b4584ebbf2ad6e6b04c) เป็น neutral organization alias
- Greptile review ที่ [`a84c4ccb63c7`](https://github.com/BerriAI/litellm/commit/a84c4ccb63c7e2df3307c3509856cece3e65319c) ชี้ `_EntryAdjustment.entry` เป็น bare `dict`; ต่อมามี commit แก้ด้วย [`df2a3056892a`](https://github.com/BerriAI/litellm/commit/df2a3056892ab3ddc493625ea5b39855fc024fcb) ให้ type ชัด
- Cursor Bugbot รันซ้ำหลาย head และ mark report เก่าว่า stale; review ที่ `b4f81a7262` ระบุว่าไม่พบ issue ใหม่ แต่ submitted เวลา 16:06:51Z หลัง merge 16:05:51Z จึงเป็น post-merge recheck ([final review](https://github.com/BerriAI/litellm/pull/40841#pullrequestreview-5187056347))
- Codecov รายงาน patch coverage 96.29630% และชี้ 9 missing lines; ผู้เขียนยังคงทดสอบต่อ ไม่ได้ใช้ coverage เป็น binary proof เดียว
- maintainer `yassin-berriai` approve ที่ `b4f81a7262`; auto-squash เปิดก่อน merge และ merge เวลา 16:05:51Z เป็น [`1c61c2606e36`](https://github.com/BerriAI/litellm/commit/1c61c2606e36061db4fce10f7bb94745d76bc84f)

### หลักฐานการพิสูจน์ก่อน merge

สิ่งที่ผู้เขียน **อ้างใน PR body** ที่ tip measurement `0626401197`:

- `make check` ผ่าน: ruff, strict/type discipline, basedpyright, test-quality, OpenAPI/dashboard sync
- มีรายงานคนละชุด: checklist ระบุ 1,926 passed ในเก้าไฟล์ ขณะที่ส่วน Tests and gates ระบุ ten touched files ที่ measurement tip เป็น 736 passed / 1 failed โดยผู้เขียนอ้างว่า failure เกิดซ้ำที่ merge base และไฟล์เดี่ยวผ่าน 76/76; ตัวเลขเหล่านี้มี scope ต่างกัน จึงไม่นำมาบวกรวม
- 82 checks passed, 0 failed, 1 skipped; codecov patch 96.29% เทียบ target 80.77%; Buildkite e2e passed; CodSpeed ไม่รันเพราะไฟล์ไม่อยู่ใน benchmark set
- mutation check 13 mutants ถูก kill หลังเพิ่ม tests ที่ `189c563bac`; แสดงว่าทีมใช้ mutation evidence เพื่อกัน test ที่ผ่านแต่ไม่จับ regression
- `/qa` เป็น two-pod real-provider run (OpenAI/Anthropic), denied body byte-identical และ Redis/Postgres command counts เปลี่ยนตามที่ออกแบบ

สิ่งที่ **GitHub API สังเกตได้โดยตรง** จาก final head `b4f81a7262`:

- ณ snapshot มี 86 check-runs หลังเรียกครบ: 85 `success` และ 1 `skipped` แต่ก่อน merge เสร็จเพียง 84 รายการ (83 success + 1 skipped); อีก 2 รายการคือ Codecov upload เวลา 16:06:03Z และ Cursor Bugbot เวลา 16:06:52Z เสร็จหลัง merge 16:05:51Z ส่วน commit status contexts 2 รายการเป็น success ณ snapshot โดย codecov/patch อัปเดต 16:08:53Z หลัง merge จึงไม่นับสถานะสุดท้ายทั้งหมดเป็นหลักฐานก่อนรับงาน
- CodSpeed check/comment รายงาน 31 untouched benchmarks และ “will not alter performance” ([comment](https://github.com/BerriAI/litellm/pull/40841#issuecomment-5646996787))
- มี human approval, auto-merge event และ merge SHA ตาม timeline

ข้อจำกัด: log ของ `make check`, ชุด tests ที่อ้าง, mutation run, real-provider two-pod QA และ `/live-pr-risk` ไม่ได้ถูกแนบเป็น artifact ที่อ่านได้ครบใน API ที่เก็บ จึงต้องอ้างว่าเป็น author-reported evidence; check-runs ที่ดึงได้เป็นส่วนหนึ่งของภาพ CI และไม่ควรนับเป็น test case 82 รายการ

### หลักฐานนับได้ของเคส B

| สิ่งที่นับ | จำนวน | ความหมาย |
|---|---:|---|
| commit objects | 20 | งาน auth + post-call ถูกแยกเป็นชุดย่อยและ sync staging |
| commit ที่มี Devin co-author trailer | 18 | สัญญาณ authorship โดยตรงที่แรงมาก |
| changed files | 21 | ข้าม proxy, caching, budget state, Prometheus และ tests |
| additions/deletions | 1,368 / 157 | ขนาด diff ของ performance refactor |
| issue comments | 17 | bot control, review triggers, coverage, CodSpeed |
| review records | 8 | Greptile, Cursor และ human approval |
| inline review comments | 2 | customer-name และ typing concerns; ทั้งคู่มี code response |
| timeline events | 65 | stacked/base update, rerun review, auto-merge, merge |
| final head check-runs | 86 | 85 success / 1 skipped ณ snapshot; 84 เสร็จก่อน merge และ 2 หลัง merge |
| final merge SHA | `1c61c2606e36061db4fce10f7bb94745d76bc84f` | หลักฐานว่า merge แล้ว |

