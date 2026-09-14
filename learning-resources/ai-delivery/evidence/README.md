# อ่านหลักฐานอย่างไร

- `case-catalog.json`: 16 PR ที่เล่าในชุด พร้อม head/merge SHA, status, จำนวนรายการและ checks
- `pr-catalog.csv`: ตารางสั้นสำหรับเทียบ cases
- `checks.csv`: checks ที่ผูกกับ head, เวลาเสร็จ และเสร็จก่อน merge หรือไม่ การผูก head ไม่ได้บอกคำสั่ง checkout ภายใน job; ดู run/checkout หากต้องรู้ test merge revision จริง
- `source-register.csv`: 227 URLs จากคำอ้างในหนังสือ รายการอาจเพิ่มเมื่อแก้หนังสือ
- `review-thread-index.csv`: ดัชนี conversation/inline/review ที่ดึงมา เพื่อเปิดอ่านต้นทาง เป็น metadata ไม่มีสำเนาเนื้อหาทั้งหมด
- `repository-screening.json`: metadata 13 repositories; contributor จำนวนหน้าแรกไม่ใช่จำนวนมนุษย์

A/B คือหลักฐานการเปิดเผย AI writing หรือ agent execution ในงานนั้น ไม่พิสูจน์สัดส่วนทุกบรรทัด C คือ workflow comparison ที่ยังไม่พอนับเป็น AI writing

จำนวน check-runs ไม่ใช่จำนวน test cases บางรายการเป็น review workflow, coverage uploader หรือ skipped และบางรายการจบหลัง merge ค่า merged_at ว่างหมายถึงยังไม่มีหลักฐานว่า merge แม้ API จะมี merge_commit_sha สำหรับการทดสอบผสาน

ไฟล์ดิบจาก API ไม่รวมในชุดนี้ เพื่อลดข้อมูลซ้ำและหลีกเลี่ยงส่งต่อ logs/config ที่ไม่จำเป็น เปิด URL ต้นทางเมื่อต้องอ่านบทสนทนาเต็ม Snapshot: 2026-09-13
