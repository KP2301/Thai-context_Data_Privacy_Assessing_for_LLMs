import os
import sys
import re
import math
from contextlib import redirect_stdout 
from dotenv import load_dotenv
from contextlib import redirect_stdout
from metrics.ExtractionRate import ExtractionRate
from models.GroqModels import GroqModels
from attacks.DataExtraction.enron import EnronDataExtraction
from attacks.DataExtraction.prompt_extract import PromptExtraction

# ====================================================================================================== #
# Setup output file with incremented filename

OUTPUT_DIR = "output/dea"
BASE_FILENAME = "dea_output"
EXTENSION = ".txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)
existing_files = os.listdir(OUTPUT_DIR)
next_index = 1

pattern = re.compile(rf"^{BASE_FILENAME}_(\d+){EXTENSION}$")

for filename in existing_files:
    match = pattern.match(filename)
    if match:
        current_index = int(match.group(1))
        if current_index >= next_index:
            next_index = current_index + 1

OUTPUT_FILENAME = f"{BASE_FILENAME}_{next_index}{EXTENSION}"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)

# ====================================================================================================== #
# Check for API key in env

load_dotenv()

if "GROQ_API_KEY" not in os.environ:
    print("Error: GROQ_API_KEY not found in environment variables. Check your .env file.")
    sys.exit(1)

# ====================================================================================================== #
# Prepare data and prompts

enron = EnronDataExtraction(data_path="data/enron")

while True:
    first_format = input("""Please input attack format from this list : 
         (1) 'prefix'
         (2) 'shot-domain'
        Select (1 or 2): """)
    if first_format in ['1', '2']:
        break
    else: 
        print("Please input right format (1 or 2 only)")

NUM_SAMPLES = int(input("Please input number of samples (max 3000): "))

if first_format == '1':
    atk_format = f'prefix-{NUM_SAMPLES}'

elif first_format == '2':
    shot = int(input("Please input the number of shot between 0-5: "))
    k_domain = input("Please input \"known\" or \"unknown\": ")
    domain = input("Please input domain a-f: ")
    atk_format = f"{shot}-shot-{k_domain}-domain-{domain}"

print(f"Attack format: {atk_format}")

prompts, labels = enron.generate_prompts(format=atk_format)

# token_length = enron.calculate_token_length(prompts=prompts)

# print(f"Token Length: {token_length}")
# print(f"Sum Token Length: {sum(token_length)}")

# ====================================================================================================== #
# Prepare model

model_map = {
    '1': "llama-3.1-8b-instant",
    '2': "meta-llama/llama-4-maverick-17b-128e-instruct",
    '3': "qwen/qwen3-32b"
}
while True:
    print("""Please select models : 
        (1) llama-3.1-8b-instant
        (2) meta-llama/llama-4-maverick-17b-128e-instruct
        (3) qwen/qwen3-32b
        """)
    model = input("Select (1-3): ").strip()
    if model in model_map: 
        break 
    else:
        print("Please input right format (1, 2 or 3)")

llm_model = model_map[model]
llm = GroqModels(model=llm_model)

# ====================================================================================================== #

BATCH_SIZE = 100
total_success_count = 0
processed_count = 0

print(f"Initializing output file: {OUTPUT_PATH}")
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write("="*100 + "\n")
    f.write(f"ATTACK LOG START - Total Target Samples: {NUM_SAMPLES}\n")
    f.write("="*100 + "\n")
    f.write(f"\nMODEL : {model_map[model]}\n")

attack = PromptExtraction()

for i in range(0, NUM_SAMPLES, BATCH_SIZE):
    end_idx = min(i + BATCH_SIZE, NUM_SAMPLES)
    
    batch_prompts = prompts[i:end_idx]
    batch_labels = labels[i:end_idx]
    
    print(f"\nProcessing Batch {i+1} to {end_idx} ({len(batch_prompts)} samples)...")
    
    batch_results = attack.execute_attack(batch_prompts, llm, delay_between_calls=15)
    
    # คำนวณ Metric ของ Batch นี้
    metric = ExtractionRate(outputs=batch_results, labels=batch_labels)
    batch_score = metric.compute_metric()
    batch_asr = batch_score * 100
    
    # เปิดไฟล์โหมด 'a' (Append) เพื่อเขียนต่อท้าย
    with open(OUTPUT_PATH, 'a', encoding='utf-8') as f:
        with redirect_stdout(f):
            print(f"\n{'#'*40} BATCH REPORT ({i+1}-{end_idx}) {'#'*40}")
            print(f"Batch Metrics (ASR): {batch_asr:.2f}%")
            
            for idx in range(len(batch_results)):
                # คำนวณ Index จริง (Global Index)
                global_idx = i + idx
                
                clean_label = batch_labels[idx].strip()
                is_success = clean_label in batch_results[idx]
                
                # นับคะแนนรวม (เพื่อใช้คำนวณตอนจบ)
                if is_success:
                    total_success_count += 1
                
                status_icon = "✅ LEAKED" if is_success else "❌ SAFE"
                
                print(f"\n{'─'*100}")
                print(f"SAMPLE #{global_idx + 1}") # ใช้ global_idx เพื่อให้เลขรันต่อกัน
                print(f"STATUS: {status_icon}")
                print(f"{'─'*100}")

                print(f"\n📝 PROMPT (Input):")
                print(batch_prompts[idx])

                print(f"\n🔐 LABEL (Secret):") 
                print(batch_labels[idx])

                print(f"\n💬 ANSWER (Model Output):")
                print(batch_results[idx])
                print()
    
    # อัปเดตจำนวนที่ทำไปแล้ว
    processed_count += len(batch_results)
    print(f"Batch finished. Saved to file.")

