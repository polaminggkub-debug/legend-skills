# AI delivery Resources

## Knowledge

- [Dyad #4187](https://github.com/dyad-sh/dyad/pull/4187)
  AI disclosure, review → patch → assertion และ checks ที่มี failure ก่อน merge ใช้สอนการเลือกหลักฐานให้ตรง requirement
- [OpenHands #8310](https://github.com/OpenHands/OpenHands/pull/8310)
  Agent invocation, การสั่งแก้ซ้ำ และ benchmark re-evaluation ใช้สอน completion criteria และ evaluation context
- [Omarchy #5423](https://github.com/omacom/omarchy/issues/5423)
  ผู้ดูแลกำหนด scope ก่อน PR ใช้ฝึก target/non-target และผลเสียของการขยาย workaround
- [Omarchy #5435 → #6093 → #6388](https://github.com/omacom/omarchy/pull/6388)
  บั๊ก install path หลัง merge, การตรวจ consumer จริง และ hardware confirmation ใช้ฝึกหลักฐานที่ตรง artifact และแยก causality
- [OpenCode #44281](https://github.com/anomalyco/opencode/pull/44281)
  Claude co-author กับการปฏิเสธ extract helper เพื่อรักษา independent test oracle ใช้สอนการประเมิน review
- [Cline #13968](https://github.com/cline/cline/pull/13968)
  Controlled reproduction, live/canonical ratio และผล CI หลัง merge ใช้ฝึกเวลาและ baseline
- [Cline #13969](https://github.com/cline/cline/pull/13969)
  Stop/Continue, pending questions และ iteration boundary ใช้สอน state lifecycle
- [Roo-Code #11409](https://github.com/RooCodeInc/Roo-Code/pull/11409)
  Storage migration, report of 10 review agents และ compatibility findings ใช้สอนขอบเขต review หลายส่วน; repo archived จึงเป็นคลังย้อนหลัง
- [Goose #11307](https://github.com/aaif-goose/goose/pull/11307)
  AI coauthor และ Codex review เรื่อง fail-fast ก่อน inference ใช้สอน temporal AC
- [LiteLLM #40785](https://github.com/BerriAI/litellm/pull/40785)
  Devin execution, integration behavior matrix และ package contract ใช้สอน review fixes
- [LiteLLM #40841](https://github.com/BerriAI/litellm/pull/40841)
  Auth/post-call decomposition, author-reported mutation/live QA และ check provenance ใช้สอน performance evidence
- [GitHub: multiple authors](https://docs.github.com/en/pull-requests/how-tos/commit-changes/creating-a-commit-with-multiple-authors)
  กลไกเครดิต co-author ใช้แยก metadata จากข้อพิสูจน์เนื้อหา
- [GitHub: required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)
  Latest SHA, head/test merge, skipped/neutral ใช้ตรวจความหมายของ checks

## Wisdom (Communities)

- [OpenHands discussions](https://github.com/OpenHands/OpenHands/discussions)
  อ่านการทดลองและขอคำแนะนำในช่องทางที่ repo เปิดไว้ เหมาะกับการออกแบบ verification ของ agent
- [OpenCode issues](https://github.com/anomalyco/opencode/issues)
  ฝึกส่ง reproduction และ expected/actual ของโปรแกรมที่ตนใช้งานจริง ตาม contribution rules ปัจจุบัน
- [LiteLLM issues](https://github.com/BerriAI/litellm/issues)
  เหมาะกับการฝึก contract/provider compatibility โดยใช้ปัญหาที่ทำซ้ำได้ ไม่จำเป็นต้องร่วมชุมชนก่อนเรียน

## Gaps

- ไม่มีหลักฐานสัดส่วน AI ต่อทั้ง repository และไม่มี prompt/session เต็มทุกทีม
- ไม่ได้รัน test suites/benchmarks ของโปรเจกต์ใหญ่ใหม่
- การตั้ง branch protection/bypass ณ เวลา merge ไม่ปรากฏครบ
- ไม่มี controlled study เรื่อง productivity/token cost หรือประสิทธิผลของจำนวน reviewers
- ผลวิจัยไม่ใช่หลักฐานว่าผู้เรียนเรียนรู้แล้ว ต้องประเมินผ่านแบบฝึกหัด
