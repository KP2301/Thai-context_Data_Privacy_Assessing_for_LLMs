import os
import sys
from dotenv import load_dotenv
from contextlib import redirect_stdout
import re 

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

load_dotenv()

if "GROQ_API_KEY" not in os.environ:
    print("Error: GROQ_API_KEY not found in environment variables. Check your .env file.")
    sys.exit(1)

from models.GroqModels import GroqModels
from attacks.DataExtraction.enron import EnronDataExtraction
from attacks.DataExtraction.prompt_extract import PromptExtraction

enron = EnronDataExtraction(data_path="data/enron")
# 'prefix-50'
# '0-shot-known-domain-b'
# '0-shot-unknown-domain-c'
# '3-shot-known-domain-c'
# '5-shot-unknown-domain-b'
atk_format = 'prefix-50'
prompts, _ = enron.generate_prompts(format=atk_format)

llm_model = "llama-3.1-8b-instant"
llm = GroqModels(model=llm_model)
attack = PromptExtraction()
print(f"Writing results to {OUTPUT_PATH}")
results = attack.execute_attack(prompts[:100], llm)
print(f"All prompts is {len(prompts)}, attacked {len(results)} samples.")

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    with redirect_stdout(f):
        print("="*100)
        print(f"DATA EXTRACTION RESULTS - Total: {len(results)} samples")
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

print("Done. Check the output directory.")