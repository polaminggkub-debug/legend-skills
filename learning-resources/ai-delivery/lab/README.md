# Lab: test เขียวพอรับงานหรือยัง

ตัวอย่างนี้สร้างใหม่เพื่อสอน ไม่ใช่ source จาก GitHub เคสใด ใช้ Python 3.9+ standard library และทำงาน offline ไม่มี dependency เพิ่ม

## โจทย์

บริการรับคำขอ เมื่อเครือข่ายหลุด ผู้ใช้คนเดิมส่งซ้ำด้วย request key และ payload เดิม ต้องได้ id เดิมและ record เดียว Key เดิมแต่ payload ต่างต้องปฏิเสธ ลูกค้าคนอื่นใช้ key เดียวกันได้ จำนวนเงินศูนย์หรือติดลบต้องไม่เกิด record

ขอบเขต: การเรียกทีละรายการในหน่วยความจำ ไม่ครอบคลุม concurrency, restart, database transaction หรือเครือข่ายจริง

## ก่อนเปิดเฉลย

1. เขียน AC จากโจทย์อย่างน้อย 3 ข้อ
2. ดู Smoke test แล้วทำนายว่า test นี้ตรวจพบบั๊กส่งซ้ำหรือไม่
3. สร้างตาราง AC → observable → test และระบุกรณีนอกขอบเขต
4. รัน `python3 verify.py` จากโฟลเดอร์นี้

ผลคาดหวัง:

- `smoke-naive`: exit 0 แม้ implementation ยังสร้างรายการซ้ำ
- `contract-naive`: exit 1 เพราะ assertion จับปัญหาการส่งซ้ำ/payload ต่าง/amount ไม่ถูกต้อง
- `contract-fixed`: exit 0 เมื่อใช้ ContractService
- `verify.py` เองคืน exit 0 เมื่อทั้งสามสถานการณ์ให้ผลตรงที่คาด ตัวอย่างที่ตั้งใจให้ fail จึงไม่ใช่ setup พัง

## เฉลยและข้อจำกัด

`test_contract.py` เป็นเกณฑ์เชิงพฤติกรรม ส่วน `ContractService` ใน `submissions.py` เป็นตัวอย่างแก้ เฉลยไม่ได้พิสูจน์ว่าเหมาะกับ production หรือ concurrent requests ให้เขียน AC เพิ่มสำหรับการเรียกพร้อมกัน แล้วอธิบายว่าทำไม lab นี้ยังยืนยัน AC นั้นไม่ได้

`verify.py` เขียนรายงาน `verification.json` ในโฟลเดอร์นี้เพื่อช่วยอ่าน exit code และ diagnostic แยก expected assertion failure ออกจาก import/environment error รายงานนี้เป็นผลรันเฉพาะเครื่องและถูก ignore โดยชุด repository จึงไม่ใช่หลักฐานที่ commit ไว้ล่วงหน้า
