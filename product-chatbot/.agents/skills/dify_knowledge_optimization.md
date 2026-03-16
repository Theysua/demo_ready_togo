---
name: Dify Knowledge Base Optimization
description: Techniques and scripts for extracting complex PDF data, bypassing Dify chunking limits, merging multi-page products, and fixing LLM truncation.
---

# Dify Knowledge Base Optimization Strategy

When building a high-accuracy, structured knowledge base in Dify from complex PDFs (such as product catalogs with extensive tables or multi-page product sheets), standard OCR and Dify's native chunking often fail. This skill outlines the proven strategies to overcome these limitations.

## Core Problems Addressed
1. **LLM Vision Truncation**: When asking OpenAI Vision API to extract a huge table (e.g., 94 available tire sizes), the LLM often gets "lazy", hallucinates, or truncates the results.
2. **Dify `###` Chunking Rupture**: Dify's default Markdown Document chunking aggressively splits parent chunks whenever it encounters `###` headers, breaking the integrity of a single product's context.
3. **Bulleted List Fragmentation**: A list of 30 sizes (separated by `\n`) will be split by Dify into 30 tiny, completely useless child segments without product context.
4. **Multi-Page Product Splits**: A single product spanning pages 10 and 11 creates duplicate, identical product names in the KB, isolating the performance charts from the features.

## 1. Safe Markdown Structuring (Anti-Chunk-Splitting)
To prevent Dify from ripping apart a single product entity:
- **Use custom boundaries instead of standard Markdown rules**:
  ```markdown
  ---PRODUCT_BOUNDARY---
  Product Name: **Super Tire X**
  
  [Product Features]
  - Feature 1
  - Feature 2
  
  [Available Sizes]
  225/40R18, 235/45R18, 245/40R19
  ```
- **Why?** Replacing `### Product Features` with `[Product Features]` hides the structural hierarchy from Dify's default chunker, keeping it all inside a single parent chunk.

## 2. Horizontal Data Density for Lists
Dify uses `\n` to chop child segments.
- **Bad Form**:
  ```
  [Available Sizes]
  - Size 1
  - Size 2
  - Size 3
  ```
  *(Result: 3 isolated child segments)*
- **Good Form**:
  ```
  [Available Sizes]
  - Size 1, Size 2, Size 3
  ```
  *(Result: 1 dense, context-rich child segment)*

## 3. Merging Multi-Page PDFs Structure
If `Page 14` has the Features and `Page 15` has the Sizes for the identical product, you MUST merge them programmatically before uploading to Dify.
- Build a Python script that splits the text by `---PRODUCT_BOUNDARY---`.
- Group by the `Product Name:` regex.
- Aggregate all lists uniquely (set union for sizes, features, etc).
- Output a single merged Markdown block per unique product name.

## 4. Dify API direct segment patching
When manual data patching is required, use Dify's REST API.

**List Document Segments**:
```python
GET http://{DIFY_API}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments
Headers: {"Authorization": "Bearer {DATASET_KEY}"}
```

**Update Segment**:
```python
POST http://{DIFY_API}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments/{SEGMENT_ID}
Headers: {"Authorization": "Bearer {DATASET_KEY}", "Content-Type": "application/json"}
Payload:
{
  "segment": {
    "content": "Full comma-separated string...",
    "answer": "",
    "keywords": ["..."]
  }
}
```

## 5. Streaming Validation (Bypassing Nginx Timeouts)
When performing bulk QA tests against your Dify API, use `response_mode: streaming` (SSE).
- The `blocking` mode will often be severed by Nginx with a `502/504 Bad Gateway` timeout if the LLM generation takes >60 seconds (common for enumerating 100+ sizes).
- Use `response.iter_lines()` in `requests` to capture Server-Sent Events dynamically to keep the connection alive.
