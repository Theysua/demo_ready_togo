import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
BACKUP_DIR = PROJECT_ROOT / "optimization_tools" / "backups"

DEFAULT_DOCUMENT_NAME = "Product Catalogue 2023.pdf"
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_LIMIT = 100
LOCAL_DIFY_FALLBACK = "http://172.19.0.10:5001/v1"
RAW_HEADER = "## 📄 [RAW ORIGINAL TEXT]"
AI_HEADER = "## 🤖 [AI OPTIMIZED STRUCTURED DATA]"
PRODUCT_GUARDRAILS = {
    "Assurance ComfortTred": "This parent segment belongs only to Assurance ComfortTred. Do not mix with Assurance TripleMax, EfficientGrip Performance, or SUV products.",
    "Assurance TripleMax": "This parent segment belongs only to Assurance TripleMax. Do not mix with Assurance TripleMax 2 or OEM fitment tables.",
    "Cargo Marathon 2": "This parent segment belongs only to Cargo Marathon 2 light truck sizes. Do not mix with SUV or passenger tire sizes.",
    "Eagle F1 Asymmetric 3": "This parent segment belongs only to Eagle F1 Asymmetric 3. Do not mix with Eagle F1 Asymmetric 5, Eagle F1 Asymmetric 6, or Eagle F1 Asymmetric 3 SUV.",
    "Eagle F1 Asymmetric 6": "This parent segment belongs only to Eagle F1 Asymmetric 6. Do not mix with Eagle F1 Asymmetric 3 or Eagle F1 Asymmetric 5.",
    "EfficientGrip Performance": "This parent segment belongs only to EfficientGrip Performance passenger tire sizes. Do not mix with EfficientGrip Performance SUV, EfficientGrip SUV, SealTech, SoundComfort, or OEM fitment tables.",
    "EfficientGrip Performance SUV": "This parent segment belongs only to EfficientGrip Performance SUV. Do not mix with EfficientGrip Performance passenger sizes or EfficientGrip SUV.",
    "Optilife 3": "This parent segment belongs only to Optilife 3 passenger sizes. Do not mix with Optilife 3 SUV or Optilife 3 Plus SUV.",
    "Wrangler AT SilentTrac": "This parent segment belongs only to Wrangler AT SilentTrac. Do not mix with Wrangler AT Adventure, Wrangler Duratrac RT, or Wrangler MT/R.",
}


def load_env() -> dict[str, str]:
    load_dotenv(ENV_PATH)
    values: dict[str, str] = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def normalize_api_endpoint(raw_endpoint: str) -> str:
    endpoint = raw_endpoint.strip().rstrip("/")
    if "localhost" in endpoint or "127.0.0.1" in endpoint:
        try:
            resp = requests.get(f"{endpoint}/info", timeout=3)
            if resp.ok or resp.status_code in {401, 404}:
                return endpoint
        except requests.RequestException:
            return LOCAL_DIFY_FALLBACK
    return endpoint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="In-place hybrid optimization for Dify PDF parent segments.")
    parser.add_argument("--document-name", default=DEFAULT_DOCUMENT_NAME, help="Target Dify document name.")
    parser.add_argument("--dataset-id", default="", help="Optional explicit Dify dataset ID.")
    parser.add_argument("--document-id", default="", help="Optional explicit Dify document ID.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="API pagination limit.")
    parser.add_argument("--start-position", type=int, default=1, help="Start processing from this parent segment position.")
    parser.add_argument("--max-segments", type=int, default=0, help="Only process the first N segments for verification.")
    parser.add_argument("--delay-seconds", type=float, default=0.5, help="Delay between segment updates.")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL), help="OpenAI model for extraction.")
    parser.add_argument("--dry-run", action="store_true", help="Build hybrid content locally without pushing updates.")
    parser.add_argument("--force", action="store_true", help="Rebuild even if the segment already contains the hybrid headers.")
    return parser.parse_args()


def build_headers(dify_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {dify_key}", "Content-Type": "application/json"}


def request_json(method: str, url: str, headers: dict[str, str], **kwargs: Any) -> dict[str, Any]:
    response = requests.request(method, url, headers=headers, timeout=60, **kwargs)
    response.raise_for_status()
    return response.json()


def list_datasets(api_url: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    return request_json("GET", f"{api_url}/datasets", headers).get("data", [])


def list_documents(api_url: str, headers: dict[str, str], dataset_id: str, limit: int) -> list[dict[str, Any]]:
    page = 1
    documents: list[dict[str, Any]] = []
    while True:
        payload = request_json(
            "GET",
            f"{api_url}/datasets/{dataset_id}/documents?page={page}&limit={limit}",
            headers,
        )
        batch = payload.get("data", [])
        documents.extend(batch)
        if not batch or not payload.get("has_more"):
            break
        page += 1
    return documents


def discover_dataset_and_document(
    api_url: str,
    headers: dict[str, str],
    document_name: str,
    explicit_dataset_id: str,
    explicit_document_id: str,
    limit: int,
) -> tuple[str, str]:
    if explicit_dataset_id and explicit_document_id:
        return explicit_dataset_id, explicit_document_id

    if explicit_dataset_id:
        documents = list_documents(api_url, headers, explicit_dataset_id, limit)
        for document in documents:
            if document["name"] == document_name:
                return explicit_dataset_id, document["id"]
        raise ValueError(f"Document '{document_name}' not found in dataset {explicit_dataset_id}.")

    for dataset in list_datasets(api_url, headers):
        dataset_id = dataset["id"]
        documents = list_documents(api_url, headers, dataset_id, limit)
        for document in documents:
            if document["name"] == document_name:
                return dataset_id, document["id"]

    raise ValueError(f"Document '{document_name}' not found in accessible datasets.")


def fetch_segments(api_url: str, headers: dict[str, str], dataset_id: str, document_id: str, limit: int) -> list[dict[str, Any]]:
    page = 1
    segments: list[dict[str, Any]] = []
    while True:
        payload = request_json(
            "GET",
            f"{api_url}/datasets/{dataset_id}/documents/{document_id}/segments?page={page}&limit={limit}",
            headers,
        )
        batch = payload.get("data", [])
        segments.extend(batch)
        if not batch or not payload.get("has_more"):
            break
        page += 1
    return sorted(segments, key=lambda segment: segment.get("position", 0))


def extract_raw_content(content: str) -> str:
    if RAW_HEADER in content and AI_HEADER in content:
        match = re.search(
            rf"{re.escape(RAW_HEADER)}\s*(.*?)\s*---\s*{re.escape(AI_HEADER)}",
            content,
            flags=re.DOTALL,
        )
        if match:
            return match.group(1).strip()
    if "<original_content>" in content:
        match = re.search(r"<original_content>\s*(.*?)\s*</original_content>", content, flags=re.DOTALL)
        if match:
            return match.group(1).strip()
    return content.strip()


def build_backup(segments: list[dict[str, Any]], dataset_id: str, document_id: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = BACKUP_DIR / f"segments_before_{dataset_id}_{document_id}_{timestamp}.jsonl"
    with backup_path.open("w", encoding="utf-8") as handle:
        for segment in segments:
            raw_content = extract_raw_content(segment.get("content", ""))
            handle.write(
                json.dumps(
                    {
                        "id": segment["id"],
                        "position": segment.get("position"),
                        "word_count": segment.get("word_count"),
                        "keywords": segment.get("keywords"),
                        "content": segment.get("content", ""),
                        "raw_content": raw_content,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return backup_path


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        cleaned = " ".join(item.split()).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        output.append(cleaned)
    return output


def build_extraction_prompt(previous_product: str | None, previous_raw: str, current_raw: str, next_raw: str) -> str:
    last_product = previous_product or "None"
    return f"""
You are optimizing a Dify knowledge base for high-precision retrieval over a complex Goodyear tire catalogue PDF.

Your job is to analyze the CURRENT parent segment while using adjacent parent-segment context to repair broken tables and page-split products.

Rules:
1. Never invent facts that are not supported by the current/adjacent text.
2. Prefer CURRENT segment facts first. Use PREVIOUS/NEXT context only to repair continuity.
3. If the CURRENT segment is clearly a continuation of the previous product, inherit the product identity from last_identified_product.
4. Extract the information that will make this single parent segment answerable for:
   - Product features
   - Performance charts / performance test result
   - Available sizes
   - Technology descriptions
   - Category / target audience
5. If a field is not present, return an empty string or empty array.
6. keywords must be <= 10 items, high-signal, retrieval-focused, including product names and exact tire sizes when present.
7. Very important: if the CURRENT segment is an OEM fitment table, a cross-brand compatibility table, a generic technology explainer
   (for example SoundComfort or SealTech), a company/brand history page, or a family/series overview page without a single concrete
   sellable product focus, then set "is_product" to false, leave "product_name" empty, and do not assign sizes/keywords to a specific product.
8. Do not attach OEM fitment sizes to a retail product. If the text contains repeated columns such as COUNTRY/OEM/MODEL/TIRE SIZE/GOODYEAR PRODUCT,
   that is not a product page and must stay unassigned.
9. Do not attach generic technology benefits to a specific product unless the current segment explicitly states the product name on that page.

last_identified_product: {last_product}

Return strictly valid JSON with this shape:
{{
  "is_product": true,
  "product_name": "",
  "category": "",
  "target_audience": "",
  "features": [],
  "performance_charts": [],
  "technology_descriptions": [],
  "sizes": [],
  "keywords": []
}}

PREVIOUS SEGMENT:
{previous_raw}

CURRENT SEGMENT:
{current_raw}

NEXT SEGMENT:
{next_raw}
""".strip()


def extract_structured_data(
    client: OpenAI,
    model: str,
    previous_product: str | None,
    previous_raw: str,
    current_raw: str,
    next_raw: str,
) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You extract structured product context for RAG optimization."},
            {
                "role": "user",
                "content": build_extraction_prompt(previous_product, previous_raw, current_raw, next_raw),
            },
        ],
    )
    payload = json.loads(response.choices[0].message.content)
    return {
        "is_product": bool(payload.get("is_product")),
        "product_name": str(payload.get("product_name", "")).strip(),
        "category": str(payload.get("category", "")).strip(),
        "target_audience": str(payload.get("target_audience", "")).strip(),
        "features": dedupe([str(item) for item in payload.get("features", [])]),
        "performance_charts": dedupe([str(item) for item in payload.get("performance_charts", [])]),
        "technology_descriptions": dedupe([str(item) for item in payload.get("technology_descriptions", [])]),
        "sizes": dedupe([str(item) for item in payload.get("sizes", [])]),
        "keywords": dedupe([str(item) for item in payload.get("keywords", [])])[:10],
    }


def apply_non_product_overrides(raw_content: str, structured: dict[str, Any]) -> dict[str, Any]:
    raw_upper = raw_content.upper()
    oem_markers = ["OEM", "GOODYEAR PRODUCT", "TIRE SIZE", "MODEL", "OE FITMENT"]
    if all(marker in raw_upper for marker in oem_markers):
        structured.update(
            {
                "is_product": False,
                "product_name": "",
                "category": "",
                "target_audience": "",
                "features": [],
                "performance_charts": [],
                "technology_descriptions": [],
                "sizes": [],
                "keywords": [],
            }
        )
        return structured

    generic_technology_markers = [
        "SEALTECH",
        "SOUNDCOMFORT",
        "ROAD HAZARD PROTECTION",
        "EMERGENCY ROADSIDE ASSISTANCE",
        "ORIGINAL CAR FITMENT",
    ]
    if any(marker in raw_upper for marker in generic_technology_markers) and "AVAILABLE SIZES" not in raw_upper:
        structured.update(
            {
                "is_product": False,
                "product_name": "",
                "category": "",
                "target_audience": "",
                "sizes": [],
                "keywords": [],
            }
        )
        return structured

    if not structured.get("is_product"):
        structured.update(
            {
                "product_name": "",
                "category": "",
                "target_audience": "",
                "features": [],
                "performance_charts": [],
                "technology_descriptions": [],
                "sizes": [],
                "keywords": [],
            }
        )
    return structured


def build_hybrid_content(raw_content: str, structured: dict[str, Any]) -> str:
    lines: list[str] = [RAW_HEADER, raw_content.strip(), "---", AI_HEADER]

    product_name = structured.get("product_name") or "Not confidently identified"
    lines.append(f"**Product:** {product_name}")

    if structured.get("category"):
        lines.append(f"**Category:** {structured['category']}")
    if structured.get("target_audience"):
        lines.append(f"**Target Audience:** {structured['target_audience']}")

    lines.append("")
    lines.append("**Product Features:**")
    features = structured.get("features", [])
    lines.extend(f"- {item}" for item in features) if features else lines.append("- Not identified in this parent segment")

    lines.append("")
    lines.append("**Performance Charts:**")
    charts = structured.get("performance_charts", [])
    lines.extend(f"- {item}" for item in charts) if charts else lines.append("- Not identified in this parent segment")

    lines.append("")
    lines.append("**Technology Descriptions:**")
    tech = structured.get("technology_descriptions", [])
    lines.extend(f"- {item}" for item in tech) if tech else lines.append("- Not identified in this parent segment")

    lines.append("")
    lines.append("**Available Sizes:**")
    sizes = structured.get("sizes", [])
    lines.extend(f"- {item}" for item in sizes) if sizes else lines.append("- Not identified in this parent segment")
    if sizes:
        lines.append("")
        lines.append(f"**Available Size Count:** {len(sizes)}")

    guardrail = PRODUCT_GUARDRAILS.get(product_name)
    if guardrail:
        lines.append("")
        lines.append(f"**Product Boundary Note:** {guardrail}")

    lines.append("")
    lines.append(f"**Keywords:** {', '.join(structured.get('keywords', [])) or 'None'}")
    return "\n".join(lines).strip() + "\n"


def update_segment(
    api_url: str,
    headers: dict[str, str],
    dataset_id: str,
    document_id: str,
    segment_id: str,
    hybrid_content: str,
    keywords: list[str],
) -> None:
    update_url = f"{api_url}/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}"

    # Dify parent-child documents do not persist keywords when content changes in the same update.
    # We therefore update content first, then immediately perform a second pass that sets keywords
    # while the content is unchanged, forcing child chunk regeneration in both steps.
    content_payload = {
        "segment": {
            "content": hybrid_content,
            "answer": "",
            "regenerate_child_chunks": True,
        }
    }
    response = requests.post(update_url, headers=headers, json=content_payload, timeout=60)
    response.raise_for_status()

    keyword_payload = {
        "segment": {
            "content": hybrid_content,
            "answer": "",
            "keywords": keywords,
            "regenerate_child_chunks": True,
        }
    }
    response = requests.post(update_url, headers=headers, json=keyword_payload, timeout=60)
    response.raise_for_status()


def main() -> None:
    args = parse_args()
    env = load_env()
    dify_key = env.get("DIFY_DATABASE_KEY", "").strip()
    openai_key = env.get("OPENAI_API_KEY", "").strip()
    api_url = normalize_api_endpoint(env.get("API_ENDPOINT", "http://localhost/v1"))

    if not dify_key or not openai_key:
        raise SystemExit("Missing DIFY_DATABASE_KEY or OPENAI_API_KEY in product-chatbot/.env")

    headers = build_headers(dify_key)
    dataset_id, document_id = discover_dataset_and_document(
        api_url,
        headers,
        args.document_name,
        args.dataset_id,
        args.document_id,
        args.limit,
    )
    print(f"Using dataset={dataset_id} document={document_id} ({args.document_name})")

    segments = fetch_segments(api_url, headers, dataset_id, document_id, args.limit)
    backup_path = build_backup(segments, dataset_id, document_id)
    print(f"Backed up {len(segments)} segments to {backup_path}")

    segments = [segment for segment in segments if segment.get("position", 0) >= args.start_position]

    if args.max_segments > 0:
        segments = segments[: args.max_segments]
        print(f"Processing {len(segments)} segments for this run starting at position {args.start_position}.")

    client = OpenAI(api_key=openai_key)
    last_identified_product: str | None = None

    for index, segment in enumerate(segments):
        raw_current = extract_raw_content(segment.get("content", ""))
        already_hybrid = RAW_HEADER in segment.get("content", "") and AI_HEADER in segment.get("content", "")
        if already_hybrid and not args.force:
            print(f"[{index + 1}/{len(segments)}] segment={segment['id']} already hybrid, skipping")
            continue

        raw_previous = extract_raw_content(segments[index - 1]["content"]) if index > 0 else ""
        raw_next = extract_raw_content(segments[index + 1]["content"]) if index + 1 < len(segments) else ""

        print(
            f"[{index + 1}/{len(segments)}] segment={segment['id']} pos={segment.get('position')} "
            f"last_product={last_identified_product or 'None'}"
        )

        structured = extract_structured_data(
            client=client,
            model=args.model,
            previous_product=last_identified_product,
            previous_raw=raw_previous,
            current_raw=raw_current,
            next_raw=raw_next,
        )
        structured = apply_non_product_overrides(raw_current, structured)

        if structured.get("is_product") and structured.get("product_name"):
            last_identified_product = structured["product_name"]

        hybrid_content = build_hybrid_content(raw_current, structured)

        if args.dry_run:
            print(hybrid_content[:1600])
        else:
            update_segment(
                api_url=api_url,
                headers=headers,
                dataset_id=dataset_id,
                document_id=document_id,
                segment_id=segment["id"],
                hybrid_content=hybrid_content,
                keywords=structured["keywords"],
            )
            print(
                f"  updated product={structured.get('product_name') or 'N/A'} "
                f"features={len(structured['features'])} sizes={len(structured['sizes'])} "
                f"keywords={len(structured['keywords'])}"
            )
            time.sleep(args.delay_seconds)

    print("Optimization run complete.")


if __name__ == "__main__":
    main()
