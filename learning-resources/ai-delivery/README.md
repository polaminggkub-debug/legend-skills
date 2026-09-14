# AI Delivery Learning Resources

[กลับไปยังดัชนี learning resources](../README.md)

ชุดบทเรียนภาษาไทยสำหรับฝึกสั่ง AI ให้ส่งงานซอฟต์แวร์ที่ตรวจรับได้ ตั้งแต่ issue และ scope ไปจนถึง acceptance criteria, evidence, review, merge และ post-merge learning เนื้อหาสังเคราะห์จากหลักฐานสาธารณะใน GitHub และแยกข้อเท็จจริงออกจากบทเรียนกับโจทย์สมมติไว้ในตัวเอกสาร

## เริ่มเรียน

1. เปิด [`START-HERE.html`](START-HERE.html) ด้วย browser เพื่อเรียน 8 บทแบบ offline
2. ถ้าต้องการให้ ChatGPT สอน ให้แนบ [`ai-delivery-learning-pack.md`](ai-delivery-learning-pack.md) แล้วใช้คำแนะนำต้นไฟล์
3. ใช้ [`reference/checklist.html`](reference/checklist.html) และไฟล์ใน [`templates/`](templates/) เมื่อต้องการฝึกกับ task จริง
4. รัน lab ด้วยคำสั่งต่อไปนี้จากโฟลเดอร์ `lab`:

   ```sh
   python3 verify.py
   ```

   ใช้ Python 3.9+ และ standard library เท่านั้น ไม่ต้องติดตั้ง dependency หรือใช้เครือข่าย

## ภายในชุด

- [`ai-delivery-learning-pack.md`](ai-delivery-learning-pack.md) — learning pack ฉบับ canonical สำหรับให้ ChatGPT สอน
- [`lessons/`](lessons/) — บทเรียน HTML 8 ตอน พร้อม quiz และ self-check
- [`reference/`](reference/) — glossary และ checklist สำหรับเปิดทวนหรือพิมพ์
- [`cases/`](cases/) — กรณีศึกษาและการเปรียบเทียบ workflow
- [`evidence/`](evidence/) — source register และดัชนี PR, review, checks และ repository metadata
- [`templates/`](templates/) — task brief, acceptance/evidence, review response และ merge decision
- [`exercises/`](exercises/) — โจทย์ฝึกตัดสินใจพร้อม rubric
- [`lab/`](lab/) — ตัวอย่าง Python แบบ offline ที่แสดงว่า smoke test อาจเขียวทั้งที่ contract ยังผิด
- [`MISSION.md`](MISSION.md) และ [`RESOURCES.md`](RESOURCES.md) — เป้าหมาย ข้อจำกัด และแหล่งอ่านต่อ

## ขอบเขตและที่มาของข้อมูล

ชุดนี้เป็น snapshot วันที่ 13 กันยายน 2026 มีกรณีศึกษาหลัก 10 กรณีจาก 8 repository และกรณีเปรียบเทียบเพิ่มเติม รวม 16 PR ใน 9 repository ตามดัชนีหลักฐาน บทเรียน แบบฝึกหัด และ template บางส่วนเป็นการสังเคราะห์เพื่อการเรียน ไม่ใช่ prompt ลับหรือ workflow ที่อ้างว่าทุกทีมใช้เหมือนกัน

หลักฐาน raw จาก API ไม่ได้รวมไว้ เพราะดัชนีและ URL ต้นทางเพียงพอสำหรับเปิดตรวจซ้ำ และการเปิดลิงก์ GitHub ต้องใช้อินเทอร์เน็ต ส่วนบทเรียน HTML, แบบฝึกหัด และ lab ทำงาน offline ได้ อ่าน [`evidence/README.md`](evidence/README.md) เพื่อดูความหมายและข้อจำกัดของแต่ละชุดข้อมูล

ไฟล์ `verification.json` ที่เคยอยู่ในชุดต้นฉบับเป็น snapshot ของการตรวจ ณ เครื่องและเวลาหนึ่ง ไม่ใช่ผล validation ปัจจุบันของ clone นี้ การรัน `lab/verify.py` จะสร้างผลตรวจใหม่เฉพาะเครื่องตามโค้ดที่ checkout อยู่

## ไฟล์ที่ตั้งใจไม่รวม

- ZIP ที่ซ้ำกับไฟล์ที่แตกไว้ และ learning pack สำเนาซ้ำระหว่างไฟล์เดี่ยวกับชุด lab ต้นฉบับ
- `verification.json` ที่เป็นผลรันซึ่งผูกกับเครื่องและเวลา; `lab/verify.py` จะสร้างรายงานนี้เมื่อรัน และ `.gitignore` จะไม่ให้ถูก track
- `manifest-sha256.txt` ซึ่งเป็น manifest ของชุดส่งมอบเดิม ไม่ใช่เนื้อหาการเรียน
- `.DS_Store` และ cache ของเครื่อง

ไม่มีข้อมูลรับรองหรือ auth ส่วนตัวในชุดที่คัดไว้ อีเมลและ account names ที่ปรากฏใน evidence เป็น metadata สาธารณะของแหล่งอ้างอิงตามที่บันทึกไว้ ไม่ใช่ credential
