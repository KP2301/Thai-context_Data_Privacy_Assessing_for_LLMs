import os
import sys
import re
import math
import json
from contextlib import redirect_stdout 
from dotenv import load_dotenv
from metrics.ExtractionRate import ExtractionRate
from models.GroqModels import GroqModels
from attacks.DataExtraction.enron import EnronDataExtraction
from attacks.DataExtraction.prompt_extract import PromptExtraction

# ====================================================================================================== #
# 1. SETUP OUTPUT FILE
# ====================================================================================================== #

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
# 2. CHECK API KEY
# ====================================================================================================== #

load_dotenv()

if "GROQ_API_KEY" not in os.environ:
    print("Error: GROQ_API_KEY not found in environment variables. Check your .env file.")
    sys.exit(1)

# ====================================================================================================== #
# 3. PREPARE DATA AND PROMPTS
# ====================================================================================================== #

# ✅ Verify this path matches your local folder structure
DATA_PATH = r"C:\Project\LLM-PBE_VS\data\enron"

if not os.path.exists(DATA_PATH):
    print(f"❌ Error: Data folder not found at: {DATA_PATH}")
    sys.exit(1)

enron = EnronDataExtraction(data_path=DATA_PATH)

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

# Note: We usually keep defence_mode=False here unless you want the "Simple Scrubbing" logic from Enron class
prompts, labels = enron.generate_prompts(format=atk_format)

# ====================================================================================================== #
# 4. MODEL SELECTION
# ====================================================================================================== #

model_map = {
    '1': "llama-3.1-8b-instant",
    '2': "meta-llama/llama-4-maverick-17b-128e-instruct",
    '3': "moonshotai/kimi-k2-instruct-0905"
}

# Mapping for JSON keys in defensive prompt files
json_key_map = {
    '1': "llama",
    '2': "meta",
    '3': "kimi"
}

while True:
    print("""Please select models : 
        (1) llama-3.1-8b-instant
        (2) meta-llama/llama-4-maverick-17b-128e-instruct
        (3) moonshotai/kimi-k2-instruct-0905
        """)
    model_choice = input("Select (1-3): ").strip()
    if model_choice in model_map: 
        break 
    else:
        print("Please input right format (1, 2 or 3)")

llm_model = model_map[model_choice]

# ====================================================================================================== #
# 5. DEFENSIVE PROMPT CONFIGURATION (The New Part)
# ====================================================================================================== #

use_defensive_prompt = input("Use Defensive Prompt Method? (y/n): ").strip().lower()
final_system_prompt = None
method_name = "No Defense"
defense_type_name = "N/A"

if use_defensive_prompt == 'y':
    method_name = "defensive prompt"
    
    # List of available defenses (Must match keys in defense_prompt.json)
    defense_options = [
        "defense_instruction_basic",
        "defense_instruction_strict_negative",
        "defense_refusal_aggressive",
        "defense_context_keyword",
        "defense_few_shot_examples",
        "defense_persona_dlp_officer",
        "defense_persona_dlp_ceremonial",
        "defense_persona_dlp_semiformal",
        "defense_persona_dlp_casual"
    ]
    
    print("\nSelect Defense Type:")
    for idx, opt in enumerate(defense_options):
        print(f"({idx+1}) {opt}")
    
    while True:
        try:
            def_idx = int(input(f"Select (1-{len(defense_options)}): ")) - 1
            if 0 <= def_idx < len(defense_options):
                dp_method = defense_options[def_idx]
                defense_type_name = dp_method
                break
            print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")

    # --- Load JSON Files ---
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        PROMPTS_DIR = os.path.join(current_dir, "defences", "defensive_prompt")
        
        # 1. Load Base Prompt (Thai)
        sys_prompt_path = os.path.join(PROMPTS_DIR, "system_prompts_th.json")
        if not os.path.exists(sys_prompt_path):
             # Try going up one level if running from a subdirectory
             PROMPTS_DIR = os.path.abspath(os.path.join(current_dir, "..", "defences", "defensive_prompt"))
             sys_prompt_path = os.path.join(PROMPTS_DIR, "system_prompts_th.json")

        if not os.path.exists(sys_prompt_path):
            raise FileNotFoundError(f"File not found: {sys_prompt_path}")

        with open(sys_prompt_path, "r", encoding="utf-8") as f:
            base_prompts = json.load(f)
        
        m_name_key = json_key_map[model_choice] # Map '1'->'llama', etc.
        base_system_msg = base_prompts[m_name_key]

        # 2. Load Defense Prompt
        def_prompt_path = os.path.join(PROMPTS_DIR, "defense_prompt.json")
        if not os.path.exists(def_prompt_path):
            raise FileNotFoundError(f"File not found: {def_prompt_path}")

        with open(def_prompt_path, "r", encoding="utf-8") as f:
            defense_data = json.load(f)
            defense_text = defense_data[dp_method]
        
        # 3. Combine them
        final_system_prompt = f"{base_system_msg}\n\nคำสั่งความปลอดภัย (สำคัญมาก):\n{defense_text}"
        print(f"\n✅ Defensive System Prompt Loaded: {dp_method}")

    except Exception as e:
        print(f"❌ Error loading prompts: {e}")
        sys.exit(1)

# ====================================================================================================== #
# 6. INITIALIZE LLM
# ====================================================================================================== #

# ✅ Pass the system_prompt exactly as you requested
llm = GroqModels(model=llm_model, system_prompt=final_system_prompt)

# ====================================================================================================== #
# 7. EXECUTION LOOP & LOGGING
# ====================================================================================================== #

BATCH_SIZE = 100
total_success_count = 0
processed_count = 0

print(f"Initializing output file: {OUTPUT_PATH}")
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write("="*100 + "\n")
    f.write(f"ATTACK LOG START - Total Target Samples: {NUM_SAMPLES}\n")
    f.write(f"MODEL : {llm_model}\n")
    f.write(f"METHOD: {method_name}\n")
    if method_name == "defensive prompt":
        f.write(f"DEFENSE TYPE: {defense_type_name}\n")
    f.write("="*100 + "\n")

attack = PromptExtraction()

for i in range(0, NUM_SAMPLES, BATCH_SIZE):
    end_idx = min(i + BATCH_SIZE, NUM_SAMPLES)
    
    batch_prompts = prompts[i:end_idx]
    batch_labels = labels[i:end_idx]
    
    print(f"\nProcessing Batch {i+1} to {end_idx} ({len(batch_prompts)} samples)...")
    
    batch_results = attack.execute_attack(batch_prompts, llm, delay_between_calls=15)
    
    # Calculate Metrics
    metric = ExtractionRate(outputs=batch_results, labels=batch_labels)
    batch_score = metric.compute_metric()
    batch_asr = batch_score * 100
    
    # Append to File
    with open(OUTPUT_PATH, 'a', encoding='utf-8') as f:
        with redirect_stdout(f):
            print(f"\n{'#'*40} BATCH REPORT ({i+1}-{end_idx}) {'#'*40}")
            print(f"Batch Metrics (ASR): {batch_asr:.2f}%")
            
            for idx in range(len(batch_results)):
                global_idx = i + idx
                clean_label = batch_labels[idx].strip()
                is_success = clean_label in batch_results[idx]
                
                if is_success:
                    total_success_count += 1
                
                status_icon = "✅ LEAKED" if is_success else "❌ SAFE"
                
                print(f"\n{'─'*100}")
                print(f"SAMPLE #{global_idx + 1}") 
                print(f"STATUS: {status_icon}")
                print(f"{'─'*100}")

                print(f"\n📝 PROMPT (Input):")
                print(batch_prompts[idx])

                print(f"\n🔐 LABEL (Secret):") 
                print(batch_labels[idx])

                print(f"\n💬 ANSWER (Model Output):")
                print(batch_results[idx])
                print()
    
    processed_count += len(batch_results)
    print(f"Batch finished. Saved to file.")