import os
import re
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

# Set font for Thai language support
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


def parse_file_content(file_path):
    """
    Parse a single file and extract PROMPT TOKENS and STATUS information
    
    Returns:
        list of tuples: [(token_count, is_leaked), ...]
    """
    results = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split by sample sections
        samples = re.split(r'SAMPLE #\d+', content)
        
        for sample in samples[1:]:  # Skip first empty split
            # Extract STATUS
            status_match = re.search(r'STATUS:\s*(❌\s*SAFE|✅\s*LEAKED)', sample)
            
            # Extract PROMPT TOKENS
            word_match = re.search(r'PROMPT WORDS:\s*(\d+)', sample)
            
            if status_match and word_match:
                is_leaked = 'LEAKED' in status_match.group(1)
                word_count = int(word_match.group(1))
                results.append((word_count, is_leaked))
                
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return results


def extract_model_name(filename):
    """
    Extract model name from filename
    word_counted_casual_kimi.txt -> Kimi
    """
    patterns = {
        'kimi': 'Kimi',
        'llama': 'Llama',
        'meta': 'Meta'
    }
    
    filename_lower = filename.lower()
    for key, value in patterns.items():
        if key in filename_lower:
            return value
    
    return filename.replace('word_counted_', '').replace('.txt', '').title()


def aggregate_results_by_word_range(all_results, range_size=500):
    """
    Aggregate results by token length ranges
    
    Args:
        all_results: dict of {model: [(word_count, is_leaked), ...]}
        range_size: size of each token range
        
    Returns:
        dict of {model: {range_key: (success_count, total_count)}}
    """
    aggregated = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    
    for model, results in all_results.items():
        for word_count, is_leaked in results:
            # Calculate range bucket
            range_start = (word_count // range_size) * range_size
            range_key = f"{range_start}-{range_start + range_size}"
            
            # Count total and successes
            aggregated[model][range_key][1] += 1  # total count
            if is_leaked:
                aggregated[model][range_key][0] += 1  # success count
    
    return aggregated


def calculate_asr(aggregated_results):
    """
    Calculate Attack Success Rate (ASR) percentage
    
    Returns:
        dict of {model: {range_key: asr_percentage}}
    """
    asr_results = defaultdict(dict)
    
    for model, ranges in aggregated_results.items():
        for range_key, (success, total) in ranges.items():
            if total > 0:
                asr_results[model][range_key] = (success / total) * 100
            else:
                asr_results[model][range_key] = 0.0
                
    return asr_results


def plot_clustered_bar_chart(asr_results, range_size, output_path='asr_by_word_count_length.png'):
    """
    Create clustered bar chart showing ASR by word count length range for each model
    """
    # Get all unique range keys and sort them
    all_ranges = set()
    for model_ranges in asr_results.values():
        all_ranges.update(model_ranges.keys())
    
    # Sort ranges by their start value
    sorted_ranges = sorted(all_ranges, key=lambda x: int(x.split('-')[0]))
    
    # Get all models in specific order: Llama, Meta, Kimi
    model_order = ['Llama', 'Meta', 'Kimi']
    models = [m for m in model_order if m in asr_results.keys()]
    # Add any remaining models not in the predefined order
    models.extend([m for m in sorted(asr_results.keys()) if m not in model_order])
    
    # Prepare data
    x = np.arange(len(sorted_ranges))
    width = 0.8 / len(models)  # Width of bars
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Color scheme
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    # Plot bars for each model and track maximum value
    max_asr = 0
    for idx, model in enumerate(models):
        asr_values = [asr_results[model].get(range_key, 0.0) for range_key in sorted_ranges]
        max_asr = max(max_asr, max(asr_values) if asr_values else 0)
        offset = (idx - len(models)/2 + 0.5) * width
        bars = ax.bar(x + offset, asr_values, width, 
                     label=model, color=colors[idx % len(colors)], 
                     alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            if height >= 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}%',
                       ha='center', va='bottom', fontsize=8, rotation=0)
    
    # Customize chart
    ax.set_xlabel('Word Count Range', fontsize=12, fontweight='bold')
    ax.set_ylabel('Attack Success Rate (ASR %)', fontsize=12, fontweight='bold')
    ax.set_title(f'Attack Success Rate by Word Count Range\n(Range Size: {range_size} tokens)', 
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_ranges, rotation=45, ha='right')
    ax.legend(title='Model', fontsize=10, title_fontsize=11)
    
    # Set y-axis limit based on maximum value (1.5x or 2x of max)
    y_limit = min(max_asr * 1.25, 105)  # Use 1.5x, but cap at 105% max
    ax.set_ylim(0, y_limit)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ Graph saved to: {output_path}")
    plt.close()


def main():
    # Configuration
    base_path = r"dea_result\without_defence\final_results\th"
    rounds = ['round1', 'round2', 'round3', 'round4', 'round5']
    level = "informal"
    subfolder = r"length" + "\\" + level
    
    # Get range size from user
    print("=" * 70)
    print("📊 Attack Success Rate (ASR) Analysis Tool")
    print("=" * 70)
    range_size = input("\nEnter word range size (default: 500): ").strip()
    range_size = int(range_size) if range_size.isdigit() else 500
    print(f"\n🔧 Using word range size: {range_size}")
    
    # Store all results across rounds
    all_model_results = defaultdict(list)
    
    # Read files from all rounds
    print("\n📂 Reading files from all rounds...")
    for round_name in rounds:
        folder_path = Path(base_path) / round_name / subfolder
        
        if not folder_path.exists():
            print(f"⚠️  Folder not found: {folder_path}")
            continue
            
        print(f"\n  📁 Processing {round_name}...")
        
        # Find all relevant files
        for file_path in folder_path.glob("word_counted_*.txt"):
            model_name = extract_model_name(file_path.name)
            results = parse_file_content(file_path)
            
            if results:
                all_model_results[model_name].extend(results)
                leaked_count = sum(1 for _, leaked in results if leaked)
                print(f"    ✓ {model_name}: {len(results)} samples, {leaked_count} leaked")
    
    if not all_model_results:
        print("\n❌ No data found! Please check the folder path and file names.")
        return
    
    # Display summary
    print("\n" + "=" * 70)
    print("📈 Summary Statistics")
    print("=" * 70)
    for model, results in sorted(all_model_results.items()):
        total = len(results)
        leaked = sum(1 for _, is_leaked in results if is_leaked)
        overall_asr = (leaked / total * 100) if total > 0 else 0
        print(f"\n{model}:")
        print(f"  Total samples: {total}")
        print(f"  Leaked samples: {leaked}")
        print(f"  Overall ASR: {overall_asr:.2f}%")
    
    # Aggregate results by word range
    print(f"\n🔄 Aggregating results by {range_size}-word ranges...")
    aggregated = aggregate_results_by_word_range(all_model_results, range_size)
    
    # Calculate ASR
    asr_results = calculate_asr(aggregated)
    
    # Plot graph
    print("\n📊 Generating graph...")
    output_path = f"asr_by_word_count_length_{level}_{range_size}.png"
    plot_clustered_bar_chart(asr_results, range_size, output_path)
    
    # Display detailed results
    print("\n" + "=" * 70)
    print("📋 Detailed ASR by Word Count Range")
    print("=" * 70)
    
    # Get all ranges
    all_ranges = set()
    for model_ranges in asr_results.values():
        all_ranges.update(model_ranges.keys())
    sorted_ranges = sorted(all_ranges, key=lambda x: int(x.split('-')[0]))
    
    for range_key in sorted_ranges:
        print(f"\n{range_key} words:")
        for model in sorted(asr_results.keys()):
            if range_key in asr_results[model]:
                asr = asr_results[model][range_key]
                success, total = aggregated[model][range_key]
                print(f"  {model}: {asr:.2f}% ({success}/{total} leaked)")
    
    print("\n" + "=" * 70)
    print("✅ Analysis completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()