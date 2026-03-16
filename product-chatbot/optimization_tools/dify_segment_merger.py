import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("DIFY_DATABASE_KEY")
API_ENDPOINT = os.getenv("API_ENDPOINT", "http://localhost/v1").rstrip('/')
DATASET_ID = "67d007c0-9c92-4f2d-a99b-da6bd3f5f8a5"
DOC_ID = "f45cdee5-dc63-4012-af9a-4bfaa559469e"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def get_segments(doc_id):
    print(f"Fetching segments for document {doc_id}...")
    url = f"{API_ENDPOINT}/datasets/{DATASET_ID}/documents/{doc_id}/segments?limit=100"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", [])
    print(f"Failed to fetch segments: {response.text}")
    return []

def update_segment(seg_id, content):
    url = f"{API_ENDPOINT}/datasets/{DATASET_ID}/documents/{DOC_ID}/segments/{seg_id}"
    payload = {
        "segment": {
            "content": content
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return True
    else:
        print(f"  [X] Update failed for {seg_id}: {response.text}")
        return False

def main():
    segments = get_segments(DOC_ID)
    if not segments:
        print("No segments found.")
        return

    print(f"Found {len(segments)} segments total. Scanning for '[Available Sizes]'...")
    
    merged_count = 0
    
    for idx, seg in enumerate(segments):
        content = seg.get("content", "")
        # Only process if we see the sizes section
        if "[Available Sizes]" in content:
            # We split by [Available Sizes]
            parts = content.split("[Available Sizes]")
            if len(parts) != 2:
                continue # Safety net if formatting differs
            
            head, tail = parts[0], parts[1]
            lines = tail.strip().split('\n')
            
            sizes = []
            other_lines = []
            for line in lines:
                if line.startswith('-'):
                    sizes.append(line.replace('- ', '').strip())
                elif line.strip() != "":
                    other_lines.append(line.strip())
            
            # If no actual size bullets, skip
            if not sizes:
                continue
                
            merged_sizes = ", ".join(sizes)
            print(f"Merging segment {idx+1}/{len(segments)} [{seg['id']}] - Found {len(sizes)} sizes.")
            
            # Reconstruct the tail
            new_tail = f"\n- {merged_sizes}\n"
            if other_lines:
                new_tail += "\n".join(other_lines) + "\n"
                
            new_content = head + "[Available Sizes]" + new_tail
            
            # Optional check: If it's already merged, sizes might just be length 1 comma separated.
            # E.g. if we already ran it.
            if len(sizes) == 1 and ',' in sizes[0]:
                print(f"  [-] Already merged.")
                continue

            success = update_segment(seg['id'], new_content)
            if success:
                print(f"  [+] Successfully updated segment.")
                merged_count += 1
            
            # Rate limiting
            time.sleep(0.5)

    print(f"\nCompleted modifying {merged_count} out of {len(segments)} segments.")
    print("All 'Available Sizes' sections are now comma-separated lists to ensure they form a single child chunk in Dify.")

if __name__ == '__main__':
    main()
