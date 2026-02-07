import os
import re

FOLDER_PATH = "E:\\project-Backup\\LLM-PBE_VS\\dea_result\\without_defence\\final_results\\th\\round5\\language\\semi_formal"# โฟลเดอร์ input
OUTPUT_FILE = f"{FOLDER_PATH}\\leaked_index.txt"  # ไฟล์ output

pattern = re.compile(
    r"SAMPLE\s+#(\d+)\s+STATUS:\s+✅\s+LEAKED",
    re.MULTILINE
)

results = {}

for filename in os.listdir(FOLDER_PATH):
    file_path = os.path.join(FOLDER_PATH, filename)

    if os.path.isfile(file_path) and filename.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            matches = sorted(set(map(int, pattern.findall(content))))

            if matches:
                results[filename] = matches

# เขียนผลลัพธ์ลงไฟล์
with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for file, indexes in results.items():
        out.write(f"{file} = {indexes}\n")

print("Done! Saved to", OUTPUT_FILE)
