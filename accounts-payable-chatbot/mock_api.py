from fastapi import FastAPI, Depends, HTTPException, Header, Body
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_api")

app = FastAPI(title="Goodyear AP Mock External Tools API")

# --- Mock Database ---
INVOICES = {
    "INV-1001": {"invoice_id": "INV-1001", "vendor_id": "VEND001", "amount": 5000.0, "status": "Pending", "po_number": "PO-9901", "due_date": "2026-04-15", "missing_gr": False},
    "INV-1002": {"invoice_id": "INV-1002", "vendor_id": "VEND001", "amount": 1200.0, "status": "Paid", "po_number": "PO-9902", "due_date": "2026-03-01", "missing_gr": False},
    "INV-2001": {"invoice_id": "INV-2001", "vendor_id": "VEND002", "amount": 8500.0, "status": "Pending", "po_number": "PO-9903", "due_date": "2026-05-01", "missing_gr": True},  # Missing GR scenario
    "INV-2002": {"invoice_id": "INV-2002", "vendor_id": "VEND002", "amount": 4300.0, "status": "In Review", "po_number": "PO-9904", "due_date": "2026-04-22", "missing_gr": False},
}

VENDOR_EMAIL_TO_ID = {
    "vendor@demo.com": "VEND001",
    "vendora@demo.com": "VEND001",
    "vendorb@demo.com": "VEND002",
}

# In Dify, we'll pass the user ID/email via headers or query to determine role/identity for tool calls.
# Dify tool context can pass parameters. For simplicity, we'll accept 'X-User-Email' and 'X-User-Role' headers
# to simulate the identity context if needed, or take vendor_id/role in the body if it's a POST.

def get_auth_context(x_user_email: str = Header("unknown"), x_user_role: str = Header("internal")):
    # Derive the vendor scope from the authenticated email so vendors cannot
    # widen access by passing a different vendor_id in the tool parameters.
    email = x_user_email.lower().strip()
    role = x_user_role.strip().lower()
    return {
        "email": email,
        "role": role,
        "vendor_id": VENDOR_EMAIL_TO_ID.get(email),
    }

# --- Models ---
class Invoice(BaseModel):
    invoice_id: str
    vendor_id: str
    amount: float
    status: str
    po_number: str
    due_date: str
    missing_gr: bool

class GRRequest(BaseModel):
    po_number: str
    quantity: int
    delivery_date: str
    requester_email: str

class NotificationRequest(BaseModel):
    user_email: str
    message_content: str
    platform: str = "teams"

# --- 1. Invoice Query ---
@app.get("/api/invoices", response_model=List[Invoice])
async def list_invoices(vendor_id: Optional[str] = None, context: dict = Depends(get_auth_context)):
    role = context["role"]
    scoped_vendor_id = context.get("vendor_id")

    if role == "vendor" and not scoped_vendor_id:
        raise HTTPException(status_code=403, detail="Vendor account is not mapped to an authorized vendor_id.")

    results = []
    for inv in INVOICES.values():
        if role == "vendor":
            if inv["vendor_id"] != scoped_vendor_id:
                continue
        elif vendor_id and inv["vendor_id"] != vendor_id:
            continue
        results.append(inv)
    return results

@app.get("/api/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str, context: dict = Depends(get_auth_context)):
    role = context["role"]
    inv = INVOICES.get(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if role == "vendor":
        scoped_vendor_id = context.get("vendor_id")
        if not scoped_vendor_id:
            raise HTTPException(status_code=403, detail="Vendor account is not mapped to an authorized vendor_id.")
        if inv["vendor_id"] != scoped_vendor_id:
            raise HTTPException(status_code=404, detail="Invoice not found")

    return inv

# --- 2. Invoice Approval ---
@app.post("/api/invoices/{invoice_id}/approve")
async def approve_invoice(invoice_id: str, action: str = Body(default="approve", embed=True), context: dict = Depends(get_auth_context)):
    role = context["role"]
    if role != "internal":
        raise HTTPException(status_code=403, detail="Only internal approvers can approve invoices.")
        
    inv = INVOICES.get(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if action.lower() == "approve":
        inv["status"] = "Approved"
        logger.info(f"Invoice {invoice_id} approved by {context['email']}")
        return {"status": "success", "message": f"Invoice {invoice_id} has been Approved."}
    elif action.lower() == "reject":
        inv["status"] = "Rejected"
        logger.info(f"Invoice {invoice_id} rejected by {context['email']}")
        return {"status": "success", "message": f"Invoice {invoice_id} has been Rejected."}
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")

# --- 3. Goods Receipt Creation ---
@app.post("/api/goods-receipt")
async def create_goods_receipt(req: GRRequest, context: dict = Depends(get_auth_context)):
    role = context["role"]
    if role != "internal":
        raise HTTPException(status_code=403, detail="Only internal users can create a Goods Receipt.")
        
    logger.info(f"Initiating GR creation for PO {req.po_number} with quantity {req.quantity} on {req.delivery_date} by {req.requester_email}")
    
    # Mock updating the invoice status if it was waiting for GR
    for inv in INVOICES.values():
        if inv["po_number"] == req.po_number and inv["missing_gr"]:
            inv["missing_gr"] = False
            logger.info(f"Resolved missing GR for Invoice {inv['invoice_id']}")
            
    return {"status": "success", "message": f"Goods Receipt sequence initiated for PO {req.po_number}. A confirmation has been logged."}

# --- 4. Notifications ---
@app.post("/api/notifications")
async def send_notification(req: NotificationRequest, context: dict = Depends(get_auth_context)):
    logger.info(f"[MOCK NOTIFICATION via {req.platform.upper()}] To: {req.user_email} | Message: {req.message_content}")
    return {"status": "success", "message": f"Notification sent to {req.user_email} via {req.platform}."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
