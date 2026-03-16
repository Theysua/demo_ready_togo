import ast
import json
import re
from datetime import datetime
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field


app = FastAPI(title="Procurement External Services Demo", version="1.0.0")

CATALOG_OVERRIDES = {
    "macbook pro": 14999.0,
    "laptop": 6000.0,
    "notebook": 6000.0,
    "dell monitor": 2800.0,
    "monitor": 2800.0,
    "mouse": 299.0,
    "keyboard": 499.0,
    "razer blackwidow": 1299.0,
    "razer keyboard": 1299.0,
    "razer deathadder": 499.0,
    "razer mouse": 499.0,
    "razer headset": 899.0,
    "headset": 699.0,
}


class VendorItem(BaseModel):
    name: str = Field(..., description="Item name")
    quantity: int = Field(..., ge=1, description="Requested quantity")
    unit: str = Field(default="pcs", description="Unit of measure")
    target_unit_price: Optional[float] = Field(
        default=None, description="Target unit price for reference"
    )


class VendorQuoteRequest(BaseModel):
    request_id: str
    currency: str = "RMB"
    items: List[VendorItem]


class PoTemplateResponse(BaseModel):
    template_id: str
    template_name: str
    version: str
    format: str
    fields: List[str]
    template: dict


def build_quote(item: VendorItem, vendor_name: str, multiplier: float, eta_days: int) -> dict:
    base_price = item.target_unit_price or guess_target_unit_price(item.name)
    unit_price = round(base_price * multiplier, 2)
    total_price = round(unit_price * item.quantity, 2)
    return {
        "item_name": item.name,
        "quantity": item.quantity,
        "unit": item.unit,
        "vendor_name": vendor_name,
        "unit_price": unit_price,
        "total_price": total_price,
        "currency": "RMB",
        "lead_time_days": eta_days,
    }


def guess_target_unit_price(item_name: str) -> float:
    normalized = re.sub(r"[^a-z0-9]+", " ", item_name.lower()).strip()
    for keyword, price in CATALOG_OVERRIDES.items():
        if keyword in normalized:
            return price
    return 120.0


def parse_items_json_string(raw_value: str) -> list[dict[str, Any]]:
    candidate = raw_value.strip()
    if not candidate:
        raise ValueError("item_json_string is empty")

    for _ in range(3):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and isinstance(parsed.get("items"), list):
                return parsed["items"]
            candidate = json.dumps(parsed, ensure_ascii=False)
        except json.JSONDecodeError:
            if (
                len(candidate) >= 2
                and candidate[0] == candidate[-1]
                and candidate[0] in {"'", '"'}
            ):
                candidate = candidate[1:-1].strip()
                continue
            match = re.search(r"(\[[\s\S]*\])", candidate)
            if match:
                candidate = match.group(1)
                continue
            break
    raise ValueError(f"Failed to parse item_json_string: {raw_value}")


def parse_request_payload(raw_body: str) -> Any:
    body = raw_body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Request body is empty")

    for candidate in (body, body.replace("\r", "").replace("\n", "")):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Dify raw-text mode can occasionally send Python-like literals or a single quoted blob.
    try:
        return ast.literal_eval(body)
    except (SyntaxError, ValueError):
        pass

    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", body)
    if match:
        snippet = match.group(1)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(snippet)
            except (SyntaxError, ValueError):
                pass

    # Compatibility for Dify raw-text bodies such as:
    # The items:[...] Total budget mentioned (can be null):3000
    # The items:'[...]' Total budget mentioned (can be null):null
    if "The items:" in body:
        items_match = re.search(
            r"The items:\s*(.+?)\s*Total budget mentioned(?:\s*\(can be null\))?:\s*(.+)\s*$",
            body,
            flags=re.DOTALL,
        )
        if items_match:
            raw_items = items_match.group(1).strip()
            raw_budget = items_match.group(2).strip()
            payload: dict[str, Any] = {"item_json_string": raw_items}

            if raw_budget.lower() in {"null", "none", ""}:
                payload["total_budget_mentioned"] = None
            else:
                budget_match = re.search(r"-?\d+(?:\.\d+)?", raw_budget)
                payload["total_budget_mentioned"] = (
                    float(budget_match.group(0)) if budget_match else None
                )
            return payload

    raise HTTPException(
        status_code=422,
        detail="Request body is not valid JSON. Check the HTTP node body template.",
    )


def normalize_quote_request(payload: Any) -> VendorQuoteRequest:
    if isinstance(payload, list):
        return VendorQuoteRequest(
            request_id="PR-LOCAL-COMPAT",
            currency="RMB",
            items=[VendorItem(**item) for item in payload],
        )

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Expected a JSON object or list")

    request_id = payload.get("request_id") or "PR-LOCAL-COMPAT"
    currency = payload.get("currency") or "RMB"
    items = payload.get("items")

    if items is None and payload.get("item_json_string") is not None:
        try:
            items = parse_items_json_string(str(payload["item_json_string"]))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    if isinstance(items, str):
        try:
            items = parse_items_json_string(items)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not isinstance(items, list) or not items:
        raise HTTPException(
            status_code=422,
            detail=(
                "Missing valid items. Provide either an 'items' array or an "
                "'item_json_string' that can be parsed into an items array."
            ),
        )

    normalized_items: list[VendorItem] = []
    for raw_item in items:
        if not isinstance(raw_item, dict):
            raise HTTPException(status_code=422, detail="Each item must be an object")
        normalized_items.append(VendorItem(**raw_item))

    return VendorQuoteRequest(
        request_id=request_id,
        currency=currency,
        items=normalized_items,
    )


def build_quote_response(payload: VendorQuoteRequest, budget: Optional[float] = None) -> dict:
    quotes = []
    grand_total = 0.0

    for item in payload.items:
        vendor_quotes = [
            build_quote(item, "Goodyear Supplier A", 0.98, 3),
            build_quote(item, "Goodyear Supplier B", 1.02, 5),
            build_quote(item, "Goodyear Supplier C", 0.95, 7),
        ]
        cheapest = min(vendor_quotes, key=lambda x: x["total_price"])
        quotes.append(
            {
                "item_name": item.name,
                "recommended_vendor": cheapest["vendor_name"],
                "options": vendor_quotes,
            }
        )
        grand_total += cheapest["total_price"]

    response = {
        "request_id": payload.request_id,
        "currency": payload.currency,
        "quote_count": len(quotes),
        "estimated_total": round(grand_total, 2),
        "quotes": quotes,
    }
    if budget is not None:
        response["total_budget_mentioned"] = budget
        response["budget_gap"] = round(budget - grand_total, 2)
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/vendor/quotes")
async def get_vendor_quotes(request: Request) -> dict:
    raw_body = (await request.body()).decode("utf-8", errors="ignore")
    payload = normalize_quote_request(parse_request_payload(raw_body))
    return build_quote_response(payload)


@app.post("/api/vendor-quotations-bulk")
async def get_vendor_quotations_bulk(request: Request) -> dict:
    raw_body = (await request.body()).decode("utf-8", errors="ignore")
    raw_payload = parse_request_payload(raw_body)
    payload = normalize_quote_request(raw_payload)

    budget = raw_payload.get("total_budget_mentioned") if isinstance(raw_payload, dict) else None
    if budget is not None:
        try:
            budget = float(budget)
        except (TypeError, ValueError):
            budget = None

    return build_quote_response(payload, budget=budget)


@app.get("/api/po-template", response_model=PoTemplateResponse)
def get_po_template(
    company_code: str = Query(default="GYCN"),
    business_unit: str = Query(default="procurement"),
    language: str = Query(default="zh-CN"),
) -> PoTemplateResponse:
    return PoTemplateResponse(
        template_id=f"po-{company_code.lower()}-{language.lower()}",
        template_name="Standard Purchase Order Template",
        version="2026.03",
        format="json",
        fields=[
            "po_number",
            "request_id",
            "requester",
            "department",
            "supplier_name",
            "currency",
            "items",
            "subtotal",
            "tax",
            "total_amount",
            "delivery_address",
            "payment_terms",
            "approval_status",
        ],
        template={
            "po_number": "",
            "request_id": "",
            "requester": "",
            "department": business_unit,
            "supplier_name": "",
            "currency": "RMB",
            "items": [
                {
                    "item_name": "",
                    "quantity": 0,
                    "unit": "pcs",
                    "unit_price": 0,
                    "total_price": 0,
                }
            ],
            "subtotal": 0,
            "tax": 0,
            "total_amount": 0,
            "delivery_address": "",
            "payment_terms": "Net 30",
            "approval_status": "pending",
            "language": language,
            "company_code": company_code,
            "generated_at": datetime.utcnow().isoformat(),
        },
    )
