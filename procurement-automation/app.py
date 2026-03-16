from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field


app = FastAPI(title="Procurement External Services Demo", version="1.0.0")


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
    base_price = item.target_unit_price or 120.0
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


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/vendor/quotes")
def get_vendor_quotes(payload: VendorQuoteRequest) -> dict:
    quotes = []
    grand_total = 0.0

    for item in payload.items:
        vendor_quotes = [
            build_quote(item, "Goodyear Supplier A", 0.98, 3),
            build_quote(item, "Goodyear Supplier B", 1.02, 5),
            build_quote(item, "Goodyear Supplier C", 0.95, 7),
        ]
        quotes.append(
            {
                "item_name": item.name,
                "recommended_vendor": min(vendor_quotes, key=lambda x: x["total_price"])[
                    "vendor_name"
                ],
                "options": vendor_quotes,
            }
        )
        grand_total += min(vendor_quotes, key=lambda x: x["total_price"])["total_price"]

    return {
        "request_id": payload.request_id,
        "currency": payload.currency,
        "quote_count": len(quotes),
        "estimated_total": round(grand_total, 2),
        "quotes": quotes,
    }


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
