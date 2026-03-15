# without_metric

โฟลเดอร์นี้เก็บสคริปต์สำหรับรันการโจมตีโดยไม่คำนวณ metrics (เช่น ASR)

## สคริปต์หลัก
- `dea.py` - รัน DEA โดยไม่คำนวณ metric
- `ja.py` - รัน JA โดยไม่คำนวณ metric

## การใช้งาน
1. ตั้งค่า API keys ในไฟล์ `.env`
2. รันสคริปต์ตามต้องการ:
   ```bash
   python without_metric/dea.py
   python without_metric/ja.py
   ```

## หมายเหตุ
- สคริปต์เหล่านี้ถูกออกแบบมาเพื่อทดสอบการโจมตีแบบพื้นฐานโดยไม่ต้องคำนวณและบันทึก metric
