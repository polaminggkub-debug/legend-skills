# Context Discovery: หลักฐานจากงาน Coding Agents

เอกสารนี้เก็บกรณีศึกษาและขอบเขตที่พิสูจน์ได้ สำหรับใช้ประกอบ [บทเรียน Context Discovery](context-discovery-lessons.md) ตรวจแหล่งข้อมูลวันที่ **14 กันยายน 2026** วันที่เหตุการณ์ในเอกสารเป็น UTC เว้นแต่ระบุเป็นอย่างอื่น

<a id="method"></a>

## วิธีอ่านและขอบเขตการศึกษา

คำถามคือ ตั้งแต่ task ถึง implementation และ review ข้อมูลใดปรากฏว่าเข้าไปมีส่วนในการทำงานของ agent ไม่ใช่เพียง repository มี instruction file แบบใด

ใช้การคัดกรณีแบบเจาะจง: กรณีหลักต้องมีหลักฐาน AI implementation ใน contribution และมี task, patch, review หรือ transcript ที่ตรวจต่อได้ เก็บ C3b แยกเป็นกรณีเปรียบเทียบที่มี agent integration แต่ model authorship ยัง U เน้นโปรเจกต์ AI และงานใหม่; แยกกรณีเก่าหรือเอกสารกลไกออกเป็นส่วนเสริม “ขนาดใหญ่” ในที่นี้หมายถึง repo มีหลาย subsystem และมีการใช้งาน/กิจกรรมสาธารณะมากพอเป็นบริบทจริง ไม่ใช้จำนวน stars พิสูจน์คุณภาพ code หรือสัดส่วนงานที่ AI ทำ

**Direct evidence — D:** สิ่งที่เห็นตรงจาก artifact, คำรายงาน หรือ trace โดยกำกับชนิดเสมอเมื่ออาจสับสน **Reasonable inference — I:** การตีความจาก D ที่ยังไม่ใช่การสังเกตโดยตรง **Unknown — U:** หลักฐานที่ตรวจยังตอบไม่ได้ คำว่า Unknown ไม่ได้แปลว่าไม่เคยเกิดขึ้น

ข้ออ้างหนึ่งอาจมีหลายระดับพร้อมกัน: “ไฟล์กฎมีอยู่” เป็น D-artifact; “agent กล่าวถึงกฎในคำตอบ” เป็น D-report; “agent ใช้คำสั่งอ่านไฟล์นั้นเวลาใด” ยังเป็น U หากไม่มี trace การมี session URL เพียงอย่างเดียวก็ไม่เปิดเผยเนื้อหา session

หลักฐานหลักมาจาก GitHub issue, PR body, commit/diff, review และ repo files ที่ระบุ revision; transcript และเอกสารของผู้พัฒนาเครื่องมือใช้เป็นหลักฐานเสริม งานเก่า [ai-delivery-learning-pack.md](../ai-delivery/ai-delivery-learning-pack.md) ใช้เป็นเบาะแสค้นต่อ โดยตรวจแหล่งต้นทางใหม่สำหรับข้ออ้างที่นำมาใช้

ข้อจำกัดร่วม:

- ไม่ใช่ตัวอย่างสุ่ม ไม่มี denominator ของงาน AI ทั้งหมด จึงสรุป prevalence หรืออัตราสำเร็จไม่ได้
- PR body แก้ภายหลังได้ จึงไม่ถือเป็น initial prompt; commit หลัง rebase อาจไม่ใช่ SHA ที่ review เดิมเห็น
- base SHA ปัจจุบันของ PR ไม่จำเป็นต้องเป็นฐานตอนเริ่มงาน เอกสารที่ตรึง revision ยืนยันเนื้อหาที่ revision นั้น ไม่ยืนยันว่า runtime โหลด
- ระบุ AI-heavy แยกสองมิติ: ผลิตภัณฑ์เกี่ยวกับ AI และ contribution มีหลักฐานใช้ AI; ไม่ได้คำนวณสัดส่วน AI-authored ทั้ง repo
- คำรายงานผล tests ไม่เท่ากับ raw test logs; การมี test code ไม่พิสูจน์ว่า run ผ่าน; merge ไม่เติมช่องว่างนี้
- ไม่ใช้ข้อเท็จจริงที่ได้จาก diff แต่งลำดับการค้นไฟล์หรือความคิดของ agent

<a id="case-index"></a>

## ดัชนีกรณีศึกษา

อ่านเร็ว: [คำตอบสิบคำถาม](#findings) · [ความละเอียดของหลักฐาน](#coverage) · [ทะเบียน session](#sessions) · [หลักฐานที่ต้องเก็บเพิ่ม](#next-evidence)

| กรณี | โปรเจกต์ / งาน | หลักฐาน AI implementation | จุดที่ใช้เรียน |
|---|---|---|---|
| [C1](#c1) | Dyad #4187 — Coolify feature | PR disclosure + Claude-attributed replies | rules/analogue ถูกอ้างใน response |
| [C2a](#c2) | OpenHands #8310 — compatibility | automatic-fix PR + agent conversation | reviewer ส่ง architecture/file/test pointers |
| [C2b](#c2) | OpenHands #8252 — pre-commit | automatic-fix attempt + unresolved reports | ให้ context แล้วงานยังไม่ converge |
| [C3a](#c3) | OpenCode #6014 — custom-provider TUI | exact invocation → bot response/commit/PR | request เห็น; session เปิดไม่ได้; ไม่ merge |
| [C3b](#c3) | OpenCode #47455 — child-session UI | agent-integration workflow; model authorship U | issue hints → interaction contract |
| [C3c](#c3) | OpenCode #44281 — provider wire | Claude co-author disclosures | review เพิ่ม test-oracle invariant |
| [C4](#c4) | Cline #13969 + #13968 | Claude co-author และ linked sessions | lifecycle, runtime probe, unknown trace |
| [C5](#c5) | Roo #11409 — storage migration | PR disclosure + Claude co-author | readers, compatibility, save failures |
| [C6](#c6) | Goose #11307 — fail fast | Claude co-author; Codex review แยกบทบาท | PR อ้าง AGENTS parity; review เจาะ timing |
| [S1](#s1) | Claude Code Action #726 | PR disclosure | ช่องทางโหลด context |
| [S2](#s2) | Aider — input mocking | transcript + Context ใน commits | เห็น context addition แต่เป็นเคสเล็กปี 2023 |

รวมกรณีหลัก/เปรียบเทียบ **10 PR จาก 6 repo** โดย C3b ใช้ศึกษาบริบทงาน/UI และไม่รวมเป็นหลักฐานยืนยัน model authorship เพิ่ม S1 อีก 1 PR และ S2 เป็น transcript/commits ของ repo เก่า จำนวนนี้เป็นขอบเขตการอ่าน ไม่ใช่จำนวน independent experiments

### อายุและขนาดของโปรเจกต์

วันสร้างและ stars เป็น **D-metadata ปัจจุบัน** ที่ตรวจ 14 ก.ย. 2026 ไม่ใช่ขนาดตอนเกิดทุกเคส วันสร้าง repo อาจไม่ใช่วันเริ่ม code หากมีการย้ายหรือแยกโปรเจกต์

| Repository / metadata | สร้าง | Stars ณ วันที่ตรวจ | เหตุผลที่ใช้และข้อจำกัด |
|---|---|---:|---|
| [Dyad](https://api.github.com/repos/dyad-sh/dyad) | 2025-04-11 | 21,519 | ใหม่; UI/IPC/storage/deploy หลายชั้น |
| [OpenCode](https://api.github.com/repos/anomalyco/opencode) | 2025-04-30 | 207,082 | ใหม่; หลาย packages และ interfaces |
| [Roo Code](https://api.github.com/repos/RooCodeInc/Roo-Code) | 2024-10-31 | 24,305 | ไม่ถึงสองปี; migration 103 files; ปัจจุบัน archived |
| [Cline](https://api.github.com/repos/cline/cline) | 2024-07-06 | 67,938 | เกินสองปี; งาน desktop/sidecar ล่าสุดมีหลักฐานละเอียด |
| [Goose](https://api.github.com/repos/aaif-goose/goose) | 2024-08-23 | 54,211 | เกินสองปีเล็กน้อย; มี architecture migration parity |
| [OpenHands](https://api.github.com/repos/OpenHands/OpenHands) | 2024-03-13 | 87,764 | เก่ากว่า; มี invocation/review และ failure case |

อายุไม่ใช่ตัวแทนของ AI usage เคสส่วนมากเป็นงานปี 2026; OpenHands เดือน พ.ค. 2025 และ OpenCode #6014 เดือน ธ.ค. 2025 เป็นข้อยกเว้นที่คงไว้เพราะมี workflow evidence ต่างจากเคสใหม่

<a id="c1"></a>

## C1 — Dyad #4187: feature ข้าม UI, deploy, database และ auth

**ชนิดงาน:** feature + cross-module · **หลักฐาน AI:** D-การเปิดเผยโดยผู้เขียน PR และคำตอบที่กำกับว่า Claude สร้าง · **ช่วงงาน:** เปิด 4 ส.ค. และ merge 14 ส.ค. 2026

[PR #4187 — feat(coolify): deploy apps to a self-hosted server](https://github.com/dyad-sh/dyad/pull/4187) โดย RyanGroch เพิ่ม Coolify เป็นปลายทาง deploy หลัง experiment flag พร้อมระบบตั้งค่า UI และ deployment pipeline PR เปิดเผยว่าทั้ง description และ code สร้างด้วย Claude นี่เป็นหลักฐานการเปิดเผยของ contribution ไม่ใช่การพิสูจน์ทุกบรรทัด

[GitHub metadata](https://api.github.com/repos/dyad-sh/dyad) ระบุ repo สร้าง 11 เม.ย. 2025 และมี 21,519 stars ณ วันที่ตรวจ เป็น AI app builder; [PR metadata](https://api.github.com/repos/dyad-sh/dyad/pulls/4187) ระบุ 71 changed files และ 126 commits ที่ปลายงาน จำนวนนี้รวมวิวัฒนาการของ PR ไม่ใช่ขนาด initial task

### เส้นทาง context เท่าที่มองเห็น

| ขั้น | หลักฐานและขอบเขต |
|---|---|
| Task / issue | **D-artifact:** PR อธิบาย deploy ไป Coolify ที่มีอยู่ และอ้างเอกสาร Basecamp; **U:** เนื้อหา Basecamp และ task brief ที่ส่งให้ agent ไม่ปรากฏในหลักฐานที่ตรวจ |
| Initial instructions | **U:** ไม่มี prompt ตั้งต้นหรือ runtime/system context ให้ตรวจครบ |
| Repository instructions | **D-artifact:** [AGENTS ที่ 8e6d0d0](https://github.com/dyad-sh/dyad/blob/8e6d0d0245f6e5159badb5ef8a45e91ce81d8736/AGENTS.md) มีตาราง Read when และชี้ CONTRIBUTING; **D-report:** คำตอบใน review อ้าง rule รายไฟล์; **U:** ลำดับโหลดและการอ่านก่อนเริ่ม |
| Docs / architecture | **D-artifact:** [CONTRIBUTING ณ revision เดียวกัน](https://github.com/dyad-sh/dyad/blob/8e6d0d0245f6e5159badb5ef8a45e91ce81d8736/CONTRIBUTING.md) ชี้ `docs/architecture.md` และ agent architecture; **U:** implementer เปิด architecture doc ใดจริง |
| Code discovery | **D-artifact/report:** review ระบุ path และ helper ของ Vercel/Neon; **U:** คำค้นและรายการไฟล์ที่อ่าน |
| Existing implementation / analogue | **D:** [review](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3709212241) ชี้ flow เดิม; [reply](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717925547) ระบุ reuse helper และ [patch](https://github.com/dyad-sh/dyad/commit/43110685df945df319bf0cea53030707f2ffbf26) แสดง imports/calls ที่เปลี่ยน |
| Tests / contracts | **D-artifact:** patch เพิ่ม assertions ของ env, branch และ trusted origin; **D-report:** reply รายงานว่าเจอ auth 500 ใน testing; **U:** raw live-login run ที่ผูกกับคำรายงานนั้น |
| Implementation | **D-artifact:** commit แก้ env resolver ให้ใช้ helper ร่วมกับ Vercel; มีโค้ดและ tests ตรวจกลับได้ |
| Review feedback | **D-artifact:** reviewers ชี้ auth, classification, IPC invalidation และช่องโหว่ใน test coverage |
| Additional context discovered | **D-report:** reply ระบุว่าการแก้ auth ยังแก้การไม่เคารพ database branch ที่ผู้ใช้เลือก; **I:** review ช่วยขยายขอบเขต contract ที่นำมาพิจารณา; **U:** สิ่งนี้เพิ่งถูกรู้ครั้งแรกใน session หรือไม่ |
| เมื่อไรหยุดค้น / handoff | **U:** ไม่มีเกณฑ์หยุดก่อน implementation และไม่มี payload ส่งต่อ session/subagent; มีเหตุผลรับ/เลื่อน finding ใน PR แต่ไม่ใช่ trace การจัด context |

### ลูป A: review ชี้ analogue แล้ว contract ที่หลุดปรากฏเพิ่ม

1. **D:** 4 ส.ค. [Codex reviewer](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3709212241) ชี้ว่า connection string อย่างเดียวไม่ครบสำหรับ Neon Auth และให้เทียบ flow เดิมของ Vercel
2. **D-report:** 5 ส.ค. [คำตอบที่กำกับว่า Claude สร้าง](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717925547) รายงานอาการ 500, ระบุ helper ที่ใช้ และบอกว่าพบการเลือก branch ผิดเพิ่ม
3. **D-artifact:** [43110685df945df319bf0cea53030707f2ffbf26](https://github.com/dyad-sh/dyad/commit/43110685df945df319bf0cea53030707f2ffbf26) เพิ่ม `getSelectedDeployBranchType`, `resolveNeonBranchEnvVars`, `ensureNeonAuthTrustedDomain` พร้อม tests ของ behavior เหล่านี้
4. **I:** analogue ทำหน้าที่เก็บ contract ที่กระจายอยู่หลายส่วน และ review เป็นช่องทางนำ contract กลับมาสู่งาน
5. **U:** พิสูจน์ไม่ได้ว่า defect เกิดจากไม่อ่าน helper หรืออ่านแล้วตีความผิด ความสัมพันธ์ที่เห็นคือ defect → feedback → คำตอบ/patch ไม่ใช่บันทึกสภาวะความรู้ภายใน

### ลูป B: กฎถูกนำมาอ้างในคำตอบจริง

**D:** [review เรื่อง invalid token](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3709262819) ให้จัดเป็น Auth; [reply](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717927845) อ้าง `rules/dyad-errors.md` และ analogue ของ Neon/Vercel/model client โดยตรง [ตัวกฎ ณ 8e6d0d0](https://github.com/dyad-sh/dyad/blob/8e6d0d0245f6e5159badb5ef8a45e91ce81d8736/rules/dyad-errors.md) มีการแยก kind จริง จึงเชื่อม “rule มีอยู่” กับ “ถูกอ้างเป็นเหตุผล” ได้

**D:** [อีก reply](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717934535) อ้าง `rules/windows-spawn.md`; [review IPC](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3725757214) มีลิงก์ rule พร้อม SHA และบรรทัดเฉพาะ นี่คือ context pointer ใน feedback ที่จับต้องได้ **U:** agent เปิด target ผ่าน tool หรือได้รับ excerpt จากคน/เครื่องมือช่องทางใด

### การจำกัด context และการตัด scope

**D-report:** [review summary 14 ส.ค.](https://github.com/dyad-sh/dyad/pull/4187#issuecomment-5288401457) เปิดเผยว่า patch ของ test file ถูกตัดและไม่ได้ตรวจเนื้อหาไฟล์นั้น **U:** ไม่เห็น payload เต็มของ reviewer หรือหลักฐานว่าเกิดจาก token limit เท่าไร จึงไม่สรุปเหตุเชิงเทคนิคเกินข้อความ

**D-report:** [คำตอบเรื่อง coordination](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3785713522) แยกเงื่อนไขของ rule ออกจาก race ที่ยังควรแก้ และระบุว่าการแก้เต็มต้องเปลี่ยน public API กว้างกว่า PR นี้ **I:** context ใหม่อาจนำไปสู่การแยก follow-up ไม่จำเป็นต้องขยาย patch เดิมทุกครั้ง

**Revision note:** ปลายงาน base `c1a9b9e29e7c0dd314b1629f6d2bcd9df2a8bece`, head `6e5abff6dad5355c5ebffb7c884ea54a57aacf52`, merge `ba782f433205935979de8a9cc2d606944fe534a1` ตาม [metadata](https://api.github.com/repos/dyad-sh/dyad/pulls/4187) เอกสารด้านบนอ่านที่ parent `8e6d0d0...` ของ [revision `da0836ded5...`](https://github.com/dyad-sh/dyad/commit/da0836ded506331b80b882e562a4f3448cec1145) ที่ review รอบแรกระบุ ไม่อ้างว่าเป็นไฟล์ที่ runtime โหลดจริง; SHA `43110685...` เป็น patch ที่คำตอบเดิมอ้างและยังเข้าถึงได้ ลำดับปัจจุบันมี SHA ต่างหลังประวัติถูกปรับ

**นำไปใช้ — I:** งาน feature ใหม่ควรค้น analogue ที่ดูแล integration เดียวกันก่อนนิยาม contract เอง และให้ review ส่งตำแหน่ง rule/consumer ที่ขาดเข้ามาได้ **ยังไม่พิสูจน์:** progressive disclosure ลด token/rework เท่าไร หรือ implementer ปฏิบัติตาม index ตั้งแต่ต้น

<a id="c2"></a>

## C2 — OpenHands: review เติมแผนที่ context และมีงานที่ยังแก้ไม่สำเร็จ

### C2a — #8310 / #8304: tool-calling compatibility

**ประเภท:** bug fix + compatibility · **ช่วงงาน:** 6–17 พ.ค. 2025 · **D-หลักฐาน AI:** [PR #8310](https://github.com/OpenHands/OpenHands/pull/8310) ระบุเป็น automatic OpenHands fix และมีการเรียก agent/คำตอบแก้ไขใน discussion

[Issue #8304](https://github.com/OpenHands/OpenHands/issues/8304) รายงาน non-native tool calling ล้มเหลวเมื่อปิด built-in tools ใน OpenHands 0.36.1 ส่วน PR มี 27 commits และ final diff 8 ไฟล์ การแก้รวมงาน agent กับการแก้ conflict/เก็บรายละเอียดโดยคน จึงไม่ถือว่า final patch ทั้งหมดเป็นฝีมือ agent

| ขั้น | หลักฐานและขอบเขต |
|---|---|
| Task / issue | **D:** issue ให้ symptom/version; **U:** ไม่มี reproduction transcript ครบ |
| Initial instructions | **D:** PR ระบุ automatic fix; review เป็น context เพิ่มหลัง initial attempt; **U:** assembled initial prompt และ system context |
| Repository instructions | **D:** [historical repo microagent](https://github.com/OpenHands/OpenHands/blob/722711db3b5beb470aaac4d533b5ac87088ffc07/.openhands/microagents/repo.md) และ [CONTRIBUTING](https://github.com/OpenHands/OpenHands/blob/722711db3b5beb470aaac4d533b5ac87088ffc07/CONTRIBUTING.md) มี setup/module/test pointers; **U:** run นี้โหลดไฟล์เหล่านั้นหรือไม่ |
| Docs / architecture | **D:** [maintainer architecture map](https://github.com/OpenHands/OpenHands/pull/8310#issuecomment-2855353576) อธิบาย compatibility layer ของ CodeAct และเสนอทางแก้; **U:** เอกสารภายนอกที่ agent อ่าน |
| Code discovery | **D:** reviewer ระบุ `fn_call_converter.py`, caller ใน `llm.py`, `codeact_agent.py`, `function_calling.py`; **U:** actual search/read order |
| Analogue | **D:** review อธิบาย static in-context example เดิมและชี้ tests ของ behavior เก่า; concrete transcript ปรากฏใน comment วันที่ 17 พ.ค.; **I:** ใช้เป็น contract ตั้งต้นได้; **U:** agent ค้น analogue เองก่อน review หรือไม่ |
| Tests / contracts | **D:** [diff](https://github.com/OpenHands/OpenHands/pull/8310/files) เปลี่ยน `tests/unit/test_llm_fncall_converter.py`; [maintainer comment](https://github.com/OpenHands/OpenHands/pull/8310#issuecomment-2855448885) รายงาน unit-test failures และให้แก้ที่ tests เดิม; **U:** raw logs ครบ |
| Implementation | **D:** dynamic tool examples, tool-name module และ tests ปรากฏใน diff/commits; มี human amendments |
| Review | **D:** มีการสั่งแก้ซ้ำ เช่น [discussion_r2083685712](https://github.com/OpenHands/OpenHands/pull/8310#discussion_r2083685712) และการประเมินเพิ่มเติม [review-2847914134](https://github.com/OpenHands/OpenHands/pull/8310#pullrequestreview-2847914134) |
| Additional context | **D-report/artifact:** เพิ่ม architecture pointers, ที่อยู่ tests, ตัวอย่าง transcript และ evaluation discussion หลัง initial attempt; **I:** feedback ขยาย contract ที่ต้องตรวจ |
| หยุดค้น / handoff | **D:** agent รายงานเสร็จและมีการแก้ต่อก่อน merge; **U:** เกณฑ์หยุดค้นภายใน, payload ข้าม session/subagent |

**I:** เคสนี้รองรับ progressive disclosure ผ่านการสนทนาทำงาน: issue ที่ยังบาง → reviewer เติมกลไกและตำแหน่ง → tests ชี้ contract → evaluation เพิ่มข้อจำกัดการใช้งาน ไม่ได้พิสูจน์ว่า agent เดินทางนี้เองอย่างอัตโนมัติ

**U:** [Action run ที่ PR ลิงก์](https://github.com/OpenHands/OpenHands/actions/runs/14865734014) ตอบ 404 ตอนตรวจ จึงใช้ยืนยัน prompt/tool calls ไม่ได้ [resolver source ณ historical revision](https://github.com/OpenHands/OpenHands/blob/722711db3b5beb470aaac4d533b5ac87088ffc07/openhands/resolver/resolve_issue.py) อธิบายกลไกประกอบ request ได้ในระดับ D-code แต่ไม่ใช่ execution log ของ #8310

**D-report:** [agent implementation report](https://github.com/OpenHands/OpenHands/pull/8310#issuecomment-2855377889) ตามด้วย [correction report](https://github.com/OpenHands/OpenHands/pull/8310#issuecomment-2855474729); maintainer ยังต้อง [ย้ำตำแหน่ง test](https://github.com/OpenHands/OpenHands/pull/8310#issuecomment-2855519317) ก่อน [agent ตอบเรื่อง coverage](https://github.com/OpenHands/OpenHands/pull/8310#issuecomment-2855533872) นี่เป็นวงจรสื่อสาร context ที่เห็นจากข้อความสาธารณะ

Revision: head `bb767e8a1809f7815875d15c5ea09ffd406e710d`, merge `c17b0ebfc6195fd37bea999abbc629da4335c0ad`; [commits](https://github.com/OpenHands/OpenHands/pull/8310/commits) ใช้ดู chronology เอกสาร `722711db...` เป็น historical snapshot ที่อ่านประกอบ ไม่อ้างเป็น initial checkout ที่พิสูจน์จาก run

### C2b — #8252 / #8250: task ให้ทางค้นแล้ว แต่ patch ยังไม่ตอบ

**ประเภท:** debugging/build tooling · **สถานะ:** เปิดและปิด 4 พ.ค. 2025 โดยไม่ merge

**D:** [issue #8250](https://github.com/OpenHands/OpenHands/issues/8250) ขอให้ตาม chain ของ terminal `git commit`, เปรียบเทียบ frontend กับ Python และชี้ Makefile/Husky [PR #8252](https://github.com/OpenHands/OpenHands/pull/8252) ระบุ automatic fix attempt แต่ maintainer ทักว่าการเพิ่ม hook-type ยังไม่แก้สาเหตุ แล้วชี้กลับไป `.husky` และ Python config คำตอบรอบถัดไปยังยอมรับว่าไม่จบ และ PR ถูกปิด

หลักฐานเฉพาะ **D-report**: [initial rejection](https://github.com/OpenHands/OpenHands/pull/8252#issuecomment-2848884629) → [agent บอก root cause ยังไม่รู้และยังไม่ได้เทียบ frontend/Python](https://github.com/OpenHands/OpenHands/pull/8252#issuecomment-2848887157) → [maintainer ชี้ Husky/dev_config](https://github.com/OpenHands/OpenHands/pull/8252#issuecomment-2848892132) → [final unresolved report](https://github.com/OpenHands/OpenHands/pull/8252#issuecomment-2848894552)

**D-artifact:** [final files](https://github.com/OpenHands/OpenHands/pull/8252/files) มี config/dependency/symlink/test changes รวม 7 ไฟล์ โดยไม่มีการแก้ `frontend/.husky/pre-commit` **U:** การไม่เปลี่ยนไฟล์ไม่พิสูจน์ว่า agent ไม่อ่านมัน และข้อความ issue ก็ไม่พิสูจน์ว่า assembled prompt ส่งทั้งหมดเข้า model

| Context stage | สิ่งที่สรุปได้ |
|---|---|
| Task → initial input | **D:** issue มีคำถามและ pointers ชัด; **U:** initial runtime prompt |
| Instructions → architecture | **D:** historical repo guide/config กับ issue แสดง chain ที่ควรตรวจ; **U:** consumption |
| Discovery → analogue | **D:** review ให้ตรวจ Husky และใช้ frontend เป็นตัวเทียบ; **U:** การค้น/เปรียบเทียบที่ agent ทำจริง |
| Tests → implementation | **D:** commits และคำรายงานว่าปัญหายังไม่จบ; **U:** evidence ว่าทดลอง terminal commit path สำเร็จ |
| Review → context ใหม่ | **D:** maintainer เพิ่ม path/คำชี้แจงและ agent ตอบหลายรอบ; **I:** supplied context ยังไม่แปรเป็นการพิสูจน์สาเหตุที่ตรงโจทย์ |
| Stop / handoff | **D:** ปิดโดยไม่ merge; **U:** เกณฑ์ภายในของ agent และการส่งต่อ session |

**I — บทเรียนเชิงลบ:** context ที่เตรียมไว้ละเอียดไม่ได้รับประกันว่าจะถูกใช้หรือตีความถูก การให้ agent แสดง causal path และ reproduction ที่ตรง trigger มีเหตุผลมากกว่านับจำนวนเอกสารที่มีอยู่ **U:** ยังฟันธงไม่ได้ว่า failure มาจาก retrieval, reasoning, tool environment หรือหลายอย่างร่วมกัน

Revision: compare base `722711db3b5beb470aaac4d533b5ac87088ffc07`, head `d531237ab7586fdc80c27f40ddcfd7793b3a8d44` ตาม [commit history](https://github.com/OpenHands/OpenHands/pull/8252/commits)

<a id="c3"></a>

## C3 — OpenCode: แยกคำสั่งเรียกจริง, UI hints และ AI attribution

[Repository metadata](https://api.github.com/repos/anomalyco/opencode) ระบุสร้าง 30 เม.ย. 2025, 207,082 stars ณ วันที่ตรวจ เป็น coding-agent product; หลักฐาน implementation ต้องดูแยกราย contribution ด้านล่าง

### C3a — #5937 → #6014: เห็นคำสั่งเรียก แต่ session เปิดไม่ได้

**ประเภท:** TUI feature/bug fix · **D:** [issue #5937](https://github.com/anomalyco/opencode/issues/5937) รายงานว่า docs บอกให้เลือก Other แต่ใน `/connect` หาไม่พบ และมี [คำสั่ง `/oc` จริง](https://github.com/anomalyco/opencode/issues/5937#issuecomment-3685275707) ขอให้แก้ TUI และพิจารณา server ถ้าจำเป็น [คำตอบ bot](https://github.com/anomalyco/opencode/issues/5937#issuecomment-3685293218) ลิงก์ [PR #6014](https://github.com/anomalyco/opencode/pull/6014), run และ session

| ขั้น | หลักฐานและขอบเขต |
|---|---|
| Task / issue | **D:** symptom, reproduction, expected Other option และ environment อยู่ใน issue |
| Initial instructions | **D:** exact invocation comment; **U:** context ที่ action ประกอบทั้งหมด |
| Repository instructions | **D:** [run/workflow](https://github.com/anomalyco/opencode/actions/runs/20453017602/workflow) มี checkout และการเรียก OpenCode; **U:** ไฟล์ instruction ที่โหลดจริง |
| Docs / architecture | **D:** issue ชี้ความไม่ตรง docs; PR อธิบาย credential/config boundary; **U:** docs ที่ agent เปิดเอง |
| Code discovery | **D:** [commit](https://github.com/anomalyco/opencode/commit/499ae9f32a7569190efd7dbf19efa2b836cd3169) แก้ `dialog-provider.tsx`; **U:** ไฟล์ที่ค้นหรืออ่านก่อน patch |
| Analogue | **D-report:** PR ระบุว่าเลียนแบบ CLI auth login ทั้ง validation และ config warning; **U:** log การเปิด CLI code |
| Tests / contracts | **D:** expected UI อยู่ใน issue; diff ไม่เพิ่ม test; **U:** behavior test จริง การที่ action สำเร็จไม่ตอบข้อนี้ |
| Implementation | **D:** bot-authored commit เพิ่ม Other และ custom-provider input flow 1 ไฟล์ |
| Review | **D:** มี `/review` และ bot ตอบ lgtm ใน PR; **U:** เนื้อหาการตรวจและเหตุผลปิด |
| Additional context | **U:** ไม่พบ follow-up ที่พิสูจน์ context ใหม่ถูกใช้แก้ PR นี้ |
| Stop / handoff | **D:** PR เปิด 23 ธ.ค. และปิด 26 ธ.ค. 2025 โดยไม่ merge; **U:** internal stopping rule และสาเหตุที่ไม่ merge |

**D:** session link [xCAflZA6](https://opencode.ai/s/xCAflZA6) มีอยู่ใน issue/PR แต่การตรวจเข้าถึงรอบนี้ไม่ได้นำ transcript กลับมา (การตรวจโดยนักวิจัยคู่ขนานได้ 404; การเปิดอีกช่องทางถูกปฏิเสธ) **U:** search, file reads, token usage และ handoff ภายใน session

**I:** issue/comment เป็นทางส่ง context ที่ชัด และ PR ระบุ analogue ได้ **U:** ไม่ควรสรุปว่า agent โหลด issue ทุกข้อความหรือ AGENTS ตามเอกสาร integration ปัจจุบันโดยไม่มี historical execution evidence

[PR metadata](https://api.github.com/repos/anomalyco/opencode/pulls/6014): 1 commit, 1 file; base `5843eca7d6db0acf7ec4db58a736649de68f13ba`, head `499ae9f32a7569190efd7dbf19efa2b836cd3169`

### C3b — #47265 → #47455: issue เป็น pointer สำหรับ UI

**ประเภท:** Web UI · **ช่วงงาน:** issue 4 ก.ย., PR 5 ก.ย., merge 9 ก.ย. 2026

**D:** [issue #47265](https://github.com/anomalyco/opencode/issues/47265) ให้ task ID ที่มี child-session ID อยู่แล้วและชื่อ `sessionHref`/`navigateToSession` พร้อมขอบเขต UI [PR #47455](https://github.com/anomalyco/opencode/pull/47455) เปิดผ่าน opencode-agent bot และระบุว่า requested by Brendonovich via Slack **U:** ข้อความ Slack และหลักฐานที่แยกได้ว่า model ผลิตแต่ละส่วนของ code; bot author เพียงอย่างเดียวจึงจัดเป็นหลักฐาน workflow ที่ผ่าน agent integration ไม่ยกระดับเป็นการยืนยัน AI authorship ทั้ง patch

**D-artifact:** [ee2ca0c1](https://github.com/anomalyco/opencode/commit/ee2ca0c1ce671da267546fa468894116b02c43d8) และ [99a101c2](https://github.com/anomalyco/opencode/commit/99a101c2d67da0893964fdb37c7cc07e2b15870f) แสดงการ reuse navigation และเพิ่ม regression tests **D-report:** PR ระบุการตรวจ click, keyboard, modified/middle click, narrow layout, cache-missing child และการกลับ parent; **U:** raw local logs ตามตัวเลขทั้งหมด

| ส่วนของ workflow | หลักฐาน |
|---|---|
| Task / initial prompt | **D:** issue กับคำรายงานว่า request มาทาง Slack; **U:** actual prompt |
| Instructions / docs | **D:** มี repository docs; **U:** historical version ที่ run ใช้และการโหลดจริง |
| Discovery / analogue | **D:** issue ให้ helper pointers และ patch reuse; **U:** ลำดับค้น/อ่าน |
| Contract / implementation | **D:** tests/diff สำหรับ interaction; **I:** issue ใช้เป็นแผนที่ย่อของเส้นทาง UI ได้ |
| Review / additional context | **D:** มีการส่งให้ code owners; **U:** substantive review และการพบ context ใหม่ใน session |
| Stop / handoff | **D:** PR merge และมีผู้รับ review; **U:** internal stop/subagent payload |

**I:** ใช้เคสนี้สอนว่า “make clickable” ต้องแปลงเป็น interaction contract; ไม่ใช้เป็นหลักฐานว่า agent ตัดสินใจสร้าง matrix นี้เอง คำว่า subagent ใน feature หมายถึงสิ่งที่ผลิตภัณฑ์แสดง ไม่ใช่หลักฐานว่า implementer ใช้ subagents ทำ PR

Revision ปลายงานหลัง force-push: base `f9bc2233ddcc11503a0804b317401bc221ef0e7f`, head `99a101c2d67da0893964fdb37c7cc07e2b15870f`, merge [f1ce69d2](https://github.com/anomalyco/opencode/commit/f1ce69d2ceae4ed7e39c49210ae9264cbf86ffec)

### C3c — #44281: review เพิ่ม contract ของ test oracle

**ประเภท:** provider bug fix · **ช่วงงาน:** 23–24 ส.ค. 2026

**D:** [issue #44280](https://github.com/anomalyco/opencode/issues/44280) และ [PR #44281](https://github.com/anomalyco/opencode/pull/44281) อธิบาย mismatch ของ model ID ระหว่าง catalog กับ native provider wire; [implementation commit](https://github.com/anomalyco/opencode/commit/29dec99e6784f9277be14074b1f0c2b527c31126) และ [follow-up](https://github.com/anomalyco/opencode/commit/70ae4617a2edbe94c0e5450a019cf39aeaf58708) มี Claude co-author trailers จัดเป็นการเปิดเผย AI participation ไม่ใช่ execution trace

**D-report/artifact:** [automated review](https://github.com/anomalyco/opencode/pull/44281#issuecomment-5384523212) ทัก translation ที่อยู่ทั้ง production และ test harness [ผู้เขียนตอบ](https://github.com/anomalyco/opencode/pull/44281#issuecomment-5390195804) ว่าจะคง oracle อิสระและเพิ่ม invariant แทนดึง logic มาใช้ร่วมกัน; follow-up commit บันทึกเหตุผลนั้น **I:** review นำ context เรื่องหน้าที่ของ test เข้ามา ไม่ได้มีแค่ production API contract

**U ร่วมของเคสนี้:** initial prompt, instruction loading, architecture docs ที่อ่าน, exact discovery/analogue search, raw live-test logs, session/subagent handoff และเหตุผลหยุดค้น **D ที่เห็น:** task description → disclosed implementation → review → follow-up patch → merge ส่วน tests ที่รายงานใน PR ยังต้องอ่านเป็น D-report

[Metadata](https://api.github.com/repos/anomalyco/opencode/pulls/44281): 3 commits, 2 files; base `55f984126cbe26920e532d1e2b09cb16482cb451`, head `7183a7915464727578e3a7a459e0313d3e4f051c`, merge [f8b4dd70](https://github.com/anomalyco/opencode/commit/f8b4dd70ac26996436e259fc386917944c05f481)

<a id="c4"></a>

## C4 — Cline #13969: UI recovery ต้องเข้าใจ lifecycle

**ประเภท:** desktop bug fix + UI/runtime cross-module · **ช่วงงาน:** 8–9 ก.ย. 2026

**D-หลักฐาน AI:** [commit แรก e3b2e375](https://github.com/cline/cline/commit/e3b2e375c7f4e0c09cfef277ce5031c0bf8d5168) มี Claude co-author และ session URL [PR #13969](https://github.com/cline/cline/pull/13969) อธิบาย desktop ไม่แสดง recovery เมื่อเกิด invalid tool calls ติดต่อกัน ทั้งที่ CLI มี callback นี้แล้ว

| ขั้น | หลักฐานและขอบเขต |
|---|---|
| Task / issue | **D-report:** PR อ้าง desktop user report; **U:** original user task/prompt เป็น N/A public issue |
| Initial instructions | **U:** ไม่เห็นคำสั่งเริ่มหรือ assembled context |
| Repository instructions | **D-artifact:** [AGENTS ที่ first commit](https://github.com/cline/cline/blob/e3b2e375c7f4e0c09cfef277ce5031c0bf8d5168/AGENTS.md) มีโครงสร้าง desktop/sidecar และคำสั่งตรวจ; **U:** โหลดจริงหรือไม่ |
| Docs / architecture | **D-report:** PR อธิบาย SDK callback, sidecar และ question UI ที่มีอยู่; **U:** architecture doc ที่อ่าน |
| Code discovery | **D-artifact:** commit เปลี่ยน `sidecar/chat-session.ts` และ tests; **U:** คำค้น/ไฟล์ทั้งหมดที่อ่าน |
| Analogue | **D-report:** commit/PR ระบุ CLI เป็น reference และใช้ `ask-question` เดิม; **U:** actual read ของ CLI implementation |
| Tests / contracts | **D-report:** scripted probe พบว่าถามซ้ำ และ callback เองไม่ได้พัก execution ระหว่างรอคำตอบ; **D-artifact:** มี tests ของ hooks, cleanup, steering และ UI state |
| Implementation | **D-artifact:** [commit timeline](https://github.com/cline/cline/pull/13969/commits) แสดงการแก้หลายรอบโดยใช้ existing SDK hooks/callbacks |
| Review | **D-review (Greptile bot):** [cleanup finding](https://github.com/cline/cline/pull/13969#discussion_r3962894505), [iteration finding](https://github.com/cline/cline/pull/13969#discussion_r3963154102), [hydration finding](https://github.com/cline/cline/pull/13969#discussion_r3963617983) ระบุเงื่อนไขที่ patch ใน revision ที่ตรวจยังไม่ครอบคลุม ไม่ใช่หลักฐานว่า Claude ผู้เขียนค้นพบเอง |
| Additional context | **D-report/artifact:** PR อธิบายว่าส่ง guidance กลับจาก callback ไม่ถึง live model ต้องใช้ steering และ awaited hooks; **I:** การตรวจจริงขยาย context จาก callback ไป iteration/lifecycle |
| Stop / handoff | **U:** internal stop rule, session contents และ handoff; **D:** merge และ published validation report |

**D-report:** PR รายงาน browser webview + sidecar + isolated hub ใช้ scripted provider ตรวจก่อน/หลัง Continue และ Stop; ระบุ 905 tests ผ่านและ 1 failure ที่ผู้เขียนจัดว่า unrelated พร้อมข้อจำกัดว่าไม่ได้ทดสอบ native Tauri/live Kimi ครบ จึงไม่เขียนว่า “ทุก tests ผ่าน”

**D:** [Claude session 01XJb3VtvdSm9xk9opJ3Q9G6](https://claude.ai/code/session_01XJb3VtvdSm9xk9opJ3Q9G6) มีลิงก์ใน commit แต่เปิดไม่สำเร็จ (HTTP 403/challenge) **U:** agent เห็นแต่ละ finding ใน turn ใด และใช้ agent ตัวเดิมหรือไม่

**I — นำไปใช้:** งาน UI ที่ควบคุม runtime ควรค้นทั้ง working analogue และทุกทางสร้าง/ทำลาย state: start, rebuild, fork, restore, cancel รวม behavior ที่เกิดระหว่างรอคำตอบ **U:** ไม่ใช้ชื่อ paths จาก diff ย้อนแต่งว่า agent ค้นตามลำดับนี้

Revision ปลายงาน: base `9df2876c89e6a1735426b0946f39264adcf8b8d7`, head `7ed28e895c2db946d8a514c99fd24af5c3878d92`, merge [23f2197c](https://github.com/cline/cline/commit/23f2197c535f904bb4bbe17012fc81cdf3b2b8ac); first commit e3b2e375 มี parent `79bf1e8c48e468028bb8b2595c5650c66c9b3f46` ซึ่งต่างจาก base ปลายงาน [PR](https://github.com/cline/cline/pull/13969) มี 11 commits, 7 files

### เคสประกอบ #13968: code diagnosis กับ runtime verification ต่างกัน

**D-report/artifact:** [PR #13968](https://github.com/cline/cline/pull/13968) และ [commit f32bf5f](https://github.com/cline/cline/commit/f32bf5f97ef7328021857365e31bc3de5ff3a463) ที่มี Claude attribution อธิบาย duplicate delivery จาก core/hub และ index ที่ข้าม sidecar restart มี live comparison กับ canonical store ใน PR discussion พร้อมรายการสิ่งที่ยัง reproduce ไม่ได้ **U:** [session 01CNoho8fGgnh71xjQF5xMqy](https://claude.ai/code/session_01CNoho8fGgnh71xjQF5xMqy) ถูก challenge จึงไม่เห็น read trace

**I:** test oracle ที่เป็น canonical store ช่วยตอบคำถามเชิง behavior ซึ่งการอ่าน code เพียงอย่างเดียวยังไม่ตอบ แต่การมีรายงาน probe ไม่ได้พิสูจน์ว่า agent เป็นผู้ค้นพบทุกข้อเอง

<a id="c5"></a>

## C5 — Roo Code #11409: migration ต้องตาม reader และความล้มเหลวของ storage

**ประเภท:** refactor/migration ข้าม providers และ persistence · **เหตุการณ์:** 11 ก.พ. 2026 · **ขนาด:** 103 files, 11 commits ตาม [PR metadata](https://api.github.com/repos/RooCodeInc/Roo-Code/pulls/11409)

**D-หลักฐาน AI:** [PR #11409](https://github.com/RooCodeInc/Roo-Code/pull/11409) เปิดเผย Generated with Claude Code และ [native wiring commit cb4bfc9](https://github.com/RooCodeInc/Roo-Code/commit/cb4bfc9997081683ec72848ead28272de36fa272) มี Claude co-author; [foundation commit 21f4354](https://github.com/RooCodeInc/Roo-Code/commit/21f4354e2ef8dfd1f3ba214fe9435016d7466789) ไม่มี trailer นี้ จึงไม่ใช้ยืนยัน attribution ของ commit นั้น งานเปลี่ยนจาก Anthropic `ApiMessage` ไป `RooMessage` ที่ห่อ AI SDK `ModelMessage` พร้อม native response messages

| ขั้น | หลักฐานและขอบเขต |
|---|---|
| Task / issue | **D-report:** PR อธิบาย second-turn validation error; commits อ้าง EXT-646/647; **U:** internal ticket และ prompt เต็ม |
| Initial instructions | **U:** ไม่ปรากฏ session setup/initial prompt |
| Repository instructions | **D:** [root AGENTS ที่ foundation](https://github.com/RooCodeInc/Roo-Code/blob/21f4354e2ef8dfd1f3ba214fe9435016d7466789/AGENTS.md) มีคำแนะนำ Settings View; **U:** ไม่ยืนยันว่ากฎนี้มีบทบาทกับ migration หรือถูกอ่าน |
| Docs / architecture | **D-artifact:** implementation แสดง contract ของ version envelope, converter และ Task/provider wiring; **U:** architecture/SDK docs ที่เปิดจริง |
| Code discovery | **D:** diff ครอบคลุม providers, `Task.ts`, readers/export และ tests; **U:** search/read inventory |
| Analogue / contracts | **D:** converter และ backward format ปรากฏใน code; [native wiring commit](https://github.com/RooCodeInc/Roo-Code/commit/cb4bfc9997081683ec72848ead28272de36fa272) ใช้ SDK response messages; **U:** agent ค้นพบครบก่อนแก้หรือไม่ |
| Tests | **D-report:** PR ระบุ automated suite 5,469 tests ผ่าน แต่ provider manual smokes 5 ข้อยังไม่ติ๊ก; **U:** raw logs และผล smoke ที่ไม่ได้รายงาน |
| Implementation | **D:** foundation → provider wiring → follow-up commits เป็นลำดับ artifact; **I:** แบ่ง seam ของ migration ได้; ไม่ใช้เรียก hidden plan |
| Review | **D:** comments ชี้ reader ที่ไม่รองรับ envelope, save-return handling, image shape และ pending tool results |
| Additional context | **D-report (automated review):** [re-review](https://github.com/RooCodeInc/Roo-Code/pull/11409#issuecomment-3885766946) ระบุว่ามีการแก้ประเด็นหลัง 984857e; **I:** consumer/failure contracts ถูกทำให้ชัดขึ้นใน review |
| Stop / handoff | **D:** merge; **U:** internal sufficiency criterion, agent handoff และ transcript ไม่มี session link ของ implementer ที่ตรวจพบ |

### Contract ที่ review ทำให้เห็น

| ช่องว่างใน patch ตาม reviewer — D | Context ที่ต้องนำกลับมาพิจารณา — I |
|---|---|
| [Export reader ยังใช้ raw JSON.parse](https://github.com/RooCodeInc/Roo-Code/pull/11409#discussion_r2794507746) | consumer นอก main chat loop ต้องอ่าน v2 envelope ได้ |
| [Orphan filtering จับแต่ tool-call แบบใหม่](https://github.com/RooCodeInc/Roo-Code/pull/11409#discussion_r2794630411) | legacy histories และ dual-format guards ที่มีอยู่ |
| [save คืน false แต่ caller รายงาน true](https://github.com/RooCodeInc/Roo-Code/pull/11409#discussion_r2794842545) | failure semantics/retry เป็น contract แม้ type จะผ่าน |
| [Image มีทั้ง raw base64, data URL และ HTTP URL](https://github.com/RooCodeInc/Roo-Code/pull/11409#discussion_r2794842548) | concrete data shapes ที่ representation ใหม่อนุญาต |
| [ล้าง pendingToolResults หลัง save ที่อาจ fail](https://github.com/RooCodeInc/Roo-Code/pull/11409#discussion_r2794842551) | persistence success เป็นเงื่อนไขของ protocol-state cleanup |

**D-artifact:** [follow-up e37585fa](https://github.com/RooCodeInc/Roo-Code/commit/e37585fa87fcddfb3c457c4cc71549632402beb7) แก้ double cast, dual-format orphan filtering และ comment ก่อนรอบท้าย **D-report (automated review):** [re-review หลัง 984857e](https://github.com/RooCodeInc/Roo-Code/pull/11409#issuecomment-3885766946) รายงานว่าประเด็น storage ที่เหลือแก้แล้ว แยกจาก [human approval](https://github.com/RooCodeInc/Roo-Code/pull/11409#pullrequestreview-3786644844) **U:** ไม่ถือว่า agent เดิมอ่านทุก review

**I — นำไปใช้:** migration ต้อง inventory ทั้ง producer/consumer, format เก่า/ใหม่ และ failure behavior การเปลี่ยน type ตรงแกนหลักยังไม่พอ **U:** ไม่ทราบว่า defect เกิดเพราะไม่พบ consumer หรือพบแล้วใช้ผิด

Revision ปลายงาน: base `dcb33c47ad233e936a4f7a460a18c00140c7f262`, head `984857e60fbc9786e1af46881e4b075ff9e6049b`, merge `e6f0e79c389dc558338b243f6854c11c2854786f`; foundation 21f4354 มี parent `4e659b459d85035527c7225cdeceb7c17845e0a0` [Repository metadata](https://api.github.com/repos/RooCodeInc/Roo-Code) ระบุสร้าง 31 ต.ค. 2024, 24,305 stars และ archived ณ วันที่ตรวจ ไม่ใช้สถานะปัจจุบันไปสรุปการทำงานเดือน ก.พ.

<a id="c6"></a>

## C6 — Goose #11307: context ครอบคลุมสอง execution paths

**ประเภท:** agent-loop bug fix + migration parity · **ช่วงงาน:** 18–21 ส.ค. 2026

**D:** [issue #11296](https://github.com/aaif-goose/goose/issues/11296) ให้ recipe/repro ของ structured output ที่วนไม่จบ [PR #11307](https://github.com/aaif-goose/goose/pull/11307) เลือก fail fast แทนทำ tool forwarding ที่แยกไปงานอื่น [commit 5372cf21](https://github.com/aaif-goose/goose/commit/5372cf21c4c043cb25959d08529c766012cdbd48) เปิดเผย Claude co-author แยกจาก Codex ที่ทำ review

| ขั้น | หลักฐานและขอบเขต |
|---|---|
| Task / issue | **D:** recipe, provider, symptom และ scope อยู่ใน issue; **U:** exact prompt ส่งให้ implementer |
| Initial instructions | **D-artifact:** PR เชื่อม issue; **U:** issue ถูกส่งให้ implementer ตั้งแต่ต้นหรือไม่ และ assembled runtime context |
| Repository instructions | **D-artifact:** [AGENTS ณ first commit](https://github.com/aaif-goose/goose/blob/5372cf21c4c043cb25959d08529c766012cdbd48/AGENTS.md) ระบุ legacy/state-machine parity; **D-report:** PR อ้างกฎนี้โดยชื่อ; **U:** actual loading/read trace |
| Docs / architecture | **D-report:** issue/PR อธิบาย synthetic frontend tool กับ MCP forwarding boundary; **U:** เอกสารที่เปิดเพิ่ม |
| Code discovery | **D:** PR ระบุ `AcpProvider::stream`, provider และสอง loops; **U:** คำค้นและไฟล์ที่อ่านทั้งหมด |
| Contract / coverage | **D-artifact:** capability check ถูกเพิ่มทั้ง legacy และ state-machine; **I:** parity ทำให้ discovery scope กว้างกว่าจุด symptom; **U:** existing analogue ที่ใช้ก่อน patch |
| Tests | **D-report:** PR ระบุ E2E ของ real state-machine และ provider capability tests; รายงาน 1 failure ว่า pre-existing; **U:** raw run ครบ |
| Implementation | **D:** [diff](https://github.com/aaif-goose/goose/pull/11307/files) และ follow-up commits แก้ timing/capability/recovery text |
| Review | **D-review (Codex bot):** review ชี้ late rejection, flag ที่แทน capability ไม่ได้ และ workaround ที่ยังทำ config invalid |
| Additional context | **D-review:** [before-inference finding](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828196036) ระบุว่า reject ช้าเกินไป และ [capability finding](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828216905) ระบุว่า context ownership ใช้แทน capability ไม่ได้; **I:** findings ทำ contract เฉพาะ boundary ชัดขึ้น |
| Stop / handoff | **D:** approval/merge; **U:** explicit stop criterion, session trace และ subagent handoff |

**D:** [recovery text finding](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828395594) ระบุว่าลบแค่ `json_schema` ยังเหลือ `response` ที่ invalid และ [follow-up ddf10a2](https://github.com/aaif-goose/goose/commit/ddf10a298497a493226908626cd45d1935ba8e90) แก้ข้อความนั้น **I:** context discovery รวมวิธีที่ผู้ใช้จะนำคำแนะนำไปใช้ ไม่ใช่เฉพาะ code path ที่ return error

**I — นำไปใช้:** เมื่องานอยู่ระหว่าง migration ให้ค้น parallel implementations ที่กฎระบุ และตรวจ negative path ทั้งสองว่า fail ก่อนทำงานที่ไม่ควรเกิด **U:** ไม่ทราบว่า implementer อ่าน AGENTS ก่อนลงมือหรือได้รับ parity requirement จากช่องอื่น การอ้างกฎใน PR ให้หลักฐานมากกว่าการมีไฟล์ แต่ยังไม่ใช่ read log

Revision ปลายงาน: base `4078158c01a1e85f317167c8262dcf66c4a5fc00`, head `ddf10a298497a493226908626cd45d1935ba8e90`, merge [a5de3781](https://github.com/aaif-goose/goose/commit/a5de37814adb1b8f7eab3046c53811d5808733fa); first implementation 5372cf21 มี parent `9915ba7eb748e07eacc7102f29c824d9b622a913` PR มี 5 commits, 8 files

<a id="s1"></a>

## S1 — Claude Code Action #726: มีไฟล์กฎ แต่ runtime อาจยังไม่โหลด

**สถานะ:** เคสเสริมเรื่องกลไก context ไม่ใช้แทน trace ของงานหลัก · **ประเภท:** bug fix · เปิดและ merge 7 ธ.ค. 2025

**D:** [PR #726](https://github.com/anthropics/claude-code-action/pull/726) เปิดเผยว่า Generated with Claude Code และอธิบายว่า SDK path ต้องเพิ่ม `settingSources` เพื่อโหลด settings/plugins/CLAUDE.md พร้อมตั้ง default system prompt; [final diff](https://github.com/anthropics/claude-code-action/pull/726/files) มีการแก้ดังกล่าวจริง นี่เป็นหลักฐานของ defect/การแก้ที่ผู้พัฒนารายงานใน version นั้น ไม่ใช่คำแนะนำ config ของ version ปัจจุบัน

**D:** [review](https://github.com/anthropics/claude-code-action/pull/726#discussion_r2595707456) ชี้ปัญหา logging env และ final patch แยก env ออกจาก object ที่ log **U:** ไม่มี initial task, ลำดับ code discovery, เอกสารที่ implementer อ่าน, raw test trace หรือจุดหยุดค้น ผู้ review [กล่าวว่าใช้ specialized agents](https://github.com/anthropics/claude-code-action/pull/726#issuecomment-3621420422) แต่ payload handoff และการ dispatch จริงไม่เปิดเผยในข้อความนี้

**I:** การวิจัย context ต้องตรวจทั้งตัวเอกสารและช่องทางนำมันเข้ารัน มีไฟล์อยู่จึงไม่เพียงพอจะสรุปว่า agent ได้รับมัน **U:** เคสนี้ไม่พิสูจน์ว่า PR อื่น ๆ ที่ศึกษาได้รับผลจากปัญหาโหลด settings เดียวกัน

[Repository metadata](https://api.github.com/repos/anthropics/claude-code-action): สร้าง 19 พ.ค. 2025, 8,863 stars ณ วันที่ตรวจ [PR metadata](https://api.github.com/repos/anthropics/claude-code-action/pulls/726): 2 files, 1 commit, base `6610520549f7c056fddb45c344d353796da65b11`, head `aba3733766d194ab0c514a6e1229c9451a16d83f`, merge `a3bb51dac19ba1ffd7bc3e0473b82cf696d2c5a7`

<a id="s2"></a>

## S2 — Aider: transcript และ Context ใน commit ของงานเปลี่ยน input mocking

**สถานะ:** กรณีเก่าสำหรับเทียบความละเอียดของหลักฐาน · **ประเภท:** refactor/test infrastructure + cross-file debugging · **เหตุการณ์:** 13 พ.ค. 2023

[Transcript ทางการ](https://aider.chat/examples/complex-change.html) แสดงการเพิ่มไฟล์ตั้งต้นสองไฟล์ แล้วผู้ใช้เพิ่ม `aider/main.py` เมื่อพบ error ต่อมาส่ง signature ของ API และเปลี่ยนแนวทางหลังคำตอบใช้ไม่ได้ จบด้วยคำยืนยันของผู้ใช้ว่าใช้ได้ นี่เป็น **D-trace ที่ผู้พัฒนาเลือกเผยแพร่** ไม่ใช่ raw full-context dump และไม่ใช่หลักฐานว่า agent ค้นเอกสารเอง

| ขั้น | หลักฐานที่ตรวจได้ |
|---|---|
| Task / initial instructions | **D-trace:** ข้อความขอเปลี่ยน input mocking; [commit แรก](https://github.com/Aider-AI/aider/commit/c177e29899f589d75302d7fbd2f184e563e63ef8) เก็บ USER/ASSISTANT ไว้ในส่วน Context; **U:** system prompt เต็ม |
| Repository instructions | **U:** ไม่เห็น AGENTS/CLAUDE ถูกโหลด |
| Docs / architecture | **D-trace:** ผู้ใช้ส่ง API signatures; **U:** agent เปิด docs เองหรือใช้ architecture doc หรือไม่ |
| Code discovery | **D-trace:** เพิ่มไฟล์เข้าบทสนทนา; **U:** full read/search log และ automatic context อื่น |
| Analogue / contracts | **D:** [commit แก้ PromptSession](https://github.com/Aider-AI/aider/commit/ac92ccac5c4ec89836c0bb3eaa9e093c0390e081) เก็บ API context และ patch ที่เปลี่ยน call จริง |
| Tests | **D-trace:** ผู้ใช้ส่ง TypeError; **U:** test command/log ครบและผล CI |
| Implementation | **D-artifact:** commits แสดง patch ต่อ tests, main และ input layer |
| Review / additional context | **D-trace:** feedback จากผู้ใช้และ signature เพิ่มเติม; **U:** formal PR review/merge workflow |
| หยุดค้น / handoff | **D-trace:** เริ่มแก้หลังคำขอและแก้ใหม่หลัง feedback; **U:** เกณฑ์ความพอภายในและ subagent/session handoff |

**D-artifact:** [commit สุดท้าย 4bb043f](https://github.com/Aider-AI/aider/commit/4bb043f5c0f52c5a99475c85aab281cf3b964c8b) เก็บคำขอรอบแก้และ diff; [ac92cca](https://github.com/Aider-AI/aider/commit/ac92ccac5c4ec89836c0bb3eaa9e093c0390e081) เก็บทั้งการขัดจังหวะและ signature ที่เข้ามาเพิ่ม จึงตรวจ prompt→patch บางช่วงได้มากกว่า PR body ย้อนหลัง

**I:** เมื่อ API contract ไม่ครบ การปรับ argument จากความจำอาจวนผิดได้; error ควรนำไปตรวจ contract ที่ถูก version มากกว่าลองชื่อใหม่ **U:** ไม่ใช่หลักฐานว่า workflow นี้มีประสิทธิภาพสูงสุด หรือ agent รุ่นใหม่จะมีอัตราพลาดเดียวกัน

[Repo metadata](https://api.github.com/repos/Aider-AI/aider) ระบุสร้าง 9 พ.ค. 2023 และปัจจุบัน 48,934 stars แต่เคสนี้เกิดเพียงไม่กี่วันหลังสร้าง repo จึง **ไม่จัดเป็นเคส large-repo ในเวลาที่เกิดเหตุ** และไม่นำดาวปัจจุบันไปใช้แทนขนาดขณะนั้น

<a id="mechanisms"></a>

## หลักฐานเสริมเรื่องกลไก

| แหล่งต้นทาง | สิ่งที่รองรับตรง — D | สิ่งที่ยังไม่รองรับ — U |
|---|---|---|
| Aider, [Repository map](https://aider.chat/docs/repomap.html), ไม่ระบุวันเผยแพร่ | เอกสารอธิบายแผนที่ symbols, graph ranking และงบ token ที่ปรับได้ | ไม่ใช่ trace ว่า task หลักใช้ map; ไม่ควรอ่านว่าไม่มีการสแกน repo ด้วยเครื่องมือ |
| Anthropic Applied AI, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), 29 ก.ย. 2025 | รายงานแนวทาง lightweight references, just-in-time retrieval, compaction และ note-taking | ไม่พิสูจน์ลำดับค้นหรือประสิทธิภาพของ PR ในชุดนี้ |
| Anthropic, [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), 26 พ.ย. 2025 | รายงานการใช้ progress file และ git history ช่วยข้าม session ในระบบที่ทีมทดลอง | ไม่ใช่ payload handoff ของ C1–C5 และไม่ใช่ controlled comparison ใน sample นี้ |

แหล่งเหล่านี้ใช้ช่วยออกแบบ **ข้อเสนอ workflow — I** โดยแยกออกจากการสังเกตว่าผู้พัฒนาแต่ละ PR ทำจริงอย่างไร

<a id="findings"></a>

## ข้อค้นพบและคำตอบสิบคำถาม

**ผลวิจัย:** GitHub ในตัวอย่างนี้เพียงพอให้ศึกษาว่า task, code, tests และ review เชื่อมกันอย่างไร รวมทั้งเห็นบางครั้งที่เอกสารหรือ analogue ถูกอ้างใช้ แต่ **ยังไม่เพียงพอให้สร้าง full Context Discovery trace ของงานใหม่** ตั้งแต่ initial context ถึง read/search sequence และเงื่อนไขหยุดค้น การเพิ่ม transcript ที่เปิดได้อย่าง S2 ช่วยเติมช่องว่างบางส่วน แต่เป็นเคสเก่าและไม่ใช่ large-repo task ในเวลานั้น

| คำถามวิจัย | Direct evidence | Reasonable inference / สิ่งนำไปใช้ | Unknown |
|---|---|---|---|
| 1. ให้อะไรตั้งต้น? | C3a มี invocation; C2b/C6 มี issue ละเอียด | ส่ง trigger, expected behavior, scope, revision และ pointers เป็น seed | assembled initial context ของ core cases |
| 2. Agent ค้นอะไรเอง? | S2 เห็นการเพิ่มไฟล์/ส่ง API โดยผู้ใช้; core cases มีรายงาน/patch | ตาม owning path, analogue และ consumers เพื่อปิดคำถาม | อะไรค้นเอง อะไรคนส่งให้ใน private channel |
| 3. Repo ช่วย discover อย่างไร? | C1 rules index → contribution → architecture; C6 named dual paths | pointer ควรบอก trigger และ target; layout ใช้เป็นแผนที่ | run ใช้เส้นทางนี้จริงหรือไม่ |
| 4. ไฟล์แต่ละชนิดต่างกันอย่างไร? | C1 rules/error response; C2 review/test pointers; C5 converters/readers | docs อธิบายเหตุผล, code แสดงกลไก, tests แสดง observable | source ใดอยู่ใน context ณ เวลาใด |
| 5. มี progressive disclosure? | C1 conditional index; C2 มี context เพิ่มใน review | ใช้ทั้งเอกสารเปิดตามงานและ feedback เจาะช่องว่าง | token savings และ causal effect |
| 6. รู้ได้อย่างไรว่าต้องอ่านเพิ่ม? | C4 probe/review; C5 storage findings; C6 late rejection | failure/finding เป็น trigger กลับไปตรวจ contract | การตัดสินใจของ agent ระหว่าง tool calls |
| 7. context ขาด/ผิดทำให้ implement ผิดหรือไม่? | มีข้อกำหนดตกหล่นใน patch และ correction; C2b ยังไม่จบ | สอดคล้องกับ retrieval/interpretation/application gaps ได้หลายแบบ | ฟันธง causal mechanism ภายในไม่ได้ |
| 8. ป้องกัน context ล้นอย่างไร? | C1 index และ reviewer รายงาน truncated input; Aider docs อธิบาย map budget | targeted reads, เปิดเผย truncation, ดึงส่วนจำเป็นเพิ่ม | core run จำกัด token/ไฟล์จริงเท่าไร; อ่านทั้ง repo หรือไม่ |
| 9. session/subagent handoff? | session/run links บางเคส; S1 reviewer รายงานใช้ specialized agents | handoff ควรมี revision, evidence pointers, contract, tests, unknown | actual payload, inherited context และ compaction ของ implementers |
| 10. เมื่อไรหยุดค้น? | commit, completion report, review, merge/close; S2 เห็นเริ่ม edit | ใช้เกณฑ์บท 5 เป็นข้อเสนอที่ตรวจได้ | internal context-sufficiency rule ของแต่ละ core run |

### รูปแบบที่ซ้ำและกรณีที่ขัดกับข้อสรุปง่าย ๆ

- **D → I:** Dyad ชี้ helper เดิม, Cline ระบุ CLI analogue, OpenCode ระบุ navigation/CLI behavior จึงสังเคราะห์ให้ค้น implementation ใกล้เคียงก่อนสร้างใหม่ได้ แต่ยัง U ว่า agent ค้นเองในลำดับใด
- **D → I:** Dyad auth, Roo persistence และ Goose inference timing แสดง contract ที่หลุดข้าม boundary ของไฟล์ที่แก้ จึงควรตรวจ caller/consumer/failure semantics ไม่หยุดที่ typecheck
- **D → I:** Dyad reply อ้าง rule และ Goose PR อ้าง migration parity แสดงการนำกฎมาใช้ในคำอธิบายได้; Cline/Roo มี instruction file แต่ไม่มี linkage แบบเดียวกัน จึงไม่เหมารวมว่าใช้จริง
- **D → I:** OpenHands #8252 มี task pointers ละเอียดแต่ unresolved เป็นกรณีค้านว่าให้ instruction ดีแล้วจะสำเร็จเสมอ; OpenCode #6014 มี successful agent run แต่ไม่ merge จึงไม่ใช้ run success เป็น outcome success
- **U:** ไม่มี controlled experiment แยกผลของ context engineering จาก model, คน, tests, task complexity และเครื่องมือ จึงไม่มีอันดับ workflow หรือเปอร์เซ็นต์ improvement

<a id="coverage"></a>

## ตารางความละเอียดของหลักฐาน

ตารางนี้แสดงสิ่งที่สังเกตได้ ไม่ใช่คะแนน agent “อ้าง” คือ D-report; “มีไฟล์” คือ D-artifact ช่อง U ต้องคงไว้เมื่อสรุปต่อ

| Case | Prompt/trigger | Instruction ถูกอ้างใช้ | Read/search trace | Analogue/contract | Review→revision | Internal stop / handoff |
|---|---|---|---|---|---|---|
| C1 Dyad | U; มี PR scope | rule ใน reply | U | review + reply + patch | D | U / U |
| C2a OpenHands | automatic workflow; review prompt เห็น | มี guide; use U | U | reviewer ให้ file/test map | D | U / U |
| C2b OpenHands | issue ชี้ chain; assembled prompt U | มี guide; use U | U | review ระบุสิ่งที่ยังไม่ทำ | D; unresolved | U / U |
| C3a OpenCode | exact `/oc` comment | U | U; session เปิดไม่ได้ | PR อ้าง CLI analogue | correction U | U / U |
| C3b OpenCode | Slack prompt U | U | U | issue hints + patch | substantive feedback U | U / U |
| C3c OpenCode | initial prompt U | U | U | wire contract/test oracle | D | U / U |
| C4 Cline | user report ใน PR; prompt U | มี guide; use U | U; sessions เปิดไม่ได้ | PR/commits อ้าง CLI/protocol | D | U / U |
| C5 Roo | internal ticket U | มี guide; use U | U | storage/reader contracts | D | U / U |
| C6 Goose | public issue; prompt U | PR อ้าง AGENTS parity | U | dual loops/capability | D | U / U |
| S2 Aider | published user turns | U | เห็น context addition บางส่วน; full trace U | user ส่ง API signatures | user feedback→commits | U / U |

<a id="sessions"></a>

## ทะเบียน session และช่องว่างการเข้าถึง

สถานะเป็นผลการเข้าถึง ณ วันที่ตรวจ ไม่สรุปว่าเจ้าของลบข้อมูลหรือบุคคลอื่นเปิดไม่ได้เสมอไป ไม่มีการใช้เนื้อหาจาก session ที่เปิดไม่สำเร็จ

| แหล่งที่ลิงก์ | เป้าหมาย | ผลการตรวจ | สิ่งที่ยัง Unknown |
|---|---|---|---|
| OpenHands #8310 | [Actions run 14865734014](https://github.com/OpenHands/OpenHands/actions/runs/14865734014) | 404 | prompt/tool/read logs; เหตุที่เข้าถึงไม่ได้ |
| OpenCode #6014 | [session xCAflZA6](https://opencode.ai/s/xCAflZA6) | เปิด transcript ไม่ได้; 404 ในการตรวจหนึ่งช่องทาง | full input/discovery order |
| Cline #13969 | [Claude session](https://claude.ai/code/session_01XJb3VtvdSm9xk9opJ3Q9G6) | 403/challenge | prompt, reads, same-session attribution |
| Cline #13968 | [Claude session](https://claude.ai/code/session_01CNoho8fGgnh71xjQF5xMqy) | 403/challenge | file reads และ chronology |
| Roo #11409 / Goose #11307 / Dyad #4187 | ไม่พบ implementer transcript ที่เปิดได้ในหลักฐานที่ใช้ | มี PR/review/diff; ไม่ใช่ผลค้นทุกที่บนอินเทอร์เน็ต | session ที่ไม่เผยแพร่/ไม่ลิงก์ และ handoff |
| Aider S2 | [published transcript](https://aider.chat/examples/complex-change.html) + commits | อ่านได้ | hidden/system context และ completeness |

<a id="next-evidence"></a>

## หากต้องการศึกษาลำดับ context จริง ต้องเพิ่มหลักฐานอะไร

รายการนี้เป็น **ข้อเสนอ — I** เพื่อทำคำถามที่ยัง U ให้สังเกตได้:

1. เก็บ sanitized initial task, instruction files ที่โหลดจริงพร้อม hash/revision และ source ของ context แต่ละชิ้น
2. เก็บ tool events แบบ timestamp: query, path/range ที่อ่าน, truncation, output reference และ checkout revision ไม่จำเป็นต้องเผยแพร่ chain-of-thought
3. ก่อน implementation บันทึกข้อเท็จจริงที่ยืนยัน, unknown, test oracle และเหตุผลที่หลักฐานพอกับ change ถัดไป
4. เชื่อม finding → context source → code revision → ผลตรวจ เพื่อแยกการรับข้อมูลออกจากการแก้ถูก
5. เก็บ handoff payload, สิ่งที่ตัดทิ้ง และ pointers ที่เปิดกลับได้ พร้อมบอกว่าคำรายงานใดผู้รับตรวจซ้ำแล้ว
6. ทดลองงานชนิดใกล้กันโดยเปลี่ยนเฉพาะวิธีให้ context แล้ววัดความถูกต้อง/รอบแก้/ต้นทุนจริง ก่อนอ้างผลเชิงสาเหตุ

สิ่งเหล่านี้ช่วยศึกษาพฤติกรรมที่ตรวจได้โดยไม่แต่งเหตุผลภายในของโมเดล และทำให้ผลว่า “ยังไม่มีหลักฐานพอ” เป็นผลวิจัยที่ใช้งานต่อได้
