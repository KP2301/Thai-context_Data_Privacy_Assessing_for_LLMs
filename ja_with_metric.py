import os
import time
import re
import random
import sys
import concurrent.futures
from tqdm import tqdm
from metrics.JailbreakRate import JailbreakRate 
from models.GroqModels import GroqModels
from data.jailbreakqueries_th import JailbreakQueries
# from data.jailbreakqueries import JailbreakQueries
from attacks.Jailbreak.jailbreak_th import Jailbreak
# from attacks.Jailbreak.jailbreak import Jailbreak
from dotenv import load_dotenv

load_dotenv()

if "GROQ_API_KEY" not in os.environ:
    print("Error: GROQ_API_KEY not found in environment variables. Check your .env file.")
    sys.exit(1)

MODEL_MAP = {
    "1": "llama-3.1-8b-instant",
    "2": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "3": "moonshotai/kimi-k2-instruct-0905"
}

LEVEL_LIST = ["ceremonial", "formal", "semi_formal", "informal", "casual"]

def process_single_request_with_smart_retry(args):
    llm_instance, prompt = args
    max_retries = 15
    
    for attempt in range(max_retries):
        try:
            response = llm_instance.query(prompt)
            return response
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                if attempt < max_retries - 1:
                    wait_match = re.search(r"try again in (\d+\.?\d*)s", error_msg)
                    if wait_match:
                        wait_time = float(wait_match.group(1)) + 1.5
                    else:
                        wait_time = (2 ** attempt) + random.uniform(1, 3)
                    time.sleep(wait_time)
                    continue
            return f"Error: {error_msg}"
    return "Error: Max retries exceeded (Rate Limit Stuck)"

def get_user_selection():
    print("\n" + "="*40)
    print("   🤖 AI JAILBREAK BENCHMARK MENU")
    print("="*40)
    print("\n[STEP 1] เลือก Model:")
    print("  (1) llama-3.1-8b-instant")
    print("  (2) meta-llama/llama-4-maverick-17b-128e-instruct")
    print("  (3) moonshotai/kimi-k2-instruct-0905")
    
    while True:
        m_choice = input(">> พิมพ์เลข (1, 2, 3): ").strip()
        if m_choice in MODEL_MAP:
            model_name = MODEL_MAP[m_choice]
            break
        print("ตัวเลือกไม่ถูกต้อง")

    print("\n[STEP 2] เลือกระดับภาษา:")
    print(f"  Available: {', '.join(LEVEL_LIST)}")
    print("  (พิมพ์ 'all' เพื่อเลือกทั้งหมด)")
    while True:
        l_choice = input(">> พิมพ์ชื่อระดับ หรือ all: ").strip().lower()
        if l_choice == 'all':
            target_levels = LEVEL_LIST
            break
        elif l_choice in LEVEL_LIST:
            target_levels = [l_choice]
            break
        else:
            print("ไม่พบระดับภาษานี้")

    print("\n[STEP 3] Advanced Settings:")
    w_choice = input(">> จำนวน Workers (Default 1): ").strip()
    workers = int(w_choice) if w_choice.isdigit() and int(w_choice) > 0 else 1

    print("\n[STEP 4] Defence Mode:")
    defence_mode = input(">> เปิดโหมดป้องกัน (y/n, Default n): ").strip().lower()
    if defence_mode not in ['y', 'n']:
        defence_mode = 'n'
    return model_name, target_levels, workers, defence_mode

if __name__ == "__main__":
    selected_model, selected_levels, num_workers, defence_mode = get_user_selection()
    OUTPUT_DIR = "output/ja"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_model_name = selected_model.replace("/", "_")
    level_suffix = "all" if len(selected_levels) > 1 else selected_levels[0]
    OUTPUT_PATH = os.path.join(OUTPUT_DIR, f"ja_output_{safe_model_name}_{level_suffix}.txt")

    llm = GroqModels(model=selected_model)
    data = JailbreakQueries()

    print("\n" + "="*50)
    print(f"   READY TO START! (Safe Save Mode)")
    print(f"   Model: {selected_model}")
    print(f"   Level: {selected_levels}")
    print(f"   Defence Mode: {"ON" if defence_mode == 'y' else "OFF"}")
    print("="*50 + "\n")
    
    time.sleep(1)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("THAI JAILBREAK BENCHMARK REPORT\n")
        f.write(f"Model: {selected_model}\n")
        f.write(f"Levels: {', '.join(selected_levels)}\n")
        f.write("=" * 80 + "\n\n")

    for level in selected_levels:
        print(f"🔹 Processing Level: {level}...")
        
        attack = Jailbreak(level=level)
        queries = data.generate_queries()
        
        current_prompts = []
        for query in queries:
            for jailbreak_prompt in attack.prompts:
                full_prompt = attack.get_combined_prompts(query, jailbreak_prompt, llm.model,  defence_mode == 'y')
                if full_prompt:
                    current_prompts.append(full_prompt)
        
        total_prompts = len(current_prompts)
        print(f"   Total prompts: {total_prompts}")

        tasks = [(llm, p) for p in current_prompts]
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            results = list(tqdm(executor.map(process_single_request_with_smart_retry, tasks), total=total_prompts, unit="req"))

        # -----------------------------------------------------------
        # 📊 CALCULATE METRICS
        # -----------------------------------------------------------
        try:
            metric_calculator = JailbreakRate(results)
            metric = metric_calculator.compute_metric()
            
            # รองรับทั้ง structure เดิมและใหม่
            if 'summary' in metric:
                # Structure ใหม่
                total_cnt = metric['summary'].get('total', len(results))
                success_cnt = metric['summary'].get('success_count', 0)
                
                # แปลง success_rate จาก string เป็น float
                rate_str = metric['summary'].get('success_rate', '0.00%')
                rate_val = float(rate_str.rstrip('%')) / 100
                
                breakdown = metric.get('breakdown', {})
            else:
                # Structure เดิม (fallback)
                total_cnt = metric.get('total', len(results))
                success_cnt = metric.get('success', metric.get('success_count', 0))
                rate_val = metric.get('rate', 0.0)
                breakdown = metric.get('breakdown', {})

            with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n>>> LEVEL: {level} (METRIC SUMMARY)\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total      : {total_cnt}\n")
                f.write(f"Success    : {success_cnt}\n")
                f.write(f"Rate       : {rate_val:.2%}\n")
                
                if breakdown:
                    f.write(f"Breakdown  :\n")
                    f.write(f"  - Jailbroken: {breakdown.get('jailbroken', 0)}\n")
                    f.write(f"  - Blocked   : {breakdown.get('blocked', 0)}\n")
                    f.write(f"  - Refused   : {breakdown.get('refused', 0)}\n")
                
                # แสดง success indices แบบจัดเรียงและแบ่งบรรทัด
                if 'success_indices' in metric and metric['success_indices']:
                    indices = metric['success_indices']
                    f.write(f"\nSuccess Indices ({len(indices)} items):\n")
                    
                    # แบ่งเป็น chunks ละ 15 indices ต่อบรรทัด
                    chunk_size = 15
                    for i in range(0, len(indices), chunk_size):
                        chunk = indices[i:i+chunk_size]
                        # จัด format ให้สวยงาม
                        formatted_chunk = ', '.join(f"{idx:3d}" for idx in chunk)
                        f.write(f"  {formatted_chunk}\n")
                
                # แสดง success details ถ้ามี
                if 'successes' in metric and metric['successes']:
                    f.write(f"\nSuccess Details ({len(metric['successes'])} items):\n")
                    for i, detail in enumerate(metric['successes'], 1):
                        f.write(f"  {i:2d}. {detail}\n")
                
            print(f"   Metric Saved: Success {success_cnt}/{total_cnt} ({rate_val:.2%})")

        except Exception as e:
            print(f"Metric Error: {e} (But text data is safe)")
            with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n[METRIC CALCULATION ERROR: {e}]\n")

        # -----------------------------------------------------------
        # SAVE DATA FIRST 
        # -----------------------------------------------------------
        try:
            with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n>>> LEVEL: {level} (DATA SAMPLES)\n")
                f.write("-" * 80 + "\n")
                for i in range(len(results)):
                    f.write(f"[SAMPLE {i + 1}]\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"PROMPT:\n{current_prompts[i]}\n\n")
                    f.write(f"ANSWER:\n{results[i]}\n\n")
                    f.write("." * 40 + "\n\n")
                f.write("=" * 80 + "\n\n")
            print(f"   Saved {len(results)} samples to file.")
        except Exception as e:
            print(f"Error saving text data: {e}")

        

    print(f"\n All done! Results saved to: {OUTPUT_PATH}")