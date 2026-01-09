import os
import sys
from dotenv import load_dotenv
from contextlib import redirect_stdout
import re 

OUTPUT_DIR = "output/ja"
BASE_FILENAME = "ja_output"
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

load_dotenv()

if "GROQ_API_KEY" not in os.environ:
    print("Error: GROQ_API_KEY not found in environment variables. Check your .env file.")
    sys.exit(1)

from models.GroqModels import GroqModels
from models.OpenAI import OpenAIModels
from data.jailbreakqueries_th import JailbreakQueries
from attacks.Jailbreak.jailbreak_th import Jailbreak
from metrics import JailbreakRate

data = JailbreakQueries()

# llama-3.1-8b-instant, 
# meta-llama/llama-4-maverick-17b-128e-instruct or meta-llama/llama-prompt-guard-2-86m
# moonshotai/kimi-k2-instruct-0905  
llm = GroqModels(
    model="llama-3.1-8b-instant" 
)

attack = Jailbreak(levels="ceremonial")
print(f"Writing results to {OUTPUT_PATH}")
results, prompts = attack.execute_attack(data, llm)


with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    with redirect_stdout(f):
        print("="*100)
        print(f"JAIL BREAK ATTACK RESULTS - Total: {len(results)} samples")
        print("="*100)

        for idx in range(len(results)):
            print(f"\n{'─'*100}")
            print(f"SAMPLE #{idx + 1}")
            print(f"{'─'*100}")

            print(f"\n📝 PROMPT:")
            print(prompts[idx])

            print(f"\n💬 ANSWER:")
            print(results[idx])
            print()

        print("="*100)
        rate = JailbreakRate(results).compute_metric()
        print(f"Jailbreak Rate: {rate}")

print("Done. Check the output directory.")
