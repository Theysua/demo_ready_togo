import os
import requests
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Dify Configuration
DIFY_API_KEY = os.getenv("DIFY_DATABASE_KEY")
DIFY_API_URL = os.getenv("API_ENDPOINT", "http://localhost/v1").rstrip('/')
DATASET_ID = "577601e7-9df4-433a-9509-8faf5f097231"
DOCUMENT_ID = "a75c4aef-dc7f-4859-b642-15771eb15db9"

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

headers = {
    "Authorization": f"Bearer {DIFY_API_KEY}",
    "Content-Type": "application/json"
}

def get_segments():
    print(f"Fetching segments from Dify for Dataset {DATASET_ID}, Document {DOCUMENT_ID}...")
    url = f"{DIFY_API_URL}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments?limit=100"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json().get('data', [])
    print(f"Success! Found {len(data)} segments.")
    return data

def enrich_segment_with_ai(client, original_content):
    """
    Uses OpenAI to analyze the segment, extract keywords, and generate FAQ pairs.
    Returns the enriched content and a list of keywords.
    """
    system_prompt = """You are an AI assistant optimizing product documentation for a semantic search engine (RAG).
    The text is from a Goodyear product manual containing tire sizes, features, and performance charts.
    Your task:
    1. Read the provided text.
    2. Extract 5-10 core keywords (e.g., product names, important features, specific sizes if few).
    3. Generate 3-5 Hypothetical Q&A pairs (FAQ) that a user might ask, based exactly on this text.
    4. Provide the output in strictly JSON format.
    
    Format:
    {
        "keywords": ["keyword1", "keyword2", ...],
        "faq": [
            {"q": "question here?", "a": "answer here."}, ...
        ]
    }"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the segment text:\n\n{original_content}"}
            ],
            response_format={ "type": "json_object" }
        )
        
        result_json = json.loads(response.choices[0].message.content)
        keywords = result_json.get("keywords", [])
        faqs = result_json.get("faq", [])
        
        # Build the enriched header
        enriched_header = "<metadata>\n"
        enriched_header += f"keywords: {', '.join(keywords)}\n"
        enriched_header += "faq:\n"
        for faq in faqs:
            enriched_header += f"- Q: {faq['q']} A: {faq['a']}\n"
        enriched_header += "</metadata>\n\n"
        
        # Combine header with original content so no original data is lost
        enriched_content = enriched_header + f"<original_content>\n{original_content}\n</original_content>"
        
        return enriched_content, keywords
    except Exception as e:
        print(f"Error enriching with OpenAI: {e}")
        return original_content, []

def update_segment_in_dify(segment_id, enriched_content, keywords):
    print(f"Updating segment {segment_id} in Dify...")
    url = f"{DIFY_API_URL}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments/{segment_id}"
    payload = {
        "segment": {
            "content": enriched_content,
            "answer": "",
            "keywords": keywords
        }
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 200:
        print(f"Successfully updated segment {segment_id}.")
        return True
    else:
        print(f"Failed to update segment {segment_id}: {resp.text}")
        return False

def main():
    if not DIFY_API_KEY or not OPENAI_API_KEY:
        print("Missing API Keys in .env file. Please check DIFY_DATABASE_KEY and OPENAI_API_KEY.")
        return
        
    client = OpenAI(api_key=OPENAI_API_KEY)
    segments = get_segments()
    
    for i, segment in enumerate(segments):
        seg_id = segment.get('id')
        original_content = segment.get('content')
        
        print(f"\n--- Processing Segment {i+1}/{len(segments)} [{seg_id}] ---")
        
        # Skip if already enriched to avoid duplicate processing
        if "<metadata>" in original_content:
             print("Segment already enriched. Skipping.")
             continue
             
        # HEALING LOGIC: If the last line of this segment is missing its load index,
        # borrow the first line of the next segment to provide context to the LLM.
        lookahead_content = original_content
        if i + 1 < len(segments):
            next_content = segments[i+1].get('content', '')
            if next_content:
                next_first_line = next_content.strip().split('\n')[0]
                # If the next segment starts with a short token (like "105Y", "99Y", etc.)
                if len(next_first_line) <= 5 and any(char.isdigit() for char in next_first_line):
                    print(f"Healing boundary: Appending '{next_first_line}' from next segment.")
                    lookahead_content = original_content + " " + next_first_line
             
        # 1. Ask OpenAI to enrich with the healed content
        print("Sending to OpenAI for enrichment...")
        enriched_content, keywords = enrich_segment_with_ai(client, lookahead_content)
        
        # 2. But we only write back the enriched header + the TRULY ORIGINAL content (Dify handles the rest)
        # enrich_segment_with_ai currently wraps lookahead_content in <original_content>
        # Let's fix that so it writes back the strict original_content.
        
        # Extract the <metadata> part from the generated enriched_content
        metadata_part = enriched_content.split("<original_content>")[0]
        final_writeback_content = metadata_part + f"<original_content>\n{original_content}\n</original_content>"
        
        # 3. Push back to Dify
        update_segment_in_dify(seg_id, final_writeback_content, keywords)
        
        # Rate limiting to be safe
        time.sleep(1)

    print("\n--- Optimization Complete! ---")

if __name__ == "__main__":
    main()
