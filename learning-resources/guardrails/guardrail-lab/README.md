# Guardrail lab

ชุดทดลองสำหรับบทเรียน guardrail และ lint เขียนขึ้นใหม่เพื่อแสดงกลไก ไม่ใช่โค้ดที่คัดลอกจากโปรเจกต์ที่สำรวจ และไม่ใช่ configuration พร้อมติดตั้งในโปรเจกต์จริง

## เริ่มทดลอง

ใช้ Node.js 24 ขึ้นไปและ npm จากนั้นรันในโฟลเดอร์นี้:

```sh
npm ci --ignore-scripts
npm run verify
```

ล็อก ESLint 10.10.0, TypeScript 6.0.3 และ typescript-eslint 8.70.0 พร้อม package-lock.json ตรวจสอบครั้งแรกด้วย Node.js 26.7.0 เมื่อ 13 กันยายน 2026 รายงานผลครั้งนั้นมี path เฉพาะเครื่องและไม่ได้รวมในคลังนี้ หากต้องการผลการรันใหม่ `verify.mjs` จะสร้าง `verification.json` ในเครื่องที่รัน

`verify` เป็นตัวทดสอบ guardrails: มันคาดหวังให้ bad fixtures fail และ good fixtures pass ดังนั้นผลรวม PASS หมายถึงตัวอย่างทำงานตามที่ตั้งใจ ห้ามนำคำสั่งนี้ไปใช้แทน production CI ของแอป

## ทดลองทีละเรื่อง

| เรื่อง | คำสั่ง | ผลที่คาด |
|---|---|---|
| UI import database | `npx --no-install eslint fixtures/imports/bad.js --max-warnings 0` | exit 1, no-restricted-imports |
| UI import service | `npx --no-install eslint fixtures/imports/good.js --max-warnings 0` | exit 0 |
| เขียน disable comment | `npx --no-install eslint fixtures/imports/suppressed.js --max-warnings 0` | exit 1, กฎยังทำงาน |
| ลืม await | `npx --no-install eslint fixtures/async/bad.ts --max-warnings 0` | exit 1, no-floating-promises |
| ใช้ void กลบ | `npx --no-install eslint fixtures/async/void.ts --max-warnings 0` | exit 1 เพราะตั้ง ignoreVoid: false |
| จัดลำดับด้วย await | `npx --no-install eslint fixtures/async/good.ts --max-warnings 0` | exit 0 |
| ใช้สมาชิก array ที่อาจไม่มี | `npx --no-install tsc -p fixtures/types/bad` | exit 2, TS2532 |
| ตรวจ undefined ก่อน | `npx --no-install tsc -p fixtures/types/good` | exit 0 |
| เปิดเผย order ข้าม tenant | `LAB_VARIANT=bad node --test fixtures/behavior/contract.test.mjs` | exit 1, assertion fails |
| จำกัด tenant | `LAB_VARIANT=good node --test fixtures/behavior/contract.test.mjs` | exit 0 |
| generated output เก่า | `node fixtures/generated/check.mjs bad` | exit 1 |
| generated output ตรง source | `node fixtures/generated/check.mjs good` | exit 0 |

สองคำสั่ง LAB_VARIANT ด้านบนเป็น syntax ของ POSIX shell เช่น zsh/bash; `npm run verify` ใช้ Node ส่ง environment ให้และไม่อาศัย syntax นี้

## ขอบเขตที่ตั้งใจ

- Import example ตรวจ string ของ static import; package @app เป็นชื่อสมมุติ ไม่ได้ติดตั้งและตัวอย่างไม่ได้รัน import นั้นจริง Alias อื่นและ dynamic import อยู่นอกกฎนี้
- Async example ใช้ declaration เพื่อให้ linter อ่านชนิดข้อมูล ไม่ได้เชื่อมฐานข้อมูล `await` ไม่ยืนยันว่าการบันทึกข้อมูลมี transaction ถูกต้อง
- noInlineConfig คุ้มครองเฉพาะ config block ที่ประกาศ ผู้ที่แก้ config หรือ CI ได้ยังเปลี่ยนนโยบายได้
- Tenant test เป็นฟังก์ชันจำลองในหน่วยความจำ โปรเจกต์จริงต้องทดสอบช่องทาง API/ฐานข้อมูลที่ใช้งานจริงเพิ่ม
- Generated checker เป็นตัวอย่าง output หนึ่งไฟล์ ไม่ได้ตรวจไฟล์เกินหรือไฟล์หายทั้ง directory ของโปรเจกต์

## แหล่งอ้างอิงของกลไก

- [ESLint restricted imports](https://eslint.org/docs/latest/rules/no-restricted-imports): static import และข้อความ error แนะนำ API ทดแทน
- [ESLint configuration](https://eslint.org/docs/latest/use/configure/configuration-files): noInlineConfig
- [ESLint CLI](https://eslint.org/docs/latest/use/command-line-interface): max-warnings และ exit code
- [typescript-eslint no-floating-promises](https://typescript-eslint.io/rules/no-floating-promises/): ต้องใช้ type information; void ไม่จัดการ rejection
- [TypeScript indexed access](https://www.typescriptlang.org/tsconfig/noUncheckedIndexedAccess.html): การตรวจ undefined จาก index

หลังทดลอง ให้ลองอธิบายจากความจำว่ากฎแต่ละตัวเห็นข้อมูลอะไร และมีความผิดแบบใดที่มันมองไม่เห็น
