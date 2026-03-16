import os
import re
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CHATFLOW_TEST_API_KEY")
API_ENDPOINT = os.getenv("API_ENDPOINT", "http://localhost/v1").rstrip('/')

url = f"{API_ENDPOINT}/chat-messages"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def load_ground_truth(filepath):
    with open(filepath, "r") as f:
        text = f.read()

    products = text.split("---PRODUCT_BOUNDARY---")
    kb = {}
    for p in products[1:]:
        name_match = re.search(r'Product Name:\s*\*\*(.*?)\*\*', p)
        if not name_match: continue
        name = name_match.group(1).strip()
        
        # Count expected items using simple line count for lists
        feat_match = re.search(r'\[Product Features\](.*?)(\n\[|$)', p, re.DOTALL)
        features = len([x for x in feat_match.group(1).strip().split('\n') if x.strip().startswith('-')]) if feat_match else 0
        
        tech_match = re.search(r'\[Technology Descriptions\](.*?)(\n\[|$)', p, re.DOTALL)
        techs = len([x for x in tech_match.group(1).strip().split('\n') if x.strip().startswith('-')]) if tech_match else 0
        
        charts = 1 if "[Performance Charts]" in p else 0
        
        sizes_count = 0
        size_match = re.search(r'\[Available Sizes\](.*?)(\n\[|$)', p, re.DOTALL)
        if size_match:
            sizes_line = size_match.group(1).replace('-', '').strip()
            if sizes_line:
                sizes_count = len([x for x in sizes_line.split(',') if x.strip()])
                
        kb[name] = {
            "features": features,
            "techs": techs,
            "charts": charts,
            "sizes": sizes_count
        }
    return kb

def query_dify_stream(product_name, expected):
    query = f"Provide the Product features, Performance charts, Available sizes, and Technology descriptions for {product_name}. List every single item explicitly. Do not abbreviate."
    payload = {
        "inputs": {},
        "query": query,
        "response_mode": "streaming",
        "conversation_id": "",
        "user": "benchmark_bot",
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=10)
        
        if response.status_code != 200:
            return (product_name, f"Error {response.status_code}: {response.text}", "❌ FAIL (API Error)", time.time()-start_time)
            
        full_answer = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    data_str = decoded_line[6:]
                    try:
                        event_data = json.loads(data_str)
                        if event_data.get('event') == 'message':
                            full_answer += event_data.get('answer', '')
                    except json.JSONDecodeError:
                        pass
        elapsed = time.time() - start_time
        
        status = "✅ PASS"
        if len(full_answer) < 100 or "I do not have" in full_answer or "I'm sorry" in full_answer:
            status = "❌ FAIL (Too short or not found)"
            
        return (product_name, full_answer, status, elapsed)
    except Exception as e:
        return (product_name, f"Exception: {e}", "❌ FAIL (Exception)", time.time()-start_time)

def main():
    print("Loading Ground Truth...")
    ground_truth = load_ground_truth("Goodyear_Structured_Knowledge_Base_Merged.md")
    total_products = len(ground_truth)
    print(f"Loaded {total_products} products for testing. Using STREAMING to avoid Gateway Timeouts.")
    
    with open("benchmark_report.md", "w") as f:
        f.write("# Knowledge Base Benchmark Report\n\n")
        f.write("| Status | Product | Expected Features | Expected Tech | Expected Charts | Expected Sizes | Time (s) | Preview |\n")
        f.write("|--------|---------|-------------------|---------------|-----------------|----------------|----------|---------|\n")
        
        for i, (name, expected) in enumerate(ground_truth.items()):
            print(f"\n[{i+1}/{total_products}] Testing: {name} ...", end="", flush=True)
            res_name, answer, status, elapsed = query_dify_stream(name, expected)
            print(f" {status} ({elapsed:.1f}s)")
            
            preview = answer[:40].replace('\n', ' ')
            preview_safe = preview.replace('|', '/')
            name_safe = name.replace('|', '/')
            
            f.write(f"| {status} | {name_safe} | {expected['features']} | {expected['techs']} | {expected['charts']} | {expected['sizes']} | {elapsed:.1f}s | {preview_safe}... |\n")

if __name__ == '__main__':
    main()
