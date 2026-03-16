import os
import base64
from io import BytesIO
from pdf2image import convert_from_path
from openai import OpenAI
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is not set in the .env file.")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# Configuration
PDF_FILE_PATH = "Product Catalogue 2023.pdf"
OUTPUT_DIR = "markdown_output"
START_PAGE = 7 # Resuming where the test left off
END_PAGE = 101 # Since convert_from_path last_page is inclusive

def encode_image(image):
    """Encodes a PIL image to a base64 string for OpenAI."""
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def parse_page_with_gpt(base64_image, page_num):
    """Sends the image to GPT-4o to extract text and tables as strict Markdown."""
    print(f"Sending Page {page_num} to GPT-4o for High-Fidelity Extraction...")
    
    prompt = """You are an expert OCR and document analysis AI. 
This is a page from a Goodyear Tyre Product Catalogue.
Your MUST perform high-fidelity extraction of this page into Markdown.

CRITICAL INSTRUCTIONS:
1. Extract ALL text faithfully. Keep headers (H1/H2) structured natively.
2. If you see ANY tabular data (like 'AVAILABLE SIZES', 'PERFORMANCE TEST RESULT', speed ratings, load indexes), you MUST format it as a STRICT Markdown table. Do not use lists for tabular data.
3. Every row in the table MUST be kept on a single line. DO NOT break table rows across multiple lines. For example, if you see '315/30ZR21' and '105Y' next to it, output: | 315/30ZR21 | 105Y |
4. Do NOT hallucinate data. If a cell is empty, leave it empty.
5. Ignore background graphics, but translate performance radar charts or bar charts into descriptive text summaries (e.g. "Performance Chart: Dry Handling 80/100, Wet Braking 90/100").
6. Output ONLY the raw Markdown content. Do not wrap it in a code block. Do not say 'Here is the markdown'.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Failed to process Page {page_num}: {e}")
        return ""

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"Loading {PDF_FILE_PATH}...")
    
    # We load pages one by one to save memory and avoid poppler timeouts
    # Only specifying the first few pages for demonstration/testing
    pages = convert_from_path(PDF_FILE_PATH, dpi=200, first_page=START_PAGE, last_page=END_PAGE)
    
    print(f"Loaded {len(pages)} pages to test.")
    
    for i, page_image in enumerate(pages):
        current_page = START_PAGE + i
        print(f"\n--- Processing Page {current_page} ---")
        
        base64_img = encode_image(page_image)
        markdown_text = parse_page_with_gpt(base64_img, current_page)
        
        if markdown_text:
            output_file = os.path.join(OUTPUT_DIR, f"page_{current_page:03d}.md")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown_text)
            print(f"Successfully saved Markdown to {output_file}")
            
    print("\nExtraction test complete! Check the 'markdown_output' folder.")

if __name__ == "__main__":
    main()
