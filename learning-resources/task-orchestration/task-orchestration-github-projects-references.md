# Task & Work Orchestration: หลักฐาน — GitHub Projects Edition

เอกสารคู่กับ [บทเรียนและ GitHub Projects Workflow for AI Coding](task-orchestration-github-projects-lessons.md) แยกข้อเท็จจริงจากงานสาธารณะ ข้อสังเคราะห์ และสิ่งที่ยังไม่ทราบ ตรวจแหล่งข้อมูลวันที่ 14 กันยายน 2026 ตามเวลาไทย; วันที่และเวลาเหตุการณ์ด้านล่างเป็น UTC เว้นแต่กำกับเป็นอย่างอื่น

## ดัชนีสำหรับเปิดหลักฐานเฉพาะเรื่อง

[E1 OpenHands](#e1) · [E2 SkyPilot](#e2) · [E3 Dyad](#e3) · [E4 Goose](#e4) · [E5 Cline](#e5) · [E6 OpenClaw](#e6) · [E7 Huf](#e7) · [G1 Projects](#g1) · [G2 Automation](#g2) · [G3 Agents](#g3) · [G4 API / limitations](#g4) · [G5 Migration mapping](#g5) · [คำตอบต่อ 15 คำถาม](#coverage) · [ข้อจำกัดการเข้าถึง](#limits)

<a id="method"></a>

## ขอบเขตและวิธีอ่าน

E1–E7 สืบทอดหลักฐาน snapshot จากชุดเดิม โดยคงระบบที่กรณีศึกษาใช้จริง เช่น Linear, Basecamp หรือ workspace ภายใน ส่วน G1–G5 ตรวจเอกสาร GitHub ทางการเพิ่มเพื่อประยุกต์ workflow ไม่ใช่การอ้างว่าทุกกรณีศึกษาใช้ GitHub Projects คลังนี้เก็บหลักฐานสาธารณะที่ใช้กับฉบับ GitHub Projects; local audit และ CLI experiments ของฉบับ Beads ไม่ได้รวมไว้ ดู [ขอบเขตการคัดเก็บ](../README.md#curation)

คำถามหลักคือ งานถูกแบ่ง มอบหมาย ตรวจ รับ และติดตามต่ออย่างไร เมื่อมี coding agents ร่วมทำงาน หน่วยศึกษาคือ **สายงานที่เชื่อม issue/PR/commit/review/ผลตรวจเข้าด้วยกัน** การมีเอกสารของ task tool อย่างเดียวไม่เพียงพอ

ใช้การเลือกกรณีแบบเจาะจงเพื่อให้เห็นกลไกและข้อผิดพลาด ไม่ใช่ตัวอย่างสุ่ม จึงไม่ประมาณสัดส่วนงานที่ AI ทำ อัตราสำเร็จ หรือประสิทธิภาพเทียบเครื่องมืออื่น แยกกรณีหลักที่เปิดเผย AI implementation ออกจากกรณีที่พิสูจน์เพียง AI review และกรณีโปรเจกต์เล็กที่ให้หลักฐาน orchestration ละเอียดกว่า

| ป้าย | สิ่งที่ยืนยันได้ | ข้อจำกัด |
|---|---|---|
| **DIRECT EVIDENCE — D-artifact** | เนื้อหา issue, patch, status event, check result หรือความสัมพันธ์ระหว่าง PR ที่ตรวจได้ | ไม่เปิดเผยเจตนาและขั้นตอนใน session โดยอัตโนมัติ |
| **DIRECT EVIDENCE — D-report** | ผู้ร่วมงานหรือ agent รายงานว่าเกิดอะไรขึ้น | ยืนยันว่ามีคำรายงาน; ผลจริงและเหตุเชิงสาเหตุอาจต้องมีหลักฐานเพิ่ม |
| **DIRECT EVIDENCE — D-trace** | log/transcript ที่เปิดได้แสดงการกระทำและผลบางช่วง | ยังอาจเป็นบางส่วนของ session |
| **DIRECT EVIDENCE — D-doc** | เอกสารทางการอธิบาย capability หรือ API | ไม่ยืนยันว่า Project ของผู้ใช้เปิดใช้แล้ว หรือกรณีศึกษาปฏิบัติตามจริง |
| **REASONABLE INFERENCE — I** | การตีความหรือ workflow เสนอใช้ซึ่งมี D รองรับ | ไม่ถือว่าเป็นขั้นตอนที่ทุกทีมใช้ หรือพิสูจน์ว่าดีกว่าวิธีอื่น |
| **UNKNOWN — U** | หลักฐานที่เข้าถึงยังตอบไม่ได้ | ไม่ได้แปลว่าสิ่งนั้นไม่เกิดขึ้น |

แยกห้าสิ่งออกจากกันเสมอ: attribution ว่า AI ร่วม implement; การเปิด PR ผ่าน bot; AI review; ผล automated checks; การตัดสินใจรับงานของผู้มีอำนาจ ไม่ใช้สิ่งหนึ่งแทนหลักฐานของอีกสิ่ง

PR body และ review comment อาจถูกแก้ภายหลัง ตาราง timeline จึงใช้เวลา event หรือ commit เมื่อมี และระบุคำรายงานล่าสุดแยกจาก prompt ตั้งต้น ค่า base/head ของ PR เปลี่ยนได้เมื่อ rebase/restack; ผลตรวจที่ระบุ revision เก่าจะไม่ถูกยกระดับเป็นผลของ head ใหม่ การมี workflow สำเร็จไม่ได้แปลว่า AC ทุกข้อถูกตรวจ และการมี skipped/cancelled check ไม่ได้แปลว่า test ที่เกี่ยวข้องผ่าน

<a id="e1"></a>

## E1 — OpenHands: SDK feature, review loop และ docs หลัง merge

**สถานะ:** กรณีหลัก มี AI implementation disclosure และคำสั่งมอบงานต่อ agent ที่เห็นตรง **ชนิดงาน:** feature/cross-module/cross-repository **ช่วงงานหลัก:** 16–20 เม.ย. 2026 **ข้อจำกัดขนาด:** [software-agent-sdk](https://api.github.com/repos/OpenHands/software-agent-sdk) เป็น SDK หลาย packages ในโครงการ OpenHands สร้าง 23 ส.ค. 2025, 1,104 stars ณ วันที่ตรวจ; ไม่อ้างว่ามีขนาดเท่ากับ repo หลักของ OpenHands

### E1a — #2840 → SDK #2841 → docs #459 (เมษายน 2026)

[Issue #2840](https://github.com/OpenHands/software-agent-sdk/issues/2840) ขอ `Conversation.fork()` และ REST endpoint เป็น primitive กลางสำหรับ consumers อื่น กำหนด behavior ของ copied state/metrics และตัด cross-server, partial streaming และ ownership policy ออกจาก scope ข้อนี้เป็น **D-artifact ของ requirement ที่เสนอ** ไม่ใช่หลักฐานว่าทุกบรรทัดถูกคงไว้จน final implementation

| เวลา UTC | เหตุการณ์ | ความหมายต่อ orchestration |
|---|---|---|
| 16 เม.ย. 00:08 | **D-artifact:** เปิด issue #2840 | ตั้งผลลัพธ์/API และชี้ consumers #1787 กับ OpenHands/OpenHands#8560; ไม่ได้แสดง native dependency graph ครบ |
| 16 เม.ย. 01:46:30 | **D-artifact:** [ผู้มอบงาน](https://github.com/OpenHands/software-agent-sdk/issues/2840#issuecomment-4256832665) ขอให้ OpenHands implement, เปิด PR และ `/verify` จน reviewer bot approve | นี่คือ visible invocation และเกณฑ์จบของคำสั่งย่อย; assembled prompt/system context ยัง U |
| 16 เม.ย. 01:46:45 | **D-artifact:** [agent รับงาน](https://github.com/OpenHands/software-agent-sdk/issues/2840#issuecomment-4256834091) และให้ session link | มี assignment ผ่านบทสนทนา แม้ไม่จำเป็นต้องมี assignee field |
| 16 เม.ย. 01:59 | **D-artifact/report:** [PR #2841](https://github.com/OpenHands/software-agent-sdk/pull/2841) เปิดพร้อม AI disclosure | implementation ครอบคลุม Base/Local/Remote conversation, server, examples และ tests; final 13 files/27 commits ไม่ใช่ 27 agents |
| 16 เม.ย. 02:02–02:18 | **D-review/report:** reviewers ชี้ mutable state, unsupported API input, remote tags และ missing endpoint tests; agent รายงาน fixes | review findings กลับเป็นงานใน PR เดิม แทนสร้าง task ใหม่ทุก finding |
| 16 เม.ย. 02:29 | **D-report:** [agent summary](https://github.com/OpenHands/software-agent-sdk/issues/2840#issuecomment-4257014437) ระบุ implement แล้ว, PR เปิดแล้ว, reviewer approve, 19 tests และ resolved threads | รายงานว่าทำ visible invocation ครบ ไม่ใช่คำยืนยันว่า feature ถูก merge/deploy แล้ว |
| 16 เม.ย. 04:31 | **D-artifact:** [docs #459](https://github.com/OpenHands/docs/pull/459) เปิดเป็นอีก PR | เริ่มเอกสารก่อน SDK merge; branch ชื่อเดียวกันเพื่อให้ example-check workflow ค้นคู่ได้ตามคำอธิบาย PR |
| 17 เม.ย. | **D-artifact:** [human approval](https://github.com/OpenHands/software-agent-sdk/pull/2841#pullrequestreview-4132199678) | เป็น review decision เพิ่มจาก bot approval; ไม่ใช่หลักฐานว่าได้ทดลองทุก behavior ด้วยตนเอง |
| 19 เม.ย. 15:44:22–23 | **D-artifact:** SDK merge แล้ว issue ปิดหนึ่งวินาทีถัดมา | เป็น integration/issue-closure event; docs ยังไม่ merge |
| 19 เม.ย. 15:44:32 | **D-artifact:** [ผู้มอบงานขอให้ sync docs](https://github.com/OpenHands/software-agent-sdk/pull/2841#issuecomment-4276246468) กับ SDK ล่าสุด | งานหลัง merge ยังมี obligation ข้าม repo |
| 19 เม.ย. 15:50:52 | **D-report:** [agent ตอบ](https://github.com/OpenHands/software-agent-sdk/pull/2841#issuecomment-4276264049) ว่าแก้ docs `dcc2019` | ปรับ example assertion และ copied-state table ให้ตรงกับ merged implementation |
| 20 เม.ย. 17:31:09 | **D-artifact:** docs merge | ปิด delivery อีกชิ้นหลัง SDK; end-user acceptance/deploy ยัง U |

### Review finding → rework ที่ตามได้

| Finding | การตอบสนองที่เปิดเผย |
|---|---|
| [mutable events](https://github.com/OpenHands/software-agent-sdk/pull/2841#discussion_r3090368070), [shallow runtime state](https://github.com/OpenHands/software-agent-sdk/pull/2841#discussion_r3090368092), [unsupported parameter](https://github.com/OpenHands/software-agent-sdk/pull/2841#discussion_r3090368101) | **D-report:** [คำตอบหลัง fixes](https://github.com/OpenHands/software-agent-sdk/pull/2841#issuecomment-4256907438) ชี้ commit `71b9751` และขอ review ใหม่ |
| [remote tags mismatch](https://github.com/OpenHands/software-agent-sdk/pull/2841#discussion_r3090400017), [missing endpoint tests](https://github.com/OpenHands/software-agent-sdk/pull/2841#discussion_r3090400023) | **D-report:** [remaining-fixes report](https://github.com/OpenHands/software-agent-sdk/pull/2841#issuecomment-4256970880) ชี้ `06919d4`; [commit history](https://github.com/OpenHands/software-agent-sdk/pull/2841/commits) แสดง rework และ tests |
| Docs ไม่ตรง merged code | **D-report/artifact:** docs sync ปรับ remote event-count assertion เพราะ WebSocket-only events ไม่ persist และแก้ copied-state table ว่า policy/analyzer ใช้ defaults ไม่ใช่ copied state ตามข้อเสนอเดิม |

**D-report:** [summary บน issue](https://github.com/OpenHands/software-agent-sdk/issues/2840#issuecomment-4257014437) บอกว่า “previous session” ทิ้งสาม commits และสอง findings ก่อน session นี้แก้ต่อ เป็นหลักฐานคำรายงานการทำต่อข้าม session **U:** ไม่เห็น handoff payload, model identity หรือว่าระบบส่ง state อย่างไร

**D-artifact:** [check-runs บน final head](https://api.github.com/repos/OpenHands/software-agent-sdk/commits/80bebdc2b028d126ff657ca2a75210e52821ab8d/check-runs?per_page=100) ที่ตรวจมี 42 records: success 33, skipped 9 รวม [unresolved-review-threads](https://github.com/OpenHands/software-agent-sdk/actions/runs/24632683300/job/72022684238) และ [pre-commit](https://github.com/OpenHands/software-agent-sdk/actions/runs/24632683260/job/72022684207) ที่ success **U:** ไม่ได้ตรวจ raw logs ทุก run หรือ branch-protection rules; จึงไม่เรียก skipped ว่า tests ผ่าน และไม่สรุปว่า check ทุกตัวเป็น required merge gate

Revision ของ SDK: base `ceeea8ab8c4d8434b2bafb90442e51471f8bbee2`, final head `80bebdc2b028d126ff657ca2a75210e52821ab8d`, merge [18d0051f4ef466cefdd06162895b5135660473d1](https://github.com/OpenHands/software-agent-sdk/commit/18d0051f4ef466cefdd06162895b5135660473d1) Docs merge [204437848184b299cc9ab77ad7d42f06ee3b9696](https://github.com/OpenHands/docs/commit/204437848184b299cc9ab77ad7d42f06ee3b9696)

**I:** มี completion หลายขอบเขต: ทำตาม invocation จน bot approve, รับ SDK change, และส่ง docs ที่ตรงกับ implementation ความต่างนี้ไม่ใช่ความผิดโดยตัวมันเอง ถ้า task ย่อยประกาศผลส่งมอบไว้ตรงและงานแม่ยังรักษา obligation ที่เหลือ **U:** full original AC acceptance, native ready/blocked states, parallel agents, private task board และ downstream UI delivery

### E1b — OpenHands #8250 → #8252: ปิด PR โดยยังแก้ไม่สำเร็จ

**สถานะ:** failure comparator ที่เก่ากว่า (4 พ.ค. 2025) [issue #8250](https://github.com/OpenHands/OpenHands/issues/8250) ขอไล่ terminal commit → Husky → Python pre-commit เทียบ frontend ที่ทำงานได้ [automatic-fix PR #8252](https://github.com/OpenHands/OpenHands/pull/8252) มีสี่ commits และปิดโดยไม่ merge

**D-report:** [maintainer ปฏิเสธ patch แรก](https://github.com/OpenHands/OpenHands/pull/8252#issuecomment-2848884629) ว่ายังไม่ตอบโจทย์; [agent ยอมรับว่าการเทียบยังไม่ครบ](https://github.com/OpenHands/OpenHands/pull/8252#issuecomment-2848887157); [maintainer ชี้ Husky/dev_config ซ้ำ](https://github.com/OpenHands/OpenHands/pull/8252#issuecomment-2848892132); [รายงานท้ายยัง unresolved](https://github.com/OpenHands/OpenHands/pull/8252#issuecomment-2848894552)

**D-artifact:** มี follow-up patches แต่ไม่พบหลักฐานที่ยืนยัน requested end-to-end behavior ผ่านในสายงานนี้ **I:** รายการแก้และคำแนะนำเพิ่มไม่รับประกันว่า workflow จะ converge; จุดรับงานต้องผูกกับ behavior ที่ขอ **U:** เหตุผลปิดที่ไม่อยู่ใน comments, งานแก้ต่อที่อื่น และไฟล์ที่ agent อ่านจริง ไม่ใช้การไม่มี `.husky` ใน diff พิสูจน์ว่าไม่เคยอ่าน

### กรณีที่ไม่ใช้เป็น workflow จริง

[SDK issue #2603](https://github.com/OpenHands/software-agent-sdk/issues/2603) เสนอแบ่ง short-term fix กับ medium-term API design แต่ยังไม่มีสาย implementation/review/merge ที่ตรวจตามได้ในหลักฐานชุดนี้ จัดเป็น **D-artifact ของแผน; U ของ execution** ไม่รวมเป็นงานหลาย PR ที่เกิดขึ้นแล้ว

<a id="e2"></a>

## E2 — SkyPilot: งานใหญ่แปด PR และข้อแก้ที่ข้ามชั้นของ stack

**สถานะ:** กรณีหลัก AI implementation disclosure ใน PRs **ชนิดงาน:** feature/schema migration/API/UI/tests/docs **ผลปลายทาง:** ยังไม่ merge ณ snapshot [repository](https://api.github.com/repos/skypilot-org/skypilot) สร้าง 11 ส.ค. 2021, 10,601 stars ณ วันที่ตรวจ เป็นโครงการ mature ที่เลือกเพราะมีหลักฐานแบ่งงานชัด ไม่ได้ใช้ยืนยันว่า code ส่วนใหญ่สร้างด้วย AI

[#10698](https://github.com/skypilot-org/skypilot/pull/10698) เปิด 9 ก.ย. 2026 20:05:49 ระบุ Part 1 of 8 สำหรับ SKY-5285: ให้ job ที่ launch จากภายใน job group ถูกนับ รวมการ cancel และ sweep เข้ากับ group **D-artifact:** มี ticket reference และ scope ใน public PR **U:** เนื้อหา Linear ticket SKY-5285, parent/subtask metadata และ original assignment

### Decomposition ที่ระบุจริง

| ลำดับ review | ผลส่งมอบ | Dependency ที่เปิดเผย |
|---|---|---|
| [#10698](https://github.com/skypilot-org/skypilot/pull/10698) | schema/state, controller compatibility | ฐานของ stack |
| [#10701](https://github.com/skypilot-org/skypilot/pull/10701) | launch path | อยู่บนฐาน state; ระบุให้ลงพร้อม #10702 |
| [#10702](https://github.com/skypilot-org/skypilot/pull/10702) | cancel cascade/sweep | อีกครึ่งของ attach/cancel correctness |
| [#10725](https://github.com/skypilot-org/skypilot/pull/10725) | rendering | ใช้ data/API ของชั้นก่อน |
| [#10734](https://github.com/skypilot-org/skypilot/pull/10734) | dynamic task index | เป็น address ที่ downstream ใช้ |
| [#10736](https://github.com/skypilot-org/skypilot/pull/10736) | task pages | UI ใช้ index/contract |
| [#10726](https://github.com/skypilot-org/skypilot/pull/10726) | smoke tests | พิสูจน์ integrated outcomes |
| [#10732](https://github.com/skypilot-org/skypilot/pull/10732) | docs/example | อธิบาย contract ที่ชั้นก่อนส่งมอบ |

**D-report/artifact:** body ระบุว่าทุก diff เป็น commits ของตนบน PR ก่อนหน้า และ #10701/#10702 ต้อง land ด้วยกัน **I:** แบ่งตามชั้นที่ review ได้และ contract ที่ downstream ใช้ ไม่ใช่แค่ file partition **U:** ใครเป็น coordinator ของ agents, ใครถือสิทธิ์แก้ shared interface และมี parallel agents หรือไม่ คำว่า `parallel_appends` ใน test เป็น concurrency ของผลิตภัณฑ์ ไม่ใช่หลักฐานว่า coding agents ทำ parallel

### Timeline ของ review และการเปลี่ยนงาน

| เวลา / source | สิ่งที่เกิดขึ้น |
|---|---|
| 10 ก.ย. — [Devin review รอบแรก](https://github.com/skypilot-org/skypilot/pull/10698#pullrequestreview-5163331174) | **D-report:** พบ explicit index creation, old-controller field compatibility และ stale description; PR บันทึกว่าแก้ใน pushes ถัดมา |
| 11 ก.ย. — [human approval](https://github.com/skypilot-org/skypilot/pull/10698#pullrequestreview-5174777033) และ [Devin อีกครั้ง](https://github.com/skypilot-org/skypilot/pull/10698#pullrequestreview-5176289700) | **D-report:** ลด version round trip ที่ไม่จำเป็นใน `7c700bd`; approval นี้ไม่ใช่ blanket approval ของ revisions หลังจากนั้น |
| 12 ก.ย. — [cancel review](https://github.com/skypilot-org/skypilot/pull/10702#pullrequestreview-5184852652) | **D-report:** race ระหว่าง parent cancellation กับ child insertion ต้องแก้ทั้ง state/launch boundary และ cancel-side half; ไม่ใช่ finding ที่แก้ได้ในไฟล์ของ PR เดียวเสมอ |
| 13 ก.ย. — [Devin round 2](https://github.com/skypilot-org/skypilot/pull/10698#pullrequestreview-5190007456) | **D-report:** lock เฉพาะ direct parent ยังพลาด root cancellation และ controller codegen path ยังขาด guard; PR ชี้ `b9d8bbe65` แก้เพิ่ม |
| smoke iteration — [#10726](https://github.com/skypilot-org/skypilot/pull/10726) | **D-report:** run #12922 บน `2ef9ff0fe` fail เพราะ helper ที่รอ status ไม่ได้ดึง field `details`; แก้ให้อ่าน full row แล้ว runs #12924/#12926 ผ่านเจ็ด tests, #12927 บน `8859fb7a0` ผ่านแปด |
| docs rework — [#10732](https://github.com/skypilot-org/skypilot/pull/10732) | **D-report:** supersedes #10727 เพราะ bad rebase ทำให้ branch ไม่มี commits ของตัวเองจน GitHub auto-close; example review ยังแก้ scoped polling, exit handling และ client version |
| snapshot | **D-artifact:** stack ทั้งแปดยัง open; **U:** merge และ ticket completion ไม่ปรากฏ |

**D-artifact ของ snapshot:** [checks ของ #10698 head `31a8cd3`](https://api.github.com/repos/skypilot-org/skypilot/commits/31a8cd3246aafac87377d3eb52a96e2937a1eb95/check-runs?per_page=100) ใน capture ระหว่างวันที่ 14 ก.ย. เวลาไทยมี 21 records: success 8, queued 10, in progress 3 (สถานะเปลี่ยนระหว่างการตรวจซ้ำ จึงไม่ใช้ตัวเลขนี้เป็น live status) รวม [unit tests ที่ยังรัน](https://github.com/skypilot-org/skypilot/actions/runs/34777993202/job/103779518623) จึงไม่ยกคำรายงาน “green” ของ run ก่อนเป็นผล head นี้ **U:** raw Buildkite logs ของทุก smoke run และ full AC ใน Linear

**D-report:** #10726 ระบุชัดว่าแต่ละ test พิสูจน์อะไร ตั้งแต่ attach, sweep, opt-out จน nested cancellation; การแดงครั้งแรกถูกวิเคราะห์ว่าเป็น test data retrieval defect แล้วแก้ helper โดยคง expected cancel reason ไว้ **I:** verification เป็นงานชิ้นหนึ่งที่มี contract ของตัวเอง และ finding ต้องได้รับการวิเคราะห์ก่อนเลือกแก้ product หรือ test

**I:** stack นี้สนับสนุน dependency สองชนิดที่ต้องแยก: code ที่ต้องมีเพื่อให้ทำงานต่อได้ กับชุด changes ที่ต้องลงด้วยกันเพื่อไม่เปิดช่วง behavior ผิด การมีหลาย PR จึงไม่เท่ากับทำงานทุกชิ้นแยกกันได้ **U:** task scheduler รู้ dependency นี้จาก field, prompt หรือคนคุมอย่างไร

<a id="e3"></a>

## E3 — Dyad: scope ใหญ่กว่าที่คาด และ finding ที่ยอมเลื่อนอย่างมีเหตุผล

**สถานะ:** กรณีหลัก AI disclosure + Claude-attributed responses **ชนิดงาน:** feature/cross-module **ช่วงงาน:** 4–14 ส.ค. 2026

**D-report/artifact:** [#4187](https://github.com/dyad-sh/dyad/pull/4187) เปิดเผยว่า code/description สร้างด้วย Claude เป็นขั้นแรกของงาน Coolify หลายส่วนที่อยู่ใน Basecamp และผู้เขียนระบุว่า PR ใหญ่กว่าที่คาด Final diff มี 71 files และ PR metadata มี 126 commits ก่อน merge 14 ส.ค. 18:57:09 **U:** Basecamp task tree, planned dependencies, full AC และว่าขั้นต่อไปมี PR ใดครบแล้ว จึงไม่ใช้คำว่า “หลายขั้น” เป็นหลักฐานว่า orchestration ทั้งแผนสำเร็จ

Scope ที่เปิดเผยรวม deploy ไป instance ที่ผู้ใช้มีอยู่แล้ว และตัด install/SSH/database provisioning/schema migration ออก **D-review/report/artifact:** [review auth](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3709212241) → [คำตอบว่าพบ auth/branch-selection gap](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717925547) → [historical patch/tests](https://github.com/dyad-sh/dyad/commit/43110685df945df319bf0cea53030707f2ffbf26) เป็นการแก้ใน PR เดิม เพราะอยู่บนเส้นทาง deploy ที่ต้องทำงานได้ SHA นี้เปิดได้แต่ไม่อยู่ใน final 126-commit history; history ปัจจุบันมีการแก้หัวข้อเดียวกันที่ [bb90998e](https://github.com/dyad-sh/dyad/commit/bb90998e72e937b463b65c0c7247857f6c466c15) จึงไม่อ้างว่า historical SHA ถูก merge ตรง ๆ

**D-report:** [คำตอบ 14 ส.ค. 17:00](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3785713522) ที่กำกับว่า Claude สร้าง แยก finding เรื่อง coordinator ออกเป็นสองส่วน: อธิบายว่าข้อบังคับ mutation/deletion fence ที่ reviewer อ้างมีการรองรับอยู่แล้ว แต่ยอมรับ read race ที่เหลือ และให้เหตุผลว่าจะแก้ให้ครบต้องเพิ่ม public API ของ service ที่หลายไฟล์พึ่งอยู่ จึงควรเป็นอีก change

**D-artifact:** PR merge เป็น [ba782f43](https://github.com/dyad-sh/dyad/commit/ba782f433205935979de8a9cc2d606944fe534a1) **U:** ไม่เห็น linked task ที่ยืนยันการติดตาม/ปิด read race จาก reply นี้ และไม่รู้ handoff ไป owner ของ coordinator อย่างไร

**D-artifact ของ post-merge failure:** [Actions run 31831053389](https://github.com/dyad-sh/dyad/actions/runs/31831053389) เกิดจาก push บน merge SHA `ba782f433205935979de8a9cc2d606944fe534a1` เริ่ม 14 ส.ค. 18:57:12 และจบ failure เวลา 19:41:56 [ผล Playwright ที่โพสต์ 19:42:18](https://github.com/dyad-sh/dyad/pull/4187#issuecomment-5297447563) รายงาน passed 861, failed 5, flaky 3, skipped 310; failures อยู่บน Windows รวม Coolify สองกรณีและ editor สามกรณี **U:** ยังไม่พิสูจน์ว่าการเปลี่ยนแปลงนี้ทำให้ทั้งห้ารายการเสีย หรือมี follow-up/reopen ใดปิดปัญหาเหล่านี้แล้ว ห้ามเปลี่ยนคำว่า “failure หลัง merge” เป็น “regression ที่พิสูจน์สาเหตุแล้ว”

**I:** เป็นหลักฐานให้แยก finding disposition ตาม impact/contract ไม่ใช่ตามความสะดวก: auth ที่จำเป็นต่อ outcome แก้ในงานเดิม ส่วน API expansion ที่เป็นผลลัพธ์แยกถูกเลื่อนพร้อมเหตุผล แต่การบันทึกเหตุผลเลื่อนยังไม่เท่ากับมี follow-up ที่ scheduler จะหยิบมาทำเอง

<a id="e4"></a>

## E4 — Goose: แก้อาการให้หยุดอย่างปลอดภัย แล้วแยกความสามารถที่ใหญ่กว่า

**สถานะ:** กรณีหลัก มี Claude co-author ใน [implementation commit](https://github.com/aaif-goose/goose/commit/5372cf21c4c043cb25959d08529c766012cdbd48); Codex ทำ review แยกบทบาท **ชนิดงาน:** bug fix/cross-module ระหว่าง migration

| ขั้น / เวลา | หลักฐาน |
|---|---|
| Requirement — 17 ส.ค. 2026 | **D-artifact:** [issue #11296](https://github.com/aaif-goose/goose/issues/11296) ให้ recipe/repro ของ structured output ที่วนไม่จบผ่าน ACP; expected outcome เปิดทางให้ส่ง tool ได้จริงหรือ fail อย่างชัดเจน |
| Scope / implementation — 18 ส.ค. | **D-report/artifact:** [#11307](https://github.com/aaif-goose/goose/pull/11307) เลือก fail-fast และอ้าง migration parity ใน AGENTS; patch/tests ครอบคลุม legacy loop และ state machine |
| Review → rework | **D-review:** [reject ก่อน inference](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828196036), [capability ไม่ใช่ context ownership](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828216905) และ [คำแนะนำต้องลบ response block ทั้งก้อน](https://github.com/aaif-goose/goose/pull/11307#discussion_r3828395594) |
| Follow-up commits | **D-artifact:** [d656b43](https://github.com/aaif-goose/goose/commit/d656b43bfddc7df8bfdd49da13c3efbc896c99d0) แก้ timing; [ddf10a2](https://github.com/aaif-goose/goose/commit/ddf10a298497a493226908626cd45d1935ba8e90) แก้ recovery text |
| Verification | **D-report:** PR รายงาน 1,909 tests ผ่านพร้อมหนึ่ง failure ที่เทียบว่าเป็นปัญหาเดิม, capability tests และ state-machine E2E; **U:** ไม่ได้ตรวจ raw logs ทั้งหมด |
| Merge — 21 ส.ค. | **D-artifact:** PR merge เป็น [a5de3781](https://github.com/aaif-goose/goose/commit/a5de37814adb1b8f7eab3046c53811d5808733fa); เป็นการรับ bounded repair ไม่ใช่การเพิ่ม forwarding capability |

**D-report:** PR แยก actual forwarding ไป [#10955](https://github.com/aaif-goose/goose/issues/10955) ซึ่งเปิดไว้ตั้งแต่ 5 ส.ค. และพูดถึง disabled extensions ที่ external harness ค้น/เปิดใช้ไม่ได้ ไม่ใช่ issue ที่เพิ่งสร้างหลัง finding นี้

**D-artifact:** หน้า #10955 ณ วันที่ตรวจแสดง open, ผู้รับผิดชอบ `DOsinga` และ GitHub Project “Goose Issues” มี Status = Ready ส่วน Relationships ยังไม่มี และ Development ไม่แสดง branch/PR **U:** ไม่เห็นเวลาที่เปลี่ยนเป็น Ready, selected design หรือความหมายที่ถูกบังคับใช้จริงของสถานะนี้ใน agent run ของ #11307

**D-artifact:** [AGENTS ณ first implementation](https://github.com/aaif-goose/goose/blob/5372cf21c4c043cb25959d08529c766012cdbd48/AGENTS.md) กำหนด issue เป็นแหล่งขอบเขต/verification plan, ให้เริ่มจาก Ready และให้ยก material design change กลับไปคุยใน issue; แต่ linkage ที่เห็นใน #11307 มีเฉพาะการอ้าง parity จึงคง **U ว่าปฏิบัติตาม readiness/board protocol ทุกขั้นหรือไม่**

**I:** การเลือก fail-fast ทำให้ปิดงานแก้อาการโดยไม่ต้องรอ capability ใหญ่ทั้งหมด เงื่อนไขคือ scope ของ repair ต้องตรง expected outcome และลิงก์สิ่งที่ยังทำไม่ได้ไว้ **U:** ไม่มีหลักฐานว่า #10955 เป็น blocker/child ของ #11307 หรือว่ามี agents ทำสองเรื่องพร้อมกัน คำว่า AI-filed ใน #10955 เป็นหลักฐานผู้ช่วยเขียนรายงาน ไม่ใช่ AI implementation

<a id="e5"></a>

## E5 — Cline: companion tasks และปัญหาที่ปรากฏหลังงานก่อนหน้าลงแล้ว

**สถานะ:** กรณีหลักใน [Cline](https://api.github.com/repos/cline/cline), สร้าง 6 ก.ค. 2024, 67,938 stars ณ วันที่ตรวจ มี Claude attribution ใน PR/commits ที่ระบุด้านล่าง **U:** session URLs เปิดเนื้อหาไม่ได้ ไม่ใช้พิสูจน์ agent count หรือ parallel execution

### E5a — #13969 + #13970: แบ่ง report เดียวเป็นสองผลลัพธ์

| งาน | ขอบเขต | ผลที่เห็น |
|---|---|---|
| [#13969](https://github.com/cline/cline/pull/13969) | เชื่อม mistake-limit callback, question UI, steering และการพัก runtime ระหว่างรอคำตอบ | เปิด 8 ก.ย. 22:34:54; merge 9 ก.ย. 02:45:25 มี Claude attribution ใน [e3b2e375](https://github.com/cline/cline/commit/e3b2e375c7f4e0c09cfef277ce5031c0bf8d5168) |
| [#13970](https://github.com/cline/cline/pull/13970) | เปลี่ยน model-facing editor error เมื่อ `old_text` เป็น null/ไม่ได้ส่ง โดยคง behavior ของ valid calls | เปิด 8 ก.ย. 22:36:45; merge 23:14:58 body ระบุ companion จาก report เดียวกันและ Generated with Claude Code |

**D-artifact/report:** สอง PR แยก run-control/UI recovery ออกจากคำแนะนำสำหรับ tool error; #13970 จำกัดไว้หนึ่ง string และยอมคง VS Code copy ไว้นอก scope **I:** เป็น decomposition ตามผลลัพธ์/contract ที่ตรวจแยกได้ **U:** ใครตัดสินใจแบ่ง, มี task graph หรือไม่ และทำ implementation พร้อมกันหรือ sequential ใน session ที่ลิงก์

**D-review/report:** ใน #13969 [teardown finding](https://github.com/cline/cline/pull/13969#discussion_r3962894505) และ [duplicate prompt finding](https://github.com/cline/cline/pull/13969#discussion_r3963154102) กลับเป็น fixes/tests ใน PR เดิม PR รายงาน scripted hub/browser probe ที่ทำให้เห็นว่าต้อง hold execution จริง ไม่ใช่เพียงส่ง callback; ระบุข้อจำกัดว่าไม่ใช่ native Tauri/live Kimi/full monorepo validation

**D-review/report:** [scope negotiation](https://github.com/cline/cline/pull/13969#discussion_r3963789085) แยก ordinary questions ที่ค้างจากปัญหาเดิมออกจาก callback scope และถอน blocker ของเรื่องนั้น นี่เป็น finding disposition ที่เปิดเผย ไม่ใช่การถือว่าทุก finding ต้องขยายงานปัจจุบัน

**D-artifact/report:** #13970 ลด scope จาก schema/test changes กลับเป็น executor error ใน [db67f4b](https://github.com/cline/cline/commit/db67f4b) [review เรื่อง coverage](https://github.com/cline/cline/pull/13970#discussion_r3962933109) ระบุ focused test ที่ถูกถอดเป็น non-blocking; [human approval](https://github.com/cline/cline/pull/13970#pullrequestreview-5147922881) รับความถูกต้องของ wording แต่บอกว่ายังต้องทดสอบกับ model จึงจะรู้ว่าลด repeated Kimi calls ได้จริง

**I:** “รับ string change” กับ “พิสูจน์ว่าปัญหา loop หายบน model จริง” เป็นคนละ claim PR ที่ merge แล้วจึงมี validation gap ที่บอกตรง ๆ ได้ **U:** ไม่ทราบผล model-level test ภายหลัง และไม่สรุปว่าช่องว่างนี้ถูกยอมรับด้วยนโยบายสากลของทีม

### E5b — #13969 → #13999: อาการคล้ายกัน แต่เป็นอีก path

[#13999](https://github.com/cline/cline/pull/13999) เปิด 9 ก.ย. 19:56:41, ระบุ follow-up หลัง #13969 shipped และ supersedes #13165 **D-report:** มีรายงาน chat หยุดอีกครั้ง แต่คราวนี้เป็น reasoning-only turn ที่ไม่มีข้อความหรือ tool call และ runtime ถือเป็น completed จึงเสนอ empty-turn signal/nudge พร้อม mistake accounting

**D-report:** PR รายงาน agents tests 65/65, core 69/69, typecheck และ Biome ผ่าน พร้อม Claude disclosure **D-artifact:** PR ยัง open/unmerged ณ snapshot **U:** final acceptance/deploy และผลใช้จริงของ candidate

**I:** signal หลัง merge อาจเป็น path ที่ยังไม่เคยครอบคลุม ไม่จำเป็นต้องเป็น regression ที่ patch ก่อนหน้าสร้างขึ้นโดยตรง ในเคสนี้ source ระบุชัดว่าไม่ใช่ mistake-limit path เดิม จึงใช้คำว่า **post-shipment gap** และ linked follow-up แทนกล่าวว่า #13969 เป็นสาเหตุของบั๊กใหม่

### E5c — #13968 → #13976 → #13978: repair chain ที่ต้องเปลี่ยนกลไก

| PR / เวลา merge UTC | งานต่อที่ระบุใน source | ขอบเขตหลักฐาน |
|---|---|---|
| [#13968](https://github.com/cline/cline/pull/13968), 8 ก.ย. 23:04 | แก้ desktop duplicate stream และ index หลัง sidecar เปลี่ยน | **D:** Claude attribution; [live harness report](https://github.com/cline/cline/pull/13968#issuecomment-5593008205) เทียบกับ canonical store และระบุส่วนที่ reproduce ไม่ได้ |
| [#13976](https://github.com/cline/cline/pull/13976), 9 ก.ย. 02:26 | follow-up เพราะ lease ห้าวินาทีหมดระหว่าง long-running work; ต้องล้าง stale owner บน stop/reset/rebuild/rollback | **D:** Claude disclosure และ [review](https://github.com/cline/cline/pull/13976#discussion_r3963965849) → [fix response](https://github.com/cline/cline/pull/13976#discussion_r3964052088) → [c075473](https://github.com/cline/cline/commit/c075473a80b36ced3bedf8221629bc1585a3d254) |
| [#13978](https://github.com/cline/cline/pull/13978), 9 ก.ย. 04:24 | follow-up ทั้งสอง PR เปลี่ยนจากเวลาเป็น subscription ownership ที่ตรวจตรงได้ | **D:** explicit chain และ merged artifact; **U:** AI implementation attribution ของ PR นี้ ไม่ยืม attribution จาก predecessor |

**D-report:** #13978 บันทึกว่า one-socket redesign เลื่อนเพราะ blast radius และ live-stack/manual repro ยังไม่ตรวจ [architecture-doc finding](https://github.com/cline/cline/pull/13978#discussion_r3964504328) มีคำตอบว่าจะเพิ่มพร้อม broader change **U:** ในสายหลักฐานนี้ไม่เห็น follow-up task ที่ยืนยันว่า obligation ดังกล่าวถูกปิดแล้ว

**I:** สายนี้แสดงการเปลี่ยน decomposition/mechanism ตามสิ่งที่พบระหว่างงาน การแก้ follow-up แบบแคบทำได้ แต่ผู้ประสานงานยังต้องเก็บ unresolved redesign/verification ไว้ต่างหาก มิฉะนั้นจำนวน PR ที่ merge จะดูเหมือนปิดผลลัพธ์รวม ทั้งที่หลักฐานยังไม่ถึงขั้นนั้น

<a id="e6"></a>

## E6 — OpenClaw: เปลี่ยน PR ใหญ่เป็น stack และคง merge gate

**สถานะหลักฐาน:** กรณีเปรียบเทียบของโปรเจกต์ใหญ่และ active ที่มี AI review ชัด; **U: AI implementation ของ stack นี้** ไม่มีหลักฐาน attribution ที่พอจาก commits ที่ตรวจ จึงไม่รวมเป็นเคสยืนยัน AI เขียน patch ทั้งชุด

[Repository metadata](https://api.github.com/repos/openclaw/openclaw) ระบุสร้าง 24 พ.ย. 2025 และ 389,609 stars ณ วันที่ตรวจ ขนาด/ความนิยมปัจจุบันไม่ใช่หลักฐานสัดส่วน AI authorship ส่วน feature “Workboard” เป็นสิ่งที่ทีมกำลังสร้าง ไม่ใช่หลักฐานว่าผู้พัฒนาใช้ Workboard จัด PR นี้

### E6a — #143728 → แปด PR: decomposition เปลี่ยนกลางทาง

| เวลา UTC / ขั้น | หลักฐาน |
|---|---|
| 10 ก.ย. 05:32 — เปิดงาน | **D-artifact:** [#143728](https://github.com/openclaw/openclaw/pull/143728) รวม cards, lists, controls, editor และ bulk actions บัญชีผู้เปิด PR คือ `vyctorbrzezowski` (ไม่ยืนยันตัวผู้ implement); **U:** initial request และ task board ภายใน |
| 10 ก.ย. — iteration/hold | **D-report:** description ที่เก็บไว้ระบุว่ากำลังปรับ UI และขออย่า merge; มีผล visual comparison, focused tests และ CI บางส่วน พร้อมช่องว่างการตรวจ |
| 10 ก.ย. 08:12 — review ที่แก้ล่าสุด | **D-report:** [ClawSweeper/Codex review](https://github.com/openclaw/openclaw/pull/143728#issuecomment-5613746593) บน `31b24a138818d6425af525d1dec62a36141c12b5` คงสอง findings เรื่อง stale peer status และ stored colors พร้อมรายการก่อน merge; reviewer ระบุว่าไล่จาก source โดยไม่ได้รัน target code |
| 11 ก.ย. 06:55–07:00 — แตกงาน | **D-artifact:** [timeline](https://api.github.com/repos/openclaw/openclaw/issues/143728/timeline?per_page=100) เชื่อม PR ใหม่แปดตัว; body ของ original ระบุให้ review จากล่างขึ้นบนและคง UI/UX ที่รับไว้ |
| 11 ก.ย. 08:36 — ปิด original | **D-artifact:** original ปิดโดยไม่ merge เพราะ superseded; **U:** ใครสั่งให้แตกงานและเกณฑ์ขนาดที่ใช้ ไม่ปรากฏเป็น initial instruction |
| 13 ก.ย. — ตรวจ stack/rework | **D-report:** body ของแต่ละชั้นบันทึก scoped review, integration validation และการแก้ fixtures/CI; การลง stack ถูกปฏิเสธครั้งหนึ่งเพราะมี required gate ถูกยกเลิก แม้อีก suite ผ่าน |
| snapshot ที่ตรวจ | **D-artifact:** PR ทั้งแปดยัง open/unmerged; **U:** acceptance/deploy/completion ภายหลัง snapshot |

มีคำรายงานที่ต้องอ่านร่วมกัน: original body รายงาน autoreview สะอาดบน `31b24a...` แต่ public review บน revision เดียวกันยังมี findings นี่เป็น **D ว่ามีผลประเมินต่างกัน** ไม่ใช่หลักฐานว่า review ชุดหนึ่งถูกโดยอัตโนมัติ หรือว่า agent จงใจประกาศเสร็จเท็จ

| ชั้น | ขอบเขต | ฐานที่ PR ระบุ |
|---|---|---|
| [#144747](https://github.com/openclaw/openclaw/pull/144747) | preview session lifecycle | main |
| [#144748](https://github.com/openclaw/openclaw/pull/144748) | shared agent/appearance controls | lifecycle branch |
| [#144751](https://github.com/openclaw/openclaw/pull/144751) | navigation, filters, mobile | controls branch |
| [#144752](https://github.com/openclaw/openclaw/pull/144752) | cards/status และ concurrent edits | navigation branch |
| [#144753](https://github.com/openclaw/openclaw/pull/144753) | responsive list | cards branch |
| [#144754](https://github.com/openclaw/openclaw/pull/144754) | card/board editors | list branch |
| [#144755](https://github.com/openclaw/openclaw/pull/144755) | details/session context | editors branch |
| [#144756](https://github.com/openclaw/openclaw/pull/144756) | selection/bulk actions | details branch |

**D-artifact:** เป็น dependency ผ่านฐาน branch และทั้งแปด PR มีบัญชี GitHub `vyctorbrzezowski` ใน assignees **I:** แบ่งตามผลลัพธ์และชั้น integration มากกว่านับจำนวนไฟล์; แต่ลำดับ stack ไม่ใช่หลักฐานว่าทุกขั้นจำเป็นต้องทำ sequential ตั้งแต่เริ่ม **U:** จำนวน implementer agents, การแบ่งทำ parallel, file/contract ownership ภายใน execution และ payload handoff

### Evidence และสถานะที่มีความหมายจำกัด

**D-report:** [#144748](https://github.com/openclaw/openclaw/pull/144748) และ [#144756](https://github.com/openclaw/openclaw/pull/144756) รายงาน 570 tests บน integrated top `8de11a6` แยกจาก upgrade proof บน `73482ef` และภาพที่จับจาก revision ก่อนหน้า พร้อมบอกว่าจำนวน tests ที่ซ้ำกันบวกสะสมไม่ได้ body ยังรายงานว่า merge stack ถูกปฏิเสธเพราะ cancelled gate และการรันซ้ำพบ prerequisite ของ runner ที่ต้องแก้ในชั้นฐาน

**D-artifact:** [check-runs ของ `043c4aa7`](https://api.github.com/repos/openclaw/openclaw/commits/043c4aa79516047bb02fad5e8ff7235c07eba439/check-runs?per_page=100) หน้าแรกที่ตรวจมี 100 จาก 384 records: cancelled 85, skipped 12, in progress 3 จึงยืนยันได้ว่ามี cancelled/pending checks บน revision นี้ **U:** ไม่ได้ตรวจทุกหน้า หรือกฎ required checks ทั้งหมด; ตัวเลขนี้ไม่ใช่สรุป CI ทั้ง stack และไม่ใช่หลักฐานอิสระของเหตุปฏิเสธ merge ที่ผู้เขียนรายงาน

**D-report/artifact:** [review ของ #144748](https://github.com/openclaw/openclaw/pull/144748#issuecomment-5631266658) เก็บ verdict, reviewed SHA, findings, history และคำอธิบาย labels ไว้ใน comment ที่แก้ซ้ำได้ ผล “ไม่พบ actionable defect” ยังมาพร้อม `needs-human` และ blocked state ในรอบที่ตรวจ [comment เริ่ม review รอบใหม่](https://github.com/openclaw/openclaw/pull/144748#issuecomment-5655577483) มี revision, run owner และ lease expiry นี่เป็นร่องรอยการมอบหมายงาน review; ไม่ใช่ transcript ของ reviewer

**U:** portal ที่ PR ลิงก์ เช่น [integration run](https://crabbox.openclaw.ai/portal/runs/run_6e4467fd7a0c40477940f778305c2b08) เปิดเนื้อหาไม่ได้ในการตรวจนี้ จึงใช้ได้เพียงคำรายงานใน PR ส่วน body อ้าง native stack #144757 แต่ endpoint PR ที่ลองเปิดไม่พบ จึงไม่สร้าง project metadata เติมเอง

**I:** ข้อสังเคราะห์ที่รองรับคือให้ outcome, dependency, review result และ evidence revision มีที่อยู่คนละส่วนที่เชื่อมกันได้ ไม่ใช้ label “clean” เป็นตัวแทนของ acceptance

### E6b — reported post-merge CI regression: #143968 → #147293

**D-artifact:** [#143968](https://github.com/openclaw/openclaw/pull/143968) merge 13 ก.ย. 18:23:12; [#147293](https://github.com/openclaw/openclaw/pull/147293) เปิด 18:57:37 และ merge 19:17:53 เป็น PR แยกสำหรับแก้ routing expectation ของ tests

**D-report:** #147293 ระบุว่า predecessor เพิ่ม test ใหม่จน expectation เดิมทำ main CI แดง พบใน [run ของ PR อื่น](https://github.com/openclaw/openclaw/actions/runs/34775551749) และรายงานหนึ่ง test fail บน main ก่อนแก้ กับ 602 ผ่านหลังแก้ **D-report:** [review](https://github.com/openclaw/openclaw/pull/147293#issuecomment-5655455292) ให้พร้อมสำหรับ maintainer review; [merge receipt](https://github.com/openclaw/openclaw/pull/147293#issuecomment-5655499777) เชื่อม prepared head `9aecc88d...` กับ landed commit `01d9d686...`

**U:** เหตุผลเชิงนโยบายที่เลือก PR ใหม่แทน reopen issue และ AI implementation attribution ของ repair นี้ **I:** สายงานนี้แสดงว่าการปิดวงจรหลัง merge ต้องรับ signal จาก CI ของงานอื่นได้ และรักษาลิงก์กลับ predecessor

<a id="e7"></a>

## E7 — Huf: หลักฐาน parallel work และ integration failure ในโปรเจกต์เล็กกว่า

**สถานะ:** เคสเสริม ใช้อธิบายกลไกที่เปิดเผยละเอียด; ไม่ใช้แทนหลักฐานจากโปรเจกต์ใหญ่ [metadata](https://api.github.com/repos/tridz-dev/huf) ระบุสร้าง 11 ส.ค. 2025 และ 111 stars ณ วันที่ตรวจ **D-report:** ผู้เขียนเปิดเผยการใช้ parallel subagents ใน PR; **U:** model, จำนวน agents และ transcript

### E7a — #644: endpoint ownership กับ shared router

[PR #644](https://github.com/tridz-dev/huf/pull/644) สร้าง public developer API และ Developer Settings UI โดยเลือก phases 0–3 ของ spec ภายใน ส่วน files/multimodal, SDK polish, OAuth และ webhooks ถูกประกาศว่านอกขอบเขต **U:** `GOAL.md` และ task-by-task `TRACKER.md` อยู่ใน workspace ภายใน จึงไม่เห็น AC ต้นฉบับหรือ dependency graph ครบ

**D-report ที่เชื่อมตรงกับ execution:** ผู้เขียนระบุว่าให้ subagents ทำ endpoint modules แยกไฟล์ มอบ runtime code เดิมให้แต่ละงานนำไปห่อ และอ่าน diff ของทุก module ก่อนเชื่อมเข้ากับ `router.py` ซึ่งเก็บให้มีผู้แก้เพียงคนเดียว **I:** เป็นการทำ parallel รอบ contract ร่วมพร้อมผู้ดูแลจุด integration; ไม่ได้พิสูจน์ว่าระบบป้องกันการชนกันอัตโนมัติ

| เวลา UTC | เหตุการณ์และหลักฐาน |
|---|---|
| 23 ส.ค. 13:29–13:30 | **D-artifact/report:** [backend commit](https://github.com/tridz-dev/huf/commit/74953502a58ca935e8886ebc484ec9daf4608ee0) ระบุ syntax-only และยังไม่มี bench; [frontend commit](https://github.com/tridz-dev/huf/commit/437ef0622ff69bdbb218863a8188e76335e6bc7c) ระบุ typecheck จากสำเนาเทียบเท่า เพราะ worktree ไม่มี dependencies และต้องตรวจต่อ |
| 23 ส.ค. 13:31 | **D-artifact:** เปิด PR; body แยกสิ่ง implement แล้วกับสิ่งยังไม่ได้ตรวจ end-to-end พร้อม checklist ก่อน merge |
| 23 ส.ค. 14:59–15:07 | **D-artifact/report:** commits แก้สามปัญหาจาก live bench ตามตารางด้านล่าง |
| 23 ส.ค. 15:14 | **D-report:** [update](https://github.com/tridz-dev/huf/pull/644#issuecomment-5386726075) ระบุสร้าง disposable bench แล้วตรวจ curl, key auth/revoke, scope deny และ UI; ให้ถือ core paths ของ phases 0–3 ที่รายงานตรวจแล้ว |
| 24 ส.ค. | **D-artifact:** มี frontend changes เพิ่ม รวม final unused-helper fix `54450373...`; **U:** live report ก่อนหน้านั้นไม่ใช่หลักฐานว่าทุกอย่างบน final head ถูกตรวจซ้ำ |
| 24 ส.ค. 20:37 | **D-artifact:** base branch ถูกลบแล้ว PR ปิดอัตโนมัติ ตาม [timeline](https://api.github.com/repos/tridz-dev/huf/issues/644/timeline?per_page=100) |
| 25 ส.ค. 06:37–07:41 | **D-artifact:** reopen → เปลี่ยน base → ready for review 07:41:11 → merge 07:41:49; closure ครั้งแรกไม่ใช่ completion |

| ปัญหาที่ live verification เปิดเผย — D-report | Patch — D-artifact |
|---|---|
| fixture ติดตั้งไม่ได้ เพราะรายการ capability ของ Select field ไม่ตรงกับ permissions | [ae3aa6ec](https://github.com/tridz-dev/huf/commit/ae3aa6ec111213f16d0cc9b052955464fda392f7) |
| Frappe ดัก Bearer header ก่อน handler ทำให้ auth ใหม่ไม่ทำงาน | [252adec3](https://github.com/tridz-dev/huf/commit/252adec3eeb4b0d787cf70c5b45fc647efe895ad) เปลี่ยน resolver เป็น `X-Huf-Api-Key` |
| `/v1/me` คืน Guest เพราะอ่าน ambient session แทน resolved principal | [2dcb64dc](https://github.com/tridz-dev/huf/commit/2dcb64dc5b45236844cfe0788f9598b13e485446) |

**D:** มี implementation และ fixes ที่ตรวจกลับได้; **D-report:** มีการทดสอบระบบจริง **U:** ไม่มี raw recording/log ครบและไม่มี formal review records ใน [endpoint ที่ตรวจ](https://api.github.com/repos/tridz-dev/huf/pulls/644/reviews?per_page=100) คำว่า “personally reviewed” ใน body ไม่ใช่ formal independent approval

**I:** เคสนี้สนับสนุนให้สร้าง verification obligation เป็นส่วนของงานที่ agent ต้องจัดการต่อเอง การส่งรายการ manual tests ให้คนทำทุกข้อไม่ใช่จุดจบโดยจำเป็น เพราะในเคสนี้ผู้ทำงานกลับไปจัด environment และรายงานผลเพิ่ม อย่างไรก็ดีไม่ควรใช้ checkbox ใน body ที่ยังค้างเพื่อสรุปว่าไม่มี live test: comment ภายหลังให้หลักฐานเพิ่ม

### E7b — integration branch หาย และ merged PR ที่ต้อง re-land

**D-report:** [#666](https://github.com/tridz-dev/huf/pull/666) บันทึกว่า integration branches ถูกลบ ทำให้ 55 commits อยู่บน branch ที่หายและเก้า PR ถูกปิดตามไปด้วย ก่อนกู้จาก clone ที่ยังเก็บ tip แล้วเปิด PR กลับ การระบุวันที่ 25 ส.ค. ในคำรายงานอ่านร่วมกับ UTC timeline ของ #644 ซึ่งปิด 24 ส.ค. 20:37 **U:** ผู้หรือ agent ที่ลบ branch ไม่ได้รับการยืนยัน จึงไม่จัดว่าเป็น “agent ลบ branch”

**D-report:** [promotion #667](https://github.com/tridz-dev/huf/pull/667) อธิบายว่า backend CI trigger เฉพาะ `develop` ทำให้ PR ที่ลง `pre-develop` ไม่ได้ backend run; suite จึงสะสมปัญหาจนรันไม่ถึง tests มีการแก้ test environment และพบ product bugs เพิ่ม ข้อความนี้เป็นคำรายงานของผู้ดูแล ไม่ใช่การตรวจทุก historical workflow run

**D-report:** [#672](https://github.com/tridz-dev/huf/pull/672) อธิบายว่าต้อง re-land #646 แม้ GitHub แสดง MERGED เพราะ merge commit ไม่อยู่ใน integration branch ผู้เขียนระบุการ merge สอง PR ห่างกัน 57 วินาทีและใช้ tip เก่าเป็นสาเหตุ พร้อมรายงาน audit ancestry ของงานอื่น **D-artifact:** มี PR ใหม่เพื่อ re-land จริง เปิด 25 ส.ค. 09:49:38 และ merge 09:49:55 **U:** ไม่มี execution log ของผู้ทำ merge ที่พิสูจน์กลไกการสูญหายครบ จึงคงเหตุเชิงสาเหตุเป็น D-report

การ integrate #672 ยังบันทึก decision ที่ต้องรักษา interface: refactor ของ `sdk_tools.py` ต้องนำ Send Email ที่อีก branch เพิ่มไว้เข้ามาด้วย; สอง branch แก้ leak เดียวกันใน test และมี route conflict ที่ต้องเลือกตาม intent **D-report:** มี shared-file/contract conflict **U:** ไม่ทราบว่าทั้งสอง branch มาจาก agents ที่รันพร้อมกันหรือไม่

**I:** “merged” เป็น event ของ GitHub; การส่งมอบไปยัง branch เป้าหมายต้องมีหลักฐานว่า change อยู่ในผล integration ด้วย กรณีนี้เลือก PR ใหม่เพื่อ re-land และรักษาประวัติ PR เดิม เป็นเหตุผลเฉพาะที่เปิดเผย ไม่ใช่นโยบายสากลว่าต้องสร้าง follow-up ทุกครั้ง
<a id="g1"></a>

## G1 — GitHub Projects ปัจจุบัน: โครงสร้างงานและ fields

**ขอบเขต:** ตรวจเอกสาร GitHub.com ทางการวันที่ 14 ก.ย. 2026 เป็น **D-doc ของ capability** แยกจาก D-artifact/D-report ใน E1–E7 ไม่ได้ทดลองแก้ Project จริง และไม่ใช้เอกสาร product ไปยืนยัน adoption ของกรณีศึกษา

| Capability | DIRECT EVIDENCE จากเอกสาร | การประยุกต์ — I / ขอบเขตที่ยัง UNKNOWN |
|---|---|---|
| Projects เป็นมุมมองรวม | [About Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects) อธิบาย table/board/roadmap ระดับ user หรือ organization, views และ custom fields สำหรับ issues/PRs/drafts | ใช้เป็น execution board โดยให้ repository Issue ถือ outcome/AC; U ของ Project ปลายทางที่ผู้ใช้จะเลือก |
| Issue/PR metadata เชื่อมสองทาง | หน้าเดียวกันระบุว่าแก้ข้อมูลอย่าง assignee ใน Project แล้ว Issue เปลี่ยนตาม และกลับกัน | ไม่ต้องทำ task copy อีกชุด; Project Status ยังเป็นคนละความหมายกับ issue open/closed |
| Draft item แปลงเป็น Issue ได้ | [Adding items](https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project) อธิบายเพิ่ม Issues/PRs และสร้าง draft ที่แปลงเป็น Issue ได้ | เสนอให้แปลง draft เป็น repository Issue ก่อนมอบหมายงานถาวร ไม่ใช้เป็นที่เก็บ AC/PR workflow ของงานที่เริ่มแล้ว |
| Hierarchy | [Adding sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues) อธิบาย nested sub-issues; [parent/sub-issue progress](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields) แสดง parent และความคืบหน้าลูกใน Project | hierarchy ไม่ใช่ prerequisite edge และ progress ไม่พิสูจน์ parent integration; U ของ automation ปิด parent ที่ผู้ใช้ตั้งเพิ่ม |
| Dependency | [Creating issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies) มี Blocked by/Blocking ผ่าน Relationships และ blocked indicator บน board; ต้องมีสิทธิ์อย่างน้อย triage เพื่อสร้าง | เก็บ dependency แบบ native ได้; docs ไม่รับรอง AC-aware ready/claim/close guard จึงต้องตรวจเงื่อนไขเพิ่มเติมใน coordinator |
| การจัดมุมมอง | [Best practices for Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects) อธิบาย filtering/grouping และแยกงานด้วย sub-issues/dependencies | เสนอ Work/Review/Needs attention views; U ว่า view จะอ่าน missing AC จาก comment ได้เอง จึงต้องมีตัวเติม field/label หากต้องการ filter |

### Project custom fields กับ organization issue fields

**D-doc:** [Managing issue fields in your organization](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/managing-issue-fields-in-your-organization#issue-fields-and-projects) แยก issue fields ซึ่ง value อยู่บน Issue และคงค่าข้าม Projects ออกจาก project-level fields ซึ่ง Issue เดียวกันมีค่าต่างกันในแต่ละ Project ได้ Organization owners เป็นผู้จัดการ issue fields

**D-doc:** [About issue fields in projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-issue-fields) ระบุว่า issue fields ใช้กับ Issues ของ organization นั้น; ช่องของ PRs, drafts หรือ Issue จาก organization อื่นไม่ใช่ record ประเภทเดียวกัน และ field visibility มีผลต่อการแสดง **U:** ช่องว่างหนึ่งช่องจึงไม่พิสูจน์เสมอไปว่าไม่มีข้อมูล underlying

**I:** เริ่มด้วย AC/spec ใน Issue body และ Status ของ execution Project เดียว หากต้องการ priority/ข้อมูล issue-level ที่คงค่าในหลาย Projects และใช้ organization ที่รองรับ จึงค่อยใช้ issue fields เลือก canonical layer ก่อนสร้าง field ชื่อซ้ำอย่าง Priority หรือ Acceptance ไม่บังคับ issue fields ระดับ organization ให้ solo workflow ที่ใช้ personal Project

**D-doc / U:** เอกสาร sub-issue progress แสดงตัวนับ แต่ไม่ได้รับรองว่าลูกครบจะ auto-close parent หรือทดสอบ parent AC ให้ การปิดลูกแบบ not planned/duplicate ยังต้องอ่าน disposition ตาม policy ก่อนถือว่า parent ได้ capability ที่ต้องใช้

<a id="g2"></a>

## G2 — Automation, review และความหมายของ Done

### Default workflows เป็นการตอบสนอง event

**D-doc:** [Using the built-in automations](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations) ระบุ default สองตัวเมื่อสร้าง Project: issue/PR closed → Status Done และ PR merged → Status Done รวมถึงความสามารถ workflow ทิศ Status change → issue close และเปิด/ปิด workflow ได้

**D-doc:** [Closing an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/administering-issues/closing-an-issue) มีเหตุปิดทั้งงานเสร็จและไม่วางแผนทำ ส่วน [GraphQL IssueClosedStateReason](https://docs.github.com/en/graphql/reference/issues#issueclosedstatereason) มี COMPLETED, DUPLICATE, NOT_PLANNED; [Closing a PR](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/closing-a-pull-request) อธิบายการปิดโดยไม่ merge

**I:** default event mapping จึงไม่ใช่ acceptance predicate และตัวอักษร Done ไม่บอกว่าปิดเพราะส่งมอบหรือเลิกทำ เวอร์ชันบทเรียนเลือกสงวน Done ให้ accepted: ปิด/ปรับ automation ที่เขียน Done ก่อน receipt และให้ coordinator ตรวจความสอดคล้อง ไม่ใช่ข้อกล่าวอ้างว่า platform บังคับ policy นี้อยู่แล้ว

### PR linkage และ branch เป้าหมาย

**D-doc:** [Linking a PR to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue) อธิบาย closing keywords และ manual Development links; linked PR ที่ merge เข้า default branch จะปิด linked issue Closing keyword ใน PR description ที่ base เป็น branch อื่นถูกละเลย ส่วน keyword ใน commit message อาจปิด Issue เมื่อ commit ไปถึง default branch

**D-doc — configuration boundary:** [GitHub Changelog 23 เม.ย. 2025](https://github.blog/changelog/2025-04-23-users-can-now-choose-whether-merging-linked-pull-requests-automatically-closes-the-issue/) ระบุ repository setting สำหรับเปิด/ปิดการ auto-close linked issues เมื่อ merge ตั้งไว้ใน Settings → General → Issues และเปิดเป็น default พฤติกรรม auto-close ด้านบนจึงต้องอ่านร่วมกับ setting นี้ ซึ่งแยกจาก Project workflows; ไม่ได้ตรวจ setting ของ repo ปลายทาง

**I:** แยก “กล่าวถึง Issue” ออกจาก “ผูกเป็น closing reference” เช่น PR ของ child ที่ยังไม่ส่ง outcome รวมไม่ควรปิด parent เมื่อ merge หาก task delivery อยู่ที่ integration branch ให้บันทึก receipt/target นั้นโดยตรง ไม่รอหรืออ้าง auto-close rule ของ default branch แทน policy Manual Development link ก็อาจเป็น closing reference ได้ จึงใช้อ้างอิงข้อความธรรมดาหรือกำหนด auto-close setting ตาม policy เมื่อต้องคง Issue เปิด

**U:** branch/release policy ของผู้ใช้ยังไม่ได้ตรวจ การมี Development link ใน PR ไม่พิสูจน์ว่าครบ acceptance; การไม่มี auto-close เมื่อเข้า intermediate branch ไม่พิสูจน์ว่างานย่อยยังส่งมอบไม่ครบ

### Required checks / review / merge queue

**D-doc:** [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) อธิบาย required reviews, dismiss stale approvals, review ของ latest push และ required status checks รวมถึงขอบเขต bypass ตาม configuration ไม่ใช่การรับประกันว่าทุก repo เปิดใช้ทุกกฎ

**D-doc:** [Troubleshooting required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks) ระบุ checks ต้องสัมพันธ์กับ latest SHA และ successful check statuses รวม success/skipped/neutral; แยก workflow ที่ไม่ trigger แล้วค้าง pending ออกจาก job ที่ skipped และผ่านเกณฑ์ merge ได้ หากใช้ merge queue กับ Actions ต้องมี `merge_group` trigger เพื่อได้ checks ของ queue

**I:** merge eligibility ไม่เท่ากับ “AC ทั้งหมดถูก exercise” ให้ receipt แสดงว่า tests ใดรันจริง, บน candidate/test-merge/integrated revision ใด และ required checks ใดเป็นแค่ aggregate signal ใช้ required checks/review rules เพื่อกัน merge ที่ขาดเงื่อนไขซึ่งกฎครอบคลุม ส่วน Issue/Project acceptance และ deployed behavior ต้องมี policy/evidence เพิ่มตาม scope

**D-doc เฉพาะ Copilot review:** [Using Copilot code review](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/request-a-code-review/use-code-review) แยก approval assessment ใน comment ออกจาก approving review ที่นับใน merge requirements โดย default ไม่นับ แต่ optional Copilot approvals ที่เปิดตาม settings สามารถนับได้ และถูก dismiss เมื่อมี commits ใหม่ เอกสารกำกับ approvals เป็น public preview **I/U:** ตรวจ reviewer product และ config จริงก่อนใช้ AI review แทน required approval ไม่สรุปว่า AI review ทุกระบบนับได้หรือไม่ได้เหมือนกัน

**U:** plan, branch rules/rulesets, bypass actors, reviewer authority และ runner triggers ของ repo ปลายทางยังไม่ถูกอ่าน จึงไม่อ้างว่า merge protection ทำงานอยู่จริง

### Auto-add และ evidence retention

**D-doc:** [Adding items automatically](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically) เพิ่ม matching items เมื่อ created/updated; เปิด auto-add ไม่ได้ backfill items ที่มีอยู่ทั้งหมด **I:** migration ต้องมีขั้นนำเข้า selected existing Issues และตรวจ membership เอง ไม่ถือว่าเปิด workflow แล้วครบ

**I:** auto-archive ใช้จัด active views ไม่ใช่ลบ outstanding obligation; คง acceptance receipt ที่ชี้ run/revision และข้อมูลพอให้ตรวจย้อนหลัง เมื่อ artifact เก็บแบบมีอายุให้รักษาหลักฐานที่จำเป็นตาม policy ของ repo **U:** retention/access ของ artifacts จริงยังไม่ได้ตรวจ การมีลิงก์ไม่รับรองว่าจะเปิดได้ตลอด

<a id="g3"></a>

## G3 — Assignment, agent execution, handoff และ parallel work

### Assignment แบบทั่วไปกับการสั่ง enabled agent

**D-doc:** [Assigning issues and PRs](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users) อธิบาย assignees เพื่อระบุผู้รับผิดชอบ และรองรับหลาย assignees **U:** หน้าที่ตรวจไม่รับรอง exclusive claim, lease expiry หรือ first-claim-wins สำหรับ arbitrary local agents และการเขียน Status/Assignee ไม่ใช่ API transaction เดียวที่ตรวจ AC/readiness แล้วจอง execution ให้

**D-doc:** [Use cloud agent on GitHub](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github) มี assignment ให้ Copilot เพื่อเริ่มทำงานและสร้าง PR; [About agent apps](https://docs.github.com/en/copilot/concepts/agents/agent-apps) อธิบาย issue assignment/PR mention/Agents UI เป็น entry points ของ app ที่ติดตั้งและเปิดใช้ พร้อม account/organization policy ที่เกี่ยวข้อง Agent apps ถูกกำกับ public preview ในเอกสารที่ตรวจ

**I:** แยก human/account metadata ออกจาก explicit agent invocation และบันทึก route/run ID เมื่อมอบงาน เสนอ single coordinator เพื่อจัดคิวหลาย workers ใน solo workflow แทนการสมมติว่า agent ทุกตัวอ่าน Ready แล้วแก้ Assignee ได้แบบ atomic ถ้าระบบมีหลาย coordinators จริงต้องมี arbitration/lease ที่เชื่อถือได้เพิ่ม ไม่ใช้ reread หลังเขียนเป็นคำรับรอง mutual exclusion

### Context และ handoff ต้องส่งทางที่ agent ได้รับ

**D-doc เฉพาะ Copilot cloud-agent flow:** [Use cloud agent on GitHub](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github) ระบุว่าการ assign ส่ง title, description, comments ที่มีตอนนั้น และ additional instructions; issue comments ที่เพิ่มภายหลังไม่อยู่ใน context ที่ assignment นั้นเห็น ข้อมูลใหม่ให้ส่งผ่านช่องทาง PR/session ที่รองรับ

**I:** Issue comment เป็น canonical handoff record ได้ แต่การบันทึกกับการส่งถึง worker เป็นคนละ action Coordinator ต้องส่ง pointer/ข้อเปลี่ยนแปลงผ่านช่องทางที่ agent นั้นรับจริง และบันทึก attempt ถัดไปหรือ acknowledgement เมื่อมี **U:** ไม่อนุมานว่า local/third-party agents ทุกตัวมี context boundary แบบ Copilot

**D-doc:** [Manage and track agents](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/manage-and-track-agents) อธิบาย session/log และการ steer/stop/ตรวจ changes ส่วน [Agent activity in Issues and Projects](https://github.blog/changelog/2026-03-26-agent-activity-in-github-issues-and-projects/) และ [View/manage agent sessions](https://github.blog/changelog/2026-04-23-view-and-manage-agent-sessions-from-issues-and-projects/) ประกาศ session activity บน Projects/Issues

**D-doc เฉพาะ hosted-agent route:** [Risks and mitigations for Copilot cloud agent](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/risks-and-mitigations) ระบุข้อกำหนด human review/merge และข้อจำกัดการอนุมัติ PR ของผู้มอบหมาย รวมทั้ง Actions ที่อาจต้อง approve ก่อนรันตาม configuration **I:** การเลือกใช้ route นี้ต้องรักษา product controls เหล่านี้ ไม่อนุมานจาก Project Ready หรือ generic coordinator policy ว่าจะทำทุกขั้นโดยไม่มีคนได้; workflow ในบทเรียนยังใช้กับ local/agent route อื่นตามอำนาจของ route นั้นได้

**I:** ใช้ supported session state เป็น execution signal เพิ่มได้ หากบัญชีเปิดใช้ แต่ session completed ไม่ใช่ parent AC accepted **U:** availability และการแสดง session ใน Project ปลายทางยังไม่ได้ตรวจ อีกทั้งเอกสาร capability ใหม่ไม่ทำให้ session เก่าของ E1/E5 ที่เปิดไม่ได้กลายเป็น trace ที่อ่านแล้ว

### Concurrency และ integration

**D-doc:** [Actions concurrency](https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency) ควบคุม workflow/job concurrency; behavior ขึ้นกับ group และการตั้ง cancellation/queue ตามที่รองรับ **I:** ใช้ serialize reconciliation บางขั้นได้ แต่ไม่ใช่ generic issue lock หรือ durable FIFO task scheduler ให้ local agents ระบบต้องรักษา pending obligations และ idempotency ของตน

**I:** worktree/branch isolation และ contract ownership ยังเป็นหน้าที่ coordinator ตามบทเรียน E2/E7 GitHub merge queue/checks ช่วยพิสูจน์ integration ตาม config ส่วนการแบ่งงาน/เลือก agent/ส่ง handoff เป็นอีกชั้นหนึ่ง ไม่มี claim ว่า Projects ทำทั้งหมดให้อัตโนมัติ

<a id="g4"></a>

## G4 — API, Actions, permissions และขอบเขตการตรวจ

| สิ่งที่ต้องเชื่อม | DIRECT EVIDENCE | ขอบเขตต่อ workflow |
|---|---|---|
| Project item identity | [GraphQL Projects reference](https://docs.github.com/en/graphql/reference/projects) แยก ProjectV2Item จาก content ที่เป็น Issue/PR/Draft และมี redacted item | I: เก็บ source Issue ID/URL กับ Project item ID แยก; U/permission error ไม่แปลว่า Issue ถูกลบ |
| เพิ่ม item/ตั้ง field | [Using the API](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects) แสดง addProjectV2ItemById แล้ว updateProjectV2ItemFieldValue เป็นคนละขั้น; ถ้า item อยู่แล้ว add คืน item ID เดิม | I: ใช้ idempotent ingestion + retry field update ได้; ไม่ใช่ transaction ของทั้ง Issue/Project/assignment |
| Source properties | API guide แยก Assignees/Labels/Milestone/Repository ออกจาก fields ที่เปลี่ยนผ่าน Project item mutation | I: adapter ต้องเลือก Issue/PR mutation ให้ตรงข้อมูล ไม่คิดว่า field update ตัวเดียวเปลี่ยนทุกอย่าง |
| CLI | [gh project](https://cli.github.com/manual/gh_project), [item-list](https://cli.github.com/manual/gh_project_item-list), [item-edit](https://cli.github.com/manual/gh_project_item-edit) มีเส้นทางอ่าน/เพิ่ม/แก้ items และ fields | U: ไม่ได้ตรวจ CLI ที่ติดตั้งหรือ auth ในบัญชีปลายทางรอบนี้; ไม่อ้างว่า command ทุกตัวพร้อมรันแล้ว |
| REST ปัจจุบัน | [REST Projects](https://docs.github.com/en/rest/projects/projects) มี projectsV2 endpoints และระบุ token support ต่างกันระหว่าง user/org endpoints | ไม่กล่าวว่า Projects ใช้ได้เฉพาะ GraphQL; ต้องเลือก endpoint/API version และสิทธิ์ตามเอกสารของ operation จริง |
| Actions credentials | [Automating Projects using Actions](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions) ระบุ repository GITHUB_TOKEN เข้าถึง Projects ไม่ได้ใน flow นี้ และแนะนำ GitHub App/PAT ตาม user/org context | I: สิทธิ์ repository ที่รัน tests ไม่ทำให้เขียน Project ได้อัตโนมัติ; U ของ installed App/token/policies จริง ไม่ได้สร้าง credential ในงานนี้ |
| Events/webhooks | API guide อธิบาย projects_v2_item webhook; Actions example เป็น flow ของ repo ที่ตั้ง workflow | I: Project ข้าม repo ต้องรับ event จาก repos ที่เกี่ยวข้องจริง; webhook ไม่ให้ receipt/dispatch policy/ordering/exactly-once โดยตัวมันเอง |
| การตัดสินที่ใช้ context | Actions guide ชี้ GitHub Agentic Workflows สำหรับงานอย่าง triage/classification/summary | I: เป็น implementation option เพิ่มได้ ไม่จำเป็นต้องใช้เพื่อเริ่ม workflow นี้ และยังไม่ใช่หลักฐานว่า agentic workflow ใดถูกเปิดใช้จริง |

**D-doc:** [Storing workflow data as artifacts](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-what-your-workflow-does/storing-and-sharing-data-from-a-workflow) อธิบาย artifact retention ที่กำหนดได้ **I:** receipt ควรเก็บสรุป AC/run/revision/environment และ pointer ไปหลักฐานที่มี retention เหมาะสม ไม่ฝากความหมายของ DONE ไว้กับ URL ที่อาจหมดอายุเพียงอย่างเดียว

**D-doc:** [Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms) อธิบาย input/validation/defaults ของแบบฟอร์ม **I:** required fields ช่วย intake แต่ไม่ใช่ runtime test หรือ acceptance evaluator จึงคง receipt แยกจากการกรอกแบบฟอร์ม

**ขอบเขต audit — U:** ไม่มีการสร้าง Project/Issue, รัน Actions, เรียก API mutations, ทดสอบ assignment race หรือการเปลี่ยน Done จริงในบัญชีผู้ใช้ในรอบนี้ หลักฐาน platform เป็น documentation/schema inspection; การทดสอบ configuration และ end-to-end automation ต้องเกิดก่อนใช้งานจริง ไม่อ้างผลทดลอง CLI ของ Beads ในเวอร์ชันเดิมเป็นผลทดลอง GitHub

<a id="g5"></a>

## G5 — Mapping จาก tracker เดิมและเกณฑ์ตรวจการย้าย

**I ทั้งส่วน:** เป็นแผนประยุกต์ใช้ ไม่ใช่ผลการ migrate ที่เกิดขึ้นแล้ว แหล่งข้อมูล Beads/local audit ของผู้ใช้คงอยู่ในต้นฉบับเฉพาะเครื่องและไม่ได้เผยแพร่ในคลังนี้ ไม่ได้ถือว่า Project ปลายทางมี fields, issue types, policies หรือ agent integrations เหล่านี้พร้อมแล้ว

| ข้อมูลเดิม | ที่อยู่ใหม่ที่เสนอ | สิ่งที่ต้องทบทวน |
|---|---|---|
| Bead/task ID | `Legacy task:` ใน Issue body หรือ migration mapping | เก็บ stable mapping ป้องกันสร้าง Issue ซ้ำ; GitHub URL/node ID เป็น key ใหม่ |
| Title/description/AC | Repository Issue body หรือ pointer ไป canonical spec | ย้ายความหมายและ AC IDs; คงช่องว่างหลักฐานเป็น unknown ไม่ทำให้ดูเหมือนผ่าน |
| Notes/comments | สรุป handoff ที่ใช้ทำต่อได้ พร้อมลิงก์ประวัติเดิม | แยกผู้เขียน/เวลาเดิมจาก importer และเวลานำเข้า; ไม่สร้างประวัติ GitHub ย้อนหลังปลอม |
| Parent-child | Native sub-issues | รักษา parent outcome; การปิดลูกไม่เท่ากับยืนยัน integrated acceptance |
| Hard prerequisite | Relationships: Blocked by / Blocking | ทิศทางถูกและ prerequisite ส่งมอบ capability ที่ต้องใช้จริง; งานถูกยกเลิกไม่เท่ากับได้ prerequisite |
| discovered-from / related | ข้อความอ้างอิง Issue ต้นทางและเหตุที่พบ | ถ้าจำเป็นต่อ AC เพิ่ม blocking relation แยก; plain reference ไม่ใช่ scheduler edge |
| Assignee / agent name | GitHub assignee ที่ระบบรองรับ + worker/run ID ใน handoff | account identity ไม่เท่ากับ process/session; coordinator ต้องยืนยัน active owner ใหม่ |
| ready/open/in_progress | Project Status ตาม readiness/current assignment ที่ตรวจใหม่ | งาน open อาจยัง Backlog; in_progress เก่าอาจไม่มี active run แล้ว |
| blocked/deferred | dependency/เหตุรอ หรือ Backlog สำหรับงานเลื่อน | แยก “ทำต่อไม่ได้” กับ “ยังไม่เลือกทำ”; status เดิมไม่พิสูจน์ native graph ใหม่ |
| closed/close_reason | Completed เฉพาะผลที่รับแล้ว; Not planned/เหตุปิดอื่นตามจริง หรือเก็บ history เดิม | ไม่แปลง closed ทั้งหมดเป็น Done; scope ของ receipt ต้องตรงผลย่อย/ผลรวม |
| Evidence/test logs | Issue/PR receipt ที่ชี้ run/artifact/spec/revision เดิม | ต้องเข้าถึงได้จากบริบท agent ใหม่; path ในเครื่องหนึ่งอาจยังไม่ใช่หลักฐานที่ remote runner อ่านได้ |

**ลำดับย้ายที่เสนอ:** ยืนยันแหล่งข้อมูลเดิมที่ current และ repo/Project ปลายทาง → เลือก active outcomes กับ prerequisites ที่ยังจำเป็น → สร้าง mapping ของ records ก่อนเชื่อม relations → ตรวจ links/AC/owner/evidence → ทดสอบหนึ่งวงจรรับงาน → เปลี่ยน execution source of truth เป็น GitHub แล้วเลิก dispatch ซ้ำจากระบบเก่าเมื่ออนุมัติการ cutover

**เกณฑ์รับ migration — I:** ทุก active obligation ที่อยู่ใน scope มี Issue หรือเหตุยกเว้น; legacy ID ไม่ซ้ำ; hierarchy/dependency direction ถูก; missing evidence ยังแสดงอยู่; owner/run ที่อ้างเป็นปัจจุบัน; required links อ่านได้; Project workflows ไม่เปลี่ยน Done ก่อน policy; ทดลอง event ซ้ำและ partial update แล้วไม่สร้าง task/run ซ้ำ

**U:** target repository, user/organization Project, plan/policies, fields ที่มีจริง, installed agent apps, runner credentials และความพร้อมนำ artifact เดิมไปใช้ ยังไม่ได้ตรวจในรอบเอกสารนี้ จึงไม่อ้างว่าย้ายเสร็จหรือมี automation ทำงานแล้ว

<a id="coverage"></a>

## คำตอบต่อคำถามวิจัยทั้ง 15 ข้อ

ตารางนี้แยกสิ่งที่เห็นจากข้อเสนอ ไม่ยก workflow ที่เสนอไปใส่ใน timeline ของ repository

| ข้อ / คำถาม | DIRECT EVIDENCE ที่ตอบได้ | REASONABLE INFERENCE สำหรับ model | UNKNOWN ที่ยังเหลือ |
|---|---|---|---|
| 1. งานใหญ่แตกอย่างไร | SkyPilot แปด PR ตาม layers; OpenClaw แทนก้อนใหญ่ด้วยแปดชิ้น; Huf รายงานแบ่ง endpoint modules [E2](#e2), [E6](#e6), [E7](#e7) | แบ่งเมื่อช่วย assignment/review/verification โดยยังมีผู้รับ outcome รวม | original planning session และ task tree ใน private systems |
| 2. แตกตามอะไร | schema/launch/cancel/UI/tests/docs; Cline แยก behavior กับ copy; Goose คงสอง runtime paths ในงานเดียว [E2](#e2), [E4](#e4), [E5](#e5) | contract และผลส่งมอบสำคัญกว่าจำนวนไฟล์; task/PR ไม่จำเป็นต้องหนึ่งต่อหนึ่ง | เกณฑ์ทางการของแต่ละทีมที่ไม่ได้เปิดเผย |
| 3. Dependency/blocked/ready | explicit stacked bases, must-land-together, Ready ใน Goose Project [E2](#e2), [E4](#e4); GitHub รองรับ native dependencies ตาม D-doc แยกใน [G1](#g1) | แยก start dependency กับ delivery dependency | board transitions/ready criteria ที่ agent run ใช้จริงส่วนใหญ่ |
| 4. อะไร parallel ได้ | Huf รายงาน subagents ทำ endpoint modules แยกกัน [E7](#e7) | ต้องมี write/contract boundary, owner และ integrated check | actual concurrency ในเคสใหญ่; stack/หลาย commits ไม่พิสูจน์ agents |
| 5. ใครเป็นเจ้าของ shared contract | Huf ผู้เขียนระบุเก็บ router ส่วนกลางไว้ทำเอง [E7](#e7) | เลือก accountable integration owner และให้ dependents รู้เมื่อ contract เปลี่ยน | role/ACL/ownership protocol ในเคสหลัก |
| 6. Handoff ส่งอะไร | OpenHands ส่งคำขอ sync กับ merged SDK, agent ตอบ commit; summary ระบุ previous-session work [E1](#e1) | package ควรมี artifact/revision/evidence/missing work/decision/next owner | machine payload, prompt/session transport และ context ที่สูญหาย |
| 7. เจอนอก scope ทำอะไร | Dyad เลื่อน read-race API expansionพร้อมเหตุผล; Goose แยก forwarding; Cline ถอน out-of-scope blocker [E3](#e3), [E4](#e4), [E5](#e5) | fix same / follow-up / block / decision ตาม AC และ impact | private follow-up ownership และการปิดปัญหาที่เลื่อนบางข้อ |
| 8. Review กลับเป็นงานอย่างไร | comments → patch/test → request review ซ้ำใน PR เดิมหลายโครงการ [E1](#e1), [E3](#e3), [E4](#e4), [E5](#e5) | material finding ต้องมี disposition; ไม่ต้องสร้าง task ทุก comment | scheduler สร้าง rework task อัตโนมัติหรือไม่ |
| 9. ใหม่หรือ task เดิม | auth/timing ใน scope แก้เดิม; capability ใหม่และ re-land มี PR แยก [E3](#e3), [E4](#e4), [E7](#e7) | ใช้ AC/delivery boundary และเหตุผลการเลื่อนเป็นหลัก | policy สากลหรือ threshold ของแต่ละทีม |
| 10. สถานะมีความหมายจริงว่าอะไร | Goose Ready เป็น Project field; GitHub open/closed/merged events; closed-unmerged/superseded พบจริง [E1](#e1), [E4](#e4), [E6](#e6), [E7](#e7) | แยก progress, evidence, delivery; closed ไม่เท่ากับ accepted เสมอ | complete lifecycle ใน Linear/Basecamp และ mapping ทุกสถานะ |
| 11. Completion criterion คืออะไร | OpenHands visible invocation จบที่ bot approve; PR delivery/doc merge จบคนละเวลา; SkyPilot integrated obligations ยังเหลือ [E1](#e1), [E2](#e2) | กำหนด criterion ตามขอบเขตงานพร้อมผู้รับ | original AC และผู้รับทุกชั้นที่ไม่ได้เปิดเผย |
| 12. DONE หมายถึงอะไร | มีทั้ง reported implementation complete, approvals, merge, docs sync และ post-merge failures | successful closure ต้องตรวจ AC/evidence/review/delivery ตาม mandate ไม่สมมติว่าทุกงานต้อง deploy | ไม่มีหลักฐานว่านิยาม DONE เดียวใช้ข้ามทุกโครงการ |
| 13. ป้องกันปิดเร็วอย่างไร | reviews ทำให้ rework, OpenHands มี unresolved-review-threads check success; OpenClaw ยัง hold [E1](#e1), [E6](#e6) | acceptance predicate + required evidence freshness + scoped child/parent completion | branch protection/agent close permissions ที่บังคับจริงครบทุก repo |
| 14. AC/tests/evidence/review ผูกอย่างไร | issue scope → PR references → test/fix commits → check runs/reviews [E1](#e1), [E4](#e4); platform capability แยกใน [G2](#g2) | เก็บ AC IDs และ completion receipt ที่ชี้ run/review/revision; reuse artifact เดิม | full machine-readable AC coverage ในเคสหลัก และ mapping ใน GitHub Project ปลายทาง |
| 15. หลัง merge reopen หรือ follow-up | Cline มี linked repair/follow-up PRs; Huf re-land ใหม่พร้อมเหตุผล; Dyad failed run แต่ outcome ต่อ U [E3](#e3), [E5](#e5), [E7](#e7) | new repair outcome ใช้ linked task; reopen เมื่องานเดิมถูกปิดผิดตาม policy พร้อมเก็บประวัติ | ไม่พบ policy reopen/follow-up แบบครบวงจรที่ยืนยันได้ทุกทีม |

<a id="limits"></a>

## ข้อจำกัดการเข้าถึงและความหนักแน่นของข้อสรุป

**การคัดเลือก:** ใช้ห้าโครงการหลัก OpenHands, SkyPilot, Dyad, Goose, Cline ที่ contribution ที่เลือกมี disclosure/co-author/invocation เชื่อม AI implementation; OpenClaw พิสูจน์ AI review จึงแยกเป็น comparator; Huf ให้คำรายงาน parallelization ที่ละเอียดแต่เป็น repo เล็ก ห้ามใช้สองกรณีหลังเติมจำนวน “large AI-coded projects” โดยไม่บอกข้อจำกัด

ขนาด/ความ active ใช้ metadata และงานล่าสุดที่มี discussion/rework/checks ประกอบ ไม่ใช่การวัด LOC, contributor diversity หรือสัดส่วน AI commits แบบเป็นระบบ Stars เป็นบริบทความแพร่หลาย ไม่ใช่ขนาดระบบหรือคุณภาพ workflow เคส OpenHands SDK และ Huf จึงถูกกำกับข้อจำกัดไว้ชัดเจน ช่วงหลักเน้นงานปี 2026 และใช้ OpenHands #8252 ปี 2025 เป็น failure comparator ไม่ใช่ตัวแทนรุ่น agent ปัจจุบัน

**สิ่งที่ตรวจจากต้นทาง:** issue/PR bodies, linked issue/PR, commit history/diffs, issue/review comments, reviews, timeline events, repository metadata และ check-run/workflow result เท่าที่ระบุในแต่ละ E ไม่ได้อ่าน raw CI log ทุก job ไม่ได้ตรวจ private branch rules หรือ project metadata ทุก field ตัวเลข checks เป็น snapshot ของ API ที่ระบุ; ชุดที่เป็น partial page เช่น OpenClaw 100 จาก 384 ไม่ถูกนับเป็น coverage ทั้งหมด

**แหล่งที่ไม่เปิดให้ตรวจครบ:**

| แหล่ง | ผลการเข้าถึง / ข้อสรุปที่อนุญาต |
|---|---|
| [OpenHands conversation](https://app.all-hands.dev/conversations/bd587df90af54900bf227e2c27d85b06) ที่ agent reply ลิงก์ | ตรวจลิงก์ได้จาก agent reply แต่เข้าถึง action transcript ไม่ได้ในการตรวจนี้; D ว่ามี session link, U ของ file reads/full prompt/handoff |
| Cline Claude sessions ใน implementation commits [E5](#e5) | ได้ 403 ในการตรวจรอบนี้; D-link ไม่กลายเป็น D-trace |
| SkyPilot Linear SKY-5285 [E2](#e2) | อ่านได้เฉพาะ reference ใน PR; private task tree/AC/assignment เป็น U |
| Dyad Basecamp plan [E3](#e3) | PR รายงานหลาย planned steps แต่ไม่เข้าถึง task board; U ของ dependency และ completion ทุกขั้น |
| OpenClaw external review portal/native stack [E6](#e6) | portal เปิดไม่สำเร็จในการตรวจ; native-stack PR ที่อ้างบางลิงก์คืน 404 จึงไม่ใช้เป็น metadata ที่ตรวจแล้ว |
| Huf GOAL.md/TRACKER.md และ coordinator session [E7](#e7) | มีคำรายงานอ้างถึง แต่ไม่ได้อ่านเอกสาร/trace เหล่านี้; สรุปเฉพาะ report และ GitHub artifacts |

**ข้อสรุปที่หลักฐานรองรับ:** ตาม review → rework → verification report/check → merge/follow-up ได้หลายสายงาน เห็นชัดว่าขอบเขต task ย่อยกับ outcome รวมไม่จำเป็นต้องจบพร้อมกัน และมีความคลาดเคลื่อนระหว่างสถานะ/คำรายงานกับหลักฐานส่งมอบที่ต้องตรวจเพิ่ม

**สิ่งที่ยังสรุปไม่ได้:** รูปแบบ handoff ที่ใช้จริงอย่างครบถ้วนในโครงการใหญ่, scheduler/agent count, สาเหตุของ coordination failure ที่ไม่มี trace, นิยาม DONE สากล, และผลเชิงสาเหตุว่าการใช้ model หรือ GitHub Projects Workflow จะลด human follow-up/manual testing เท่าไร

ดังนั้น GitHub **เพียงพอสำหรับสกัดข้อกำหนดที่ workflow ควรรับมือบางส่วน แต่ไม่เพียงพอสำหรับ reconstruct internal agent orchestration ทั้งวงจร** โมเดลและ GitHub Projects Workflow ในไฟล์บทเรียนจึงเป็นข้อเสนอที่ตรวจย้อนกลับถึงเหตุผลได้ ไม่ใช่การค้นพบว่าโครงการทั้งหมดใช้ระบบเดียวกัน
