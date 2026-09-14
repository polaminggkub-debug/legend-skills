<a id="case-O1"></a>

## O1 — OpenCode #44281: human author + Claude trailer + AI review ที่ตอบกลับด้วย follow-up commit

**ระดับหลักฐาน AI: B** · หลักฐานเฉพาะ contribution ที่เปิดเผยหรือมีร่องรอยลงมือ ไม่ยืนยันทุกบรรทัดหรือทุก commit · [ดูหลักฐาน](https://github.com/anomalyco/opencode/commit/29dec99e6784f9277be14074b1f0c2b527c31126)

PR: [fix(provider): send Anthropic's dashed native slug through the AI Gateway](https://github.com/anomalyco/opencode/pull/44281) เป็นเคสหลักฐาน AI ร่วมเขียนที่ชัดที่สุดในชุดนี้ เพราะ PR author คือมนุษย์ superhighfives แต่ commit [29dec99e](https://github.com/anomalyco/opencode/commit/29dec99e6784f9277be14074b1f0c2b527c31126) มีข้อความ Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com> และ follow-up [70ae4617](https://github.com/anomalyco/opencode/commit/70ae4617a2edbe94c0e5450a019cf39aeaf58708) มี Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com> นี่เป็น direct disclosure ของ AI coauthor ระดับ commit ไม่ใช่การอนุมานจากสไตล์

ต้นทางคือ issue [#44280](https://github.com/anomalyco/opencode/issues/44280) ที่มี version, environment, credentials ที่ต้องใช้, reproduction command และ error 404 ครบ issue bot ชี้ว่าซ้ำกับ #44252 แล้วผู้เปิดยืนยันและปิด duplicate ในคอมเมนต์ ([bot comment](https://github.com/anomalyco/opencode/issues/44280#issuecomment-5383411729), [author reply](https://github.com/anomalyco/opencode/issues/44280#issuecomment-5399182214)) PR จึงกำหนด scope แคบ: แปลง dots เป็น dashes เฉพาะ Anthropic native passthrough, ปล่อย OpenAI dotted slug และ unified route เดิม, เพิ่ม wire-level regression test และยืนยัน live completion

การแบ่งงานมี production loader กับ e2e harness ใน 2 ไฟล์ และ 3 commits: implementation [29dec99e](https://github.com/anomalyco/opencode/commit/29dec99e6784f9277be14074b1f0c2b527c31126), documentation/safety invariant [70ae4617](https://github.com/anomalyco/opencode/commit/70ae4617a2edbe94c0e5450a019cf39aeaf58708) และ branch merge [7183a791](https://github.com/anomalyco/opencode/commit/7183a7915464727578e3a7a459e0313d3e4f051c) ก่อน merge โดย rekram1-node วันที่ 24 สิงหาคมไปที่ [f8b4dd70](https://github.com/anomalyco/opencode/commit/f8b4dd70ac26996436e259fc386917944c05f481)

จุดเด่นคือมี review feedback ที่เห็นลำดับ comment-response-change จริง:

- Enough1122 ระบุชัดว่าเป็น automated “AI code review” และชี้สามประเด็น: อย่าทำ translation helper ซ้ำระหว่าง production กับ test, บันทึก invariant ว่า native Anthropic slug ไม่มี dot, และ sanity-check branch อื่น ([review comment](https://github.com/anomalyco/opencode/pull/44281#issuecomment-5384523212))
- ผู้เขียนตอบว่าผ่านข้อเสนอให้ AI แก้ต่อ แล้วเพิ่ม invariant ใน commit [70ae4617](https://github.com/anomalyco/opencode/commit/70ae4617a2edbe94c0e5450a019cf39aeaf58708) แต่ตั้งใจไม่ extract helper เพราะ test harness ต้องเป็น independent routing mirror และ assertion ใช้ literal claude-haiku-4-5 เพื่อจับ production/test drift ([response](https://github.com/anomalyco/opencode/pull/44281#issuecomment-5390195804))
- นี่เป็นตัวอย่างที่ดีของการรับ review แบบมีเหตุผล: แก้ suggestion ที่เพิ่มความปลอดภัย แต่ปฏิเสธ suggestion ที่ทำให้ test oracle ผูกกับ production implementation มากเกินไป

ผู้เขียนรายงาน live gateway ว่า dotted Anthropic id เปลี่ยนจาก 404 เป็น normal completion, OpenAI/Workers AI ไม่ได้รับผลกระทบ, regression test แดงก่อนแก้และเขียวหลังแก้; package suite ผ่านโดยมี unrelated pre-existing flake หนึ่งรายการและ tsgo --noEmit สะอาด ส่วนหลักฐานจาก GitHub API ที่ตรวจได้คือ head มี check-runs สำเร็จ 8 รายการ ได้แก่ unit/e2e Linux/Windows, typecheck, nix-eval, standards และ compliance ใน [Actions run 32744944205](https://github.com/anomalyco/opencode/actions/runs/32744944205) และ [run 32744944379](https://github.com/anomalyco/opencode/actions/runs/32744944379) live gateway และ local test count ยังเป็น claim ของ PR ต้องไม่เรียกว่า CI evidence โดยตรง

ข้อจำกัดคือ reviewer ที่ระบุว่า AI ไม่ใช่หลักฐานว่า implementation ทั้งหมดมาจาก AI และ PR นี้ไม่มี inline review comment มีเพียง issue/PR conversation สองชุด อีกทั้ง live verification ขึ้นกับ gateway ภายนอกและการ sanity pass branch อื่นไม่ได้เทียบเท่า test matrix ครบทุก provider

บทเรียนสำหรับการสั่ง AI คือให้กำหนด test oracle ที่เป็นอิสระ, ระบุ invariants ที่เหตุผลของการแปลงข้อมูลพึ่งพา และให้ agent ตอบ review ทีละข้อโดยเลือกได้ว่าจะรับหรือปฏิเสธพร้อมเหตุผล กรณีนี้ทำให้เห็นว่า “AI มีส่วนเขียน” กับ “AI review ถูกทุกข้อ” เป็นคนละคำถาม และคุณภาพเกิดจากการรักษา boundary ระหว่างสองอย่างนี้

