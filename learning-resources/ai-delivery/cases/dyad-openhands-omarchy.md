<a id="case-P1"></a>

## P1 — Dyad: deploy สำเร็จยังไม่เท่ากับแอปใช้งานได้

**ระดับหลักฐาน AI: B** · หลักฐานเฉพาะ contribution ที่เปิดเผยหรือมีร่องรอยลงมือ ไม่ยืนยันทุกบรรทัดหรือทุก commit · [ดูหลักฐาน](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717925547)

**เคสหลัก:** [dyad-sh/dyad #4187](https://github.com/dyad-sh/dyad/pull/4187) · เปิด 4 ส.ค. 2026 · merge 14 ส.ค. 2026 18:57 UTC โดย RyanGroch · 71 ไฟล์, 126 commits ในประวัติ PR ที่เรียกดูได้ · 27 conversation comments, 343 inline comments, 235 review submissions (จำนวน submission รวมคำตอบสั้นและ review ว่าง ไม่ใช่ผู้รีวิว 235 คน)

### หลักฐานว่า AI เขียน

ย่อหน้าเปิด PR ระบุว่าคำอธิบายและโค้ดสร้างโดย Claude ส่วนคำตอบ review ในนาม RyanGroch มีข้อความระบุว่า Claude ตอบแทนเจ้าของบัญชี ตัวอย่างชัดเจนคือ [คำตอบเรื่อง Neon Auth](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717925547) จัดเป็นหลักฐานการเปิดเผยโดยผู้ร่วมงานพร้อมเส้นทางแก้จริง ไม่ใช่หลักฐานนิติวิทยาศาสตร์หรือเปอร์เซ็นต์โค้ด AI ทั้งโปรเจกต์

### เขาตั้งเป้าหมายและแบ่งขอบเขตอย่างไร

เป้าหมายคือให้แอปของผู้ใช้ deploy ไปยัง Coolify ที่ผู้ใช้มีอยู่แล้ว แทนที่จะเลือกโฮสต์ได้ทางเดียว ขอบเขตสำคัญที่ PR เขียนไว้เองคือย้ายส่วน compute แต่คงฐานข้อมูลเดิม ฟีเจอร์อยู่หลัง experiment ที่ปิดเป็นค่าเริ่มต้น ผู้ใช้ต้องติดตั้ง Coolify และเตรียม token มาก่อน PR นี้ยังไม่ติดตั้งเซิร์ฟเวอร์ผ่าน SSH ไม่จัดหาฐานข้อมูล และไม่ย้าย schema

นี่คือการแบ่งงานตามผลลัพธ์ที่ส่งมอบได้: ขั้นแรก deploy ไปที่ปลายทางที่พร้อมแล้ว ขั้นถัดไปจึงจัดเตรียมปลายทางเอง อย่างไรก็ตาม PR อ้างแผนใน Basecamp ซึ่งไม่ได้อยู่ในหลักฐานสาธารณะที่ตรวจ จึงไม่สามารถสรุปว่าทีมแจกงานทุกขั้นให้ agent ใด หรือใช้ prompt ต้นฉบับอย่างไร อีกข้อที่ควรเห็นคือผู้เขียนเองบอกว่า PR ใหญ่กว่าที่คาดและเสนอให้แตกเพิ่ม การที่มีขอบเขตระดับ feature ชัด ไม่ได้ทำให้ diff เล็กโดยอัตโนมัติ

เกณฑ์รับงานที่ถอดจาก PR เป็นพฤติกรรมได้ ได้แก่เลือก server/project ได้, deploy จาก repository และ branch ที่เลือก, เห็นความคืบหน้าและ error, แอปที่มีฐานข้อมูลยังใช้ฐานข้อมูลนั้น, callback ของงานที่ยกเลิกไม่เขียนทับงานใหม่ ข้อความเหล่านี้มีอยู่ในเนื้อหา PR แต่ **ไม่ได้พบเอกสาร AC ที่ลงนามก่อนเริ่มงาน** ตารางเกณฑ์ในบทเรียนจึงเป็นการเรียบเรียงย้อนหลังจากข้อกำหนดและ review

### การโต้ตอบที่เปลี่ยนงานจริง

| ลำดับ | ข้อทักท้วงและคำตอบ | สิ่งที่เปลี่ยนและหลักฐาน |
|---|---|---|
| 4–5 ส.ค. | Codex reviewer พบว่ามีเพียง DATABASE_URL จึง build ได้ แต่เส้นทาง login ของ Neon Auth ยังพัง ผู้ตอบยืนยันว่าระหว่างทดสอบพบ HTTP 500 จริง | เปลี่ยนไปใช้ตัวช่วยชุดเดียวกับ Vercel สำหรับ branch/env และ trusted domain; [ข้อทักท้วง](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3709212241), [คำตอบ](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717925547), [commit 43110685](https://github.com/dyad-sh/dyad/commit/43110685df945df319bf0cea53030707f2ffbf26) มีทั้ง implementation และ tests |
| 4–5 ส.ค. | cubic ชี้ว่า test ชื่อเหมือนครอบคลุมทุกสถานะ แต่ assert แค่ running กับ idle ผู้ตอบยอมรับว่าเคยคิดผิดว่าตาราง test ที่อื่นปิดช่องนี้แล้ว | เพิ่ม succeeded/failed และสถานะที่ไม่ running ให้ครบใน selector test; [ข้อทักท้วง](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3709262835), [คำตอบ](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717928781), [commit 83d03f03](https://github.com/dyad-sh/dyad/commit/83d03f03de1fdfb32cf74b6108bd6b83d71a0d5c) |
| 5–6 ส.ค. | cubic พบว่าการ reuse แอป Coolify ไม่อัปเดต repository/branch จึง deploy โค้ดเก่าแต่แสดงผลสำเร็จ ผู้ตอบยอมรับ defect | ส่ง source ปัจจุบันทั้ง create/update และเพิ่ม test ตรวจ request เมื่อเปลี่ยน branch; [ข้อทักท้วง](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717963627), [คำตอบ](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3725731148), [commit 231ab2d7](https://github.com/dyad-sh/dyad/commit/231ab2d7cb493297607b4d4de82da29dd6becf6e) |
| 5–6 ส.ค. | reset ปิดฐานข้อมูลขณะที่ deployment ยังทำงาน เพราะ dispose ไม่ถูก await คำตอบไม่ได้บอกเพียงว่าแก้แล้ว แต่แจกแจงว่าต้องแก้สาม commits | เพิ่มการรอและ fence; พบต่อว่า Promise.allSettled ได้ wrapper objects แทน promises จึงรอเป็นศูนย์; สุดท้ายรวม bookkeeping เพื่อลดสถานะขัดกัน; [ข้อทักท้วง](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717963623), [คำตอบ](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3725733107), [แก้การรอจริงพร้อม test เวลา](https://github.com/dyad-sh/dyad/commit/0f10c2326d132f9d8b54ab4d51774bac65453b64) |
| 5–6 ส.ค. | Claude reviewer เสนอ confirm dialog เพราะ disconnect ล้าง config ของทุกแอป ผู้ตอบเห็นด้วยกับปัญหาแต่เลือกแก้ semantics | เอาการล้างข้อมูลที่ไม่จำเป็นออก รักษาข้อมูลไว้เมื่อ reconnect instance เดิม แล้วเพิ่ม confirmation เฉพาะ disconnect รายแอปที่มีผลลบจริง; [ข้อทักท้วง](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3717997232), [คำตอบ](https://github.com/dyad-sh/dyad/pull/4187#discussion_r3725735279), [commit 6d768325](https://github.com/dyad-sh/dyad/commit/6d768325b57afdfd7da5ebb778baef779a0e7f83) |

คำตอบแบบสุดท้ายสอนเรื่องการรับ review ได้ดี: ตรวจว่าปัญหาจริงหรือไม่ แยกปัญหาออกจากวิธีแก้ที่ reviewer เสนอ แล้วส่งวิธีแก้ที่รักษาเจตนา พร้อมหลักฐาน ไม่ใช่รับทุกคำแนะนำโดยอัตโนมัติ

### เขาพิสูจน์อย่างไร และยังพิสูจน์อะไรไม่ได้

PR อธิบายการทดสอบ pipeline ด้วย routing fetch fake, in-memory database และ injected clock รวมถึง E2E ผ่าน fake Coolify ที่กรอก URL เหมือนผู้ใช้ เส้นทาง branch/env และ state race จึงมี assertion ที่ตรงกับ defect มากกว่าการเช็กว่า function คืนค่าได้ แต่ test fake ยังไม่เท่ากับยืนยันพฤติกรรมของ Coolify จริงทุก version

หลักฐานโค้ดที่ตรวจเพิ่มคือ commit ของการรอ: test เดิมเพียงตรวจว่า disposeAll resolve ได้ ทั้งการรอศูนย์วินาทีและการรอครบเวลาจึงผ่านเหมือนกัน test ใหม่ตรวจว่ายังไม่เสร็จก่อน deadline และเสร็จหลัง deadline นี่เป็นตัวอย่างของการเลือก observable ที่สามารถแยก implementation ผิดออกจากถูกได้

ต้องอ่านผล CI อย่างระมัดระวัง: ใน checks ที่ผูกกับ final head `6e5abff6dad5355c5ebffb7c884ea54a57aacf52` พบ unit-tests-macos และ unit-tests-windows เป็น failure รวมถึง macOS E2E shard 3/4 เป็น failure เสร็จราว 17:13–17:16 UTC **ก่อน** merge 18:57 UTC; [CI run](https://github.com/dyad-sh/dyad/actions/runs/31821951795), [macOS unit job](https://github.com/dyad-sh/dyad/actions/runs/31821951795/job/94837110193), [E2E shard ที่ fail](https://github.com/dyad-sh/dyad/actions/runs/31821951795/job/94837573273) ส่วน [review สุดท้าย](https://github.com/dyad-sh/dyad/pull/4187#issuecomment-5296148330) บอกว่าไม่มี HIGH blocker แต่เปิดเผยว่ามี test patch ถูกตัดทอนใน context

หลัง merge มี [รายงานอีก run](https://github.com/dyad-sh/dyad/pull/4187#issuecomment-5297447563) เวลา 19:42 UTC แจ้ง Windows E2E failures จึงแยกจากหลักฐานก่อน merge และไม่เอาไปย้อนอ้างว่า reviewer เห็นรายงานนี้ก่อนอนุมัติ จากข้อมูลนี้ยืนยันว่า merge เกิดแล้วได้ด้วย [merge commit](https://github.com/dyad-sh/dyad/commit/ba782f433205935979de8a9cc2d606944fe534a1) แต่ยืนยันไม่ได้ว่าทุก test ผ่าน ไม่พบเหตุผลสาธารณะที่เพียงพอจะตัดสินว่าทุกรายการ fail เป็น flaky หรือไม่เกี่ยวข้อง และไม่เห็นนโยบาย branch protection ณ ตอนนั้น

### บทเรียนสำหรับสั่ง AI

เริ่มจากผลที่ผู้ใช้ต้องได้รับ เช่นเลือก development แล้วต้องไม่ deploy กับ production DB แปลงเป็น assertion ที่ดู request จริงและ branch จริง เมื่อตอบ review ให้รายงาน defect → decision → commit → assertion → ผลรันบน SHA หลังแก้ สำหรับ feature ขนาดใหญ่ควรมีจุดทบทวนขอบเขตระหว่างทาง เพราะความละเอียดของ review เพิ่มขึ้นพร้อมขนาด diff และ reviewer เองอาจได้ context ไม่ครบ

<a id="case-P2"></a>

## P2 — OpenHands: AI บอกว่าจบ แต่คนยังต้องเจาะจงงานและตรวจ benchmark

**ระดับหลักฐาน AI: A** · หลักฐานเฉพาะ contribution ที่เปิดเผยหรือมีร่องรอยลงมือ ไม่ยืนยันทุกบรรทัดหรือทุก commit · [ดูหลักฐาน](https://github.com/OpenHands/OpenHands/issues/8304#issuecomment-2855275930)

**เคส:** [issue #8304](https://github.com/OpenHands/OpenHands/issues/8304) → [PR #8310](https://github.com/OpenHands/OpenHands/pull/8310) · เปิด 6 พ.ค. 2025 · merge 17 พ.ค. 2025 04:37 UTC โดย enyst · 8 ไฟล์, 27 commits, 39 conversation comments, 14 inline comments, 15 review submissions · โปรเจกต์เกิด มี.ค. 2024 จึงเป็นกรณีเปรียบเทียบที่เกินช่วงอายุสองปี

### จากปัญหาที่เล่ามา สู่ปัญหาที่ต้องแก้จริง

issue เริ่มจากความต้องการปิด microagents และหน้าจอที่ยังแสดงข้อมูล หลังผู้ดูแลช่วยแก้ชื่อ environment variable [ผู้แจ้งยืนยันว่า AGENT_ENABLE_EDITOR=false ปิด editor ได้](https://github.com/OpenHands/OpenHands/issues/8304#issuecomment-2855217978) แต่กลับพบ converter ล้มเมื่อใช้โมเดลที่ไม่มี native function calling ดังนั้นอ่านเพียงชื่อ issue หรือย่อหน้าแรกจะได้โจทย์ผิด [การรายงาน failure หลังปิด editor](https://github.com/OpenHands/OpenHands/issues/8304#issuecomment-2855257850) และ [การจำกัดเงื่อนไขบั๊กโดย enyst](https://github.com/OpenHands/OpenHands/issues/8304#issuecomment-2855377063) ทำให้ขอบเขตชัดว่าเป็นชุด tool ที่ปรับได้กับ in-context examples ที่ยังแข็งตัว

พบคำสั่งถึง agent โดยตรง [enyst เรียก openhands-agent](https://github.com/OpenHands/OpenHands/issues/8304#issuecomment-2855275930) ให้ปรับตัวตรวจ compatibility และมี [การตอบรับเริ่มทำพร้อม run](https://github.com/OpenHands/OpenHands/issues/8304#issuecomment-2855276458) จากนั้น PR ถูกสร้างโดย openhands-agent และมีชุด commit จากการแก้ตาม feedback นี่เป็นหลักฐานการปฏิบัติงานของ agent ที่แรงกว่าการมีไฟล์ AGENTS.md แต่ยังมีมนุษย์แก้บางส่วนใน PR ด้วย

### งานย่อยค่อย ๆ ชัดจาก review

ผลที่ต้องการคือเมื่อปิด tool บางตัว converter ยังทำงานและตัวอย่างยังสอดคล้องกับ tool ที่เปิดอยู่ การแยก TOOL_EXAMPLES และประกอบเฉพาะส่วนที่มีจึงเป็นแนวทางที่ปรากฏใน patch/review ไม่ใช่ task list ที่เปิดเผยครบก่อนเริ่มงาน ผู้แจ้งได้ [ลอง image ของ commit e26ca14 และรายงานว่าใช้ได้](https://github.com/OpenHands/OpenHands/issues/8304#issuecomment-2859398773) ทำให้มี feedback จากเส้นทางใช้งานจริงเพิ่มจาก unit tests

| เวลา | การพูดคุย | สิ่งที่เรียนได้ |
|---|---|---|
| 12 พ.ค. | xingyaoww ทักว่าต้องคง finish example; enyst ส่งคำสั่งใหม่โดยระบุ TOOL_EXAMPLES และให้ประกอบเมื่อ finish เปิดอยู่ | [คำสั่งงานที่เจาะจง](https://github.com/OpenHands/OpenHands/pull/8310#discussion_r2083672095) ระบุทั้งตำแหน่ง รูปแบบที่ต้องรักษา และเงื่อนไขการทำงาน |
| 12 พ.ค. | [xingyaoww เสนอ .replace](https://github.com/OpenHands/OpenHands/pull/8310#discussion_r2083661449) แทน regex; agent กลับใช้ startswith/find/slicing แล้วตีความว่าตรงเจตนา | [คำตอบ agent](https://github.com/OpenHands/OpenHands/pull/8310#discussion_r2083672241) เป็นคำอธิบายความสำเร็จของ agent ไม่ใช่ผลรับงานโดยผู้ดูแล |
| 12 พ.ค. | enyst ยังต้องกลับมาบอกว่าไม่ตรงและชี้บรรทัด 661–668 | [คำสั่งแก้ซ้ำ](https://github.com/OpenHands/OpenHands/pull/8310#discussion_r2083685712) แสดงความจำเป็นของ target ที่ตรวจได้; commit ต่อมาใน PR มีชื่อ use .replace และ fix tests, add |
| 12–15 พ.ค. | reviewer ขอรัน Qwen 3 eval แทนเชื่อว่า refactor ไม่น่าเปลี่ยน behavior; ผู้ทำถามจำนวน instances, iterative mode และ editor setting | [คำขอ eval](https://github.com/OpenHands/OpenHands/pull/8310#pullrequestreview-2833830914), [คำถามเรื่องชุดทดสอบ](https://github.com/OpenHands/OpenHands/pull/8310#issuecomment-2874363398) ทำให้รู้ว่า benchmark ต้องบอก config ไม่ใช่มีแค่เปอร์เซ็นต์ |
| 15 พ.ค. | enyst รายงาน 169/487 = 34.70% และระบุ interruption/จำนวนไม่ครบ | [รายงานพร้อมข้อจำกัด](https://github.com/OpenHands/OpenHands/pull/8310#issuecomment-2884584530) ดีกว่ารายงานว่าเทสผ่านโดยซ่อน denominator |
| 17 พ.ค. | xingyaoww โหลดข้อมูลมาประเมินใหม่ด้วย local Docker และได้ 180/500 = 36% เทียบ baseline ที่รายงานไว้ 36.2%; ยังขอแก้ merge conflict ก่อน | [review อนุมัติแบบมีเงื่อนไข](https://github.com/OpenHands/OpenHands/pull/8310#pullrequestreview-2847914134) แสดงว่าหลักฐานประเมินและสถานะ mergeability เป็นคนละเรื่อง |
| 17 พ.ค. | มีการแก้ conflict, cleanup และ tests ก่อน [approval สุดท้าย](https://github.com/OpenHands/OpenHands/pull/8310#pullrequestreview-2847958918) แล้ว [merge](https://github.com/OpenHands/OpenHands/commit/c17b0ebfc6195fd37bea999abbc629da4335c0ad) | การขยับ branch หลัง review ต้องถูกนับเป็นส่วนหนึ่งของงาน ไม่ใช่จบที่คำว่า approved |

### ระดับหลักฐานและข้อจำกัด

มีการเปิดเผย agent invocation, draft PR, feedback loop, human changes, author-reported unit tests, การลอง image โดยผู้แจ้ง และผู้ดูแลประเมินผลซ้ำ อย่างไรก็ตามตัวเลข eval เป็นสิ่งที่ผู้ร่วมงานรายงานใน GitHub ไม่ใช่ผลที่ชุดบทเรียนนี้รันขึ้นใหม่ ผล 36% ใกล้ baseline เป็นดุลยพินิจของ reviewer ในเคสนี้ **ไม่ได้พิสูจน์ทางสถิติว่าไม่ถดถอย** และตัวเลข 169/487 กับ 180/500 ใช้การประเมินต่างกัน จึงไม่ควรเอามาลบกันแล้วบอกว่าคุณภาพเพิ่มกี่เปอร์เซ็นต์จาก patch

ณ snapshot ไม่พบ check-runs บน final head `bb767e8a18…` จาก endpoint ที่ตรวจ และ legacy status ไม่ได้ให้ผลรันครบ การไม่พบข้อมูลไม่เท่ากับไม่เคยรัน CI จึงสรุปเพียงว่ามี review/ผลทดลองที่รายงานและ merge event ส่วน CI ครบทุก job ย้อนหลังยังยืนยันไม่ได้

### บทเรียนสำหรับสั่ง AI

ก่อนออก task brief ให้แยกอาการตอนเปิด issue ออกจาก reproduction ล่าสุด ระบุ input/config ที่ทำให้ fail เมื่อ reviewer ทัก ให้ส่งข้อความที่มีตำแหน่งและเกณฑ์จบ ไม่ฝากไว้กับคำว่าแก้ตามคอมเมนต์ทั้งหมด ถ้าการเปลี่ยนกระทบพฤติกรรมโมเดล ให้แนบ eval configuration, denominator, baseline, error/missing cases และแยกผู้สร้าง patch จากผู้ตีความผล

<a id="case-P3"></a>

## P3 — Omarchy: จากขอบเขตแคบ สู่บั๊กหลัง merge และการพิสูจน์บนเครื่องจริง

**ระดับหลักฐาน AI: B** · หลักฐานเฉพาะ contribution ที่เปิดเผยหรือมีร่องรอยลงมือ ไม่ยืนยันทุกบรรทัดหรือทุก commit · [ดูหลักฐาน](https://github.com/omacom/omarchy/pull/6388)

**เส้นเรื่อง:** [issue #5423](https://github.com/omacom/omarchy/issues/5423) → [PR #5435](https://github.com/omacom/omarchy/pull/5435) → [PR #6093](https://github.com/omacom/omarchy/pull/6093) → [PR #6388](https://github.com/omacom/omarchy/pull/6388) · เม.ย.–ส.ค. 2026 · repo เกิด 1 มิ.ย. 2025 · สถานะ ณ 13 ก.ย. 2026: #5435 merged, #6093 closed โดยถูกแทนที่, #6388 ยัง open

### หลักฐานการใช้ AI และการตัดขอบเขตก่อนลงมือ

ผู้แจ้ง mijuny ระบุใน issue ว่าวิเคราะห์และผลิต fix ด้วย Claude Code พร้อมเครื่อง รุ่น BIOS/kernel และตารางทดลองลด kernel flags ทีละชุดเพื่อหาตัวแก้ขั้นต่ำ ตัวเลขและการวิเคราะห์ hardware เป็นรายงานจากผู้แจ้ง ไม่ใช่ผลที่เราวัดบนเครื่องนั้นเอง [issue ต้นทาง](https://github.com/omacom/omarchy/issues/5423)

ผู้แจ้งเสนอทางเลือกแคบเฉพาะ ExpertBook กับทางเลือกกว้างทุก ASUS Panther Lake; [dhh ยืนยันให้ทำแต่จำกัดเฉพาะ ExpertBook](https://github.com/omacom/omarchy/issues/5423#issuecomment-4313024503) การตัดสินใจก่อนเขียนนี้มีเหตุผลชัด: ยังไม่มีหลักฐานว่าเครื่องรุ่นอื่นต้องรับ workaround เดียวกัน PR #5435 จึงตรวจชื่อ B9406 ร่วมกับ Intel Panther Lake และรวม display, brightness, touchpad ส่วน live ISO เป็น PR คนละ repository ที่ผู้เขียนระบุว่าจะตามมา

นี่เป็นหลักฐานการแบ่ง scope ที่เกิดจริงก่อน PR ซึ่งต่างจากการถอด AC ย้อนหลัง เกณฑ์เชิงพฤติกรรมที่สังเคราะห์ได้คือเครื่องเป้าหมายกลับมาใช้งานได้ และเครื่องไม่ตรง matcher ไม่ได้รับ config นี้ แต่รายการ AC ฉบับมาตรฐานในบทเรียนเป็นสิ่งที่เราเรียบเรียง ไม่ได้อ้างว่าทีมเขียนตารางแบบนั้นไว้

### Review ไม่ได้มีหน้าที่แค่หาข้อผิดพลาดในโค้ด

ช่วงแรก Copilot ทัก migration เรื่อง boot config, การ source หลายไฟล์ และ pipeline ที่ซ่อน error ผู้เขียนแก้และ force-push พร้อมขอ [review บน commit ล่าสุด](https://github.com/omacom/omarchy/pull/5435#issuecomment-4314480436) จึงต้องระวังไม่เอาคอมเมนต์ของ commit ที่ถูกทิ้งไปตัดสิน final diff

ต่อมา dhh ถามคำถามระดับผลิตภัณฑ์: [จำเป็นต้องมี migration นี้จริงหรือไม่](https://github.com/omacom/omarchy/pull/5435#discussion_r3142496458) ถ้าคนแทบติดตั้งบนเครื่องนี้ไม่ได้ตั้งแต่แรก ผู้เขียนตอบว่าจริงและเอา migration ออก [คำตอบ](https://github.com/omacom/omarchy/pull/5435#discussion_r3143669287), [commit ที่ตัดออกพร้อม Claude co-author](https://github.com/omacom/omarchy/commit/e28d4955caac33ecda8bf8b50f8d0c1c90325762) ผลลัพธ์จึงเหลือ 4 ไฟล์ เพิ่ม 51 บรรทัด และ merge โดย dhh วันที่ 26 เม.ย. 2026 16:31 UTC [merge commit](https://github.com/omacom/omarchy/commit/b164549b51d790d42a725baa21fc86a34111b00f)

ก่อน merge Copilot ยังทักว่าทางที่เขียนไฟล์ quirks ไม่ตรงกับ issue ผู้เขียน [ปรับเอกสารให้ตรง implementation](https://github.com/omacom/omarchy/pull/5435#discussion_r3143720285) เหตุผลคืออยากแยกไฟล์ของโปรเจกต์ออกจาก local overrides แต่การทำเอกสารกับโค้ดให้ตรงกันยังไม่พิสูจน์ว่า libinput จะอ่านไฟล์นั้นจริง นี่คือจุดหักมุมของเคส

### หลัง merge: สิ่งที่ manual test มองไม่เห็น

3 มิ.ย. ผู้ใช้ simon-scarlet รายงานว่าลงใหม่แล้ว touchpad ยังไม่ขยับ และต้องย้ายไฟล์ไปอีกตำแหน่ง [รายงานหลัง merge](https://github.com/omacom/omarchy/pull/5435#issuecomment-4616309590) ผู้เขียนเปิด #6093 และอธิบายว่าตัวแก้เดิมเคยทดสอบเป็น manual edit แต่ไม่ได้ทดสอบ packaged install path จึงไม่พบว่าไฟล์ที่สคริปต์ติดตั้งสร้างนั้นไม่ถูกอ่าน [PR #6093](https://github.com/omacom/omarchy/pull/6093)

#6093 ระบุสองสาเหตุ คือ path และ MatchUdevType พร้อม Claude disclosure แต่การยืนยันของผู้รายงานเปลี่ยนสองอย่างพร้อมกัน ต่อมา dhh จึงไม่รับทั้งสองสาเหตุด้วยความมั่นใจเท่ากัน ใน [คำอธิบายเมื่อแทนที่ PR](https://github.com/omacom/omarchy/pull/6093#issuecomment-5086374297) เขายืนยันเรื่อง path ผ่านการตรวจเอง และย้ายไป #6388 ที่ target quattro พร้อมปรับวิธีติดตั้งและ migration ให้เข้ากับ branch ใหม่ #6093 **ปิดโดยไม่ merge**; ค่า merge_commit_sha ใน API ของ PR ที่ยังไม่ merge ไม่ควรถูกใช้เป็นหลักฐานว่า merged

### หลักฐานที่ดีขึ้นในรอบแก้

[PR #6388](https://github.com/omacom/omarchy/pull/6388) ระบุการสร้าง probe กับ libinput ที่ติดตั้งจริง โดยจงใจใส่ malformed .quirks file ใน data directory แล้วเห็น parser fail วิธีนี้ตรวจว่าตัวระบบอ่าน directory จริง ไม่เพียงตรวจว่าไฟล์ถูกสร้าง หลังจากนั้นทดสอบ rerun แล้วไฟล์เหมือนเดิม, migration แบบ stubbed sudo, non-matching hardware ไม่เขียน และ shell checks แต่ยอมรับว่ายังไม่ได้ทดสอบบนเครื่องเป้าหมาย

[dhh ขอให้รอ hardware test](https://github.com/omacom/omarchy/pull/6388#issuecomment-5086383113) และระบุรายการที่ต้องดูเกินคำว่าเคอร์เซอร์ขยับ ได้แก่ไฟล์ถูกวางที่ไหน libinput อ่านค่าใด event node ถูก tag อย่างไร และ gestures ทำงานหรือไม่ นี่เป็น acceptance criteria ที่เกิดในคอมเมนต์อย่างชัดเจน

17 ส.ค. argrig666 [ทดลองสคริปต์ของ PR บน B9406 จริง](https://github.com/omacom/omarchy/pull/6388#issuecomment-5321029803) ใช้ data-dir ที่ไม่พึ่งไฟล์ local overrides เดิม ยืนยันค่าที่ libinput โหลดและการขยับเคอร์เซอร์ พร้อมแก้ข้อเท็จจริงว่าเครื่องตนถูก tag เป็น touchpad อยู่แล้ว ดังนั้นหลักฐานสนับสนุน path fix แต่ไม่สนับสนุนคำกล่าวเดิมว่าทุกเครื่องผิดเพราะ ID_INPUT_MOUSE

หลัง reboot ผู้ทดสอบ [รายงานว่าดีขึ้นแต่แยก causality ไม่ได้](https://github.com/omacom/omarchy/pull/6388#issuecomment-5321855391) เพราะ BIOS เปลี่ยนพร้อมการตั้งค่าอื่น ความซื่อสัตย์แบบนี้ควรเก็บไว้ในบทเรียน ไม่ตัดออกเพื่อให้เรื่องดูจบสวย ณ snapshot #6388 ยัง open แม้มี hardware confirmation แล้ว จึงรายงานว่า “มีหลักฐานยืนยันเพิ่มเติมแต่ยังไม่ merge” ไม่แต่งตอนจบแทน maintainer

### บทเรียนสำหรับสั่ง AI

งานที่ส่งคือ installer ต้องทดสอบ installer; งานที่ส่งคือ migration ต้องทดสอบจากสถานะเก่าจริงหรือ fixture ที่แทนมันได้ อย่ารับ manual workaround เป็นหลักฐานแทน artifact ที่จะ merge เพิ่ม negative case ว่าเครื่องนอกขอบเขตไม่เปลี่ยน เมื่อเปลี่ยนหลายตัวแปรพร้อมกันให้แยกสิ่งที่ยืนยันได้กับสมมติฐาน และให้ review มีสิทธิ์ลด scope ที่ไม่จำเป็นแทนการซ่อมความซับซ้อนนั้นต่อไป
