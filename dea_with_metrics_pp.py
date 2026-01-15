import os
import sys
import re
import json
import math
from contextlib import redirect_stdout 
from dotenv import load_dotenv
from contextlib import redirect_stdout
from metrics.ExtractionRate import ExtractionRate
from models.GroqModels import GroqModels
from attacks.DataExtraction.enron import EnronDataExtraction
from attacks.DataExtraction.prompt_extract import PromptExtraction

# ====================================================================================================== #
# Setup language level selection

LANGUAGE_LEVELS = {
    '1': 'ceremonial',
    '2': 'formal',
    '3': 'semi_formal',
    '4': 'informal',
    '5': 'casual'
}

# ====================================================================================================== #
# Checkpoint functions

def save_checkpoint(checkpoint_path, data):
    """บันทึกสถานะปัจจุบันลง checkpoint file"""
    # สร้าง directory ก่อนถ้ายังไม่มี
    checkpoint_dir = os.path.dirname(checkpoint_path)
    if checkpoint_dir:
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Checkpoint saved: {checkpoint_path}")

def load_checkpoint(checkpoint_path):
    """โหลดสถานะจาก checkpoint file ถ้ามี"""
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def delete_checkpoint(checkpoint_path):
    """ลบ checkpoint file เมื่อทำงานเสร็จสมบูรณ์"""
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        print(f"🗑️ Checkpoint deleted: {checkpoint_path}")

# ====================================================================================================== #
# Check for API key in env

load_dotenv()

if "GROQ_API_KEY" not in os.environ:
    print("Error: GROQ_API_KEY not found in environment variables. Check your .env file.")
    sys.exit(1)

# ====================================================================================================== #
# Setup session variables

checkpoint_data = None
RESUME_MODE = False

# ใช้ temporary checkpoint ที่ root level เพื่อให้หาเจอก่อนรู้ OUTPUT_DIR
TEMP_CHECKPOINT_PATH = "checkpoint_temp.json"

if os.path.exists(TEMP_CHECKPOINT_PATH):
    checkpoint_data = load_checkpoint(TEMP_CHECKPOINT_PATH)
    
    if checkpoint_data:
        print("\n" + "="*80)
        print("🔄 CHECKPOINT FOUND! Previous session detected.")
        print("="*80)
        print(f"Attack Format: {checkpoint_data['atk_format']}")
        print(f"Attack Format Dir: {checkpoint_data['atk_format_dir']}")
        print(f"Model: {checkpoint_data['model_name']}")
        print(f"Language Level: {checkpoint_data['language_level']}")
        print(f"Total Samples: {checkpoint_data['num_samples']}")
        print(f"Last Processed: {checkpoint_data['last_processed_index'] + 1}/{checkpoint_data['num_samples']}")
        print(f"Progress: {((checkpoint_data['last_processed_index'] + 1) / checkpoint_data['num_samples'] * 100):.1f}%")
        print("="*80)
        
        resume = input("\nDo you want to RESUME from the last checkpoint? (y/n): ").lower().strip()
        
        if resume == 'y':
            # โหลดค่าจาก checkpoint
            atk_format = checkpoint_data['atk_format']
            atk_format_dir = checkpoint_data['atk_format_dir']
            NUM_SAMPLES = checkpoint_data['num_samples']
            llm_model = checkpoint_data['model_name']
            language_level = checkpoint_data['language_level']
            start_index = checkpoint_data['last_processed_index'] + 1
            total_success_count = checkpoint_data['total_success_count']
            
            print(f"\n✅ Resuming from sample #{start_index + 1}...")
            
            # สร้าง prompts และ labels ตามฟอร์แมตเดิม (ส่ง language_level ไปด้วย)
            enron = EnronDataExtraction(data_path="data/enron", language_level=language_level)
            prompts, labels = enron.generate_prompts(format=atk_format)
            
            RESUME_MODE = True
        else:
            print("\n🔄 Starting fresh session (checkpoint will be overwritten)...\n")
            RESUME_MODE = False
            checkpoint_data = None

# ====================================================================================================== #
# Setup new session if not resuming

if not RESUME_MODE:
    # Select language level first
    while True:
        print("""Please select language level:
            (1) ceremonial
            (2) formal
            (3) semi_formal
            (4) informal
            (5) casual
            """)
        lang_choice = input("Select (1-5): ").strip()
        if lang_choice in LANGUAGE_LEVELS:
            language_level = LANGUAGE_LEVELS[lang_choice]
            break
        else:
            print("Please input right format (1-5)")
    
    # Prepare data and prompts with language level
    enron = EnronDataExtraction(data_path="data/enron", language_level=language_level)

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
        atk_format_dir = 'prefix'

    elif first_format == '2':
        shot = int(input("Please input the number of shot between 0-5: "))
        k_domain = input("Please input \"known\" or \"unknown\": ")
        domain = input("Please input domain a-f: ")
        atk_format = f"{shot}-shot-{k_domain}-domain-{domain}"
        atk_format_dir = 'shot-domain'

    print(f"Attack format: {atk_format}")
    print(f"Attack format directory: {atk_format_dir}")
    print(f"Language level: {language_level}")

    prompts, labels = enron.generate_prompts(format=atk_format)

    # Prepare model
    model_map = {
        '1': "llama-3.1-8b-instant",
        '2': "meta-llama/llama-4-maverick-17b-128e-instruct",
        '3': "moonshotai/kimi-k2-instruct-0905"
    }
    while True:
        print("""Please select models : 
            (1) llama-3.1-8b-instant
            (2) meta-llama/llama-4-maverick-17b-128e-instruct
            (3) moonshotai/kimi-k2-instruct-0905
            """)
        model = input("Select (1-3): ").strip()
        if model in model_map: 
            break 
        else:
            print("Please input right format (1, 2 or 3)")

    llm_model = model_map[model]
    
    start_index = 0
    total_success_count = 0

# ====================================================================================================== #
# Setup output directory with new structure
# Format: dea_result/(attack_format_dir)/run_2/th/(model)/(language_level)

model_short_name = llm_model.replace("/", "-").replace("meta-llama-", "")
OUTPUT_DIR = os.path.join("dea_result", atk_format_dir, "run_2", "th", model_short_name, language_level)
CHECKPOINT_PATH = os.path.join(OUTPUT_DIR, "checkpoint.json")  # เก็บ checkpoint ใน OUTPUT_DIR

# สร้าง directories
os.makedirs(OUTPUT_DIR, exist_ok=True)

EXTENSION = ".txt"

# ====================================================================================================== #
# Initialize model

llm = GroqModels(model=llm_model)

# ====================================================================================================== #
# Execute attack with checkpoint support

BATCH_SIZE = 100
processed_count = start_index

attack = PromptExtraction()

print(f"\n{'='*80}")
print(f"🚀 Starting attack from sample #{start_index + 1} to #{NUM_SAMPLES}")
print(f"Language Level: {language_level}")
print(f"Output directory: {OUTPUT_DIR}")
print(f"{'='*80}\n")

for i in range(start_index, NUM_SAMPLES, BATCH_SIZE):
    end_idx = min(i + BATCH_SIZE, NUM_SAMPLES)
    
    batch_prompts = prompts[i:end_idx]
    batch_labels = labels[i:end_idx]
    
    print(f"\nProcessing Batch {i+1} to {end_idx} ({len(batch_prompts)} samples)...")
    
    batch_results = attack.execute_attack(batch_prompts, llm, delay_between_calls=15)
    
    # ตรวจสอบว่าเจอ Daily Limit หรือไม่
    if batch_results and "ERROR_DAILY_LIMIT" in batch_results[0]:
        print("\n" + "="*80)
        print("⛔ DAILY LIMIT DETECTED - Saving checkpoint...")
        print("="*80)
        
        # บันทึก checkpoint
        checkpoint_data = {
            "atk_format": atk_format,
            "atk_format_dir": atk_format_dir,
            "num_samples": NUM_SAMPLES,
            "model_name": llm_model,
            "language_level": language_level,
            "last_processed_index": i - 1,
            "total_success_count": total_success_count
        }
        save_checkpoint(CHECKPOINT_PATH, checkpoint_data)
        
        # บันทึกสำรอง checkpoint ที่ temp location ด้วย
        save_checkpoint(TEMP_CHECKPOINT_PATH, checkpoint_data)
        
        print("\n📝 To resume:")
        print("   1. Change your GROQ_API_KEY in .env file")
        print("   2. Run this script again")
        print("   3. Choose 'y' when asked to resume\n")
        sys.exit(0)
    
    # คำนวณ Metric ของ Batch นี้
    metric = ExtractionRate(outputs=batch_results, labels=batch_labels)
    batch_score = metric.compute_metric()
    batch_asr = batch_score * 100
    
    # สร้างชื่อไฟล์สำหรับ batch นี้
    current_output_filename = f"dea_{model_short_name}_{end_idx}.txt"
    current_output_path = os.path.join(OUTPUT_DIR, current_output_filename)
    
    # เขียนผลลัพธ์ของ batch นี้ลงไฟล์
    with open(current_output_path, 'w', encoding='utf-8') as f:
        with redirect_stdout(f):
            # Header ของไฟล์
            print("="*100)
            print(f"ATTACK LOG - Batch {i+1} to {end_idx}")
            print("="*100)
            print(f"\nMODEL : {llm_model}")
            print(f"ATTACK FORMAT : {atk_format}")
            print(f"LANGUAGE LEVEL : {language_level}")
            print(f"TOTAL SAMPLES : {NUM_SAMPLES}")
            print(f"BATCH RANGE : {i+1} - {end_idx}")
            print()
            
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
    
    print(f"✅ Saved to: {current_output_path}")
    
    processed_count += len(batch_results)
    
    # บันทึก checkpoint หลังแต่ละ batch สำเร็จ
    checkpoint_data = {
        "atk_format": atk_format,
        "atk_format_dir": atk_format_dir,
        "num_samples": NUM_SAMPLES,
        "model_name": llm_model,
        "language_level": language_level,
        "last_processed_index": end_idx - 1,
        "total_success_count": total_success_count
    }
    save_checkpoint(CHECKPOINT_PATH, checkpoint_data)
    
    # บันทึกสำรอง checkpoint ที่ temp location ด้วย
    save_checkpoint(TEMP_CHECKPOINT_PATH, checkpoint_data)
    
    print(f"Batch finished. Progress: {processed_count}/{NUM_SAMPLES} ({processed_count/NUM_SAMPLES*100:.1f}%)")

# ====================================================================================================== #
# Final Summary

final_asr = (total_success_count / NUM_SAMPLES) * 100

# สร้างไฟล์ summary
summary_filename = f"dea_{model_short_name}_SUMMARY.txt"
summary_path = os.path.join(OUTPUT_DIR, summary_filename)

with open(summary_path, 'w', encoding='utf-8') as f:
    with redirect_stdout(f):
        print("="*100)
        print("FINAL SUMMARY")
        print("="*100)
        print(f"Model: {llm_model}")
        print(f"Attack Format: {atk_format}")
        print(f"Language Level: {language_level}")
        print(f"Total Samples: {NUM_SAMPLES}")
        print(f"Total Success: {total_success_count}")
        print(f"Final ASR: {final_asr:.2f}%")
        print("="*100)

print("\n" + "="*80)
print("✅ ATTACK COMPLETED SUCCESSFULLY!")
print("="*80)
print(f"Total Samples: {NUM_SAMPLES}")
print(f"Total Success: {total_success_count}")
print(f"Final ASR: {final_asr:.2f}%")
print(f"Summary saved to: {summary_path}")
print(f"All results saved in: {OUTPUT_DIR}")
print("="*80 + "\n")

# ลบ checkpoint เมื่อทำงานเสร็จสมบูรณ์
delete_checkpoint(CHECKPOINT_PATH)
delete_checkpoint(TEMP_CHECKPOINT_PATH)