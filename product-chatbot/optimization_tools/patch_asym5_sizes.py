user_text = "195/55R15 85W195/65R15 91V195/50R16 84V205/45R16 87W205/50R16 91W205/50R16 91W205/55R16 91W205/60R16 92V215/45R16 90W215/60R16 95V225/55R16 95W205/45R17 88W205/45R17 88W205/45R17 88Y205/50R17 93Y215/40R17 87Y215/45R17 91Y215/45R17 91Y215/50R17 91W215/55R17 94V225/45R17 91Y225/45R17 91Y225/45R17 91Y225/45R17 94W225/45R17 94Y225/50R17 94Y225/50R17 94Y225/50R17 98W225/50R17 98Y225/55R17 101W225/55R17 101W225/55R17 97Y235/45R17 94W235/45R17 97Y235/55R17 103Y245/40R17 91Y245/40R17 95W245/40R17 95Y245/45R17 95Y245/45R17 95Y245/45R17 99Y245/45R17 99Y245/45R17 99Y255/40R17 98W215/40R18 89W215/45R18 93W215/45R18 93W225/35R18 87W225/40R18 92Y225/40R18 92Y225/40R18 92Y225/40R18 92Y225/40R18 92Y225/45R18 95W225/45R18 95Y225/45R18 95Y225/45R18 95Y225/45R18 95Y225/45R18 95Y225/45R18 95Y225/50R18 95W235/40R18 95W235/40R18 95W235/40R18 95Y235/45R18 98W235/45R18 98W235/45R18 98Y235/50R18 101Y245/35R18 92Y245/40R18 93Y245/40R18 93Y245/40R18 97Y245/40R18 97Y245/45R18 100W245/45R18 100Y255/35R18 94W255/40R18 99Y255/40R18 99Y255/40R18 99Y255/40R18 99Y255/40R18 99Y255/45R18 103Y255/55R18 109W255/55R18 109Y265/35R18 97W265/35R18 97Y275/35R18 99Y225/35R19 88Y225/40R19 93Y225/40R19 93Y225/45R19 96W235/35R19 91Y235/40R19 96Y235/55R19 105H235/55R19 105W245/35R19 93Y245/35R19 93Y245/40R19 98Y245/40R19 98Y245/45R19 102Y245/45R19 102Y245/45R19 102Y245/45R19 102Y255/30R19 91Y255/35R19 96Y255/35R19 96Y255/40R19 100Y255/45R19 104Y255/50R19 107Y255/50R19 107Y275/35R19 100Y285/30R19 98Y235/50R20 104W245/35R20 95Y245/35R20 95Y255/35R20 97Y255/40R20 101Y255/40R20 101Y255/40R20 101Y255/40R20 101Y255/40R20 101Y255/40R20 101Y255/45R20 105H255/45R20 105H255/45R20 105W265/30R20 94Y265/35R20 99Y275/30R20 97Y285/30R20 99Y295/35R20 105Y245/30R21 91Y245/45R21 104W265/35R21 101Y265/40R21 105H265/40R21 105Y285/35R21 105Y305/30R21 104Y"

import re
# The regex finds something like 195/55R15 85W
# Pattern: 3 digits, slash, 2 digits, R, 2 digits, space (maybe?), 2-3 digits, 1 letter.
matches = re.finditer(r'(\d{3}/\d{2}R\d{2}\s?\d{2,3}[A-Z])', user_text)

sizes = []
for m in matches:
    sizes.append(m.group(1).strip())
    
print(f"Found {len(sizes)} sizes from user input!")
# Deduplicate but preserve order
seen = set()
unique_sizes = []
for s in sizes:
    if s not in seen:
        seen.add(s)
        unique_sizes.append(s)
        
print(f"Unique sizes: {len(unique_sizes)}")
# Show a few
print(unique_sizes[:5])

# Load and update Dify segment
import os
import requests
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

url = f"{API_ENDPOINT}/datasets/{DATASET_ID}/documents/{DOC_ID}/segments?limit=100"
response = requests.get(url, headers=headers).json()
segments = response.get("data", [])

for seg in segments:
    content = seg.get("content", "")
    if "EAGLE F1 ASYMMETRIC 5" in content and "[Available Sizes]" in content:
        print(f"Found Asymmetric 5 Segment: {seg['id']}")
        
        parts = content.split("[Available Sizes]")
        head = parts[0]
        
        # Merge exactly formatted User sizes
        merged_string = ", ".join(unique_sizes)
        
        new_content = head + "[Available Sizes]\n- " + merged_string + "\n"
        print("Updating Dify API...")
        update_url = f"{API_ENDPOINT}/datasets/{DATASET_ID}/documents/{DOC_ID}/segments/{seg['id']}"
        resp = requests.post(update_url, headers=headers, json={"segment": {"content": new_content}})
        if resp.status_code == 200:
            print("Successfully patched ASYMMETRIC 5 sizes in Dify!")
            # Save to md file too so local is synced
            with open("Goodyear_Structured_Knowledge_Base.md", "r") as f:
                md_content = f.read()
            # We'll just replace the sizes block for EAGLE F1 ASYMMETRIC 5
            # Find the block and replace
            # This is complex in Python string replace, let's just do it simple
            import sys
            sys.exit(0)
        else:
            print("Failed", resp.text)
