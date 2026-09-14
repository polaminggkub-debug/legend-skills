<a id="case-C1"></a>

## C1 — Cline #13968: stream ซ้ำและหายหลัง sidecar เปลี่ยน

**ระดับหลักฐาน AI: B** · หลักฐานเฉพาะ contribution ที่เปิดเผยหรือมีร่องรอยลงมือ ไม่ยืนยันทุกบรรทัดหรือทุก commit · [ดูหลักฐาน](https://github.com/cline/cline/pull/13968)

PR: [cline/cline#13968](https://github.com/cline/cline/pull/13968)  
สร้าง 2026-09-08 22:28:46Z โดย saoudrizwan; 5 commits, 8 files, +438/-2; merge 23:04:15Z โดย saoudrizwan ที่ [62ba6539](https://github.com/cline/cline/commit/62ba65397fca8d583540319fa574a62d1ac7d498)

### หลักฐาน AI

PR body ลงท้าย [Generated with Claude Code และ Claude session](https://github.com/cline/cline/pull/13968) โดยตรง และ commit แกนหลักมี Claude Opus 5 (1M context) เป็น co-author: [f32bf5f](https://github.com/cline/cline/commit/f32bf5f97ef7328021857365e31bc3de5ff3a463) เวลา 22:25:02Z, [b6486204](https://github.com/cline/cline/commit/b6486204ef2845daa085035fb7ffa1c7043f3b77) เวลา 22:25:13Z, [5ec58c1](https://github.com/cline/cline/commit/5ec58c1232f2f5036748329ae4734fa0d501495c) เวลา 22:32:43Z และ [9337b4e](https://github.com/cline/cline/commit/9337b4ebdb5ebaa431848c77ec8a57b2efc7311f) เวลา 22:37:58Z

### เป้าหมายและ acceptance criteria

ผู้ใช้เห็น text ใน live view ซ้ำ และ message/tool row หายระหว่าง turn แต่กลับมาถูกต้องเมื่อสลับ task หรือรอ turn จบ เจ้าของ PR แยก root cause เป็นสองเรื่อง: core subscription กับ hub observer แปล event เดียวกันเข้า emitChunk พร้อมกัน และ webview เก็บ high-water index ไว้ขณะ sidecar ใหม่เริ่ม index จาก 1

Acceptance ที่เขียนไว้คือ:

- core pipe เป็นแหล่งหลัก; observer ถูก suppress ขณะ core active และ takeover ได้เมื่อ core เงียบ
- stamp chunk ด้วย boot id; boot เปลี่ยนแล้ว rebase index แต่ replay จาก process เดิมยังถูก drop
- มี tests สำหรับ dual-pipe, observer-only, takeover, isolation, local chunk, sidecar restart และ replay
- เปลี่ยนเฉพาะ desktop sidecar/webview; ไม่แตะ SDK/CLI

### Feedback → response → patch

| เวลา | actor | เหตุการณ์ |
|---|---|---|
| 22:25:02Z | saoudrizwan + Claude | [f32bf5f](https://github.com/cline/cline/commit/f32bf5f97ef7328021857365e31bc3de5ff3a463) ใช้ symmetric five-second ownership lease |
| 22:25:13Z | saoudrizwan + Claude | [b6486204](https://github.com/cline/cline/commit/b6486204ef2845daa085035fb7ffa1c7043f3b77) เพิ่ม boot-id stamping |
| 22:32:33Z | greptile-apps[bot] | [P1 replay](https://github.com/cline/cline/pull/13968#discussion_r3962858573): observer reconnect/replay อาจ reclaim ownership |
| 22:32:43Z | saoudrizwan + Claude | [5ec58c1](https://github.com/cline/cline/commit/5ec58c1232f2f5036748329ae4734fa0d501495c) ลบ symmetric ownership และ hardcoded six-stream list; core event เป็นหลักฐานว่า core subscription มีอยู่ |
| 22:35:55Z | greptile-apps[bot] | [P1 liveness](https://github.com/cline/cline/pull/13968#discussion_r3962882599): status/queue event อาจ mute observer content ถ้า core หยุด |
| 22:37:58Z | saoudrizwan + Claude | [9337b4e](https://github.com/cline/cline/commit/9337b4ebdb5ebaa431848c77ec8a57b2efc7311f) บันทึก fan-out ordering; content-only marking จะ duplicate first delta |
| 22:39:34Z | saoudrizwan | [ตอบ replay](https://github.com/cline/cline/pull/13968#discussion_r3962903690): finding จับ design เก่าที่ถูกลบ; event identity ต้องแก้ระดับ hub/SDK นอก scope |
| 22:39:43Z | saoudrizwan | [ตอบ liveness](https://github.com/cline/cline/pull/13968#discussion_r3962905078): ยอมรับ gap แต่ bounded และ canonical reconciliation ซ่อมตอนจบ turn |
| 22:40:13Z | Greptile | [ถอน finding](https://github.com/cline/cline/pull/13968#discussion_r3962909424) หลังเห็น ordering |
| 22:56:12Z | saoudrizwan | [controlled reproduction](https://github.com/cline/cline/pull/13968#issuecomment-5593008205): ปิด stand-down แล้ว live/canonical ratio = 2.000 สองครั้ง; เปิด fix แล้ว = 1.000 สองครั้ง |
| 23:04:15Z | saoudrizwan | merge |

ผู้เขียนเปลี่ยน design จริงหนึ่งครั้ง และยอมรับ residual risk อีกครั้งหนึ่ง แทนการตอบทุก finding ว่า fixed

### การพิสูจน์

ผู้เขียนรายงาน 39 context tests ผ่าน (เพิ่ม 7), sidecar/webview 337 ผ่าน, full desktop 877 ผ่านพร้อม 6 pre-existing failures ที่เหมือน untouched main และ TypeScript output เหมือน baseline การ reproduce ผ่าน WebSocket เทียบ live กับ canonical และได้ ratio 2.000 ก่อนแก้กับ 1.000 หลังแก้

CI ที่ตรวจพบ:

- [test job](https://github.com/cline/cline/actions/runs/34288934509/job/102270921042) success 23:04:29Z
- [Greptile Review](https://github.com/cline/cline/runs/102270891325) success 23:06:34Z
- [Analyze JavaScript/TypeScript](https://github.com/cline/cline/actions/runs/34288932700/job/102270872399) success
- [Analyze Rust](https://github.com/cline/cline/actions/runs/34288932700/job/102270872367) success

ข้อควรระวังเรื่องเวลา: merge เกิด 23:04:15Z ก่อน test job จบ 23:04:29Z และก่อน Greptile จบ 23:06:34Z ดังนั้น captures นี้ยืนยันได้ว่า checks ผ่านบน head ที่ merge แล้ว/กำลัง merge แต่ยืนยันไม่ได้ว่า checks เหล่านี้เป็น pre-merge gate

ช่องว่างคือ boot-id premise ถูกสังเกตจาก process ที่มี index/boot ต่างกัน แต่ยังไม่ได้ reproduce sidecar replacement ใต้ live webview end-to-end; e2e/platform หลาย job ถูก skipped

บทเรียนสำหรับ prompt: ให้ symptom, repair signal และ architecture boundary พร้อมกัน; บังคับ negative test ที่ปิด fix แล้วต้อง fail; ขอ harness ที่เทียบผล live กับ canonical oracle


<a id="case-C2"></a>

## C2 — Cline #13969: mistake limit ต้องถามผู้ใช้และหยุดอย่างถูกต้อง

**ระดับหลักฐาน AI: B** · หลักฐานเฉพาะ contribution ที่เปิดเผยหรือมีร่องรอยลงมือ ไม่ยืนยันทุกบรรทัดหรือทุก commit · [ดูหลักฐาน](https://github.com/cline/cline/commit/e3b2e375c7f4e0c09cfef277ce5031c0bf8d5168)

PR: [cline/cline#13969](https://github.com/cline/cline/pull/13969)  
สร้าง 2026-09-08 22:34:54Z โดย saoudrizwan; 11 commits, 7 files, +877/-19; merge 2026-09-09 02:45:25Z ที่ [23f2197c](https://github.com/cline/cline/commit/23f2197c535f904bb4bbe17012fc81cdf3b2b8ac)

### หลักฐาน AI และ scope

commit แรก [e3b2e37](https://github.com/cline/cline/commit/e3b2e375c7f4e0c09cfef277ce5031c0bf8d5168) เวลา 22:31:36Z มี Co-Authored-By: Claude Fable 5.1 และ session URL

Trigger คือ Kimi K3 ทำ editor call ผิดซ้ำจน desktop หยุดเงียบๆ Acceptance คือใช้ callback และ question UI เดิม, Continue ส่ง recovery ผ่าน manager.send delivery steer, Stop/cancel/timeout cleanup question, รอที่ beforeModel/beforeTool/afterTool, ครอบคลุม start/provider rebuild/fork/restore และทำให้ tool row เก่าไม่แสดงเป็น active ตัว PR ระบุชัดว่า desktop-only และ ordinary ask_question teardown เป็น follow-up

### ลำดับ commit และ review

ชื่อ 11 commits ทำหน้าที่เป็น decomposition: [e3b2e37](https://github.com/cline/cline/commit/e3b2e375c7f4e0c09cfef277ce5031c0bf8d5168) เพิ่ม callback, [ca3aafc](https://github.com/cline/cline/commit/ca3aafc99b0cb8d1d991aeaa82d6862a896862d3) pause/cancel, [e174a76](https://github.com/cline/cline/commit/e174a767ea20aa65af87aa11d5738389b1af9575) coalesce iteration backlog, [0adda99](https://github.com/cline/cline/commit/0adda99aae11ed9235db7176bbf63a876f2c765f) wait decision, [deecbe2](https://github.com/cline/cline/commit/deecbe2837a2601bad519405aab5f005659d52e8) settle rows, [b34b926](https://github.com/cline/cline/commit/b34b92640871be133bdb1019a7a1457fcf746b54) cleanup, [4c31d06](https://github.com/cline/cline/commit/4c31d06b387345664bfb9ba9bc349fd5be8ae71d) status guard, [88cc56c](https://github.com/cline/cline/commit/88cc56ccb653821700402db1e003e1580550e576) scope stopped-tool recovery, [d4f2b14](https://github.com/cline/cline/commit/d4f2b142c6ca421def06f48fb68fe07337927410) steer-only guidance, [944df2a](https://github.com/cline/cline/commit/944df2a488e76a5a1869b536a416a73015da0225) rendering-only simplification และ [7ed28e8](https://github.com/cline/cline/commit/7ed28e895c2db946d8a514c99fd24af5c3878d92) merge main

Feedback loop:

- 22:38:08Z Greptile [P1](https://github.com/cline/cline/pull/13969#discussion_r3962894505): pending question ไม่ reject ตอน stop/abort/reset/fork/restore; แก้ด้วย session-scoped cancellation ใน b34b926
- 23:25:18Z Greptile [P1](https://github.com/cline/cline/pull/13969#discussion_r3963154102): mistake records จาก iteration เดียวกันอาจสร้าง duplicate prompts; [ผู้เขียนตอบ](https://github.com/cline/cline/pull/13969#discussion_r3963457918) เวลา 00:19:47Z ว่าใช้ iteration_start, capture boundary ก่อน await steering และส่ง guidance ครั้งเดียว
- 00:51:20Z Greptile [P1](https://github.com/cline/cline/pull/13969#discussion_r3963617983): hydration อาจ mark active unfinished tool เป็น stopped; 88cc56c จำกัด behavior ให้กับ mistake recovery และเก็บ heuristic limitation ไว้ใน PR
- 01:27:57Z Greptile [P1](https://github.com/cline/cline/pull/13969#discussion_r3963848996): ordinary ask_question ยังค้างได้; ผู้เขียนตอบ 01:41:21Z ว่า pre-existing/out of scope และ [Greptile ถอนเป็น blocker](https://github.com/cline/cline/pull/13969#discussion_r3963851551)

### การพิสูจน์

ผู้เขียนอ้าง TypeScript/Biome ผ่าน, chat rendering 95 tests ผ่าน, broader sidecar/webview 905 ผ่านกับ 1 unchanged jsdom failure และ manual Chromium + real isolated sidecar/hub: invalid editor calls 5 ครั้งสร้าง question เดียว, เปิดไว้ 15 วินาทีแล้ว model/tool start หยุด, Continue steer แล้ว valid edit จบ, Stop cleanup ถูกต้อง

CI final head:

- [test](https://github.com/cline/cline/actions/runs/34303406469/job/102315007045) success 02:29:37Z
- [CodeQL](https://github.com/cline/cline/runs/102315086295) success
- [Greptile Review](https://github.com/cline/cline/runs/102314982901) success
- [Analyze Rust](https://github.com/cline/cline/actions/runs/34303405333/job/102314966284) success 02:37:07Z

ยังไม่ได้ run full monorepo, native macOS Tauri shell หรือ live Kimi API; ordinary ask_question teardown เป็น follow-up ที่ถูกยอมรับไว้

บทเรียน: ขอ state machine ตั้งแต่ request → pending → steering ack → continue/stop → teardown → new run และให้ทดสอบ duplicate event, late answer, cancellation และ old iteration แยกกัน อย่าจบที่ UI; ต้องกำหนดจุดที่ runtime หยุดและช่องทางที่ guidance เข้า model


<a id="case-C3"></a>

## C3 — Roo #11409: migration ใหญ่จาก Anthropic message เป็น AI SDK ModelMessage

**ระดับหลักฐาน AI: B** · หลักฐานเฉพาะ contribution ที่เปิดเผยหรือมีร่องรอยลงมือ ไม่ยืนยันทุกบรรทัดหรือทุก commit · [ดูหลักฐาน](https://github.com/RooCodeInc/Roo-Code/pull/11409)

PR: [RooCodeInc/Roo-Code#11409](https://github.com/RooCodeInc/Roo-Code/pull/11409)  
สร้าง 2026-02-11 17:07:15Z โดย daniel-lxs; 11 commits, 103 files, +2,648/-3,206; merge 18:58:39Z ที่ [e6f0e79c](https://github.com/RooCodeInc/Roo-Code/commit/e6f0e79c389dc558338b243f6854c11c2854786f)

### เป้าหมายและหลักฐาน AI

ปัญหาเดิมคือเก็บ conversation ใน Anthropic format แล้ว reconstruct จาก stream event พร้อม inject reasoning blocks ทำให้ second turn บาง provider fail AI SDK schema validation PR จึงเพิ่ม RooMessage, versioned storage, backward converter, ใช้ result.response.messages และอัปเดต provider ราว 25-30 ตัว

PR body ลงท้าย [Generated with Claude Code](https://github.com/RooCodeInc/Roo-Code/pull/11409) และ commit อย่างน้อยห้าตัวมี Claude Opus 4.6 เป็น co-author: [e8dfdc2](https://github.com/RooCodeInc/Roo-Code/commit/e8dfdc2e7dfa994300fde371c1aec4bcb01382c5), [57e9792](https://github.com/RooCodeInc/Roo-Code/commit/57e9792425626344686e2af8665f0bd0bdfa6d7f), [de6982e](https://github.com/RooCodeInc/Roo-Code/commit/de6982ef832a0ca70758a4f7662761235f1163a1), [cb4bfc9](https://github.com/RooCodeInc/Roo-Code/commit/cb4bfc9997081683ec72848ead28272de36fa272) และ [e37585f](https://github.com/RooCodeInc/Roo-Code/commit/e37585fa87fcddfb3c457c4cc71549632402beb7) ซึ่งชื่อระบุ address PR review comments

Acceptance ใน PR คือ full suite, TypeScript, ESLint, pre-commit ผ่าน; manual smoke ของ Anthropic extended thinking, Gemini thought signature, OpenRouter reasoning, OpenAI encrypted reasoning และ non-AI-SDK fallback ถูกระบุแต่ unchecked

### Review → patch

- 17:16:58Z Rooview [P1](https://github.com/RooCodeInc/Roo-Code/pull/11409#discussion_r2794507746): raw JSON.parse อ่าน v2 envelope ไม่ได้
- 17:44:01Z Hannes [P1](https://github.com/RooCodeInc/Roo-Code/pull/11409#discussion_r2794630411): orphan filter พลาด legacy tool_use; มี P2 เรื่อง misleading comment และ unsafe casts
- 18:01:22Z Hannes [comprehensive review](https://github.com/RooCodeInc/Roo-Code/pull/11409#pullrequestreview-3786381922): approve with required changes หลังใช้ 10 specialized AI agents; พบ critical save-failure divergence และ major เรื่อง truncation, error status, export type, legacy IDs, native-format tests, merge tests, yieldResponseMessage tests และ test casts
- 18:03:24Z [e37585f](https://github.com/RooCodeInc/Roo-Code/commit/e37585fa87fcddfb3c457c4cc71549632402beb7) แก้ dual-format/orphan filtering และ dead code
- 18:34:41Z มี [P1 save return](https://github.com/RooCodeInc/Roo-Code/pull/11409#discussion_r2794842545), [P1 pendingToolResults](https://github.com/RooCodeInc/Roo-Code/pull/11409#discussion_r2794842551) และ [P2 image URL](https://github.com/RooCodeInc/Roo-Code/pull/11409#discussion_r2794842548)
- 18:43:26Z [984857e](https://github.com/RooCodeInc/Roo-Code/commit/984857e60fbc9786e1af46881e4b075ff9e6049b) ปรับ image URL และ save error handling
- Rooview [re-review](https://github.com/RooCodeInc/Roo-Code/pull/11409#issuecomment-3885766946) ระบุว่า v2 envelope, save return, image URL และ pending tool results ถูกแก้
- Hannes [approve final head](https://github.com/RooCodeInc/Roo-Code/pull/11409#pullrequestreview-3786644844) 18:51:11Z; merge 18:58:39Z

มี anomaly ใน timestamp ของ automated Rooview comment ที่อ้าง final SHA แต่ API created_at อยู่ก่อน final commit เอกสารนี้จึงยึด anchors, SHA, check completion และ human approval ไม่อ้างลำดับ bot เกินข้อมูล

### การพิสูจน์และช่องว่าง

ผู้เขียนอ้าง 5,469 tests ใน PR body ขณะที่ commit ก่อนหน้าอ้าง 5,536 tests จึงควรถือเป็น self-reported snapshots ไม่ใช่ตัวเลขที่ reconcile แล้ว

CI ก่อน merge:

- [integration-test](https://github.com/RooCodeInc/Roo-Code/actions/runs/21918347482/job/63291556921) success 18:48:04Z
- [compile](https://github.com/RooCodeInc/Roo-Code/actions/runs/21918347482/job/63291546440) success 18:47:25Z
- [platform-unit-test Ubuntu](https://github.com/RooCodeInc/Roo-Code/actions/runs/21918347482/job/63291546413) success 18:50:57Z
- [platform-unit-test Windows](https://github.com/RooCodeInc/Roo-Code/actions/runs/21918347482/job/63291546409) success 18:56:03Z
- [CodeQL](https://github.com/RooCodeInc/Roo-Code/runs/63291755171) success 18:46:20Z

จึง merge ได้เพราะ final head มี commits แก้ findings, bot re-review รายงาน resolved, human approve และ checks ที่ถูกบันทึกไว้เป็น success แต่ raw capture นี้ไม่ได้พิสูจน์กฎ branch protection ว่า checks ใดเป็น required CI โดยเฉพาะ ส่วน manual smoke ทั้งห้ากลุ่มมีสถานะ unchecked ใน PR ซึ่งหมายความว่าไม่มี public confirmation ว่าทำแล้วหรือไม่ ไม่ใช่หลักฐานว่าไม่เคยรัน และ fast-follow เรื่อง native-format coverage/test casts ยังไม่ใช่หลักฐานว่าเสร็จ

บทเรียน: migration ใหญ่ควรสั่งเป็น additive foundation → wiring → compatibility → review fixes พร้อม invariant ของ old/new format และ persistence failure tests ไม่พอที่จะบอก full suite ผ่าน


<a id="case-C4"></a>

## C4 — Goose #11307: structured output ต้อง fail ก่อนเสีย token กับ inference

**ระดับหลักฐาน AI: B** · หลักฐานเฉพาะ contribution ที่เปิดเผยหรือมีร่องรอยลงมือ ไม่ยืนยันทุกบรรทัดหรือทุก commit · [ดูหลักฐาน](https://github.com/aaif-goose/goose/commit/5372cf21c4c043cb25959d08529c766012cdbd48)

PR: [aaif-goose/goose#11307](https://github.com/aaif-goose/goose/pull/11307)  
สร้าง 2026-08-18 05:19:10Z โดย Wolfe-Jam; 5 commits, 8 files, +244/-20; merge 2026-08-21 08:41:22Z โดย lifeizhou-ap ที่ [a5de3781](https://github.com/aaif-goose/goose/commit/a5de37814adb1b8f7eab3046c53811d5808733fa)

commit แรก [5372cf2](https://github.com/aaif-goose/goose/commit/5372cf21c4c043cb25959d08529c766012cdbd48) เวลา 04:44:55Z มี Co-Authored-By: Claude Sonnet 5

ปัญหาคือ ACP-bridged providers ไม่ forward frontend tool ผ่าน ACP; synthetic final_output จึงไปไม่ถึง model และ agent loop nudge ซ้ำไม่รู้จบพร้อมใช้ token/cost ไม่จำกัด Acceptance คือเพิ่ม capability ที่ตรงกับ frontend-tool delivery, reject ทั้ง state-machine และ legacy loop ก่อน retry/nudge และก่อน inference, มี provider unit tests + end-to-end claude-code test และไม่ทำ forwarding ผ่าน mcp-config ใน PR นี้ (แยก issue #10955)

### Review rejection → patch → approval

- 07:16:51Z [aa847d3](https://github.com/aaif-goose/goose/commit/aa847d3bb9de1f0d96de11fe96175b4ff8bfcfc1) ปรับ capability gating
- 07:20:43Z Codex ให้ [P1](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828196036): legacy path ตรวจช้า หลัง provider.stream; ต้องย้าย guard ก่อน inference และเพิ่ม legacy test
- 07:23:43Z Codex ให้ [P2](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828216905): manages_own_context เป็น proxy ผิด เพราะ wrapper อาจยัง forward tools; ใช้ capability เฉพาะทาง
- 07:45:53Z [d656b43](https://github.com/aaif-goose/goose/commit/d656b43bfddc7df8bfdd49da13c3efbc896c99d0) ย้าย rejection ก่อน inference
- 07:49:50Z Codex ให้ [P2](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828395594): recovery message ให้ลบเฉพาะ response.json_schema ยังเหลือ object ที่ legacy path อาจ panic
- 08:22:40Z [ddf10a2](https://github.com/aaif-goose/goose/commit/ddf10a298497a493226908626cd45d1935ba8e90) ปรับ user-facing text
- 08:23:32Z/08:23:36Z maintainer [mark findings fixed](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828630359) และ [legacy finding fixed](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828630796)
- 08:24:03Z maintainer [approve](https://github.com/aaif-goose/goose/pull/11307#pullrequestreview-4991286679)
- 08:41:22Z merge

Review บังคับให้คำว่า fail-fast มีความหมายเชิงเวลา: fail ก่อนเสีย inference จริง ไม่ใช่แค่สุดท้ายแสดง error

### การพิสูจน์

ผู้เขียนอ้าง cargo build 0 warnings, cargo test 1,909 ผ่าน 1 pre-existing fail ซึ่งตรวจซ้ำบน clean main, clippy/fmt ผ่าน, unit tests สำหรับ capability และ end-to-end test ที่ไม่เข้า continuation-nudge

CI:

- [Build and Test Rust Project](https://github.com/aaif-goose/goose/actions/runs/32462933787/job/96713466853) success 08:31:30Z
- [Test and Lint Electron Desktop App](https://github.com/aaif-goose/goose/actions/runs/32462933787/job/96713466896) success 08:25:37Z
- [Lint Rust Code](https://github.com/aaif-goose/goose/actions/runs/32462933787/job/96713466872) success 08:26:15Z
- [Check Rust Code Format](https://github.com/aaif-goose/goose/actions/runs/32462933787/job/96713466915) success 08:23:46Z
- [Check Generated Schemas](https://github.com/aaif-goose/goose/actions/runs/32462933787/job/96713466920) success 08:27:54Z

ช่องว่างคือ one failing test เป็นคำกล่าวของผู้เขียนว่า pre-existing และ raw check summary ไม่ได้แสดง independent baseline reproduction ส่วน issue #10955 ยังไม่ได้แก้

บทเรียน: นิยาม acceptance ด้วยตำแหน่งเวลาใน execution path (“ก่อน inference”), บอก execution paths ทั้งสอง, ตั้งชื่อ capability ตาม contract จริง และทดสอบ recovery instruction ตามตัวอักษร


