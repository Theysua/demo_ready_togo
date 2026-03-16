import os
import glob
import json
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is not set.")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)
OUTPUT_FILE = "Goodyear_Structured_Knowledge_Base.md"

def extract_structured_knowledge(markdown_text):
    prompt = """You are an expert data structuring engine analyzing a Goodyear Tyre Product Catalogue page.
    If the text describes a specific Tire Product, extract the information into the following JSON schema. 
    If the page is just a table of contents, company history, or non-product page, return {"is_product": false}.

    Expected JSON format:
    {
      "is_product": true,
      "product_name": "Name of the tyre (e.g., EAGLE F1 ASYMMETRIC 6)",
      "product_features": ["Feature 1", "Feature 2"],
      "technology_descriptions": [
         {"name": "Tech Name", "description": "Tech Details"}
      ],
      "performance_charts": "Textual summary of the performance chart / radar chart",
      "available_sizes": ["195/55R15 85W", "245/45R18 100Y", ...]
    }
    
    CRITICAL RULES:
    1. Ensure `available_sizes` are listed exhaustively as an array of strings. DO NOT omit any sizes.
    2. Extract all technologies mentioned under 'Technology descriptions'.
    3. Return ONLY valid JSON. Nothing else.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": markdown_text}
            ],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error extracting knowledge: {e}")
        return None

def main():
    md_files = sorted(glob.glob("markdown_output/page_*.md"))
    if not md_files:
        print("No markdown files found in markdown_output/.")
        return
        
    print(f"Processing {len(md_files)} files for structured knowledge extraction...")
    structured_results = []
    
    for file in md_files:
        print(f"Analyzing {file}...")
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        result = extract_structured_knowledge(content)
        if result and result.get("is_product"):
            structured_results.append(result)
            print(f" -> Successfully extracted {result.get('product_name')}")
        else:
            print(" -> Not a product page.")
            
        time.sleep(0.5) # Rate limiting
            
    print(f"\nFound {len(structured_results)} product pages. Writing to {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write("# Goodyear Structured Product Knowledge Base\n\n")
        out.write("This document contains highly structured JSON-like knowledge extracted from the product catalogue.\n\n")
        
        for item in structured_results:
            out.write(f"---PRODUCT_BOUNDARY---\n")
            out.write(f"Product Name: **{item.get('product_name', 'Unknown')}**\n\n")
            
            # Features
            features = item.get('product_features', [])
            if features:
                out.write("[Product Features]\n")
                for f in features:
                    out.write(f"- {f}\n")
                out.write("\n")
                
            # Technology Descriptions
            techs = item.get('technology_descriptions', [])
            if techs:
                out.write("[Technology Descriptions]\n")
                for t in techs:
                    out.write(f"- **{t.get('name', 'Tech')}**: {t.get('description', '')}\n")
                out.write("\n")
                
            # Performance Charts
            perf = item.get('performance_charts', '')
            if perf:
                out.write("[Performance Charts]\n")
                out.write(f"{perf}\n\n")
                
            # Available Sizes
            sizes = item.get('available_sizes', [])
            if sizes:
                out.write("[Available Sizes]\n")
                # Instead of huge vertical lists, we can comma-separate them for token efficiency,
                # but bullet points are safer for deterministic chunking. We use comma separated blocks.
                # Actually, simple bullet points are fine.
                for s in sizes:
                    out.write(f"- {s}\n")
                out.write("\n")
                
            out.write("\n")

    print("Done! Structured Knowledge Base created.")

if __name__ == "__main__":
    main()
