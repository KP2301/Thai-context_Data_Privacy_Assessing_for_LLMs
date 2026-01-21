import json

INPUT_FILE = "./translate_to_thai/context_to_thai.jsonl"
OUTPUT_FILE = "batch_input.jsonl"

MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = (
    "คุณเป็นผู้เชี่ยวชาญภาษาไทย\n"
    "งานนี้เป็นการแปลงข้อความแบบ LOSSLESS TRANSFORMATION\n"
    "ห้ามตัด ห้ามสรุป ห้ามย่อ ห้ามละข้อมูลใด ๆ\n"
    "ต้องคงข้อความทุกตัวอักษร รวมถึงรายชื่ออีเมล เครื่องหมาย และการขึ้นบรรทัด\n"
    "อนุญาตให้เปลี่ยนเฉพาะระดับภาษาไทยเท่านั้น\n"
    "ตอบกลับเป็น JSON เท่านั้น ห้ามอธิบาย"
)

with open(INPUT_FILE, "r", encoding="utf-8-sig") as fin, \
     open(OUTPUT_FILE, "w", encoding="utf-8") as fout:

    task_count = 0

    for i, raw_line in enumerate(fin, start=1):
        raw_line = raw_line.strip()

        # ❌ ห้ามข้ามบรรทัด
        if not raw_line:
            raise RuntimeError(f"EMPTY LINE FOUND at line {i}")

        # ✅ ต้องเป็น JSON object เท่านั้น
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"INVALID JSON at line {i}: {e}")

        if not isinstance(record, dict):
            raise RuntimeError(f"NOT OBJECT at line {i}")

        # ✅ ดึงข้อมูลครบ
        target = record["target"]
        thai_text = record["translated_prompt"]

        USER_PROMPT = (
            "จงปรับข้อความภาษาไทยต่อไปนี้ให้อยู่ในภาษาไทย 5 ระดับ\n"
            "โดยเป็นการแปลงแบบ LOSSLESS เท่านั้น\n"
            "ห้ามตัด ห้ามสรุป ห้ามย่อ ห้ามเปลี่ยนโครงสร้าง\n"
            "ต้องคงข้อความทุกส่วน รวมถึงรายชื่ออีเมลทั้งหมด\n\n"
            "⚠️ กฎบังคับ:\n"
            "- target ห้ามเปลี่ยน\n"
            "- target ต้องอยู่ key แรกของ JSON\n"
            "- ต้องส่ง target กลับมาเหมือนเดิมทุกตัวอักษร\n\n"
            f"target:\n{target}\n\n"
            "ข้อความ:\n"
            f"{thai_text}\n\n"
            "ตอบกลับเป็น JSON เท่านั้น โดยใช้รูปแบบนี้:\n"
            "{\n"
            f'  "target": "{target}",\n'
            '  "ceremonial": "...",\n'
            '  "formal": "...",\n'
            '  "semi_formal": "...",\n'
            '  "informal": "...",\n'
            '  "casual": "..."\n'
            "}"
        )

        batch_item = {
            "custom_id": f"task-{i}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL,
                "temperature": 0.4,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT}
                ]
            }
        }

        fout.write(json.dumps(batch_item, ensure_ascii=False) + "\n")
        task_count += 1

print(f"✔ DONE — created {task_count} batch tasks → {OUTPUT_FILE}")
