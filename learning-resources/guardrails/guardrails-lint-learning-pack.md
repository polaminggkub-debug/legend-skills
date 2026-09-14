# Guardrail และ lint สำหรับ solo developer ที่ใช้ AI เขียนโค้ด

เอกสารนี้เป็นชุดข้อมูลสำหรับให้ ChatGPT สอนต่อ มีทั้งหลักคิด ตัวอย่างจากโปรเจกต์ใหญ่ และวิธีเปลี่ยนข้อกำหนดของตนให้เป็นการตรวจที่ fail ได้ ใช้คำว่า **guardrail** หมายถึงกลไกคุมการเปลี่ยนโค้ด ส่วน **lint** เป็นเครื่องมือชนิดหนึ่งในกลไกนั้น โฟกัสการตรวจโค้ดและการบังคับรับงานของ repository

**เลือกอ่าน:** [เริ่มให้ ChatGPT สอน](#tutor-start) · [ชุดเริ่มต้นสำหรับ solo](#priorities) · [ออกแบบกฎ](#rule-design) · [ตัวอย่างที่รันแล้ว](#tested-examples) · [CI และ merge gate](#ci-enforcement) · [แผนการเรียน](#learning-path) · [12 โปรเจกต์ / 44 รายการ](#repo-evidence)

<a id="tutor-start"></a>

## วิธีใช้กับ ChatGPT

แนบไฟล์นี้ทั้งไฟล์ แล้วส่งข้อความต่อไปนี้:

> ใช้เอกสารนี้เป็นฐานข้อมูลสอนผมเรื่อง guardrail และ lint สำหรับ solo developer ที่ใช้ AI เขียนโค้ด เป้าหมายคือเปลี่ยนคำสั่งสำคัญให้เป็นการตรวจที่ทำให้โค้ดผิด fail ได้ เริ่มจากถาม stack และตัวอย่างหนึ่งเรื่องที่ AI เคยทำผิด แล้วเลือกสอนทีละแนวคิดด้วยโค้ดสั้น ๆ ให้ผมทำนายว่ากฎใดจะตรวจพบ รอคำตอบก่อนเฉลย และให้ผมลองเขียนข้อกำหนดเป็นกฎของตัวเอง ใช้หลักฐานในส่วนโปรเจกต์จริงและบอกข้อจำกัดของกฎ จบแต่ละช่วงเมื่อผมอธิบายเหตุผลและสร้างตัวอย่างผิด/ถูกได้ ไม่ต้องพาผมอ่านเอกสารทั้งหมดตามลำดับ

ส่วน 1–4 เป็นทางเข้า ส่วน 5 เป็นตัวอย่างทดลอง ส่วน 6–8 เป็นแนวทางใช้งานและหลักสูตร ส่วน “หลักฐานจากโปรเจกต์จริง” เป็นคลังที่ครูเลือกเปิดตามเรื่องที่กำลังสอน ไฟล์เดียวนี้เพียงพอสำหรับเริ่มเรียน ส่วน [guardrail-lab/](./guardrail-lab/) ใช้เมื่อต้องการรันตัวอย่างเอง โฟลเดอร์นี้เป็น lab ที่แตกไฟล์ไว้แล้ว จึงไม่เก็บ ZIP ซ้ำในคลังการเรียนรู้

### ข้อตกลงสำหรับ AI ผู้สอน

1. ยึดเป้าหมายการตรวจโค้ดตามข้อกำหนด เลือกหนึ่งปัญหาจากงานของผู้เรียนต่อช่วง จบขั้นเลือกเมื่อระบุความเสียหายและพฤติกรรมที่ต้องการได้
2. ประเมินความรู้จากคำตอบหรือโค้ดที่ผู้เรียนทำ ใช้ตัวอย่างหนึ่งคู่ก่อนเพิ่มศัพท์ จบขั้นอธิบายเมื่อผู้เรียนทำนายผลพร้อมเหตุผลได้
3. เมื่อต้องการข้อเท็จจริงของ repo ให้เปิดการ์ดโปรเจกต์นั้นและลิงก์ commit ที่แนบ แยกสิ่งที่พบใน source ออกจากคำแนะนำการย่อมาใช้ ถ้าถามสถานะปัจจุบันให้ตรวจแหล่งต้นทางใหม่
4. เมื่อต้องการลงมือ ใช้ตัวอย่างในส่วน 5 หรือ lab ให้ผู้เรียนระบุ **ขอบเขต → ตัวอย่างผิด → diagnostic → ตัวอย่างแก้** จบขั้นลงมือเมื่อมีหลักฐานของทั้ง fail และ pass ถ้าไม่มีเครื่องมือรัน ให้ระบุว่าเป็นการคาดการณ์
5. เมื่อต้องเลือกใช้จริง ให้ประเมินความผิดที่เจอบ่อย ความเสียหาย ความแม่น และต้นทุนดูแล เลือกเริ่มไม่เกินสามกฎใหม่ พร้อมอธิบายเหตุผลที่เหมาะกับ stack
6. หลังผู้เรียนตอบได้ ให้บันทึกสิ่งที่แสดงความเข้าใจและโจทย์ทบทวนครั้งถัดไป การอ่านผ่านหรือเห็นเฉลยยังไม่ใช่หลักฐานว่าเรียนรู้แล้ว

<a id="core-idea"></a>

## 1. ประเด็นที่สำคัญที่สุด

**สิ่งที่ต้องเรียนให้เป็นคือการแปลง “อยากให้ AI ทำอย่างไร” เป็น “อะไรคือหลักฐานที่เครื่องตรวจได้ว่าเปลี่ยนผิด”** จำนวน rule ไม่ใช่ตัวชี้วัดที่ดี กฎสั้นที่จับความผิดซ้ำของโปรเจกต์ได้ มีประโยชน์กว่ารายการ lint หลายร้อยข้อที่ไม่มีใครเข้าใจ

ตัวอย่างเชิงออกแบบ: “UI ต้องเข้าฐานข้อมูลผ่าน service” แปลงเป็นข้อห้าม dependency ข้ามชั้น; “ต้องจัดการ async ให้ครบ” แปลงบางส่วนเป็น typed lint; “ผู้ใช้ต้องอ่านได้เฉพาะ order ของ tenant ตน” ต้องมี test ที่เรียกช่องทางจริงด้วย tenant อื่น การเลือกระดับตรวจเป็นข้อเสนอเชิงวิศวกรรมของเอกสารนี้ ไม่ใช่ข้อพิสูจน์ว่าทุก repo ใช้สถาปัตยกรรมเดียวกัน

```text
ข้อกำหนดที่ชัด → ตัวตรวจที่มองเห็นความผิดนั้น → คำสั่งที่คืน non-zero
            → CI เรียกคำสั่งกับโค้ดที่จะรับ → required check บล็อกการรับงาน
```

GitHub กำหนดให้ required status checks ผ่านก่อน merge เมื่อเปิดใช้กฎนั้น การมี workflow อยู่ใน repository จึงเป็นหลักฐานคนละระดับกับการตั้ง required checks และสิทธิ์ bypass เป็นส่วนหนึ่งของนโยบายบังคับใช้ [GitHub: available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets), [GitHub: creating rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)

ความหมายที่ทำได้จริงของ “เขียนผิดแล้ว fail เลย” คือ **ผิดเงื่อนไขที่กำหนด ในไฟล์และเส้นทางที่ตรวจ ภายใต้ตัวตรวจและ config ชุดนั้น แล้ว fail ก่อนจุดรับงาน** ไม่มีชุด lint ที่พิสูจน์ว่าตรงเจตนาทางธุรกิจทุกด้านได้ ตัวอย่างในส่วน 5 แสดงความผิดข้าม tenant ที่ต้องใช้ assertion เพิ่ม

<a id="glossary"></a>

## 2. คำศัพท์และระดับของ guardrail

| คำ | ความหมายในเอกสารนี้ | ตัวอย่าง | สิ่งที่ยังไม่ตอบ |
|---|---|---|---|
| Instruction | ข้อตกลงที่คนหรือ AI อ่าน | เอกสารบอกให้ผ่าน service | ตรวจพบการฝ่าฝืนหรือไม่ |
| Formatter | จัดรูปแบบโค้ดตามกติกา | Ruff format, Prettier, rustfmt | ผลทางธุรกิจถูกหรือไม่ |
| Lint / static analysis | ตรวจรูปแบบหรือความสัมพันธ์จากโค้ดโดยไม่รัน flow แอปนั้น | restricted import, unused variable | input จริงทุกแบบทำงานหรือไม่ |
| Type checker | ตรวจความสอดคล้องของชนิดตามแบบจำลองที่ประกาศ | TypeScript strict, mypy | ข้อมูลภายนอกตรงชนิดที่อ้างหรือไม่ |
| Architecture check | ตรวจ dependency และขอบเขต module | UI → DB เป็นเส้นทางต้องห้าม | function ใน service ทำงานถูกหรือไม่ |
| Test / contract test | รันกรณีที่กำหนดแล้วตรวจผลที่ต้องเป็น | tenant อื่นได้ผลปฏิเสธ | กรณีที่ไม่ได้ครอบคลุม |
| Generated drift check | สร้าง output ใหม่จาก source แล้วเทียบกับไฟล์ที่ commit | schema เปลี่ยนแต่ client เก่า | generator ถูกต้องเชิงความหมายหรือไม่ |
| Enforcement / gate | จุดที่รับหรือปฏิเสธงานจากผลการตรวจ | CI + required check | คนที่มีอำนาจแก้หรือ bypass gate |
| Diagnostic | ผลตรวจที่บอกตำแหน่ง เหตุผล และทางแก้ | import นี้ต้องผ่าน application service | การแก้แบบที่เลือกตรง requirement หรือไม่ |
| False positive | เตือนกรณีที่ทีมอนุญาต | integration layer ถูกห้าม import ด้วย glob กว้างไป | ต้องจำกัด scope หรือทำ exception |
| False negative | ความผิดหลุดจากการตรวจ | dynamic import ที่ static rule ไม่ตรวจ | ต้องเพิ่มกลไกหรือยอมรับขอบเขต |
| Suppression | ข้อยกเว้นที่ปิด diagnostic | eslint-disable, noqa, allow | เหตุผลของข้อยกเว้นยังใช้ได้หรือไม่ |
| Ratchet | จำกัดหนี้เดิมให้เพิ่มไม่ได้ แล้วค่อยลดลง | allowlist เก่าลดได้ เพิ่มต้องมีเหตุผล | หนี้เก่าจะหายเองหรือไม่ |

ตารางนี้เป็นอภิธานศัพท์เพื่อใช้สอนร่วมกัน กลไกเฉพาะเครื่องมือมีหลักฐานและข้อจำกัดกำกับในส่วนตัวอย่างและการ์ดโปรเจกต์

### ระดับหลักฐานที่ใช้ทั้งเอกสาร

| ระดับ | สิ่งที่ตรวจพบ | สิ่งที่พูดได้ |
|---|---|---|
| กำหนดกฎ | config หรือ implementation ของ checker | repo มีข้อกำหนดนี้ใน snapshot |
| มีคำสั่งตรวจ | script/target ที่เรียก checker | มีเส้นทางเรียกตรวจจาก source |
| ผูกกับ CI | workflow/pipeline เรียก script ภายใต้เงื่อนไขที่เห็น | source ของ CI กำหนดให้รันในกรณีนั้น |
| บล็อกการรับงาน | required check/ruleset และ bypass ที่ตรวจยืนยัน | failure จะขวางการรับงานภายใต้นโยบายที่ยืนยัน |

สำหรับโปรเจกต์ที่สำรวจ **ไม่ได้ยืนยันการตั้ง required checks หรือ bypass ของเจ้าของโปรเจกต์** และไม่ได้รัน build/test ทั้ง repository การ์ดจะแยกกรณีที่เห็นแค่ config, เห็นคำสั่ง หรือไล่ถึง CI ได้ ผลทดลองที่รันจริงเป็น lab ที่เขียนขึ้นสำหรับเอกสารนี้เท่านั้น

<a id="priorities"></a>

## 3. Solo developer ควรเริ่มจากอะไร

ลำดับต่อไปนี้เป็นคำแนะนำที่สังเคราะห์จากกลไกในคลังหลักฐาน ไม่ใช่อันดับสากลหรือผลวัด ROI ข้ามโครงการ ให้ใช้ความผิดที่เคยเกิดกับงานตนตัดสิน

| ลำดับ | สิ่งที่จะมี | เหตุผลที่คุ้มเริ่ม | เกณฑ์ว่าพร้อมใช้ |
|---|---|---|---|
| 1 | คำสั่งตรวจหลักหนึ่งทางเข้า + CI เรียก | ลดความคลาดเคลื่อนระหว่างสิ่งที่ AI รันกับสิ่งที่ CI ตรวจ | ทำผิดหนึ่งกรณีแล้วคำสั่งและ job fail ตรงกัน |
| 2 | Formatter หนึ่งตัว + correctness lint ชุดเล็ก | ตัดภาระเรื่องรูปแบบและจับความผิดที่เครื่องมือมี rule ให้แล้ว | good fixture ผ่าน; bad fixture มี diagnostic ที่ตรงเรื่อง |
| 3 | Type checking ตามภาษาที่ใช้ | ตรวจสมมุติฐานของข้อมูลภายในและ API ที่อ้าง | source และ test ที่เกี่ยวข้องอยู่ใน scope |
| 4 | กฎเฉพาะโปรเจกต์ 1–3 ข้อ | คุมสิ่งที่ AI ชอบข้าม เช่น service, logging wrapper, public API | มีทางที่ถูกให้ใช้และ error บอกทางนั้น |
| 5 | Tests ของข้อกำหนดที่ lint มองไม่เห็น | คุม behavior เช่น authorization, totals, state transitions | ตัวอย่าง bug ทำให้ assertion ที่เกี่ยวข้อง fail |
| 6 | Required check และการทบทวนการเปลี่ยนกฎ | ทำให้ผลแดงมีผลต่อการรับงาน และมองเห็นการลดข้อกำหนด | ตรวจด้วย PR ทดลองว่าถูกบล็อกจริง |

ตัวอย่างชุดเริ่มต้นแยกตาม stack:

- **TypeScript application:** formatter ของโปรเจกต์, TypeScript strict, lint ที่อ่าน type สำหรับ async, restricted import ตามขอบเขต และ test ของ business invariant หนึ่งเรื่อง ดู VS Code/Grafana สำหรับ architecture; ส่วน 5 สำหรับตัวอย่างเล็ก
- **Python application:** Ruff สำหรับ lint/format, mypy หรือ checker ที่โปรเจกต์ใช้, tests เฉพาะ behavior และ unused suppression check ดู FastAPI/Django สำหรับชุดเครื่องมือ; pandas สำหรับกฎเฉพาะ domain
- **Go service:** formatting, vet/static analyzer ตาม config, import boundary ตามชั้น และ tests ที่ exercise handler/storage จริง ดู Moby/Kubernetes แล้วเลือก subset ที่เกี่ยวกับแอป
- **Rust application/library:** compiler checks, rustfmt, Clippy เฉพาะกลุ่มที่เหมาะ, warnings policy ที่เข้ากับ toolchain และ tests ตาม feature ที่ support ดู Tokio/Ruff; tidy ของ compiler เป็นกรณีศึกษาเมื่อ checker มาตรฐานไม่พอ

### สิ่งที่ควรเลื่อนไปก่อนเมื่อยังไม่มีเหตุผลรองรับ

- กฎจำนวนบรรทัด จำนวน argument หรือ complexity threshold ทุกแห่ง: เพิ่มเมื่อมีปัญหาที่ตรวจพบและทีมตกลงวิธีแก้ได้
- เปิดทุก rule ด้วย `ALL` หรือ preset ที่ strict ที่สุดโดยไม่ทบทวน: Ruff ระบุว่า `ALL` จะรับกฎใหม่เมื่อ upgrade จึงควรเลือกอย่างตั้งใจ [Ruff: rule selection](https://docs.astral.sh/ruff/linter/#rule-selection)
- สร้าง custom plugin ทันที: เริ่มจาก built-in rule, config หรือ script ที่มีขอบเขตชัดก่อน
- ยก monorepo policy มาทั้งชุด: เลือก invariant ที่ยังสำคัญในโปรเจกต์เล็ก แล้วลดจำนวน package/ข้อยกเว้น
- ใช้ coverage percentage เป็นข้อพิสูจน์ว่า requirement ครบ: ต้องตรวจว่ากรณีผิดที่สนใจทำให้ assertion fail ด้วย เช่นตัวอย่าง tenant ใน lab

<a id="rule-design"></a>

## 4. แปลงคำสั่งให้ AI เป็นกฎตรวจ

ตารางนี้เป็นตัวเลือกเชิงออกแบบ อ่านการ์ด repo ที่อ้างเพื่อดูตัวอย่างจริง ไม่ได้หมายความว่า repo เหล่านั้นเปิดทุกเครื่องมือที่กล่าวถึง

| สิ่งที่ต้องการ | ตัวตรวจที่น่าลอง | ตัวอย่างผิดสำหรับพิสูจน์กฎ | ต้นทุน / จุดหลุดที่ต้องคิด |
|---|---|---|---|
| UI ใช้ service ก่อนเข้าฐานข้อมูล | restricted import หรือ dependency graph | import DB จาก UI | aliases, re-export, dynamic import; ดู VS Code/Grafana |
| layer ล่างไม่อ้าง layer บน | import allowlist / architecture checker | domain import page component | จำกัด direction ให้สอดคล้องโครงสร้าง; ดู Kubernetes |
| ใช้ wrapper ของโปรเจกต์ | restricted API / custom lint | เรียก console หรือ raw API ใน scope ต้องห้าม | wrapper ต้องพร้อมใช้และไม่ห้าม infrastructure; ดู VS Code/React |
| Promise ไม่ถูกทิ้งโดยไม่ตั้งใจ | typed no-floating-promises | เรียก async โดยไม่ await/return/handle | void และ catch ว่างอาจเพียงกลบเจตนา; ดูส่วน 5 |
| ข้อมูลที่อาจไม่มีถูกตรวจ | compiler strict + indexed access setting | array[0] แล้วเรียก method ทันที | any, assertion และ runtime input อาจข้ามแบบจำลอง |
| เพิ่ม state แล้วครอบคลุม handling | exhaustive switch/type check + tests | เพิ่ม union member แต่ไม่เพิ่ม case | compile-time completeness ไม่พิสูจน์ side effects |
| client/schema ตรง source | regenerate + compare | เปลี่ยน source แล้วคง generated file เดิม | ต้อง deterministic และตรวจไฟล์เพิ่ม/หาย; ดู Kubernetes |
| version ต่ำสุดยังใช้ได้ | version matrix / compatibility test | ใช้ syntax/API ที่ใหม่กว่า target | package lock และ dependency transitive ต้องสัมพันธ์กัน |
| dependency ใช้ตัวที่ตกลง | dependency allowlist / duplicate/version check | เพิ่มไลบรารีซ้ำหน้าที่ | ทีมใหญ่มีเหตุผลเฉพาะ; ดู Rust tidy |
| test ตรวจครบโดยไม่หลงเหลือ focus | runner policy / test sanity | test.only หรือ focus marker | ใช้กลไกของ runner ที่ใช้จริง เช่น Vitest allowOnly |
| ไม่มี suppression ที่หมดเหตุผล | unused suppression lint | ทิ้ง disable หลังแก้โค้ดแล้ว | นี่ยังยอม suppression ที่มีผลอยู่; ดู Ruff RUF100 |
| โค้ดที่สร้างไม่ทำลาย policy | ตรวจ diff ของ config/script/ignore | เปลี่ยน error เป็น off เพื่อให้ผ่าน | ถ้า AI แก้ตัวตรวจได้ ผลเขียวอาจไม่รักษากฎเดิม |
| tenant อื่นอ่านข้อมูลไม่ได้ | integration/contract test + runtime controls | ใช้ ID ของ tenant อื่น | lint ไม่รู้ semantics ของสิทธิ์; lab เป็นเพียงตัวอย่างเล็ก |
| ไม่มี secret ที่ scanner รู้จักหลุดเข้า Git | secret scanner / push protection | ใช้ test fixture ของ scanner | coverage จำกัดชนิด secret; การ bypass และผลิตภัณฑ์ที่เปิดใช้มีผล |

กลไกเพิ่มเติม: [ESLint restricted imports](https://eslint.org/docs/latest/rules/no-restricted-imports), [dependency-cruiser rules](https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md), [Ruff unused-noqa](https://docs.astral.sh/ruff/rules/unused-noqa/), [Vitest allowOnly](https://vitest.dev/config/allowonly), [GitHub push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection)

### แบบฟอร์มกฎหนึ่งข้อ

```text
ชื่อ: UI accesses orders through application service
เหตุผล: ให้ validation และ authorization อยู่ที่จุดเดียว
ขอบเขต: source ของ UI ที่ระบุ (ไม่รวม implementation ของ service)
ข้อกำหนด: ใช้ public API ของ application service
ตัวตรวจ: ห้าม static import ของ @app/db และ @app/db/** ใน scope นี้
ตัวอย่างผิด: UI import @app/db/orders
ตัวอย่างถูก: UI import @app/application/orders
Diagnostic: ระบุ import ที่ผิดและชื่อ API ทดแทน
คำสั่ง: คำสั่ง lint ของโปรเจกต์ที่ครอบคลุมไฟล์นี้
จุดบังคับใช้: CI job ที่เป็น required check
ข้อยกเว้น: path ที่ระบุพร้อมเหตุผลและเงื่อนไขยกเลิก
ข้อจำกัด: alias ใหม่/dynamic import ยังต้องตรวจเพิ่ม
พิสูจน์: bad fail ด้วย diagnostic นี้; good pass; PR ทดลองถูก gate บล็อก
```

ข้อความเหตุผลช่วยให้ AI แก้ตรงเจตนา ส่วน config เป็นแหล่งจริงของรายละเอียด rule และ scope เอกสารสำหรับ agent ควรชี้ไปยังไฟล์นั้นแทนการคัด config ทุกบรรทัดไว้หลายแห่ง เพื่อให้การเปลี่ยนกฎมีแหล่งแก้ไขหลักเพียงแห่งเดียว

<a id="tested-examples"></a>

## 5. ตัวอย่างเล็กที่ทดลอง fail/pass แล้ว

ตัวอย่างส่วนนี้เขียนขึ้นใหม่สำหรับการสอน ไม่ใช่การยก source ของโปรเจกต์ใหญ่มารัน ทดสอบด้วย Node.js 26.7.0, ESLint 10.10.0, TypeScript 6.0.3 และ typescript-eslint 8.70.0 เวอร์ชันตรงถูกบันทึกใน `package-lock.json` ของ lab ผลทั้งหมด 12/12 กรณีตรงที่คาดไว้ ผลตรวจระบุทั้ง exit code และ diagnostic เพื่อแยกการ fail เพราะ rule ออกจากการ fail เพราะ setup พัง

[guardrail-lab/](./guardrail-lab/) มี config และ fixtures ครบสำหรับตัวอย่าง แตกไฟล์ไว้แล้วในคลังนี้ ให้รัน `npm ci --ignore-scripts` ตามด้วย `npm run verify` ด้วย Node.js 24 ขึ้นไป `verify` ตรวจว่าตัวอย่างผิดถูกปฏิเสธตามที่ตั้งใจ จึงเป็นตัวทดสอบตัวอย่าง ไม่ใช่คำสั่งรับโค้ด production รายงาน `verification.json` จากการรันครั้งก่อนถูกตัดออกเพราะมี path เฉพาะเครื่อง หากต้องการผลการรันใหม่ ให้สร้างจาก `verify.mjs` ในเครื่องของผู้เรียน

### 5.1 ห้าม UI import ฐานข้อมูลตรง

สมมุติว่า UI ต้องใช้ service ใน `@app/application/orders` กฎนี้ตรวจเส้นทางที่เขียนใน static import:

```js
// eslint.config.mjs — ย่อจาก config ใน lab
export default [{
  files: ['fixtures/imports/*.js'],
  linterOptions: { noInlineConfig: true },
  rules: {
    'no-restricted-imports': ['error', {
      patterns: [{
        group: ['@app/db', '@app/db/**'],
        message: 'UI uses @app/application/orders; keep database access inside the service.',
      }],
    }],
  },
}];
```

```js
// ผิด: checker ปฏิเสธด้วย no-restricted-imports
import { saveOrder } from '@app/db/orders';
export const submitOrder = saveOrder;

// ถูกตามกฎนี้: ใช้ application service
import { saveOrder } from '@app/application/orders';
export const submitOrder = saveOrder;
```

สองกรณีอยู่คนละไฟล์ใน lab และไม่ได้ resolve หรือรัน package สมมุตินี้จริง `eslint ... --max-warnings 0` คืน exit 1 สำหรับ bad และ 0 สำหรับ good การผ่านนี้พิสูจน์เพียงรูปแบบ import ตามกฎ ไม่ได้พิสูจน์ว่า service มี authorization

**จุดที่ต้องเรียน:** rule นี้ตรวจ static imports; dynamic `import()` อยู่นอกขอบเขต และชื่อ alias อื่นที่ไม่ตรง pattern อาจหลุด ถ้าต้องคุม dependency ที่ resolve แล้วให้พิจารณา graph checker และทดสอบเส้นทาง alias/re-export ที่โปรเจกต์ใช้จริง [ESLint: no-restricted-imports](https://eslint.org/docs/latest/rules/no-restricted-imports), [dependency-cruiser: rules reference](https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md)

### 5.2 กันการแก้ด้วย disable comment

```js
// eslint-disable-next-line no-restricted-imports
import { saveOrder } from '@app/db/orders';
export const submitOrder = saveOrder;
```

เมื่อ config block ตั้ง `noInlineConfig: true` comment นี้ไม่ปิด rule; lab ยังคงได้ exit 1 และ diagnostic ของ import violation สิ่งนี้เหมาะกับกฎสถาปัตยกรรมที่ต้องการ exception ผ่าน config ที่มองเห็นชัด [ESLint: configuration files](https://eslint.org/docs/latest/use/configure/configuration-files)

อีกทางเลือกคืออนุญาต inline exception แล้วใช้ `reportUnusedDisableDirectives: 'error'` ตรวจข้อยกเว้นที่ไม่จำเป็นแล้ว วิธีนี้ยังยอมรับการ disable ที่มีผลจริงอยู่ จึงเลือกตามนโยบายของทีม ไม่ควรอธิบายว่าทั้งสอง setting มีหน้าที่เดียวกัน [ESLint: configure rules](https://eslint.org/docs/latest/use/configure/rules)

### 5.3 ลืม await และการใช้ void

```ts
declare function storeInvoice(): Promise<void>;

// ผิดใน lab
export function finishInvoice(): void {
  storeInvoice();
}

// แก้ให้ลำดับการทำงานรอการบันทึก
export async function finishInvoice(): Promise<void> {
  await storeInvoice();
}
```

แต่ละกรณีอยู่คนละไฟล์ กฎที่ใช้คือ `@typescript-eslint/no-floating-promises: ['error', { ignoreVoid: false }]` พร้อม parser ที่อ่าน type information จาก `tsconfig.json` ไม่ใช่ใส่แค่ชื่อ rule แล้วทำงานได้เลย bad ได้ exit 1; good ได้ 0

lab ยังตรวจ `void storeInvoice()` ว่า fail ด้วย การตั้งนี้เป็นทางเลือกเพื่อบทเรียน: ค่าเริ่มต้นของ rule ยอม `void` แต่ `void` ไม่จับ Promise rejection และไม่เปลี่ยนการทำงานขณะรัน ถ้าแอปตั้งใจทำงานเบื้องหลังต้องออกแบบการจัดการ failure ให้ชัด การเติม `.catch(() => {})` อาจเงียบ error ได้แต่ไม่ยืนยันว่าตรงเจตนา [typescript-eslint: no-floating-promises](https://typescript-eslint.io/rules/no-floating-promises/)

### 5.4 หยุดสมมุติว่า array ต้องมีสมาชิก

```ts
// ผิดเมื่อ strict + noUncheckedIndexedAccess เปิดอยู่
export function firstLabel(labels: string[]): string {
  return labels[0].toUpperCase();
}
```

```ts
// เลือก behavior เมื่อไม่มีสมาชิกให้ชัด
export function firstLabel(labels: string[]): string {
  const label = labels[0];
  if (label === undefined) throw new Error('At least one label is required');
  return label.toUpperCase();
}
```

`tsc -p fixtures/types/bad` ได้ exit 2, `TS2532`; แบบ good ได้ 0 เลข 2 ในกรณีนี้เป็นผลที่สังเกตจาก compiler เวอร์ชันใน lab ไม่ใช่สัญญาณว่าเป็น lint configuration error เหมือนเครื่องมืออื่น หลักทั่วไปที่ CI ต้องรับคือ exit ที่ไม่ใช่ศูนย์

`strict` เปิดกลุ่ม strict checks แต่ `noUncheckedIndexedAccess` เป็นตัวเลือกที่ต้องพิจารณาเพิ่ม; `exactOptionalPropertyTypes` มีหน้าที่แยกการไม่มี property จากการมีค่า `undefined` ตาม type ที่ประกาศ อย่าเรียกรวมว่าตั้ง strict แล้วตรวจทุกเรื่อง [TypeScript: strict](https://www.typescriptlang.org/tsconfig/strict.html), [indexed access](https://www.typescriptlang.org/tsconfig/noUncheckedIndexedAccess.html), [exact optional properties](https://www.typescriptlang.org/tsconfig/exactOptionalPropertyTypes.html)

การเติม non-null assertion `!`, cast หรือ `any` อาจทำให้ type checker เลิกเตือนโดยไม่เพิ่ม runtime check ให้ผู้เรียนอธิบายว่า behavior ที่ต้องการเมื่อข้อมูลหายคืออะไร ก่อนเลือกวิธีแก้

### 5.5 Business invariant ที่ต้องใช้ test

```js
// ผิด: ค้นจาก orderId อย่างเดียว
export function findOrder(orders, tenantId, orderId) {
  return orders.find(order => order.id === orderId);
}

// ถูกตาม contract ตัวอย่าง: จำกัด tenant ด้วย
export function findOrder(orders, tenantId, orderId) {
  return orders.find(order =>
    order.id === orderId && order.tenantId === tenantId);
}
```

test ป้อน order ของ `shop-a` แต่ค้นด้วย `shop-b` แล้ว assert ว่าต้องได้ `undefined` มี positive case ของเจ้าของข้อมูลและ missing-order case ด้วย bad implementation ได้ exit 1 จาก assertion; good ผ่านทั้งสามกรณี การเพิ่ม positive case ช่วยจับการแก้แบบ “คืน undefined ทุกครั้ง” ที่ทำให้เฉพาะ negative case ผ่าน

นี่เป็น **ตัวอย่างออกแบบ test ของข้อกำหนด** ไม่ใช่การอ้างว่า function จำลองเพียงตัวเดียวป้องกันข้อมูลรั่วในแอปจริง เมื่อใช้จริงต้อง exercise API/query ที่เข้าถึงข้อมูลจริง และรวมช่องทางที่เกี่ยวข้อง เช่นรายการ ค้นหา export และ cache ตาม scope ของแอป

### 5.6 Source เปลี่ยน แต่ generated file ยังเก่า

lab มี source `states = [paid, pending, refunded]` และ checker ที่คำนวณข้อความ JSON ที่ควรได้ด้วยลำดับคงที่ แล้วเทียบ bytes กับไฟล์ตัวอย่างที่เก็บไว้ มันไม่ได้เขียน generated file ลงดิสก์ output ที่ขาด `refunded` fail; output ตรง source ผ่าน หลักคิดคือให้ source เป็นแหล่งจริงและตรวจ output ที่ derive มาได้ แทนหวังให้คนหรือ AI จำแก้ทุกไฟล์

ในโครงการจริงกำหนด generator/version/inputs ให้แน่นอน สร้าง output แล้วตรวจทั้งไฟล์เปลี่ยน ไฟล์เพิ่ม และไฟล์หาย การใช้ `git diff --exit-code` อย่างเดียวไม่แสดงไฟล์ untracked ใหม่ ควรตรวจรายการไฟล์ใน generated directory เพิ่ม หรือสร้างลง temporary directory แล้วเทียบทั้ง tree แบบที่ตรวจ missing/extra ได้ ดูการ์ด Kubernetes และ Moby สำหรับ implementation จริง [Git: diff](https://git-scm.com/docs/git-diff), [Git: ls-files สำหรับไฟล์ untracked](https://git-scm.com/docs/git-ls-files)

### ผลทดสอบที่ใช้เป็นหลักฐาน

| กลไก | กรณีที่ลอง | ผล |
|---|---|---|
| Import restriction | bad / good | 1 / 0 |
| Inline suppression policy | bad พร้อม disable comment | 1 |
| Typed Promise lint | floating / void / awaited | 1 / 1 / 0 |
| Type checking | unchecked / checked access | 2 / 0 |
| Behavior contract | missing tenant filter / correct filter | 1 / 0 |
| Generated artifact | stale / matching | 1 / 0 |

ทั้งหมดเป็นผลของ lab ที่แนบ ยังไม่ได้ทดสอบ required merge policy บน GitHub และไม่ได้ยืนยันว่า environment ของผู้เรียนจะเหมือนกันโดยไม่ใช้ lockfile

<a id="ci-enforcement"></a>

## 6. ทำให้ fail มีผลต่อการรับงาน

### เส้นทางสำหรับโครงการเล็ก

เริ่มจากทางเข้าตรวจเดียวซึ่งเรียกคำสั่งเดิมของโปรเจกต์ ตัวอย่าง shell ต่อไปนี้เป็นโครงสำหรับแอปที่มี npm scripts ดังกล่าวอยู่แล้ว ไม่ใช่คำสั่งรัน lab:

```bash
set -euo pipefail
npm ci
npm run lint
npm run typecheck
npm test
```

ตัวอย่างแอปใช้ install lifecycle ตามโปรเจกต์ ส่วน lab ใช้ `--ignore-scripts` เพราะตัวอย่างชุดนั้นไม่ต้องอาศัย install scripts ของ dependencies ให้เลือกตามการติดตั้งจริงของโปรเจกต์

ใช้ lint แบบ check ที่คืน non-zero เมื่อผิด เช่น ESLint rule ที่เป็น `error` หรือ `--max-warnings 0` เมื่อตั้งใจไม่ยอม warning ผล warning ตามค่าเริ่มต้นของ ESLint ไม่ทำให้ exit code ผิดพลาด ส่วน Ruff แยก `ruff check` จาก `ruff format --check` การ format อย่างเดียวไม่ตรวจ logic ที่ rule ของ linter ดูอยู่ [ESLint: CLI](https://eslint.org/docs/latest/use/command-line-interface), [Ruff: linter](https://docs.astral.sh/ruff/linter/), [Ruff: formatter](https://docs.astral.sh/ruff/formatter/)

ให้ CI เรียกทางเข้าเดียวกันบน event ของ PR ที่ต้องรับงาน แล้วตั้งชื่อ job นั้นเป็น required check สำหรับ branch เป้าหมาย เลือกนโยบาย bypass ให้ตรงกับคน/automation ที่ควรเปลี่ยนกฎได้ และทดสอบด้วย PR ที่ตั้งใจผิดหนึ่งข้อ เมื่อ failure ปรากฏและ merge ถูกปฏิเสธ จึงมีหลักฐานถึงชั้นบังคับใช้ [GitHub: rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)

### ช่องที่ทำให้ดูเขียวทั้งที่ไม่ได้ตรวจครบ

| กรณี | สิ่งที่ตรวจสอบหรือออกแบบเพิ่ม |
|---|---|
| lint ถูกตั้งเป็น warn | รู้ exit policy ของเครื่องมือและเลือก threshold ให้ชัด |
| คำสั่งใช้ `|| true` หรือ workflow ใช้ continue-on-error | ให้ failure ของกฎบังคับส่งต่อถึง job ที่รับงาน |
| glob/ignore ตัด source สำคัญออก | ตรวจ effective config ต่อไฟล์ตัวอย่างและใส่ bad fixture ใน directory นั้น |
| รันเฉพาะไฟล์เปลี่ยนแต่ rule ดูทั้ง graph | แยก check แบบไฟล์จาก check ทั้งระบบ |
| job ถูก skip ด้วย if | ต้องรู้ว่า skipped job ยังรายงานสำเร็จได้ |
| workflow ไม่เริ่มเพราะ path/branch filter | required status อาจค้าง pending; ออกแบบ trigger และผลรวมให้ตรง scope |
| ติ๊ก required check ผิดชื่อ | ทดสอบกับชื่อ job/check ที่ GitHub แสดงจริง |
| agent เพิ่ม ignore/disable/เปลี่ยน scripts | review การเปลี่ยนนโยบายตรวจควบคู่กับ source diff |
| generator ไม่สร้างไฟล์ใหม่เข้า diff | ตรวจไฟล์เพิ่ม/หายด้วย ไม่เทียบเฉพาะ tracked modifications |
| upgrade tool ทำให้กฎเปลี่ยน | pin versions/lockfile; ทบทวนผล bad/good fixtures เมื่ออัปเกรด |

พฤติกรรม skip สองแบบต่างกัน: GitHub อธิบายว่า job ที่ข้ามด้วย condition รายงาน success และไม่บล็อก merge แม้ required; workflow ที่ข้ามเพราะ path/branch filter อาจทิ้ง required checks ไว้ pending และทำให้ merge ค้าง [GitHub: job conditions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions), [GitHub: troubleshooting required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)

pre-commit hook ช่วย feedback ก่อน commit แต่ Git รองรับการข้าม pre-commit ด้วย `--no-verify` จึงควรมี CI ตรวจซ้ำเมื่อเป้าหมายคือบังคับรับงาน [Git: githooks](https://git-scm.com/docs/githooks)

### ใครคุมตัวตรวจ

ถ้า AI แก้ได้ทั้ง source, tests, lint config และ CI มันสามารถทำให้ผลเขียวโดยเปลี่ยนนิยามว่าอะไรผิดได้ นี่เป็นขอบเขตเชิงออกแบบของระบบรับงาน ให้ผู้ดูแลเห็นการเปลี่ยนไฟล์กำหนดกฎและประเมินเหตุผลแยกจากการแก้ feature เสมอ กรณีใช้ agent credentials กับระบบ repository ให้สิทธิ์แก้ policy สอดคล้องกับระดับอำนาจที่ตั้งใจมอบ

สำหรับ solo developer การให้ตัวเอง review diff ของ policy ไม่จำเป็นต้องสร้างระบบอนุมัติใหญ่โต แต่การ review ด้วยสายตายังเป็นกระบวนการของคน ถ้าต้องการบังคับด้วยเครื่องจริงต้องใช้สิทธิ์และ gate ภายนอกพื้นที่ที่ agent แก้ได้ตามต้องการ

### เพิ่มกฎโดยไม่ทำให้โปรเจกต์เก่าหยุดเดิน

1. เลือก failure ที่เกิดซ้ำและมีทางแก้ที่ตกลงได้ จบเมื่อเขียน bad/good example ได้
2. เปิด rule ใน scope เล็กที่เกี่ยวข้อง ดู false positives แล้วทำข้อยกเว้นเฉพาะจุดพร้อมเหตุผล
3. เก็บหนี้เก่าเป็น baseline หรือ allowlist ที่ตรวจว่าห้ามเพิ่มโดยเงียบ ทบทวนวิธีนับให้ไม่ซ่อนปัญหาใหม่ชนิดเดิม
4. ให้ error message บอก public API/path ที่ควรใช้ เพื่อลดการแก้แบบเดา
5. เมื่อนำขึ้น CI ให้คง exit failure และทดสอบ gate จริงก่อนประกาศว่าบังคับใช้แล้ว

นี่เป็นแนวทางประยุกต์ของเอกสารนี้ เหมาะเมื่อมีหนี้เดิมมาก การเลือก baseline ไม่ใช่การยืนยันว่าหนี้เดิมปลอดภัย

<a id="learning-path"></a>

## 7. แผนการเรียนที่หยุดได้เมื่อใช้เป็น

เวลาต่อช่วงต่อไปนี้เป็นกรอบที่เสนอเพื่อให้จัดการได้ ไม่ใช่ผลทดลองว่าทุกคนเรียนจบเท่ากัน เริ่มช่วงละประมาณ 15–30 นาที แล้วใช้เกณฑ์ความสามารถเป็นตัวตัดสิน

| ช่วง | เรียนเรื่องเดียว | ตัวอย่างที่ใช้ | จบเมื่อผู้เรียนทำได้ |
|---|---|---|---|
| 1 | ข้อกำหนด → ตัวตรวจ | UI import DB เทียบกับ tenant leak | บอกได้ว่าอะไรใช้ lint และอะไรต้อง test พร้อมเหตุผล |
| 2 | scope + severity + diagnostic | lab imports และ suppression | ทำนาย fail/pass และชี้ config ที่ควบคุมได้ |
| 3 | compiler กับ typed lint | indexed access และ floating Promise | อธิบายได้ว่าทำไมเปลี่ยน type/assertion อาจเพียงกลบ error |
| 4 | กฎเฉพาะโปรเจกต์ | VS Code/Grafana/pandas ตาม stack | เขียน rule card ของข้อผิดพลาดที่ตนเคยเจอได้หนึ่งข้อ |
| 5 | command → CI → merge gate | section 6 + repo CI chain | แยก config evidence จาก required-check evidence ได้ |
| 6 | generated drift / compatibility | Kubernetes/Moby/Tokio | เลือกเฉพาะเมื่อมี artifact หรือ API ที่ต้องรักษา |
| 7 | ชุดเล็กสำหรับโปรเจกต์ตน | source/config ของผู้เรียน | เลือกสามกฎพร้อมขอบเขต ตัวอย่างผิด ผลตรวจ และต้นทุน |

**ขั้นต่ำที่เพียงพอสำหรับเริ่มใช้:** ทำช่วง 1–5 ได้และมี rule card ของตนหนึ่งข้อ ยังไม่จำเป็นต้องเขียน ESLint plugin, รู้ทุก Ruff code หรือเข้าใจ build system ของ Kubernetes

### โจทย์ให้ครูเลือกถามทีละข้อ

1. โปรเจกต์มี lint config แต่ CI รันแค่ tests ข้อกำหนด lint อยู่ระดับหลักฐานใด และต้องเห็นอะไรเพิ่ม?
2. `void saveOrder()` ทำให้ lint เงียบ หมายความว่าข้อผิดพลาดตอนบันทึกถูกจัดการแล้วหรือไม่?
3. UI เปลี่ยนเป็น dynamic import แล้ว rule ที่ห้าม static import ไม่เตือน จะแก้ที่คำสั่งสอน AI หรือเพิ่มกลไกอะไร?
4. เพิ่ม field ใน schema แล้ว client type ยังเก่า จะออกแบบ bad example ให้ตรวจ stale output ได้อย่างไร?
5. กฎห้าม DB import ไปโดน implementation ของ database adapter เอง ควรปรับ scope อย่างไร?
6. test ของ tenant อื่นผ่านหลังแก้ function ให้คืน undefined ทุกครั้ง จะมี positive case อะไรจับการแก้นี้?
7. CI ขึ้น skipped ควรสรุปว่ากฎตรวจผ่านหรือไม่ ต้องดูว่า skip ระดับ job หรือ workflow?
8. ถ้า AI ทำให้ build ผ่านด้วยการเปลี่ยน error เป็น off จะรู้จากหลักฐานใดว่าข้อกำหนดเดิมยังคงอยู่?

คำตอบอยู่ในส่วน 1–6 ให้ครูรอคำตอบของผู้เรียนก่อนเปิดเฉลย และถามให้สร้างตัวอย่างใหม่หนึ่งกรณีเพื่อดูว่าเข้าใจถ่ายโอนได้หรือเพียงจำคำ

### การทบทวน

หลังช่วงแรก ให้ผู้เรียนเขียนจากความจำว่าแต่ละกฎ “เห็นอะไร / มองไม่เห็นอะไร / fail ที่ไหน” ครั้งถัดไปเริ่มจากโจทย์ที่เปลี่ยนชื่อ module และ domain ของข้อมูล หลังเว้นช่วงหลายวันให้กลับมาสร้าง rule card ใหม่โดยไม่ดูแบบ กรอบการทบทวนนี้เป็นข้อเสนอสำหรับหลักสูตร; ยังไม่มีหลักฐานการเรียนรู้เฉพาะบุคคลในชุดข้อมูลนี้

<a id="reading-source"></a>

## 8. อ่านโปรเจกต์ใหญ่ให้ได้ของกลับมา

อ่านเป็นเส้นทางสั้น ๆ: **config → implementation (เมื่อเป็น custom rule) → command → CI → valid/invalid cases** บันทึกเฉพาะสิ่งที่ตอบได้ว่าจับความผิดแบบใดและคุ้มย้ายมาโปรเจกต์ตนหรือไม่

| พบไฟล์ | สิ่งที่มองหา | ข้อสรุปที่ยังไม่ควรด่วนทำ |
|---|---|---|
| eslint/ruff/golangci config | severity, file scope, exceptions, plugins | ชื่อ dependency ใน lockfile ไม่พอจะบอกว่าเปิด rule |
| custom rule/check script | report/error branch, input coverage, exclusions | ห้าม construct ใน source ไม่เท่ากับจับได้ทุก semantic alias |
| package scripts/Makefile/tox | คำสั่งจริง args cwd shell และ exit propagation | มี target แต่ไม่มีผู้เรียกอาจยังไม่ใช่ CI gate |
| workflows/pipeline/test-infra | event, condition, job, continue-on-error | การตั้ง required checks อยู่คนละชั้น |
| tests/fixtures ของ checker | valid และ invalid พร้อมข้อความ | ชุด fixture ไม่ใช่การพิสูจน์ทุกกรณี |
| allowlist/baseline | เหตุผล ขอบเขต และสิ่งที่เพิ่มไม่ได้ | ข้อยกเว้นของทีมใหญ่ไม่จำเป็นต้องใช้ในโครงการเล็ก |

ถ้าต้องค้นเพิ่มเติมใน checkout ของโปรเจกต์ ใช้คำค้นอย่าง `no-restricted`, `forbid`, `deny`, `depguard`, `ignore`, `max-warnings`, `verify`, `tidy`, `generated`, `git diff`, `continue-on-error` แล้วอ่านบริบทรอบคำที่พบก่อนสรุป คำค้นเป็นเครื่องมือหาแหล่งอ่าน ไม่ใช่หลักฐานด้วยตัวมันเอง

### เกณฑ์เลือกกฎกลับมาใช้

ให้ตอบสี่ข้อ: เคยเจอความผิดนี้หรือมีเหตุผลว่าจะเจอหรือไม่; ความเสียหายมากเพียงใด; checker ตัดสินได้แม่นเพียงใด; ดูแลข้อยกเว้นและเวลารันไหวหรือไม่ ถ้าตอบว่าคุ้ม ให้เลือก implementation ที่ง่ายที่สุดซึ่งตรวจขอบเขตนั้นได้จริง ก่อนเพิ่มความซับซ้อนเพื่อครอบคลุมกรณีที่ยังไม่มีในงาน

ความมีชื่อเสียงของ repository เป็นเหตุผลเลือกกรณีศึกษา ไม่ใช่หลักฐานว่า rule ทุกข้อเหมาะกับ solo developer การ์ดถัดไปจึงกำกับทั้งสิ่งที่พบและส่วนที่ควรย่อมาใช้

<a id="repo-evidence"></a>

## 9. หลักฐานจากโปรเจกต์จริง

ตรวจแหล่งข้อมูลเมื่อ **13 กันยายน 2026** ใช้ commit ที่ตรึงไว้เป็นหน่วยอ้างอิง วันที่ commit ด้านล่างเป็นวันของ committer ใน UTC ไม่ใช่วันที่กฎนั้นเริ่มใช้หรือวัน release ตารางนี้เป็นดัชนีเลือกอ่าน; หลักฐานของแต่ละรายการอยู่ในการ์ดที่อ้าง

| โปรเจกต์ | จุดที่เหมาะใช้เรียน | เลือกเมื่อ |
|---|---|---|
| [VS Code](#vscode) | layer imports, accessor หลัง await, disposables, any casts | ต้องคุม architecture และ lifetime |
| [React](#react) | production logging, error catalog, runtime constraints | ต้องเข้าใจ custom rule ที่ผูกกับบริบท library |
| [Next.js](#nextjs) | AST patterns, server/browser split, async ordering, typed switches | built-in lint ยังอธิบายความผิดเฉพาะระบบไม่ได้ |
| [Grafana](#grafana) | public exports, Go imports, enum/default policy, i18n | มี package boundary หรือหลายภาษาใน UI |
| [Django](#django) | formatter/lint แยกหน้าที่, migrations, workflow lint | มี ORM และ GitHub Actions |
| [FastAPI](#fastapi) | strict typing/tests, fixer exit policy, regression diagnostics | AI เพิ่ม/แก้ tests และต้องการอ่านผล CI ให้ถูก |
| [pandas](#pandas) | banned APIs, AST/regex policy, test naming, error documentation | มี convention เฉพาะ domain ที่พูดซ้ำบ่อย |
| [Ruff](#ruff) | System abstraction, Clippy policy, generated files, hooks | ต้องรักษาขอบเขตระบบและ output ที่ derive จาก source |
| [Kubernetes](#kubernetes) | generated drift, import restrictions, verify scripts | มี codegen หรือหลาย module ที่ต้องแยกชั้น |
| [Moby](#moby) | Go package/API restrictions และ Swagger consistency | ทำ Go service หรือ API ที่มี generated contract |
| [Rust compiler](#rust) | tidy checks สำหรับข้อกำหนดระดับ repository | เครื่องมือมาตรฐานยังตรวจ metadata/dependencies ไม่พอ |
| [Tokio](#tokio) | compiler/lint policies และ compatibility checks | ทำ Rust library ที่ต้องรักษา feature/runtime support |

ทุกการ์ดแยกคำแนะนำสำหรับ solo ออกจากข้อเท็จจริงของ source ชื่อ job ที่มีคำว่า required/verify เป็นเพียงชื่อจนกว่าจะตรวจนโยบายรับงานจริง การ์ด pandas ระบุช่องว่าง CI binding แยกไว้ ส่วนตัวอย่าง action invocation จะไม่เขียนเหมารวมว่า CI เรียก local script เดียวกัน

<a id="vscode"></a>

### 9.1 VS Code — กฎสถาปัตยกรรมและอายุการใช้งาน object

**แหล่งต้นทาง:** `microsoft/vscode` · [snapshot 8e35945bae3f](https://github.com/microsoft/vscode/commit/8e35945bae3f2b0b3d0276963281180f1ce10cb0) · commit 12 กันยายน 2026

| กฎที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| `local/code-layering` | กำหนด layer ที่ import ถึงกันได้ เช่น browser ใช้ common; เป็น warn ใน [config](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/eslint.config.js#L114-L140); [implementation](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/.eslint-plugin-local/code-layering.ts#L63-L88) รายงานเมื่อพบ path ฝ่าฝืน | เริ่มด้วย UI/domain/adapter ที่มีอยู่จริง ให้ error ระบุชั้นที่อนุญาต; ต้องดูแลเมื่อย้ายโฟลเดอร์ |
| `local/code-no-accessor-after-await` | accessor ของ callback มีอายุใช้งาน synchronous; rule รายงานการเข้าถึงหลัง await [เหตุผล](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/.eslint-plugin-local/code-no-accessor-after-await.ts#L9-L29), [จุดตรวจ](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/.eslint-plugin-local/code-no-accessor-after-await.ts#L139-L153) | ใช้เมื่อระบบมี transaction/accessor/lifetime แบบนี้; สอนให้ดึง service ที่ต้องใช้ก่อน suspension ตาม contract จริง |
| `local/code-no-potentially-unsafe-disposables` | ตรวจ declaration/property ของ disposable ที่อาจถูก assign ใหม่ แล้วแนะนำ const/readonly [implementation](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/.eslint-plugin-local/code-no-potentially-unsafe-disposables.ts#L9-L36) | เหมาะกับ app ที่จัดการ subscription/listener/resource; ไม่ใช่ตัวพิสูจน์ว่าไม่มี resource leak ทุกชนิด |
| `local/code-no-any-casts` | ตรวจ assertion ไป `any` และแนะนำชนิดเฉพาะ/type guard [implementation](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/.eslint-plugin-local/code-no-any-casts.ts#L9-L19) | คุมการแก้ type error ด้วย cast; คู่กับ parser/validation ที่ boundary และข้อยกเว้นสำหรับ adapter ที่จำเป็น |

**เส้นทางเรียกจริง:** [config ของกฎ](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/eslint.config.js#L96-L140) → [npm script eslint](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/package.json#L69-L81) → [build/eslint.ts](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/build/eslint.ts#L26-L50) → [PR Compile & Hygiene job](https://github.com/microsoft/vscode/blob/8e35945bae3f2b0b3d0276963281180f1ce10cb0/.github/workflows/pr.yml#L89-L107)

**รายละเอียดที่น่าเรียน:** wrapper นับทั้ง warning และ error แล้ว throw เมื่อมีอย่างใดอย่างหนึ่ง กฎที่เขียน warn จึงทำให้คำสั่งนี้ fail ได้ นอกจากนี้ workflow มี layer/type/cycle checks แยกอยู่ด้วย จึงไม่ควรสรุปว่ากฎ ESLint ตัวเดียวคุม architecture ทุกมิติ

**โจทย์เริ่มเรียน:** “มี `await` แล้วค่อยเรียก `accessor.get`” ผิดเพราะ syntax ของ async เอง หรือเพราะ contract ของ accessor? ถ้าโปรเจกต์ไม่มี contract นี้ กฎใดในตารางยังน่ายืมมาใช้?

<a id="react"></a>

### 9.2 React — เปลี่ยนเงื่อนไขของ library เป็น custom rules

**แหล่งต้นทาง:** `facebook/react` · [snapshot 019019be403c](https://github.com/facebook/react/commit/019019be403c3269e15b8d7ebefb57d30f84086b) · commit 11 กันยายน 2026

| กฎที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| `react-internal/no-production-logging` | console.warn/error ต้องอยู่ใน DEV branch; console methods อื่นถูก report [implementation](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/scripts/eslint-rules/no-production-logging.js#L39-L82) | ถ้ามี logging policy ให้บังคับ wrapper ที่มีอยู่; macro `__DEV__` เป็นบริบทของ React ไม่ใช่ API ที่มีในทุกแอป |
| `react-internal/prod-error-codes` | error message ต้องมี mapping ใน catalog สำหรับ scope ที่ shipped; มี overrides สำหรับ tests/บาง directories [scope](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/.eslintrc.js#L310-L349), [checker](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/scripts/eslint-rules/prod-error-codes.js#L42-L67) | ใช้เมื่อมี public error catalog หรือเหตุผลเรื่อง bundle; API server เล็กอาจเริ่มจาก stable error code ที่น้อยกว่านี้ |
| `react-internal/safe-string-coercion` | แยกเงื่อนไข coercion ตาม production/performance/error context [เหตุผลของ rule](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/scripts/eslint-rules/safe-string-coercion.js#L29-L48), [diagnostics](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/scripts/eslint-rules/safe-string-coercion.js#L326-L349) | ใช้เรียนการแปลงข้อจำกัดเฉพาะ runtime เป็นกฎ; อย่าย้าย optimization มาโดยไม่รู้ชนิดข้อมูลและวัดผล |
| ข้อจำกัด `for...of` | config เปิด rule เป็น error พร้อมเหตุผลเกี่ยวกับ polyfill ของ target [config](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/.eslintrc.js#L292-L297) | เป็นกรณีศึกษาว่ากฎอาจมีไว้รองรับ target เฉพาะ; ถ้า runtime ของแอปไม่ต้องการข้อจำกัดนี้ก็ไม่ต้องรับมา |

**เส้นทางเรียกจริง:** [custom rules เป็น ERROR](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/.eslintrc.js#L299-L318) → [yarn lint](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/package.json#L134-L136) → [script ที่ exit 1 เมื่อไม่ผ่าน](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/scripts/tasks/eslint.js#L13-L26) → [eslint CI job](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/.github/workflows/shared_lint.yml#L41-L60) ตัว runner ยังพิจารณา warning หลังหักข้อความ ignored ตาม [implementation](https://github.com/facebook/react/blob/019019be403c3269e15b8d7ebefb57d30f84086b/scripts/eslint/index.js#L48-L92)

**โจทย์เริ่มเรียน:** หากแอปต้องมี production logs เพื่อดูแลระบบ จะยืมหลักการของ React มาเขียนกฎ “ผ่าน logger ของเรา” อย่างไร โดยรักษา logging ที่จำเป็นไว้? กรณีนี้ช่วยแยกหลักการที่ย้ายได้ออกจาก policy เฉพาะ library

<a id="nextjs"></a>

### 9.3 Next.js — AST rules สำหรับ pattern ที่มีผลต่อระบบจริง

**แหล่งต้นทาง:** `vercel/next.js` · [snapshot 748cc4a6e8b0](https://github.com/vercel/next.js/commit/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492) · commit 12 กันยายน 2026

| กฎที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| ast-grep `no-map-async-cell` | pattern ของ async map ที่สร้าง cell ทำให้ลำดับไม่คงที่ตามข้อจำกัดของ Rust cell abstraction ในโค้ด Next; rule เสนอให้ join ก่อนสร้าง cell [rule](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/.config/ast-grep/rules/no-map-async-cell.yml#L3-L28) | เรียนว่าข้อผิดพลาดจาก incident/abstraction เฉพาะแปลงเป็น AST pattern ได้; ไม่จำเป็นต้องรับแนวคิด cell ถ้าแอปไม่มี |
| ast-grep `no-typeof-window-require` | ตรวจ require ใต้เงื่อนไข typeof window ใน source scope ที่กำหนด เพราะกระทบ server/browser bundling [rule](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/.config/ast-grep/rules/no-typeof-window-require.yml#L3-L32) | ถ้าแอปมี server/browser split ให้ตรวจตาม convention ของ bundler จริง ไม่ถือว่าทุก conditional import ในทุกระบบผิด |
| ast-grep `no-context-format` | ตรวจการ format error context ก่อนจำเป็น และเสนอ lazy closure [rule/fix](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/.config/ast-grep/rules/no-context-format.yml#L3-L12) | ตัวอย่าง custom rule สั้นที่มีทางแก้ชัด; ต้องใช้กับ Rust API ที่มี semantics ตรงกัน |
| Typed switch exhaustiveness | CLI config เปิด `switch-exhaustiveness-check` และกำหนด default สำหรับ non-union switches [CLI config](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/eslint.cli.config.mjs#L9-L41) | เหมาะกับ state/variant ที่สำคัญ; `requireDefaultForNonUnion` มีหน้าที่คนละอย่างกับการยอม default แทนทุก union case |

**เส้นทางเรียกจริง:** [sgconfig](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/sgconfig.yml#L1-L8) ชี้ rule/test directories → [package scripts](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/package.json#L63-L76) มี `lint-ast-grep` และ ESLint command; CI เรียก [lint-no-typescript](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/.github/workflows/build_and_test.yml#L235-L256) และมี [ast-grep action job แยก](https://github.com/vercel/next.js/blob/748cc4a6e8b046f2c61cc3f28378c78c7e7a9492/.github/workflows/build_and_test.yml#L361-L373) จึงเป็นการผูก CI ผ่าน action สำหรับ AST rules ไม่ใช่การอ้างว่า YAML เรียก npm script เดียวกันทุกตัว

**รายละเอียดที่กันการสอนผิด:** CLI config ปิด `no-floating-promises` ไว้ชัดเจน จึงใช้ Next.js เป็นหลักฐานการเปิดกฎนั้นไม่ได้ ส่วน option ที่ถือว่า default ครอบคลุม union เป็นอีกตัวหนึ่งคือ `considerDefaultExhaustiveForUnions` อ่าน semantics แยกใน [เอกสารผู้สร้าง rule](https://typescript-eslint.io/rules/switch-exhaustiveness-check/)

**โจทย์เริ่มเรียน:** pattern ที่ผิดในโครงการตนสักข้อเป็นสิ่งที่ regex ตัดสินได้ หรือจำเป็นต้องรู้ว่า node อยู่ภายใน if/callback แบบไหน? เขียนคู่ invalid/valid ก่อนตัดสินใจสร้าง AST rule

<a id="grafana"></a>

### 9.4 Grafana — public package boundaries และกฎ i18n

**แหล่งต้นทาง:** `grafana/grafana` · [snapshot 9d9d93ee41b0](https://github.com/grafana/grafana/commit/9d9d93ee41b07f98d9e70eac45ff7feb48231525) · commit 12 กันยายน 2026

| กฎที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| Go `depguard` | allow/deny imports ต่อ file scope เช่น apimachinery ห้ามพึ่ง core บางส่วน [config](https://github.com/grafana/grafana/blob/9d9d93ee41b07f98d9e70eac45ff7feb48231525/.golangci.yml#L35-L75) | คุม dependency direction จาก package ที่มีจริง เริ่มด้วยเส้นห้ามที่สำคัญเพียงไม่กี่เส้น |
| Go `exhaustive` | เปิด enum switch checker และตั้ง `default-signifies-exhaustive: true` [options](https://github.com/grafana/grafana/blob/9d9d93ee41b07f98d9e70eac45ff7feb48231525/.golangci.yml#L189-L205) | ต้องตัดสินใจว่า default ควรทำให้ checker ยอมผ่านหรือไม่; policy นี้ไม่ได้บังคับเพิ่ม explicit case ทุกครั้งที่เพิ่ม enum |
| Frontend public imports | ห้าม deep source/internal exports ใน scope ของ package และห้าม runtime dependency ใน library บางกลุ่ม [base](https://github.com/grafana/grafana/blob/9d9d93ee41b07f98d9e70eac45ff7feb48231525/eslint.config.js#L41-L84), [package scopes](https://github.com/grafana/grafana/blob/9d9d93ee41b07f98d9e70eac45ff7feb48231525/eslint.config.js#L338-L390) | ใช้เมื่อ AI import internal ที่มีเฉพาะใน monorepo แต่ไม่อยู่ใน package ที่ publish; ต้องมี public export ที่ใช้งานได้ |
| Custom i18n lint | ตรวจข้อความในโครงสร้าง UI ที่กำหนด และการเรียก translation ที่ top-level [config](https://github.com/grafana/grafana/blob/9d9d93ee41b07f98d9e70eac45ff7feb48231525/eslint.config.js#L434-L471), [string checker](https://github.com/grafana/grafana/blob/9d9d93ee41b07f98d9e70eac45ff7feb48231525/packages/grafana-i18n/src/eslint/no-untranslated-strings/no-untranslated-strings.cjs#L63-L170), [lifetime checker](https://github.com/grafana/grafana/blob/9d9d93ee41b07f98d9e70eac45ff7feb48231525/packages/grafana-i18n/src/eslint/no-translation-top-level/no-translation-top-level.cjs#L30-L57) | คุ้มเมื่อแอปต้องรองรับหลายภาษา; กำหนดเฉพาะ prop/ข้อความที่ user เห็น และทำ exception สำหรับ fixture อย่างตั้งใจ |

**เส้นทาง frontend:** [yarn scripts](https://github.com/grafana/grafana/blob/9d9d93ee41b07f98d9e70eac45ff7feb48231525/package.json#L48-L55) → ESLint และ Sass lint → [frontend workflow](https://github.com/grafana/grafana/blob/9d9d93ee41b07f98d9e70eac45ff7feb48231525/.github/workflows/frontend-lint.yml#L40-L59) ที่เรียก yarn run lint

**เส้นทาง Go:** [Makefile](https://github.com/grafana/grafana/blob/9d9d93ee41b07f98d9e70eac45ff7feb48231525/Makefile#L619-L642) เรียก golangci-lint โดยระบุ `.golangci.yml`; [CI workflow](https://github.com/grafana/grafana/blob/9d9d93ee41b07f98d9e70eac45ff7feb48231525/.github/workflows/go-lint.yml#L63-L80) เรียก golangci-lint action โดยตรง หลักฐาน local config binding จึงตรงกว่า YAML ของ CI ซึ่งใช้กลไก config discovery ของ action/tool แทนการเขียน Make target เดิมใน workflow

**โจทย์เริ่มเรียน:** import ที่ใช้ได้ใน workspace แต่ใช้ไม่ได้ใน package ที่ publish เป็นความผิดแบบใด? ออกแบบ rule ที่บังคับให้ใช้ public API และแยก library package จาก application source

<a id="django"></a>

### 9.5 Django — lint หลายหน้าที่ และ migration ที่ลืมไม่ได้

**แหล่งต้นทาง:** `django/django` · [snapshot 2b30f6255b5e](https://github.com/django/django/commit/2b30f6255b5ef84afbd827993643d52ef2c0963a) · commit 8 กันยายน 2026

| กฎหรือกลไกที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| แยก Black, isort และ Flake8 | มีคำสั่ง check/diff แยกใน [tox.ini](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/tox.ini#L54-L96) และกำหนด [target/ข้อยกเว้นสำหรับ fixture](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/pyproject.toml#L56-L63) | เริ่มต้นทุนต่ำ เลือกเครื่องมือที่ทำหน้าที่ชัดและตั้ง formatter/import sorter ให้เข้ากัน |
| Test migration consistency | script โหลด test apps แล้วเรียก `makemigrations --check`; มี exit 1 เมื่อ migration ขาด [checker](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/scripts/check_migrations.py#L15-L28) | ถ้าใช้ ORM/migrations ให้มีคำสั่งตรวจ model กับ migration; ต้องเตรียม settings/dependencies ให้ตรงแอป |
| Workflow security lint | tox เรียก `zizmor .` และมี job สำหรับมัน [local command](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/tox.ini#L118-L124), [CI job](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/.github/workflows/linters.yml#L73-L85) | คุ้มพิจารณาเมื่อ AI แก้ workflows ด้วย การ lint Python อย่างเดียวไม่ครอบคลุม YAML ของ CI |
| Warning policy ของ test runner | ยกระดับ warning บาง class รวม deprecation/runtime/resource เป็น error [filters](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/tests/runtests.py#L48-L54) | เลือก category ที่มีความหมายต่อโครงการก่อน ทั้งนี้ warning ใน cleanup/destructor อาจมีเส้นทางรายงานต่างจาก exception ปกติ |

**เส้นทางเรียกจริง:** [linters workflow](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/.github/workflows/linters.yml#L20-L85) เรียก formatter/import/lint jobs; migration workflow มี [PR path filters](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/.github/workflows/check-migrations.yml#L1-L12) และ [ขั้นเรียก checker](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/.github/workflows/check-migrations.yml#L44-L68); tests workflow [เรียก runtests.py](https://github.com/django/django/blob/2b30f6255b5ef84afbd827993643d52ef2c0963a/.github/workflows/tests.yml#L20-L74)

**โจทย์เริ่มเรียน:** เพิ่ม field ใน model ของแอปสมมุติ แล้วอธิบายว่า checker ต้องเทียบอะไรกับ migration ที่มีอยู่ การตรวจว่า migration ขาดแยกจากการพิสูจน์ว่า migrate ฐานข้อมูลจริงแล้วปลอดภัย ขอบเขตที่พบใน Django คือ test apps ของโครงการนี้

<a id="fastapi"></a>

### 9.6 FastAPI — strict checks พร้อมตัวอย่างที่เป็นเพียง diagnostic

**แหล่งต้นทาง:** `fastapi/fastapi` · [snapshot 50113da16fec](https://github.com/fastapi/fastapi/commit/50113da16fec53b66b80d75e80a89296de4fa5a5) · commit 1 กันยายน 2026

| กฎหรือกลไกที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| Ruff พร้อม exit หลัง auto-fix | hook ใช้ `--exit-non-zero-on-fix` และ `--exit-non-zero-on-format` [hooks](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/.pre-commit-config.yaml#L23-L37); เลือกกลุ่มกฎและ exceptions ใน [config](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/pyproject.toml#L265-L310) | ให้ local tool ช่วยแก้ได้ แต่รู้ว่าการรันนั้นเปลี่ยนไฟล์และควรดู diff; เริ่มจาก check mode ได้ |
| Type checking พร้อม scope ชัด | mypy strict มี module overrides; mypy/ty hooks ไม่รับเฉพาะ filenames จาก hook และ ty ยกระดับ warning [mypy](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/pyproject.toml#L202-L220), [hooks](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/.pre-commit-config.yaml#L39-L51), [ty](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/pyproject.toml#L363-L400) | เริ่มจาก checker หนึ่งตัวและ package สำคัญก่อน; การมีสองตัวเป็นทางเลือกของโครงการนี้ |
| Strict test configuration | strict config/markers/xfail และ warnings-as-errors ใน [pytest config](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/pyproject.toml#L222-L233) | จับ marker สะกดผิดและผล xfail ที่เปลี่ยนไป ให้ความสำคัญกับ test ที่ถูกรันตามเจตนา |
| ตรวจ regression test กับ base revision | เก็บ test patch แล้วทดสอบกับ base; ถ้า base ยังผ่านจะเขียน warning/summary [implementation](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/.github/workflows/test.yml#L200-L268) | มีประโยชน์เมื่อ AI เพิ่ม test ให้ bug fix แต่กรณี base ผ่านใน source นี้เป็น diagnostic ไม่ได้ทำให้ job fail |

**เส้นทางเรียกจริง:** [scripts/lint.sh](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/scripts/lint.sh#L1-L9) แสดงคำสั่ง local; [pre-commit workflow](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/.github/workflows/pre-commit.yml#L52-L91) รัน prek บน diff และมีขั้น fail ตามผลตรวจ เส้นทางนี้มีการ auto-format/commit สำหรับ PR บางประเภทด้วย จึงไม่ใช่ตัวอย่างของ check-only workflow ทุกขั้น

**สิ่งที่ควรดูเมื่อทำ library:** CI ทดสอบ [dependency resolutions/รุ่นต่าง ๆ](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/.github/workflows/test.yml#L47-L149), มี [coverage threshold 100](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/.github/workflows/test.yml#L270-L312) และ [job รวมผล](https://github.com/fastapi/fastapi/blob/50113da16fec53b66b80d75e80a89296de4fa5a5/.github/workflows/test.yml#L313-L332) สิ่งเหล่านี้เป็นตัวเลือกต้นทุนสูงขึ้นสำหรับ compatibility; ตัวเลข coverage ไม่บอกว่า assertion ครบ requirement

**โจทย์เริ่มเรียน:** test ใหม่ผ่านทั้งบนโค้ดก่อนแก้และหลังแก้ บอกได้อะไรเกี่ยวกับ regression proof? ถ้าจะทำให้เป็น gate ต้องเพิ่มเงื่อนไขอะไร และจะแยกการ fail เพราะ bug ออกจาก import/dependency ที่ต่างกันอย่างไร?

<a id="pandas"></a>

### 9.7 pandas — เปลี่ยนความรู้เฉพาะโปรเจกต์เป็น lint

**แหล่งต้นทาง:** `pandas-dev/pandas` · [snapshot 14de06cf2823](https://github.com/pandas-dev/pandas/commit/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d) · commit 12 กันยายน 2026

**ระดับหลักฐานของการ์ดนี้:** พบ config, local hooks และ script ที่รายงาน failure ได้ แต่ยังเชื่อม hooks เหล่านี้ไปยัง workflow ที่เรียกโดยตรงไม่ได้จาก snapshot ที่ตรวจ จึงระบุว่า **กำหนดกฎและมีคำสั่ง; CI binding ของ hooks ยังไม่ยืนยัน** การมีส่วนตั้งค่า provider ใน pre-commit config ไม่พอจะสรุปสถานะจริงของบริการนั้น

| กฎหรือกลไกที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| Banned APIs พร้อม API ทดแทน | ห้ามบางการใช้ URL, warning helper, NumPy testing และ filesystem ตามนโยบาย [banned-api config](https://github.com/pandas-dev/pandas/blob/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d/pyproject.toml#L406-L423) | เริ่มจาก API ที่มี wrapper และเหตุผลจริง เช่น timeout/logging; อย่าคัดลอกรายชื่อห้ามโดยไม่มี wrapper |
| เวลาทดสอบคงที่และ private boundaries | มี hooks สำหรับ current-time patterns และ AST checker ของ private calls/imports [hooks](https://github.com/pandas-dev/pandas/blob/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d/.pre-commit-config.yaml#L215-L281), [AST logic](https://github.com/pandas-dev/pandas/blob/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d/scripts/validate_unwanted_patterns.py#L91-L167) | ใช้ fixed time หรือ clock ที่ควบคุมได้ใน test; test ที่ตั้งใจทดสอบ “เวลาปัจจุบัน” ต้องมี exception เฉพาะ |
| Test naming/discovery guard | hook เรียก checker ที่ตรวจชื่อ function/class และมีข้อยกเว้นสำหรับสิ่งที่ไม่ใช่ test [hook](https://github.com/pandas-dev/pandas/blob/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d/.pre-commit-config.yaml#L323-L334), [checker](https://github.com/pandas-dev/pandas/blob/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d/scripts/check_test_naming.py#L53-L96) | น่าสนใจเมื่อ AI เพิ่ม test แต่ตั้งชื่อจน runner ไม่เก็บ; แยก helper functions ให้ชัดเพื่อลด false positives |
| Error catalog และตำแหน่งนิยาม | hooks ตรวจ errors/docs และตำแหน่ง exception; script หา missing แล้ว exit 1 [hooks](https://github.com/pandas-dev/pandas/blob/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d/.pre-commit-config.yaml#L290-L322), [documentation checker](https://github.com/pandas-dev/pandas/blob/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d/scripts/pandas_errors_documented.py#L21-L52), [location checker](https://github.com/pandas-dev/pandas/blob/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d/scripts/validate_exception_location.py#L73-L88) | คุ้มเมื่อแอปมี public error codes/API contract ที่ต้องรักษา; script เล็กอาจยังไม่ต้องมี catalog |

**เส้นทาง local ที่เห็น:** [Ruff hooks](https://github.com/pandas-dev/pandas/blob/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d/.pre-commit-config.yaml#L21-L35) และ custom hook entries ระบุคำสั่งและ file filters; [AST checker exit path](https://github.com/pandas-dev/pandas/blob/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d/scripts/validate_unwanted_patterns.py#L501-L578) ทำให้พบ violation แล้วคืน failure ส่วน [code-checks workflow](https://github.com/pandas-dev/pandas/blob/14de06cf28232d7b5cc2b1a2b58fbc59a815db2d/.github/workflows/code-checks.yml#L19-L90) เป็นหลักฐานของ jobs ที่มันเรียกเอง ไม่ใช่หลักฐานโดยอัตโนมัติว่า pre-commit hooks ทั้งหมดรัน

**โจทย์เริ่มเรียน:** “ทุก test ใช้เวลาคงที่” เป็นกฎที่กว้างไปอย่างไร? ออกแบบ exception สำหรับ test ของ current-time API แล้วบอกว่าทำไม regex อาจไม่พอสำหรับ aliases หรือ calls ที่ซับซ้อน

<a id="ruff"></a>

### 9.8 Ruff — บังคับ abstraction และตรวจ output ที่สร้างขึ้น

**แหล่งต้นทาง:** `astral-sh/ruff` · [snapshot 15f3fe6b15a5](https://github.com/astral-sh/ruff/commit/15f3fe6b15a5f00172f34b0f542f8ea277f5a586) · commit 12 กันยายน 2026 · repository นี้มี Rust และส่วนที่เกี่ยวกับ ty ด้วย

| กฎหรือกลไกที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| ใช้ System abstraction ใน ty crates | รายชื่อ disallowed methods ของ environment/filesystem มีข้อความแนะนำ abstraction [clippy.toml](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/clippy.toml#L28-L43); crate เปิดกฎเอง [ty_python_core](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/crates/ty_python_core/src/lib.rs#L1-L4) | ใช้ควบคุม clock/filesystem/network ให้ผ่าน interface ที่ทดสอบได้ ต้องมี seam ชัดก่อนตั้งข้อห้าม |
| Warnings กลายเป็น CI failure | CI เรียก Clippy พร้อม `-D warnings` [command](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/.github/workflows/ci.yaml#L311-L331) | อ่าน policy ร่วมกับ crate overrides และคำสั่งจริง; ไม่สรุปจากคำว่า warn บรรทัดเดียว |
| Regenerate แล้ว repository ต้องสะอาด | job เรียก generators แล้วตรวจ `git status --porcelain`; จากนั้นตรวจ scaffolding ด้วย compiler [steps](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/.github/workflows/ci.yaml#L631-L665) | ใช้เมื่อมี schema/generated source; clean checkout และ output ที่ deterministic สำคัญต่อความน่าเชื่อถือ |
| จัดลำดับ hooks และตรวจ CI config | แบ่ง priority ของ validation/fix/format; actionlint อยู่ manual stage [priorities](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/.pre-commit-config.yaml#L22-L45), [workflow checkers](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/.pre-commit-config.yaml#L63-L97), [format priority](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/.pre-commit-config.yaml#L130-L162) | รักษา local loop ให้สั้น แล้วให้ CI รัน slow checks; ความช้าต้องวัดกับโครงการของตน |

**รายละเอียด scope ที่สำคัญ:** workspace ตั้ง `disallowed_methods` เป็น allow แล้วบาง crate เปิด warn เอง [workspace setting](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/Cargo.toml#L239-L243) ดังนั้นรายการ disallowed ในไฟล์นโยบายไม่ได้หมายความว่าห้ามทั้ง repository ทุกแห่ง

**เส้นทาง CI และข้อยกเว้น:** [prek step](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/.github/workflows/ci.yaml#L939-L967) รัน all-files/manual และรักษาผลคำสั่งเดิมผ่าน pipeline; [aggregator](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/.github/workflows/ci.yaml#L1400-L1423) รวม jobs และยอม success/skipped การมีชื่อ required-checks-passed ยังไม่ยืนยัน GitHub settings นอกจากนี้ [annotation step](https://github.com/astral-sh/ruff/blob/15f3fe6b15a5f00172f34b0f542f8ea277f5a586/.github/workflows/ci.yaml#L399-L406) ใช้ `|| true` จึงต้องแยกบทบาทจากขั้นที่บังคับ fail

**โจทย์เริ่มเรียน:** ถ้าโค้ดส่วน core ใช้ filesystem ผ่าน interface แต่ test helper ใช้ raw filesystem ได้ จะวาง rule ที่ scope ใด และทำให้ diagnostic บอกวิธีแก้ได้อย่างไร?

<a id="kubernetes"></a>

### 9.9 Kubernetes — verify คู่กับ update และการแยก hints

**แหล่งต้นทาง:** `kubernetes/kubernetes` · [snapshot d5cbb79be916](https://github.com/kubernetes/kubernetes/commit/d5cbb79be9160faa3a7d7323e3294c3781c16ae7) · commit 12 กันยายน 2026; CI อีก repository คือ [kubernetes/test-infra, ede7b4673225](https://github.com/kubernetes/test-infra/commit/ede7b4673225b2469b47a072aa3ebaaa5b6392c5) · commit 11 กันยายน 2026

| กฎหรือกลไกที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| Generated drift ใน worktree ชั่วคราว | helper ตรวจ clean tree, สร้าง worktree จาก HEAD, รัน generator และใช้ git status ตรวจการเปลี่ยน ถ้ามีคืน 1 [helper](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/hack/lib/verify-generated.sh#L22-L61); codegen ระบุ update command [entry point](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/hack/verify-codegen.sh#L17-L29) | ให้ generator สำคัญมี verify คู่กับ update พร้อมคำสั่งแก้ที่บอกใน error; เวลารันขึ้นกับ generator |
| Import restrictions | YAML กำหนด base package, allowed imports และ ignored subtrees [policy](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/staging/publishing/import-restrictions.yaml#L1-L24); script build/importverifier และเรียกตรวจ [command](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/hack/verify-imports.sh#L17-L33) | ยืม allowlist เฉพาะ package สำคัญ เพื่อให้ public/domain layer ไม่พึ่ง implementation โดยไม่ตั้งใจ |
| Pin ShellCheck และแยก strict lint จาก hints | ShellCheck มี version/image และ disabled rules ชัด [settings](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/hack/verify-shellcheck.sh#L17-L45); Go lint config อธิบายชุดหลักกับ hints [policy](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/hack/golangci.yaml#L1-L24) | ให้กฎที่เชื่อถือและตกลงแล้วเป็น gate; กฎที่ยังต้องใช้ดุลยพินิจเก็บเป็นคำแนะนำจนพร้อม |

**เส้นทางเรียกจริง:** [make verify](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/build/root/Makefile#L115-L137) → [dispatcher ของ verify scripts](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/hack/make-rules/verify.sh#L235-L251) ส่วน [Prow presubmit](https://github.com/kubernetes/test-infra/blob/ede7b4673225b2469b47a072aa3ebaaa5b6392c5/config/jobs/kubernetes/sig-testing/verify.yaml#L1-L26) เรียก [verify-dockerized.sh](https://github.com/kubernetes/kubernetes/blob/d5cbb79be9160faa3a7d7323e3294c3781c16ae7/hack/jenkins/verify-dockerized.sh#L33-L47) ซึ่งเรียก make verify

**ข้อยกเว้นที่เป็นหลักฐานชัด:** [hints presubmit](https://github.com/kubernetes/test-infra/blob/ede7b4673225b2469b47a072aa3ebaaa5b6392c5/config/jobs/kubernetes/sig-testing/verify.yaml#L47-L71) มี `optional: true` และเรียก targeted hints check นี่แสดงการเลือกว่าบางผลไม่จำเป็นต้องขวางงาน ส่วนสถานะ required merge ของ strict presubmit ยังไม่ยืนยันจากการตั้งค่ารับงานจริง

**โจทย์เริ่มเรียน:** source/schema เปลี่ยนแล้ว generator สร้างไฟล์ใหม่เพิ่มหนึ่งไฟล์ การเทียบเฉพาะ tracked diff จะเห็นอะไรต่างจาก git status? ถ้า generator ใส่เวลาปัจจุบันใน output จะทำให้ check นี้น่าเชื่อถือได้อย่างไร?

<a id="moby"></a>

### 9.10 Moby — ข้อห้าม API พร้อม wrapper และ API schema ที่ตรงกัน

**แหล่งต้นทาง:** `moby/moby` · [snapshot 5540cd0b7bb8](https://github.com/moby/moby/commit/5540cd0b7bb811d8a25701b716fe0dbce0051c8b) · commit 12 กันยายน 2026

| กฎหรือกลไกที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| `depguard` + `forbidigo` | dependency deny list มี replacement เช่น assertion library ที่ทีมเลือก; API restrictions กำหนด atomic/regexp/netlink wrapper [dependencies](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/.golangci.yml#L57-L73), [APIs](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/.golangci.yml#L101-L118) | คุ้มเมื่อทีมรู้ปัญหาของ raw API และมี wrapper แก้แล้ว เช่น retry/error handling; ให้ diagnostic บอก replacement |
| Diff-scoped package isolation | script เลือกไฟล์ Go ภายใต้ pkg ที่อยู่ใน diff แล้วดู dependencies; ตัด prefix ที่อนุญาตก่อน fail รายการที่เหลือ [script](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/hack/validate/pkg-imports#L7-L37) | ตัวอย่างลดเวลาตรวจด้วย diff scope แต่ต้องยอมรับว่า indirect change นอก scope อาจไม่ trigger |
| Swagger spec กับ generated output | validator rerun generator ใน temporary directory แล้ว diff generated files [script](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/api/scripts/validate-swagger-gen.sh#L11-L50); แยก schema check จาก output check [targets](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/api/Makefile#L54-L60) | ถ้ามี API schema/client ที่ commit คู่กัน ให้ตรวจทั้ง schema ใช้ได้และ output ตรง source |

**เส้นทางเรียกจริง:** [golangci wrapper](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/hack/validate/golangci-lint#L18-L31) เดิน modules และระบุ config → [make validate targets](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/Makefile#L244-L256) → [CI validation matrix](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/.github/workflows/test.yml#L134-L207) ที่สร้าง jobs จาก scripts; API มี [Swagger job](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/.github/workflows/test.yml#L209-L226) เรียกสอง targets ใน directory api

**รายละเอียดที่ควรอ่านแทนเดาจากชื่อ:** pkg-imports ตัด `github.com/moby/moby/v2/pkg/`, `vendor` และ `internal` ออกก่อนหา Moby dependencies ที่ต้องห้าม จึงไม่ใช่กฎ “ห้ามทุก path ที่มีคำว่า internal” ตัวอย่าง path ฝ่าฝืนต้องอยู่นอก prefixes ที่มันอนุญาต นอกจากนี้ [enabled/disabled list](https://github.com/moby/moby/blob/5540cd0b7bb811d8a25701b716fe0dbce0051c8b/.golangci.yml#L14-L55) มี override บางตัว จึงต้องอ่านทั้งสองส่วน

**โจทย์เริ่มเรียน:** AI เรียก raw network API ที่ compile ได้และ test ปกติผ่าน แต่ wrapper ของโครงการจัดการ interrupted calls เพิ่ม จะเขียน rule และ diagnostic ให้มันกลับมาใช้ wrapper อย่างไร?

<a id="rust"></a>

### 9.11 Rust compiler — tidy สำหรับกฎที่ไม่ใช่ lint ของภาษาอย่างเดียว

**แหล่งต้นทาง:** `rust-lang/rust` · [snapshot 67e8d9d65f33](https://github.com/rust-lang/rust/commit/67e8d9d65f33118199f9749343782cc287426587) · commit 13 กันยายน 2026

| กฎหรือกลไกที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| Tidy aggregator | รวม checks ของ metadata/dependencies/test placement/error codes/style และออกด้วย failure เมื่อมี check ล้ม [dispatch](https://github.com/rust-lang/rust/blob/67e8d9d65f33118199f9749343782cc287426587/src/tools/tidy/src/main.rs#L89-L145), [exit path](https://github.com/rust-lang/rust/blob/67e8d9d65f33118199f9749343782cc287426587/src/tools/tidy/src/main.rs#L167-L184) | เริ่มจาก script เล็กของ invariant ที่เครื่องมือสำเร็จรูปยังไม่มี แล้วรวมใต้ verify เดียวเมื่อมีหลายตัว |
| Dependency source policy | extdeps ตรวจ Cargo.lock และ reject source ที่ไม่อยู่ใน allowlist; มีรายชื่อ dependency ที่ต้องพิจารณาก่อนเพิ่ม [checker](https://github.com/rust-lang/rust/blob/67e8d9d65f33118199f9749343782cc287426587/src/tools/tidy/src/extdeps.rs#L1-L53), [permitted dependencies](https://github.com/rust-lang/rust/blob/67e8d9d65f33118199f9749343782cc287426587/src/tools/tidy/src/deps.rs#L288-L300) | ให้ dependency ใหม่เป็นการเปลี่ยนที่ตรวจเห็นได้; ใช้เครื่องมือทั่วไปก่อนสร้าง checker แบบ compiler project |
| Lockfile line endings | script ตรวจ CR ใน lockfiles สอง path แล้ว exit 1 [script](https://github.com/rust-lang/rust/blob/67e8d9d65f33118199f9749343782cc287426587/src/ci/scripts/verify-line-endings.sh#L16-L24) | ตัวอย่างกฎเล็กที่ระบุขอบเขตชัด เหมาะเมื่อเกิด diff ข้าม platform จริง |

**เส้นทางเรียกจริง:** [คำสั่ง local ของ tidy](https://github.com/rust-lang/rust/blob/67e8d9d65f33118199f9749343782cc287426587/src/tools/tidy/src/main.rs#L1-L6) คือ `./x.py test tidy`; [CI image](https://github.com/rust-lang/rust/blob/67e8d9d65f33118199f9749343782cc287426587/src/ci/docker/host-x86_64/test-tidy/Dockerfile#L34-L37) ระบุคำสั่ง tidy/self-tests และ extra checks ส่วน [line-ending workflow step](https://github.com/rust-lang/rust/blob/67e8d9d65f33118199f9749343782cc287426587/.github/workflows/ci.yml#L198-L207) เรียก script โดยตรง

**ข้อแตกต่างระหว่าง PR กับ Auto CI:** [jobs configuration](https://github.com/rust-lang/rust/blob/67e8d9d65f33118199f9749343782cc287426587/src/ci/github-actions/jobs.yml#L111-L128) ตั้ง PR test-tidy เป็น `continue_on_error: true` และอธิบายว่าการสร้าง Auto job override เป็น false ดังนั้น source นี้ไม่รองรับคำกล่าวว่า tidy failure บล็อกทุก PR ในทุกช่องทาง ต้องอ่านชนิด job และนโยบายรับงานที่เกี่ยวข้อง

**โจทย์เริ่มเรียน:** rule ตรวจรายชื่อ error codes ควรอยู่ใน language linter หรือ script อ่าน metadata? ถ้าตรวจพบผิดแต่ PR job ยอมให้ล้ม จะออกแบบเส้นทางรับงานของตนอย่างไร?

<a id="tokio"></a>

### 9.12 Tokio — compiler configuration และ compatibility floor

**แหล่งต้นทาง:** `tokio-rs/tokio` · [snapshot 0469d47fcc89](https://github.com/tokio-rs/tokio/commit/0469d47fcc891a7e1e7339c9bcb0fdd27eab47df) · commit 13 กันยายน 2026

| กฎหรือกลไกที่พบ | ความผิดที่จับและหลักฐาน | วิธีประยุกต์สำหรับ solo |
|---|---|---|
| cfg policy + compiler warnings + Clippy | workspace กำหนด unexpected_cfgs และ crate สืบทอด; CI ใช้ `-Dwarnings` [workspace](https://github.com/tokio-rs/tokio/blob/0469d47fcc891a7e1e7339c9bcb0fdd27eab47df/Cargo.toml#L25-L39), [inheritance](https://github.com/tokio-rs/tokio/blob/0469d47fcc891a7e1e7339c9bcb0fdd27eab47df/tokio/Cargo.toml#L202-L203), [CI env](https://github.com/tokio-rs/tokio/blob/0469d47fcc891a7e1e7339c9bcb0fdd27eab47df/.github/workflows/ci.yml#L13-L36) | จับ cfg สะกดผิดหรือ warning ใน scope ที่ compile; pin toolchain และดู override ของแต่ละ job |
| Dependency audit policy | cargo-deny config กำหนด license allowlist, deny wildcard/unknown registry/git และ allow multiple versions [policy](https://github.com/tokio-rs/tokio/blob/0469d47fcc891a7e1e7339c9bcb0fdd27eab47df/deny.toml#L3-L21) | เลือก dependency policy ตามงานของตน รวม transitive metadata; อย่าสรุปว่า config นี้ห้ามทุก duplicate version |
| Minimum compiler/dependency checks | CI มี minrust และ minimal-versions jobs ที่ตรวจ compilation ด้วย feature combinations [minrust](https://github.com/tokio-rs/tokio/blob/0469d47fcc891a7e1e7339c9bcb0fdd27eab47df/.github/workflows/ci.yml#L768-L795), [minimal versions](https://github.com/tokio-rs/tokio/blob/0469d47fcc891a7e1e7339c9bcb0fdd27eab47df/.github/workflows/ci.yml#L797-L829) | มีประโยชน์มากขึ้นเมื่อทำ library ที่ประกาศ support หลายรุ่น; app ที่ deploy runtime เดียวอาจเริ่มจาก target นั้นก่อน |

**เส้นทางเรียกจริง:** [fmt/Clippy jobs](https://github.com/tokio-rs/tokio/blob/0469d47fcc891a7e1e7339c9bcb0fdd27eab47df/.github/workflows/ci.yml#L831-L881) ระบุคำสั่งและ feature flags; [PR audit](https://github.com/tokio-rs/tokio/blob/0469d47fcc891a7e1e7339c9bcb0fdd27eab47df/.github/workflows/pr-audit.yml#L1-L23) เรียก cargo-deny action เมื่อ Cargo.toml ใน scope เปลี่ยน และมี [audit workflow ตามเวลา/push](https://github.com/tokio-rs/tokio/blob/0469d47fcc891a7e1e7339c9bcb0fdd27eab47df/.github/workflows/audit.yml#L1-L24) เพิ่มอีกทาง

**ขอบเขตที่ควรจำ:** compatibility compilation เป็นคนละหลักฐานกับ runtime behavior; audit action ใน snapshot อ้าง mutable tag `@v2` จึงไม่ได้ตรึง implementation ของ action ด้วย SHA ใน workflow นั้น และการพบ scheduled job ไม่เท่ากับได้ยืนยันการบล็อก merge

**โจทย์เริ่มเรียน:** AI ใช้ API ที่มีใน dependency ใหม่สุด แต่โปรเจกต์ประกาศรองรับรุ่นเก่า จะตรวจด้วย unit test บน dependency ใหม่ชุดเดียวพอหรือไม่? อะไรคือ compatibility floor ที่คุ้มรักษาสำหรับงานของตน?

<a id="source-notes"></a>

## 10. ขอบเขตหลักฐานและการนำไปใช้ครั้งถัดไป

ชุดข้อมูลนี้เลือกโปรเจกต์ที่มีระบบตรวจหลายชั้นและมี source สาธารณะให้ไล่เส้นทางได้ ใช้ repository config, checker implementation, scripts และ workflow definitions เป็นหลัก แหล่งเครื่องมือใช้เอกสารของผู้สร้างโดยตรง บทความสรุปของบุคคลภายนอกไม่ได้ใช้ยืนยันว่า repository เปิดกฎใด

การ์ดเป็นภาพของ commit ที่ระบุ ไม่ใช่คำยืนยันว่าทุกกฎยังเหมือนเดิมหลังวันที่ตรวจ ลิงก์ตรึง SHA ช่วยกลับไปอ่านหลักฐานเดิมได้ หากจะนำ config ไปใช้จริง ให้ตรวจ version และ config format ที่โปรเจกต์ตนติดตั้งอีกครั้ง พร้อมทำตัวอย่างผิด/ถูกของตน

**ส่วนที่เป็นข้อเท็จจริงจาก source:** ชื่อกฎ, file scope, severity/options, คำสั่งและทางเรียกใน CI ที่อ้างได้ ส่วนการจัดลำดับเรียน ต้นทุน ความเหมาะสมกับ solo และโจทย์ฝึกเป็นข้อเสนอที่สังเคราะห์ขึ้น ต้นทุนในตารางเป็นการประเมินเชิงคุณภาพ ไม่ใช่ benchmark

**ส่วนที่ตรวจรันแล้ว:** lab ต้นฉบับมี 12 กรณี พร้อม versions, expected/actual exit codes และ diagnostics ในรายงาน `verification.json` ของการรันครั้งนั้น รายงานที่มี path เฉพาะเครื่องไม่ได้รวมในคลังนี้ ให้รัน `npm run verify` ใน [guardrail-lab/](./guardrail-lab/) เพื่อสร้างผลปัจจุบันใหม่ ไม่ได้รัน test suite ของ 12 repositories และไม่ได้ทดลอง PR/merge ของโครงการเหล่านั้น การตรวจว่าลิงก์และช่วงบรรทัดมีอยู่ยืนยันตำแหน่งหลักฐาน ส่วนความหมายของ source ต้องอ่านร่วมกับ context/options ที่กำกับในแต่ละการ์ด

**สิ่งที่ยังต้องรู้จากโปรเจกต์ผู้เรียน:** ภาษาและ framework, โครงสร้าง module, CI/provider, รุ่น runtime, ข้อผิดพลาดซ้ำของ AI และข้อกำหนดทางธุรกิจที่สำคัญ เมื่อมีข้อมูลเหล่านี้ให้เลือกเพียงสามกฎแรก และสร้าง rule card ตามส่วน 4 ก่อนขยายชุดตรวจ

### แหล่งอ่านหลักตามหัวข้อ

| หัวข้อที่จะสอนต่อ | แหล่งแรกที่ควรเปิด | อ่านเพื่ออะไร |
|---|---|---|
| Scope, errors, exceptions ของ ESLint | [configuration](https://eslint.org/docs/latest/use/configure/configuration-files), [rules](https://eslint.org/docs/latest/use/configure/rules), [CLI](https://eslint.org/docs/latest/use/command-line-interface) | ดู effective policy และผลต่อ command |
| Async/type-aware lint | [no-floating-promises](https://typescript-eslint.io/rules/no-floating-promises/), [exhaustive switch](https://typescript-eslint.io/rules/switch-exhaustiveness-check/) | ดูข้อมูลชนิดที่ต้องใช้และ options ที่เปลี่ยนความเข้ม |
| TypeScript flags | [strict](https://www.typescriptlang.org/tsconfig/strict.html), [indexed access](https://www.typescriptlang.org/tsconfig/noUncheckedIndexedAccess.html) | แยกข้อจำกัดของ type model จาก runtime validation |
| Python lint/format | [Ruff linter](https://docs.astral.sh/ruff/linter/), [formatter](https://docs.astral.sh/ruff/formatter/) | เลือกกฎและรู้ exit behavior |
| Architecture imports | [ESLint imports](https://eslint.org/docs/latest/rules/no-restricted-imports), [dependency-cruiser rules](https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md) | เลือก string/AST/graph ตามขอบเขตปัญหา |
| CI ที่บล็อก merge | [rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets), [required checks troubleshooting](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks) | ตรวจว่าจุดรับงานอาศัยผลใดและ skip/bypass มีผลอย่างไร |
| Local feedback กับ enforcement | [Git hooks](https://git-scm.com/docs/githooks) | รู้ว่า local hook สามารถถูกข้ามได้ |

รายการ source ของ 12 โปรเจกต์อยู่ติดกับแต่ละ claim ในส่วน 9 พร้อม SHA และช่วงบรรทัด หากมีคำถามด้าน tradeoff ที่ source ตัดสินแทนไม่ได้ ให้เตรียม minimal example/version แล้วถามใน [ESLint discussions](https://github.com/eslint/eslint/discussions) หรือ [Ruff discussions](https://github.com/astral-sh/ruff/discussions) ตามเครื่องมือที่ใช้ โดยแยกประสบการณ์ของผู้ตอบออกจาก behavior ที่ตรวจยืนยันด้วยโค้ด
