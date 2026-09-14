# Guardrails learning resources

ชุดนี้เก็บเอกสารสำหรับเรียนเรื่อง guardrail, lint และการเปลี่ยนข้อกำหนดให้เป็นการตรวจที่ fail ได้

- [Guardrails และ lint สำหรับ solo developer](./guardrails-lint-learning-pack.md) — เอกสารหลักสำหรับใช้สอนและเลือกหัวข้อเรียนตามปัญหา
- [Guardrail lab](./guardrail-lab/) — ตัวอย่างที่แตกไฟล์ไว้แล้ว มี bad/good fixtures, config และคำสั่งตรวจสำหรับทดลอง fail/pass
- [ดัชนี learning resources](../README.md)

ใน lab ไม่เก็บ ZIP ซ้ำ, `node_modules` หรือ `verification.json` ที่เป็นรายงาน runtime จากเครื่องต้นฉบับ รายงานเดิมมี path เฉพาะเครื่องและถูกละไว้เพื่อให้ clone ไปใช้ได้สะอาด หากต้องการผลใหม่ ให้ติดตั้ง dependency ตาม README ของ lab แล้วรัน `npm run verify`

ไม่ได้รวม `ssp-erp-guardrails-checklist.md` เพราะเป็นแผนนำไปใช้เฉพาะ SSP ERP และไม่ได้รวม `chris-update-summary.md` เพราะเป็นรายงานการติดตั้ง skill ทั้งสองไฟล์ยังคงอยู่ในชุดไฟล์ต้นฉบับของ session เดิม
