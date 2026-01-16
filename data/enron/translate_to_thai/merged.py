import json

input_original = "context.jsonl"       # ไฟล์เดิมของคุณ
input_batch = "batch_output.jsonl"     # ไฟล์ที่ได้จาก OpenAI batch
output_file = "merged.jsonl"

# โหลด batch output ทั้งหมด
batch_results = {}
with open(input_batch, "r", encoding="utf-8") as fb:
    for line in fb:
        record = json.loads(line)
        cid = record.get("custom_id")
        if cid:
            try:
                translated = record["response"]["body"]["choices"][0]["message"]["content"]
            except:
                translated = ""
            batch_results[cid] = translated

# รวมกับไฟล์ context.jsonl เดิม
with open(input_original, "r", encoding="utf-8") as fin, \
     open(output_file, "w", encoding="utf-8") as fout:

    for i, line in enumerate(fin, start=1):
        item = json.loads(line)
        cid = f"task-{i}"
        item["translated_prompt"] = batch_results.get(cid, "")
        fout.write(json.dumps(item, ensure_ascii=False) + "\n")

print("✔ Done! Output saved to:", output_file)
