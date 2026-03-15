# defences

โฟลเดอร์นี้เก็บเครื่องมือและสคริปต์สำหรับป้องกันการโจมตี (defenses) โดยเฉพาะการล้างคำ (scrubbing) และ defensive prompts

## โครงสร้างหลัก
- `scrubbing_dea.py` - ฟังก์ชันสำหรับลบ/ปิดบังคำสำคัญในพรอมต์ DEA
- `scrubbing_ja.py` / `scrubbing_ja_eng.py` - ฟังก์ชันสำหรับล้างคำ/ตัวอย่างในโจมตี Jailbreak
- `defensive_prompt/` - ชุด JSON ของ system prompts ที่จะถูกนำไปใช้เป็น defensive prompt

## การใช้งาน
1. สร้างหรือแก้ไข defensive prompt ในโฟลเดอร์ `defensive_prompt/`
2. ใช้ `dea_with_dp.py` หรือ `ja_with_dp.py` เพื่อรันโจมตีพร้อม defensive prompt
3. ปรับแต่งสคริปต์ `scrubbing_*.py` หากต้องการกฎการล้างคำเพิ่มเติม

## หมายเหตุ
- การป้องกันในโฟลเดอร์นี้เป็นเพียงตัวอย่างการประยุกต์ใช้; คุณสามารถสร้างชุดการป้องกันของตัวเองได้ตามต้องการ
