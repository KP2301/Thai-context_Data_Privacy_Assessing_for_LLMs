import json

input_file = "five_hiarchy_language2.jsonl"

levels_order = ["ceremonial", "formal", "semi_formal", "informal", "casual"]

output_files = {
    level: open(f"{level}.jsonl", "w", encoding="utf-8")
    for level in levels_order
}

error_log = open("parse_errors.log", "w", encoding="utf-8")

with open(input_file, "r", encoding="utf-8") as infile:
    for idx, line in enumerate(infile, start=1):
        if not line.strip():
            error_log.write(f"[{idx}] empty line\n")
            continue

        data = json.loads(line)

        content = (
            data.get("response", {})
                .get("body", {})
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
        )

        # 🛡 parse content อย่างปลอดภัย
        try:
            levels = json.loads(content.strip())
        except Exception as e:
            error_log.write(f"[{idx}] content JSON error: {e}\n")
            levels = {}

        target = levels.get("target", "__MISSING_TARGET__")

        for level in levels_order:
            text = levels.get(level)

            if text is None:
                # ❗ fallback ไม่ให้ record หาย
                error_log.write(f"[{idx}] missing {level}\n")
                text = ""

            obj = {
                "target": target,
                "text": text
            }

            output_files[level].write(
                json.dumps(obj, ensure_ascii=False) + "\n"
            )

# ปิดไฟล์
for f in output_files.values():
    f.close()
error_log.close()

print("✔️ แยกไฟล์ครบทุกบรรทัด (no drop)")
