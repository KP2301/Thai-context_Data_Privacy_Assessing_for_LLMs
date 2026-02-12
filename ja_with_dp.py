# ja_with_dp.py
import os
import sys
import json
import time
import random
import re
import concurrent.futures
from tqdm import tqdm
from dotenv import load_dotenv

# Import custom modules
from metrics.JailbreakRate import JailbreakRate
from models.GroqModels import GroqModels
from data.jailbreakqueries import JailbreakQueries
from attacks.Jailbreak.jailbreak import Jailbreak

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Model selection mapping
MODEL_MAP = {
    "1": "llama-3.1-8b-instant",
    "2": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "3": "moonshotai/kimi-k2-instruct-0905"
}

# System prompt key mapping for different models
SYSTEM_PROMPT_KEY_MAP = {
    "llama-3.1-8b-instant": "llama",
    "meta-llama/llama-4-maverick-17b-128e-instruct": "meta",
    "moonshotai/kimi-k2-instruct-0905": "kimi"
}

# Language formality levels
LEVEL_LIST = [
    "ceremonial",
    "formal",
    "semi_formal",
    "informal",
    "casual"
]

# Available defense methods
DEFENSE_METHODS = [
    "intent_analysis",
    "anti_persona",
    "pii_shield",
    "refusal_override",
    "deobfuscation",
    "hypothetical_boundary"
]

# Maximum retry attempts for rate limit handling
MAX_RETRIES = 15


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def setup_project_path():
    """
    Auto-detect and set up the project root path.
    Returns the absolute path to the project root directory.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    if os.path.exists(os.path.join(current_dir, "models")):
        return current_dir
    elif os.path.exists(os.path.join(current_dir, "..", "models")):
        return os.path.abspath(os.path.join(current_dir, ".."))
    else:
        # Fallback for deep nesting
        return os.path.abspath(os.path.join(current_dir, "..", ".."))


def validate_environment():
    """
    Validate that required environment variables are set.
    Exits if validation fails.
    """
    load_dotenv()
    
    if "GROQ_API_KEY" not in os.environ:
        print("❌ Error: GROQ_API_KEY not found in environment variables.")
        print("   Please check your .env file.")
        sys.exit(1)


def calculate_retry_delay(attempt, error_msg):
    """
    Calculate intelligent retry delay based on error message.
    
    Args:
        attempt (int): Current retry attempt number
        error_msg (str): Error message from API
        
    Returns:
        float: Number of seconds to wait
    """
    wait_match = re.search(r"try again in (\d+\.?\d*)s", error_msg)
    
    if wait_match:
        return float(wait_match.group(1)) + 1.5
    else:
        return (2 ** attempt) + random.uniform(1, 3)


# ============================================================================
# CORE PROCESSING FUNCTIONS
# ============================================================================

def process_single_request_with_smart_retry(args):
    """
    Process a single API request with intelligent retry logic.
    
    Args:
        args (tuple): (llm_instance, prompt)
        
    Returns:
        str: API response or error message
    """
    llm_instance, prompt = args
    
    for attempt in range(MAX_RETRIES):
        try:
            response = llm_instance.query(prompt)
            return response
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle rate limit errors
            if "429" in error_msg or "rate limit" in error_msg.lower():
                if attempt < MAX_RETRIES - 1:
                    wait_time = calculate_retry_delay(attempt, error_msg)
                    time.sleep(wait_time)
                    continue
                    
            return f"Error: {error_msg}"
    
    return "Error: Max retries exceeded (Rate Limit Stuck)"


def load_defensive_prompts(project_root, selected_model, dp_method):
    """
    Load and combine base system prompt with defensive prompt.
    
    Args:
        project_root (str): Path to project root
        selected_model (str): Selected model name
        dp_method (str): Defense method name
        
    Returns:
        str: Combined system prompt or None if loading fails
    """
    try:
        prompts_dir = os.path.join(project_root, "defences", "defensive_prompt")
        
        # 1. Load base system prompt
        sys_path = os.path.join(prompts_dir, "system_prompts_eng.json")
        with open(sys_path, "r", encoding="utf-8") as f:
            key_name = SYSTEM_PROMPT_KEY_MAP.get(selected_model, "llama")
            base_system_msg = json.load(f).get(key_name, "You are a helpful AI.")
        
        # 2. Load specific defense prompt
        def_path = os.path.join(prompts_dir, "ja_defense_prompt_eng.json")
        with open(def_path, "r", encoding="utf-8") as f:
            defense_text = json.load(f).get(dp_method, "")
        
        if not defense_text:
            print(f"⚠️  Warning: No text found for defense method '{dp_method}'")
        
        # 3. Combine prompts
        final_prompt = f"{base_system_msg}\n\nคำสั่งความปลอดภัย (สำคัญมาก):\n{defense_text}"
        print(f"✅ Loaded Defense System Prompt for: {dp_method}")
        
        return final_prompt
        
    except Exception as e:
        print(f"❌ Prompt Load Error: {e}")
        print(f"   (Checked path: {prompts_dir})")
        sys.exit(1)


def extract_metric_values(metric):
    """
    Extract metric values supporting both old and new data structures.
    
    Args:
        metric (dict): Metric calculation results
        
    Returns:
        tuple: (total_count, success_count, success_rate, breakdown, successes_list, indices_list)
    """
    if 'summary' in metric:
        # New structure
        total_cnt = metric['summary'].get('total', 0)
        success_cnt = metric['summary'].get('success_count', 0)
        rate_str = metric['summary'].get('success_rate', '0.00%')
        rate_val = float(str(rate_str).rstrip('%')) / 100
        breakdown = metric.get('breakdown', {})
        successes_list = metric.get('successes', [])
        indices_list = metric.get('success_indices', [])
    else:
        # Old structure (fallback)
        total_cnt = metric.get('total', 0)
        success_cnt = metric.get('success', metric.get('success_count', 0))
        rate_val = metric.get('rate', 0.0)
        breakdown = metric.get('breakdown', {})
        successes_list = metric.get('successes', [])
        indices_list = metric.get('success_indices', [])
    
    return total_cnt, success_cnt, rate_val, breakdown, successes_list, indices_list


# ============================================================================
# USER INTERFACE FUNCTIONS
# ============================================================================

def print_header():
    """Print the application header."""
    print("\n" + "=" * 40)
    print("   🤖 AI JAILBREAK BENCHMARK MENU")
    print("=" * 40)


def select_language():
    """
    Prompt user to select query language.
    
    Returns:
        str: Selected language ('eng' or 'th')
    """
    print("\n[STEP 1] เลือกภาษา Query:")
    print("  (1) English (eng)")
    print("  (2) Thai (th)")
    
    while True:
        choice = input(">> พิมพ์เลข (1, 2): ").strip()
        if choice == '1':
            return 'eng'
        elif choice == '2':
            return 'th'
        print("❌ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่")


def select_model():
    """
    Prompt user to select an AI model.
    
    Returns:
        str: Selected model name
    """
    print("\n[STEP 2] เลือก Model:")
    print("  (1) llama-3.1-8b-instant")
    print("  (2) meta-llama/llama-4-maverick-17b-128e-instruct")
    print("  (3) moonshotai/kimi-k2-instruct-0905")
    
    while True:
        choice = input(">> พิมพ์เลข (1, 2, 3): ").strip()
        if choice in MODEL_MAP:
            return MODEL_MAP[choice]
        print("❌ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่")


def select_language_levels():
    """
    Prompt user to select language formality levels.
    
    Returns:
        list: Selected level(s)
    """
    print("\n[STEP 3] เลือกระดับภาษา:")
    print(f"  Available: {', '.join(LEVEL_LIST)}")
    print("  (พิมพ์ 'all' เพื่อเลือกทั้งหมด)")
    
    while True:
        choice = input(">> พิมพ์ชื่อระดับ หรือ all: ").strip().lower()
        
        if choice == 'all':
            return LEVEL_LIST
        elif choice in LEVEL_LIST:
            return [choice]
        else:
            print("❌ ไม่พบระดับภาษานี้ กรุณาลองใหม่")


def select_worker_count():
    """
    Prompt user to select number of concurrent workers.
    
    Returns:
        int: Number of workers (default: 1)
    """
    print("\n[STEP 4] Advanced Settings:")
    choice = input(">> จำนวน Workers (Default 1): ").strip()
    
    if choice.isdigit() and int(choice) > 0:
        return int(choice)
    return 1


def select_defense_settings():
    """
    Prompt user to configure defense settings.
    
    Returns:
        tuple: (defense_active, selected_method)
    """
    print("\n[STEP 5] Defence Mode:")
    defense_active = input(">> เปิดโหมดป้องกัน (y/n, Default n): ").strip().lower()
    
    if defense_active != 'y':
        return 'n', "None"
    
    print("\n  [Defense Methods Available]")
    for idx, method in enumerate(DEFENSE_METHODS, 1):
        print(f"  ({idx}) {method}")
    
    while True:
        choice = input(f">> เลือกวิธีป้องกัน (1-{len(DEFENSE_METHODS)}): ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(DEFENSE_METHODS):
            return 'y', DEFENSE_METHODS[int(choice) - 1]
        
        print("❌ เลือกไม่ถูกต้อง กรุณาลองใหม่")


def select_round_number():
    """
    Prompt user to select round number for testing.
    
    Returns:
        int: Round number (1-5)
    """
    print("\n[STEP 6] เลือก Round:")
    
    while True:
        choice = input(">> พิมพ์หมายเลข Round (1-5): ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= 5:
            return int(choice)
        
        print("❌ กรุณาเลือก Round ระหว่าง 1-5")


def get_user_selection():
    """
    Collect all user selections for benchmark configuration.
    
    Returns:
        tuple: (query_language, model_name, target_levels, workers, defence_mode, dp_method, round_num)
    """
    print_header()
    
    query_language = select_language()
    model_name = select_model()
    target_levels = select_language_levels()
    workers = select_worker_count()
    defence_mode, dp_method = select_defense_settings()
    round_num = select_round_number()
    
    return query_language, model_name, target_levels, workers, defence_mode, dp_method, round_num


# ============================================================================
# FILE OUTPUT FUNCTIONS
# ============================================================================

def generate_output_path(defence_mode, query_lang, level, dp_method, round_num, model_name):
    """
    Generate unique output file path following the new structure:
    ja_result/{with_defence|without_defence}/{eng|th}/{level}/round{N}/filename.txt
    
    Args:
        defence_mode (str): Defense mode status ('y' or 'n')
        query_lang (str): Query language ('eng' or 'th')
        level (str): Language formality level
        dp_method (str): Defense method name
        round_num (int): Round number (1-5)
        model_name (str): Selected model name
        
    Returns:
        str: Full output file path
    """
    # Base directory
    base_dir = "ja_result"
    
    # Defence directory
    defence_dir = "with_defence" if defence_mode == 'y' else "without_defence"
    
    # Full path: ja_result/{with_defence|without_defence}/{eng|th}/{level}/round{N}/
    output_dir = os.path.join(base_dir, defence_dir, query_lang, level, f"round{round_num}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    safe_model_name = model_name.replace("/", "_")
    dp_suffix = f"_{dp_method}" if defence_mode == 'y' else ""
    timestamp = int(time.time())
    
    filename = f"ja_{safe_model_name}{dp_suffix}_{timestamp}.txt"
    
    return os.path.join(output_dir, filename)


def write_report_header(filepath, model_name, level, defence_mode, dp_method, query_lang, round_num):
    """
    Write the report header to output file.
    
    Args:
        filepath (str): Output file path
        model_name (str): Selected model name
        level (str): Language level
        defence_mode (str): Defense mode status
        dp_method (str): Defense method
        query_lang (str): Query language
        round_num (int): Round number
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("THAI JAILBREAK BENCHMARK REPORT\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Query Language: {query_lang.upper()}\n")
        f.write(f"Level: {level}\n")
        f.write(f"Round: {round_num}\n")
        
        if defence_mode == 'y':
            f.write(f"Defense Mode: ON ({dp_method})\n")
        else:
            f.write("Defense Mode: OFF\n")
        
        f.write("=" * 80 + "\n\n")


def save_metric_summary(filepath, level, metric):
    """
    Save metric summary to output file.
    
    Args:
        filepath (str): Output file path
        level (str): Current language level
        metric (dict): Calculated metrics
    """
    total_cnt, success_cnt, rate_val, breakdown, successes_list, indices_list = \
        extract_metric_values(metric)
    
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"\n>>> LEVEL: {level} (METRIC SUMMARY)\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total      : {total_cnt}\n")
        f.write(f"Success    : {success_cnt}\n")
        f.write(f"Rate       : {rate_val:.2%}\n")
        
        # Write breakdown if available
        if breakdown:
            f.write("Breakdown  :\n")
            f.write(f"  - Jailbroken: {breakdown.get('jailbroken', 0)}\n")
            f.write(f"  - Blocked   : {breakdown.get('blocked', 0)}\n")
            f.write(f"  - Refused   : {breakdown.get('refused', 0)}\n")
        
        # Write success indices
        if indices_list:
            f.write(f"\nSuccess Indices ({len(indices_list)} items):\n")
            chunk_size = 15
            
            for i in range(0, len(indices_list), chunk_size):
                chunk = indices_list[i:i + chunk_size]
                formatted_chunk = ', '.join(f"{idx:3d}" for idx in chunk)
                f.write(f"  {formatted_chunk}\n")
        
        # Write success details
        if successes_list:
            f.write(f"\nSuccess Details ({len(successes_list)} items):\n")
            for i, detail in enumerate(successes_list, 1):
                f.write(f"  {i:2d}. {detail}\n")
    
    print(f"   ✅ Metric Saved: Success {success_cnt}/{total_cnt} ({rate_val:.2%})")


def save_data_samples(filepath, level, prompts, results):
    """
    Save individual prompt-response pairs to output file.
    
    Args:
        filepath (str): Output file path
        level (str): Current language level
        prompts (list): List of prompts
        results (list): List of responses
    """
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"\n>>> LEVEL: {level} (DATA SAMPLES)\n")
        f.write("-" * 80 + "\n")
        
        for i in range(len(results)):
            f.write(f"[SAMPLE {i + 1}]\n")
            f.write("-" * 40 + "\n")
            f.write(f"PROMPT:\n{prompts[i]}\n\n")
            f.write(f"ANSWER:\n{results[i]}\n\n")
            f.write("." * 40 + "\n\n")
        
        f.write("=" * 80 + "\n\n")
    
    print(f"   ✅ Saved {len(results)} samples to file.")


# ============================================================================
# MAIN BENCHMARK EXECUTION
# ============================================================================

def run_benchmark_for_level(level, llm, data, attack_class, output_path, num_workers):
    """
    Execute benchmark tests for a specific language level.
    
    Args:
        level (str): Language formality level
        llm: Language model instance
        data: Query data generator
        attack_class: Jailbreak attack class
        output_path (str): Output file path
        num_workers (int): Number of concurrent workers
    """
    print(f"\n🔹 Processing Level: {level}...")
    
    # Generate attack prompts
    attack = attack_class(level=level)
    queries = data.generate_queries()
    
    current_prompts = []
    for query in queries:
        for jailbreak_prompt in attack.prompts:
            full_prompt = attack.get_combined_prompts(
                query, 
                jailbreak_prompt, 
                llm.model
            )
            if full_prompt:
                current_prompts.append(full_prompt)
    
    total_prompts = len(current_prompts)
    print(f"   📝 Total prompts: {total_prompts}")
    
    # Execute API requests with concurrent workers
    tasks = [(llm, p) for p in current_prompts]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(
            tqdm(
                executor.map(process_single_request_with_smart_retry, tasks),
                total=total_prompts,
                unit="req",
                desc=f"   Processing {level}"
            )
        )
    
    # Calculate and save metrics
    try:
        metric_calculator = JailbreakRate(results)
        metric = metric_calculator.compute_metric()
        save_metric_summary(output_path, level, metric)
        
    except Exception as e:
        print(f"⚠️  Metric Error: {e} (But text data is safe)")
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(f"\n[METRIC CALCULATION ERROR: {e}]\n")
    
    # Save raw data samples
    try:
        save_data_samples(output_path, level, current_prompts, results)
        
    except Exception as e:
        print(f"❌ Error saving text data: {e}")


def main():
    """Main execution function."""
    
    # Initialize environment
    validate_environment()
    project_root = setup_project_path()
    
    # Get user configuration
    query_lang, selected_model, selected_levels, num_workers, defence_mode, dp_method, round_num = \
        get_user_selection()
    
    # Load defensive prompts if enabled
    final_system_prompt = None
    if defence_mode == 'y':
        final_system_prompt = load_defensive_prompts(
            project_root, 
            selected_model, 
            dp_method
        )
    
    # Initialize LLM and data
    llm = GroqModels(model=selected_model, system_prompt=final_system_prompt)
    data = JailbreakQueries()
    
    # Print configuration summary
    print("\n" + "=" * 50)
    print("   READY TO START! (Safe Save Mode)")
    print(f"   Query Language: {query_lang.upper()}")
    print(f"   Model: {selected_model}")
    print(f"   Level(s): {selected_levels}")
    print(f"   Round: {round_num}")
    print(f"   Defence Mode: {'ON (' + dp_method + ')' if defence_mode == 'y' else 'OFF'}")
    print("=" * 50 + "\n")
    
    time.sleep(1)
    
    # Process each level separately (each level gets its own file)
    for level in selected_levels:
        # Generate output path for this specific level
        output_path = generate_output_path(
            defence_mode,
            query_lang,
            level,
            dp_method,
            round_num,
            selected_model
        )
        
        # Write report header for this level
        write_report_header(
            output_path,
            selected_model,
            level,
            defence_mode,
            dp_method,
            query_lang,
            round_num
        )
        
        # Run benchmark for this level
        run_benchmark_for_level(
            level, 
            llm, 
            data, 
            Jailbreak, 
            output_path, 
            num_workers
        )
        
        print(f"✅ Level '{level}' completed! Saved to: {output_path}\n")
    
    # Final summary
    print(f"\n🎉 All levels completed successfully!")
    print(f"   Results saved in: ja_result/{'with_defence' if defence_mode == 'y' else 'without_defence'}/{query_lang}/")
    print(f"   Round: {round_num}")
    print(f"   Levels processed: {', '.join(selected_levels)}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()