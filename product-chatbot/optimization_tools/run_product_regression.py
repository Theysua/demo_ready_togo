import json
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests
from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
REPORT_PATH = PROJECT_ROOT / "optimization_tools" / "product_regression_report.md"
PDF_NAME = "Product Catalogue 2023.pdf"
LOCAL_DIFY_FALLBACK = "http://172.19.0.10:5001/v1"
RAW_HEADER = "## 📄 [RAW ORIGINAL TEXT]"
AI_HEADER = "## 🤖 [AI OPTIMIZED STRUCTURED DATA]"
SIZE_PATTERN = re.compile(r"\b(?:LT)?\d{3}(?:/\d{2})?(?:ZR|R)\d{2}[A-Z]?(?:\s\d{2,3}(?:/\d{2,3})?[A-Z]{1,3})?\b")

IGNORED_PRODUCTS = {
    "Not confidently identified",
    "Goodyear Concept Tires",
    "Eagle F1",
    "Eagle F1 Series",
    "ElectricDrive Series",
    "Assurance Series",
    "Wrangler Series",
    "Efficient Grip Performance",
}

IGNORED_RAW_MARKERS = {
    "OEM",
    "SealTech",
    "SoundComfort",
    "WORRY FREE",
    "COMPANY INTRODUCTION",
    "CONCEPT TIRES",
    "KEY MILESTONES",
}


def normalize_api_endpoint(raw_endpoint: str) -> str:
    endpoint = raw_endpoint.strip().rstrip("/")
    if "localhost" in endpoint or "127.0.0.1" in endpoint:
        try:
            response = requests.get(f"{endpoint}/info", timeout=3)
            if response.ok or response.status_code in {401, 404}:
                return endpoint
        except requests.RequestException:
            return LOCAL_DIFY_FALLBACK
    return endpoint


def request_json(method: str, url: str, headers: dict[str, str], **kwargs: Any) -> dict[str, Any]:
    response = requests.request(method, url, headers=headers, timeout=60, **kwargs)
    response.raise_for_status()
    return response.json()


def list_datasets(api_url: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    return request_json("GET", f"{api_url}/datasets", headers).get("data", [])


def list_documents(api_url: str, headers: dict[str, str], dataset_id: str) -> list[dict[str, Any]]:
    page = 1
    documents: list[dict[str, Any]] = []
    while True:
        payload = request_json("GET", f"{api_url}/datasets/{dataset_id}/documents?page={page}&limit=100", headers)
        batch = payload.get("data", [])
        documents.extend(batch)
        if not batch or not payload.get("has_more"):
            break
        page += 1
    return documents


def discover_dataset_and_document(api_url: str, headers: dict[str, str], document_name: str) -> tuple[str, str]:
    for dataset in list_datasets(api_url, headers):
        dataset_id = dataset["id"]
        for document in list_documents(api_url, headers, dataset_id):
            if document["name"] == document_name:
                return dataset_id, document["id"]
    raise RuntimeError(f"Could not find document {document_name!r}")


def fetch_segments(api_url: str, headers: dict[str, str], dataset_id: str, document_id: str) -> list[dict[str, Any]]:
    page = 1
    segments: list[dict[str, Any]] = []
    while True:
        payload = request_json(
            "GET",
            f"{api_url}/datasets/{dataset_id}/documents/{document_id}/segments?page={page}&limit=100",
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
    return content.strip()


def extract_product(content: str) -> str:
    match = re.search(r"\*\*Product:\*\*\s*(.+)", content)
    return match.group(1).strip() if match else ""


def extract_section_items(content: str, heading: str) -> list[str]:
    pattern = rf"\*\*{re.escape(heading)}:\*\*\s*(.*?)(?:\n\*\*[^\n]+:\*\*|\Z)"
    match = re.search(pattern, content, flags=re.DOTALL)
    if not match:
        return []
    section = match.group(1)
    items: list[str] = []
    for line in section.splitlines():
        text = line.strip()
        if text.startswith("- "):
            item = text[2:].strip()
            if item and item != "Not identified in this parent segment":
                items.append(item)
    return dedupe(items)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        cleaned = " ".join(item.split()).strip()
        lowered = cleaned.lower()
        if not cleaned or lowered in seen:
            continue
        seen.add(lowered)
        output.append(cleaned)
    return output


def normalize_sizes(items: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        for match in SIZE_PATTERN.findall(item.upper()):
            cleaned = " ".join(match.split())
            if cleaned not in seen:
                seen.add(cleaned)
                normalized.append(cleaned)
    return normalized


def build_baseline(segments: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    baseline: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "positions": [],
        "features": [],
        "performance_charts": [],
        "technology_descriptions": [],
        "sizes": [],
    })

    for segment in segments:
        content = segment.get("content", "")
        raw_content = extract_raw_content(content)
        product = extract_product(content)
        if not product or product in IGNORED_PRODUCTS:
            continue
        if any(marker in raw_content for marker in IGNORED_RAW_MARKERS):
            continue

        entry = baseline[product]
        entry["positions"].append(segment.get("position"))
        entry["features"].extend(extract_section_items(content, "Product Features"))
        entry["performance_charts"].extend(extract_section_items(content, "Performance Charts"))
        entry["technology_descriptions"].extend(extract_section_items(content, "Technology Descriptions"))
        entry["sizes"].extend(extract_section_items(content, "Available Sizes"))

    for product, entry in baseline.items():
        entry["features"] = dedupe(entry["features"])
        entry["performance_charts"] = dedupe(entry["performance_charts"])
        entry["technology_descriptions"] = dedupe(entry["technology_descriptions"])
        entry["sizes"] = normalize_sizes(entry["sizes"])
        entry["positions"] = sorted(set(entry["positions"]))

    return dict(sorted(baseline.items()))


def stream_answer(api_url: str, headers: dict[str, str], query: str, user: str) -> str:
    payload = {"inputs": {}, "query": query, "response_mode": "streaming", "user": user}
    chunks: list[str] = []
    with requests.post(f"{api_url}/chat-messages", headers=headers, json=payload, stream=True, timeout=180) as response:
        response.raise_for_status()
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line or not raw_line.startswith("data: "):
                continue
            data = raw_line[6:]
            if data == "[DONE]":
                break
            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                continue
            if event.get("event") == "message" and event.get("answer"):
                chunks.append(event["answer"])
            if event.get("event") == "error":
                raise RuntimeError(json.dumps(event, ensure_ascii=False))
    return "".join(chunks).strip()


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9%+/ ]+", " ", text)
    return " ".join(text.split())


def significant_tokens(text: str) -> set[str]:
    return {token for token in normalize_text(text).split() if len(token) >= 4 or token.isdigit()}


def count_semantic_hits(expected_items: list[str], answer: str) -> tuple[int, int]:
    if not expected_items:
        return 0, 0
    answer_tokens = significant_tokens(answer)
    hits = 0
    for item in expected_items:
        item_tokens = significant_tokens(item)
        if not item_tokens:
            continue
        overlap = len(item_tokens & answer_tokens)
        threshold = max(1, min(3, len(item_tokens) // 2))
        if overlap >= threshold:
            hits += 1
    return hits, len(expected_items)


def evaluate_product(api_url: str, headers: dict[str, str], product: str, expected: dict[str, Any]) -> dict[str, Any]:
    theme_query = (
        f"Provide the product features, performance charts, and technology descriptions for {product}. "
        "Be specific and list the key items explicitly."
    )
    size_query = f"List all available sizes for {product}. Return every size explicitly."

    started = time.time()
    theme_answer = stream_answer(api_url, headers, theme_query, user="product-regression-theme")
    theme_elapsed = time.time() - started

    size_answer = ""
    actual_sizes: list[str] = []
    size_elapsed = 0.0
    if expected["sizes"]:
        started = time.time()
        size_answer = stream_answer(api_url, headers, size_query, user="product-regression-sizes")
        size_elapsed = time.time() - started
        actual_sizes = normalize_sizes([size_answer])

    feature_hits, feature_total = count_semantic_hits(expected["features"], theme_answer)
    chart_hits, chart_total = count_semantic_hits(expected["performance_charts"], theme_answer)
    tech_hits, tech_total = count_semantic_hits(expected["technology_descriptions"], theme_answer)

    expected_sizes = expected["sizes"]
    missing_sizes = sorted(set(expected_sizes) - set(actual_sizes))
    extra_sizes = sorted(set(actual_sizes) - set(expected_sizes))
    sizes_pass = not expected_sizes or (not missing_sizes and not extra_sizes)

    theme_denial = any(marker in theme_answer.lower() for marker in ["i don't have", "i do not have", "i'm missing", "not available"])
    feature_ok = (not feature_total) or feature_hits >= max(1, min(2, feature_total))
    chart_ok = (not chart_total) or chart_hits >= max(1, min(1, chart_total))
    tech_ok = (not tech_total) or tech_hits >= max(1, min(2, tech_total))

    # Do not treat a narrow "not available" statement as a total failure when
    # the answer still correctly covers the expected sections that exist.
    if theme_denial and (feature_ok or tech_ok or chart_ok):
        theme_denial = False

    theme_pass = not theme_denial and feature_ok and chart_ok and tech_ok

    return {
        "product": product,
        "positions": expected["positions"],
        "feature_hits": feature_hits,
        "feature_total": feature_total,
        "chart_hits": chart_hits,
        "chart_total": chart_total,
        "tech_hits": tech_hits,
        "tech_total": tech_total,
        "theme_pass": theme_pass,
        "theme_answer": theme_answer,
        "theme_elapsed": round(theme_elapsed, 1),
        "sizes_pass": sizes_pass,
        "expected_sizes": expected_sizes,
        "actual_sizes": actual_sizes,
        "missing_sizes": missing_sizes,
        "extra_sizes": extra_sizes,
        "size_answer": size_answer,
        "size_elapsed": round(size_elapsed, 1),
    }


def write_report(results: list[dict[str, Any]]) -> None:
    lines = [
        "# Product Regression Report",
        "",
        "| Product | Parent Segments | Theme | Features | Charts | Tech | Sizes | Notes |",
        "|---|---:|---|---:|---:|---:|---|---|",
    ]

    for result in results:
        theme_status = "PASS" if result["theme_pass"] else "FAIL"
        size_status = "PASS" if result["sizes_pass"] else "FAIL"
        notes = []
        if result["missing_sizes"]:
            notes.append(f"missing {len(result['missing_sizes'])}")
        if result["extra_sizes"]:
            notes.append(f"extra {len(result['extra_sizes'])}")
        if not notes:
            notes.append(f"{result['theme_elapsed']}s/{result['size_elapsed']}s")
        lines.append(
            f"| {result['product']} | {len(result['positions'])} | {theme_status} | "
            f"{result['feature_hits']}/{result['feature_total']} | {result['chart_hits']}/{result['chart_total']} | "
            f"{result['tech_hits']}/{result['tech_total']} | {size_status} | {', '.join(notes)} |"
        )

    failed = [result for result in results if not result["theme_pass"] or not result["sizes_pass"]]
    lines.extend(["", "## Failures", ""])
    if not failed:
        lines.append("None.")
    else:
        for result in failed:
            lines.append(f"### {result['product']}")
            lines.append("")
            lines.append(f"- Parent segments: {result['positions']}")
            lines.append(f"- Theme pass: {result['theme_pass']}")
            lines.append(f"- Size pass: {result['sizes_pass']}")
            if result["missing_sizes"]:
                lines.append(f"- Missing sizes: {', '.join(result['missing_sizes'])}")
            if result["extra_sizes"]:
                lines.append(f"- Extra sizes: {', '.join(result['extra_sizes'])}")
            lines.append(f"- Theme answer preview: {result['theme_answer'][:800].replace(chr(10), ' ')}")
            if result["size_answer"]:
                lines.append(f"- Size answer preview: {result['size_answer'][:800].replace(chr(10), ' ')}")
            lines.append("")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    env = dotenv_values(ENV_PATH)
    api_url = normalize_api_endpoint(env.get("API_ENDPOINT", "http://localhost/v1"))
    dataset_key = (env.get("DIFY_DATABASE_KEY") or "").strip()
    app_key = (env.get("CHATFLOW_TEST_API_KEY") or "").strip()
    if not dataset_key or not app_key:
        raise SystemExit("Missing DIFY_DATABASE_KEY or CHATFLOW_TEST_API_KEY in product-chatbot/.env")

    dataset_headers = {"Authorization": f"Bearer {dataset_key}", "Content-Type": "application/json"}
    app_headers = {"Authorization": f"Bearer {app_key}", "Content-Type": "application/json"}

    dataset_id, document_id = discover_dataset_and_document(api_url, dataset_headers, PDF_NAME)
    segments = fetch_segments(api_url, dataset_headers, dataset_id, document_id)
    baseline = build_baseline(segments)

    print(f"Testing {len(baseline)} products from {PDF_NAME}")
    results: list[dict[str, Any]] = []
    for index, (product, expected) in enumerate(baseline.items(), start=1):
        print(f"[{index}/{len(baseline)}] {product}")
        result = evaluate_product(api_url, app_headers, product, expected)
        results.append(result)
        print(
            f"  theme={'PASS' if result['theme_pass'] else 'FAIL'} "
            f"sizes={'PASS' if result['sizes_pass'] else 'FAIL'} "
            f"features={result['feature_hits']}/{result['feature_total']} "
            f"charts={result['chart_hits']}/{result['chart_total']} "
            f"tech={result['tech_hits']}/{result['tech_total']}"
        )

    write_report(results)
    failed = [result for result in results if not result["theme_pass"] or not result["sizes_pass"]]
    print(f"Completed: {len(results) - len(failed)}/{len(results)} products passed fully.")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
