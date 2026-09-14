<a id="case-W1"></a>

## W1 — OpenCode #47286: PR ผ่าน agent workflow ที่ยังมี acceptance gap

**ระดับหลักฐาน AI: C** · เห็น bot workflow แต่ยังไม่พอสรุปว่าผู้ผลิตโค้ดคือ AI · [ดูหลักฐาน](https://github.com/anomalyco/opencode/pull/47286)

PR: [fix(app): align desktop agent and model switching](https://github.com/anomalyco/opencode/pull/47286) เปิดวันที่ 4 กันยายน 2026 โดย opencode-agent[bot] และ merge วันที่ 8 กันยายนโดย Brendonovich ไปยัง merge commit [f9bc2233](https://github.com/anomalyco/opencode/commit/f9bc2233ddcc11503a0804b317401bc221ef0e7f) หัว PR ที่ผ่าน CI คือ [d0fe0c2e](https://github.com/anomalyco/opencode/commit/d0fe0c2e97253b9488d96b2f4e6cfcf9e635266c) หลักฐาน bot เป็นของ PR โดยตรง แต่สาม commit แรกมี nexxeln เป็น author และ opencode-agent เป็น committer ส่วน commit สุดท้ายมี Brendonovich เป็น author ดังนั้นควรจัดเป็น “agent-produced PR workflow ที่มนุษย์ยังมีส่วน author/merge” ไม่ใช่ข้อพิสูจน์ว่า AI เขียนทุกบรรทัด

ต้นทางของเป้าหมายคือ PR [#47260](https://github.com/anomalyco/opencode/pull/47260) ซึ่งกำหนด parity ของการสลับ agent/model/variant ไว้ละเอียดมาก: จดจำ model และ variant ต่อ agent ต่อ session, fallback เมื่อ model ใช้ไม่ได้, เคารพ global/agent defaults และ explicit Default, รักษา draft, รองรับ delayed acknowledgement และไม่ให้ command override ถูกกลบ PR #47286 ขยายข้อกำหนดนี้ไปยัง Desktop/V2 renderer โดยระบุขอบเขตชัดว่าต้องครอบคลุม new-session draft และ existing session, queued prompt, custom slash command และ shortcut เดิม ไม่แก้ Protocol, Server หรือ public API

จาก acceptance criteria เหล่านี้ agent แยกงานได้เป็นสี่ชุดที่มองเห็นจาก commit และไฟล์: แก้ selection/state ใน packages/app/src/composer และ model selector; เพิ่ม controller และ variant tests; เพิ่ม fixture/provider ที่จำลอง model availability และ delayed acknowledgement; เพิ่ม browser regression suite กับ mock server แล้วจึง merge parity จาก v2 เข้า desktop ใน commit [d0fe0c2e](https://github.com/anomalyco/opencode/commit/d0fe0c2e97253b9488d96b2f4e6cfcf9e635266c) รวม 21 ไฟล์, 978 additions, 237 deletions และ 4 commits

ลำดับ feedback ชัดเจนแม้ public review สั้นมาก:

- commit หลัก [734acbaf](https://github.com/anomalyco/opencode/commit/734acbafe3c1fe9545bcffc18331ad586355c005) ทำ production logic และ test หลัก
- E2E run พบว่า shared mock ขาด GET /api/config; agent เพิ่ม fixture ใน [3666deef](https://github.com/anomalyco/opencode/commit/3666deef52891d8314cb5a1b55f4d4ffe4cca488) และ standalone mocks ใน [c54a3f6e](https://github.com/anomalyco/opencode/commit/c54a3f6e808c97e52db0090f99b0b348176f0823)
- การสาธิตบน production build พบ gap ที่สำคัญ: ใน new draft เมื่อสลับ Build → Opus/High → Plan/Sonnet/Low → Build ระบบคืน Opus แต่ variant กลายเป็น Low แทน High สาเหตุถูกชี้ไปที่ selection object ที่ไม่มี variant กับ Solid merging setter
- agent บันทึก gap นี้ไว้ใน PR body พร้อม video และไม่แกล้งสรุปว่า feature สมบูรณ์ ทั้งที่ existing-session flow ผ่าน นี่คือ acceptance criterion ที่ยังไม่ผ่านซึ่งถูกเปิดเผยอย่างตรวจสอบได้
- หลัง merge มีคอมเมนต์จาก nexxeln ว่า “woohoo” ([permalink](https://github.com/anomalyco/opencode/pull/47286#issuecomment-5584366158)); API ไม่พบ formal review หรือ inline review comment ดังนั้นรายละเอียด critical review ใน body เป็นรายงานของผู้ผลิต ไม่ใช่ transcript ของ reviewer

ผู้ผลิตรายงาน local checks ได้แก่ app typecheck, unit 738 passed/1 skipped, browser 118 passed, desktop typecheck, production build, GUI flows และ 47 follow-up E2E tests รายงานเหล่านี้ต้องแยกจากหลักฐานที่ตรวจซ้ำได้: API ของ head SHA แสดง check-runs สำเร็จ 14 รายการ รวม typecheck, unit Linux/Windows, E2E Linux/Windows และ standards/compliance ใน [Actions run 34195339626](https://github.com/anomalyco/opencode/actions/runs/34195339626) ดังนั้น “CI ผ่านที่ head นี้” เป็น fact ที่ API ยืนยัน ส่วนจำนวน local test และข้อสรุปจาก video เป็น claim/artefact ของ PR

บทเรียนสำหรับการสั่ง AI คือให้เริ่มจาก parent PR หรือ issue ที่ระบุ state และ negative cases มากกว่าคำสั่งกว้าง ๆ ให้สั่งให้แบ่ง state model, fixtures, regression tests และ browser flow ออกจากกัน และให้รายงาน expected/observed ทุก scenario รวมถึง gap ที่ยังไม่แก้ วงจรนี้แสดงการตรวจสอบหลายชั้นและการบันทึกข้อบกพร่องที่เหลืออยู่ แม้ acceptance criterion หนึ่งยังไม่ผ่าน ไม่ควรตีความการ merge ว่าเป็นหลักฐานว่าทุก criterion สำเร็จ

<a id="case-W2"></a>

## W2 — OpenCode #47455: แปลง issue reproduction เป็น interaction matrix

**ระดับหลักฐาน AI: C** · เห็น bot workflow แต่ยังไม่พอสรุปว่าผู้ผลิตโค้ดคือ AI · [ดูหลักฐาน](https://github.com/anomalyco/opencode/pull/47455)

PR: [fix(app): link background subagents to their sessions](https://github.com/anomalyco/opencode/pull/47455) เปิดโดย opencode-agent[bot] วันที่ 5 กันยายนและ merge โดย Brendonovich วันที่ 9 กันยายน 2026 ที่ [f1ce69d2](https://github.com/anomalyco/opencode/commit/f1ce69d2ceae4ed7e39c49210ae9264cbf86ffec) head [99a101c2](https://github.com/anomalyco/opencode/commit/99a101c2d67da0893964fdb37c7cc07e2b15870f) มี 2 commits, 4 ไฟล์, 194 additions และ 21 deletions

PR นี้มี issue ต้นทางที่ดีมากคือ [#47265](https://github.com/anomalyco/opencode/issues/47265) ซึ่งให้ version, OS, reproduction steps, expected และ actual behavior ครบ ผู้ใช้เห็น background subagent ใน Session details แต่กดแล้วไม่เปิด child session issue ยังระบุ implementation hint ว่า task.id มี child-session ID อยู่แล้ว และควร reuse sessionHref/navigateToSession โดยไม่ต้องแก้ server/API ตัว PR จึงใช้ Fixes #47265 และรักษาขอบเขต Web UI ไว้

Acceptance criteria ที่เขียนไว้ชัดเจนใน PR คือ (1) running subagent row ต้องเป็น link, (2) finished/failed/cancelled timeline notice ต้อง link ไป child เดียวกัน, (3) ใช้ navigation เดิมเพื่อเก็บ parent tab และให้ Escape กลับ parent, (4) คง native keyboard, modified-click และ middle-click, (5) shell rows และ notice ที่ไม่ใช่ subagent ต้องไม่กลายเป็น interactive การแยกนี้ทำให้ “ทำให้คลิกได้” ไม่กลายเป็นการเปลี่ยน semantics ของ timeline ทั้งหมด

การเปลี่ยนแปลงแบ่งเป็น route/row component, timeline notice, story fixture และ browser regression suite ใน commit [ee2ca0c1](https://github.com/anomalyco/opencode/commit/ee2ca0c1ce671da267546fa468894116b02c43d8) จากนั้น commit [99a101c2](https://github.com/anomalyco/opencode/commit/99a101c2d67da0893964fdb37c7cc07e2b15870f) ปิด behavior ของ finished child sessions การตรวจไม่ได้หยุดที่ click เดียว แต่ทำ matrix 21 browser regressions ครอบคลุม pointer/keyboard, Ctrl/Cmd-click, middle-click, narrow layouts, child session ที่ไม่อยู่ใน session-list cache, parent return, notice truncation และ desktop/mobile LTR/RTL

PR body ระบุ app และ Session UI typecheck, app unit 823 passed/1 skipped, timeline unit 60 passed, focused browser 21 passed แบบไม่มี retry, visual comparison ของ notice ทั้งหก layout เปลี่ยน 0 pixels และ production entry benchmark 9/9 ต่อ reference การแยก behavior test กับ visual invariant ทำให้รู้ว่าเป้าหมายคือ interaction-only change และไม่ทำให้หน้าตาเดิมเสีย API ตรวจสอบ head SHA พบ check-runs สำเร็จ 10 รายการ รวม unit Linux/Windows, E2E Linux/Windows, typecheck, affected packages และ standards/compliance ใน [Actions run 34219424387](https://github.com/anomalyco/opencode/actions/runs/34219424387)

ข้อจำกัดคือ PR ไม่มี public issue comment, review หรือ inline review comment และ commit แรกมี Brendonovich เป็น author/committer ขณะที่ commit สองมี Brendonovich เป็น author แต่ opencode-agent[bot] เป็น committer หลักฐานจึงบอกได้ว่า agent workflow ผลิต/ส่ง PR และมี human source commit ร่วมอยู่ แต่สรุปไม่ได้ว่า implementation ถูกสร้างโดย AI ล้วน ๆ อีก gap คือไม่มีหลักฐาน accessibility audit หรือ packaged Electron test แยกจาก browser suite

บทเรียนคือ acceptance criteria สำหรับ UI ควรเขียนเป็น interaction matrix: state ของ row, destination, keyboard/mouse semantics, parent-return behavior, cache-miss และ layout direction ทุกข้อควรมี test ที่ชี้ตรงไปยัง criterion การที่ issue ให้ reproduction และ implementation hint ก่อนเริ่ม ทำให้ AI ทำงานในขอบเขตแคบและลดการแก้ server/API ที่ไม่จำเป็น

<a id="case-W3"></a>

## W3 — OpenTUI #1481: refactor ใหญ่ที่ใช้ review, repeated tests และ CI ที่ผูกกับ revision ที่ระบุ

**ระดับหลักฐาน AI: C** · เห็น bot workflow แต่ยังไม่พอสรุปว่าผู้ผลิตโค้ดคือ AI · [ดูหลักฐาน](https://github.com/anomalyco/opentui/pull/1481)

PR: [feat(core): support PCM through the shared audio stream interface](https://github.com/anomalyco/opentui/pull/1481) เปิดโดย opencode-agent[bot] วันที่ 5 กันยายนและ merge โดย kommander วันที่ 7 กันยายน 2026 ที่ [62a7c382](https://github.com/anomalyco/opentui/commit/62a7c3828947a641927a39295889b5642c069006) head [c6f3e7c3](https://github.com/anomalyco/opentui/commit/c6f3e7c30308e18f5f5b07f2b4a12ed49d7b1b68) มี 5 commits, 14 ไฟล์, 1,141 additions และ 101 deletions

เป้าหมายคือเพิ่ม raw PCM ให้ผ่าน audio stream interface เดียวกับ MP3/FLAC โดยห้ามแตก worker loop หรือ native method family ใหม่ งานถูกแบ่งตาม contract boundary: native audioCreateStream/audioWriteStream/audioEndStream, shared worker lifecycle, PCM converter และ partial-frame state, bounded 256 KiB queue, readiness/backpressure/EOF/cancellation/teardown, resampler tail, tests, example และ docs ใน PR body มี contract ตัวอย่าง TypeScript และระบุ out-of-scope ชัด เช่น PCM reconnect ยัง unsupported

ลำดับ commit แสดงการทำงานเป็นชั้น:

- [051c1b8d](https://github.com/anomalyco/opentui/commit/051c1b8d35316b45b5f97c0e2b49549a23c9ab3d) เพิ่ม native PCM stream
- [c7e9bb37](https://github.com/anomalyco/opentui/commit/c7e9bb370b7c5af7fbce37b515b983cac28165b1) รวม PCM streaming และรักษา resampler tails
- [1a411b79](https://github.com/anomalyco/opentui/commit/1a411b79e41eeef52d0833effb84ea8faadb0f55) บังคับ one native stream interface
- [5cdb091f](https://github.com/anomalyco/opentui/commit/5cdb091f136e040459859aa7db1540934fa3d19b) ใช้ shared worker กับ PCM
- [c6f3e7c3](https://github.com/anomalyco/opentui/commit/c6f3e7c30308e18f5f5b07f2b4a12ed49d7b1b68) แก้ readiness test หลังพบว่า snapshot assumption เดิมไม่ถูก

PR body ระบุว่ามี simplification request จาก kommander, post-push critical review และการแก้ readiness-snapshot assumption โดย production code ไม่เปลี่ยนใน follow-up สุดท้าย ข้อมูล timeline ยืนยันว่ามี force-push ระหว่างทาง แต่ API ไม่พบ public issue comment, formal review หรือ inline comment ดังนั้นรายละเอียด review เป็น author-provided narrative ที่ควรอ่านคู่กับ commit/test evidence ไม่ใช่ transcript ที่ตรวจครบจาก GitHub

หลักฐาน test ที่ผู้ผลิตรายงานละเอียดมาก: native 2,168 passed/8 skipped, PCM suite ผ่าน 10 รอบ, Core Bun 5,685 passed/24 skipped, Core Node 4,936 passed/7 skipped, fresh ReleaseFast build, typecheck, format, lint, docs validation และ packed Bun/Node distribution checks ผ่าน อีกทั้งระบุว่าผลรวม production change ลดลง 44 lines เมื่อเทียบกับหัว PR เดิม API ของ head ยืนยัน check-runs สำเร็จ 30 รายการ ครอบคลุม Core, Bun compatibility, Ubuntu/Windows/macOS, native library, format/lint, packed consumers และ benchmark ใน [Actions run 34026819466](https://github.com/anomalyco/opentui/actions/runs/34026819466) และ [run 34026819417](https://github.com/anomalyco/opentui/actions/runs/34026819417)

ข้อควรระวังคือ commit แรกและบาง commit มีมนุษย์เป็น author/committer (neriousy, kommander, Tilda) และบาง commit ใช้ opencode-agent[bot] เป็น committer จึงจัดเป็น PR ผ่าน bot workflow โดยหลักฐานการผลิตโค้ดยังจำกัด ไม่ใช่ direct proof of fully AI-written code นอกจากนี้ไม่มี linked issue ให้ตรวจ goal ต้นทาง จึงต้องพึ่ง PR body และ Slack request ที่ body ระบุเอง

บทเรียนคือเมื่อ task แตะ native/FFI/streaming acceptance criteria ต้องเขียน invariants ที่ input fragmented, partial frame, queue capacity, readiness, EOF และ tail flush ไม่ใช่แค่ “เพิ่ม format ใหม่” ให้แยก production, native tests, language-runtime tests, docs และ example เป็นงานย่อย และให้ agent รันซ้ำหลังพบ assumption ผิดทุกครั้ง การเก็บ repeated test และ CI ที่ผูกกับ revision ที่ระบุ ช่วยลดความเสี่ยงจาก test ผ่านเพียงครั้งเดียว

<a id="case-W4"></a>

## W4 — OpenTUI #1314: PR bot แต่ commit history ยังเป็นมนุษย์

**ระดับหลักฐาน AI: C** · เห็น bot workflow แต่ยังไม่พอสรุปว่าผู้ผลิตโค้ดคือ AI · [ดูหลักฐาน](https://github.com/anomalyco/opentui/pull/1314)

PR: [fix(core): emit render errors](https://github.com/anomalyco/opentui/pull/1314) เปิดโดย opencode-agent[bot] วันที่ 31 กรกฎาคมและ merge โดย kommander วันที่ 2 สิงหาคม 2026 ที่ [db3137a3](https://github.com/anomalyco/opentui/commit/db3137a35aed5c958194364acee3841e7ba12f91) head [d42e6ceb](https://github.com/anomalyco/opentui/commit/d42e6cebf3564f12a43b409e57d644d984ebb628) มี 4 commits, 4 ไฟล์ และไม่มี linked issue, public comment หรือ formal review

ขอบเขตทางเทคนิคกลับละเอียด: emit RENDER_ERROR เป็น { error, renderable }, attribution ต้องชี้ renderable ที่พัง, ใช้ catch ระดับ frame ไม่ใช่ try/catch ต่อ renderable/loop, รักษา continuous/one-shot recovery และ route unobserved failure เข้า error policy เดิม งานถูกแยกเป็น implementation, traversal benchmark, attribution fix และ merge conflict resolution ใน [29ecec38](https://github.com/anomalyco/opentui/commit/29ecec38059b96fb94556e0ead1ed15ee3482b24), [ff824140](https://github.com/anomalyco/opentui/commit/ff8241406b908b2566bc556c710b2c054a2e8642), [6725f4a1](https://github.com/anomalyco/opentui/commit/6725f4a1e9733ef6d9c16612dc8a00b75a6b87d1) และ [d42e6ceb](https://github.com/anomalyco/opentui/commit/d42e6cebf3564f12a43b409e57d644d984ebb628)

ผู้ผลิตรายงาน native 1,708 passed/6 skipped, JS 5,205 passed/23 skipped, format และ lint ผ่าน รวม benchmark เปรียบเทียบ 15.093 กับ 15.041 ns/renderable และรายงาน RSD ไม่ต่ำพอจะสรุป performance improvement ใหญ่ ๆ API ตรวจสอบได้ว่าหัว PR มี check-runs สำเร็จ 29 รายการ ทั้ง Core, SSH, React, QRCode, Solid, Keymap, Windows/macOS/Ubuntu, benchmark, packed consumer และ lint/format ใน [Actions run 30765499637](https://github.com/anomalyco/opentui/actions/runs/30765499637)

เคสนี้มีประโยชน์เพราะเป็น control: PR identity เป็น bot แต่ทุก commit มี kommander เป็น author/committer (commits.json) จึงไม่ควรตีความว่า AI เขียนโค้ดจาก bot author เพียงอย่างเดียว หลักฐานที่ปลอดภัยคือ repository มี agent-mediated PR path และมนุษย์ใช้ path นั้นส่งงานเข้า review/CI
