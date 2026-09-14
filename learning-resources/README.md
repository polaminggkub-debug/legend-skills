# Learning Resources

คลังบทเรียนภาษาไทย หลักฐานจากงานจริง และแบบฝึกสำหรับกลับมาเรียนด้วยตนเองหรือให้ AI ช่วยสอน คัดเก็บจากชุดการเรียนวันที่ 13–14 กันยายน 2026 โดยคงวันที่ตรวจและข้อจำกัดของหลักฐานในแต่ละชุดไว้

## เลือกเรื่องที่จะเรียน

| เรื่อง | เรียนเพื่อทำอะไรได้ | เริ่มอ่าน | หลักฐาน / แบบฝึก |
|---|---|---|---|
| AI Delivery | ตั้งเป้าหมาย แบ่งงาน เขียน AC รับ review และตัดสินใจรับงานจากหลักฐาน | [บทเรียนและ lab](ai-delivery/README.md) | กรณี GitHub, แบบฟอร์ม และ lab อยู่ในชุดเดียวกัน |
| Context Discovery | รู้ว่าควรค้น context อะไร จากไหน เมื่อไรพอเริ่มแก้ และเมื่อไรต้องค้นเพิ่ม | [บทเรียน](context-discovery/context-discovery-lessons.md) | [หลักฐานและกรณีศึกษา](context-discovery/context-discovery-references.md) |
| Task & Work Orchestration — GitHub Projects | จัด scope, dependency, parallel work, handoff และ Done ที่ผูกกับ AC/evidence | [บทเรียน GitHub Projects](task-orchestration/task-orchestration-github-projects-lessons.md) | [หลักฐานและความสามารถของ GitHub](task-orchestration/task-orchestration-github-projects-references.md) |
| Guardrails & Lint | เปลี่ยนข้อกำหนดให้เป็นการตรวจที่จับโค้ดผิดได้ และเข้าใจข้อจำกัดของ CI/merge gates | [บทเรียนและ lab](guardrails/README.md) | ตัวอย่างผิด/ถูกและ lab อยู่ในชุดเดียวกัน |

ถ้ายังไม่รู้จะเริ่มที่ไหน ให้เริ่ม AI Delivery แล้วเลือก Context Discovery เมื่อติดเรื่องหาข้อมูล, Task Orchestration เมื่อติดเรื่องจัดงาน หรือ Guardrails เมื่อต้องการให้เครื่องตรวจข้อกำหนดแทนการตามเช็กเอง

## วิธีใช้

- อ่าน Markdown บน GitHub ได้ทันที แต่ละบทเรียนมีคำสั่งตัวอย่างสำหรับให้ AI สอนต่อ
- หากเรียนกับ AI ให้เลือกหนึ่งชุดและแนบบทเรียนพร้อม reference คู่กัน ให้สอนทีละเรื่องจากงานจริงของคุณ ทำแบบฝึกก่อนเปิดแนวคำตอบ และแยกหลักฐานจริง ข้อสังเคราะห์ และสิ่งที่ยังไม่ทราบ
- เมื่อต้องการใช้บทเรียน HTML หรือรัน lab ให้ clone หรือดาวน์โหลด repository แล้วทำตาม README ของหมวดนั้น GitHub แสดง source ของ HTML; ให้เปิดไฟล์ที่ดาวน์โหลดบนเครื่องเพื่อใช้หน้าเรียน
- ผลตรวจและข้อเท็จจริงจากกรณีศึกษามีขอบเขตตามวันที่และ revision ที่เอกสารระบุ หากถามถึงความสามารถหรือสถานะปัจจุบัน ให้ตรวจแหล่งต้นทางใหม่

คำสั่งและ prompts ที่อยู่ในบทเรียนเป็นเนื้อหาสำหรับกิจกรรมการเรียน การเก็บเอกสารไว้ในคลังนี้ไม่ได้สั่งให้รันคำสั่ง เปลี่ยนสกิล หรือแก้โปรเจกต์โดยอัตโนมัติ

<a id="curation"></a>

## ขอบเขตการคัดเก็บ

เก็บบทเรียน หลักฐานอ้างอิง กรณีศึกษา templates แบบฝึก และไฟล์ที่จำเป็นต่อ lab โดยใช้ไฟล์ที่เปิดอ่านและตรวจ diff ได้ แหล่งต้นฉบับในเครื่องยังคงอยู่

| ต้นฉบับ | การจัดเก็บในคลังนี้ |
|---|---|
| `ai-delivery-learning-pack.md`, `ai-delivery-lab/`, `ai-delivery-lab.zip` | รวมเป็นหมวด AI Delivery และเก็บบทเรียนหลักเพียงสำเนาเดียว ใช้ lab ที่แตกเป็นไฟล์แทน ZIP ซ้ำ |
| `guardrails-lint-learning-pack.md`, `guardrail-lab.zip` | เก็บบทเรียนและ lab ที่แตกเป็นไฟล์ในหมวด Guardrails |
| Context Discovery สองไฟล์ | เก็บบทเรียนและ reference พร้อมกัน |
| Task Orchestration ฉบับ GitHub Projects สองไฟล์ | เก็บบทเรียนและ reference พร้อมกัน โดยแก้ลิงก์ข้ามหมวดให้ใช้งานได้หลัง clone |
| `learning-links.md` | แทนด้วยสารบัญนี้และ README ของแต่ละหมวด เพื่อใช้ลิงก์ relative แทน path บนเครื่องเดิม |
| `chris-update-summary.md` | ไม่รวม: เป็นรายงานติดตั้ง/อัปเดตเฉพาะครั้ง |
| `ssp-erp-guardrails-checklist.md` | ไม่รวม: เป็นแผนปฏิบัติงานเฉพาะโปรเจกต์ |
| Task Orchestration ฉบับ Beads เดิม | ไม่รวม: เนื้อหาวิจัยส่วนใหญ่ซ้ำกับฉบับ GitHub Projects และมี audit workflow เฉพาะเครื่อง |

ในฉบับ GitHub Projects เปลี่ยนข้อความที่เคยลิงก์ไปฉบับ Beads/local audit ให้ระบุขอบเขตนี้อย่างชัดเจน คงตารางกรณีสาธารณะ E1–E7, แหล่งอ้างอิง และป้าย Direct evidence / Reasonable inference / Unknown ไว้ ไม่ตีความ audit ที่ไม่ได้เผยแพร่ว่าเป็นหลักฐานสาธารณะ

## ความสัมพันธ์กับสกิล

ชุดนี้เก็บรายละเอียดสำหรับการเรียน ส่วนสกิลใช้งานมี reference แบบสั้นของตนเอง: [Matt](../matt/SKILL.md) และ [Chris](../chris/SKILL.md) การดาวน์โหลดคลังเรียนไม่จำเป็นต้องติดตั้งสกิลหรือเปลี่ยน tracker ที่ใช้อยู่
