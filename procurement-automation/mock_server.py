import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Mock database of generic vendor quotations
VENDOR_QUOTES = {
    "MacBook Pro": [
        {"vendor": "Apple Store", "price": 14999, "lead_time_days": 2},
        {"vendor": "JD.com", "price": 14500, "lead_time_days": 1},
    ],
    "Dell Monitor": [
        {"vendor": "Dell Official", "price": 2999, "lead_time_days": 3},
        {"vendor": "JD.com", "price": 2800, "lead_time_days": 1},
    ],
    "Mouse": [
        {"vendor": "Gaming Gear Store", "price": 350, "lead_time_days": 1},
        {"vendor": "JD.com", "price": 299, "lead_time_days": 2},
    ],
    "Mice": [
        {"vendor": "Gaming Gear Store", "price": 350, "lead_time_days": 1},
        {"vendor": "JD.com", "price": 299, "lead_time_days": 2},
    ],
    "鼠标": [
        {"vendor": "Gaming Gear Store", "price": 350, "lead_time_days": 1},
        {"vendor": "JD.com", "price": 299, "lead_time_days": 2},
    ],
    "Chair": [
        {"vendor": "Ergo Furniture", "price": 1200, "lead_time_days": 5},
        {"vendor": "TaoBao", "price": 850, "lead_time_days": 3},
    ],
    "椅": [
        {"vendor": "Ergo Furniture", "price": 1200, "lead_time_days": 5},
        {"vendor": "TaoBao", "price": 850, "lead_time_days": 3},
    ]
}

PO_TEMPLATE = """
========================================
       PURCHASE ORDER (PO)
========================================
Date: {date}
PO Number: {po_number}

Items Requested:
{items}

Selected Vendor: {vendor}
Total Cost: {total_cost} RMB

Approval Status: {status}
========================================
"""

@app.route('/api/vendor-quotation', methods=['GET'])
def get_quotation():
    """
    Simulates fetching vendor quotes from external suppliers.
    Expects query params: ?item=itemName&quantity=X
    """
    item_name = request.args.get('item')
    quantity = request.args.get('quantity', 1, type=int)
    
    if not item_name:
        return jsonify({"error": "Missing 'item' parameter"}), 400
        
    # Case-insensitive naive match, fallback to generic numbers
    quotes = None
    for k, v in VENDOR_QUOTES.items():
        if k.lower() in item_name.lower():
            quotes = v
            break
            
    if not quotes:
        quotes = [
            {"vendor": "Generic Supplier A", "price": 5000, "lead_time_days": 3},
            {"vendor": "Generic Supplier B", "price": 4800, "lead_time_days": 5}
        ]
        
    results = []
    for q in quotes:
        results.append({
            "vendor": q["vendor"],
            "unit_price": q["price"],
            "total_price": q["price"] * quantity,
            "lead_time_days": q["lead_time_days"]
        })
        
    return jsonify({
        "item": item_name,
        "quantity": quantity,
        "quotations": results
    })
@app.route('/api/vendor-quotations-bulk', methods=['POST'])
def get_quotation_bulk():
    """
    Simulates fetching vendor quotes for multiple items at once.
    Expects JSON body: {"items": [{"name": "itemA", "quantity": 1}, ...]}
    """
    print(f"\n{'='*50}\n[RAW PAYLOAD DUMP]\n{request.data.decode('utf-8', errors='ignore')}\n{'='*50}")
    
    data = request.get_json(silent=True)
    
    # Dify might send the body as pure text if not configured perfectly, so fallback to raw data
    if data is None and request.data:
        import json
        try:
            data = json.loads(request.data)
        except json.JSONDecodeError:
            data = {}
            
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get('items')
    else:
        items = None
    
    # If Dify passed the items variable as a stringified JSON (due to our workaround), parse it here
    if isinstance(items, str):
        import json
        try:
            items = json.loads(items)
        except json.JSONDecodeError as e:
            print(f"[400 ERROR] Failed to parse stringified items: {items}")
            return jsonify({"error": f"Failed to parse stringified items: {str(e)}", "received_string": items}), 400

    if not items or not isinstance(items, list):
        print(f"[400 ERROR] Invalid items payload: {items}")
        return jsonify({"error": "Missing or invalid 'items' array in JSON body"}), 400
        
    print(f"[API HIT] Processing {len(items)} items from Dify...")
    
    all_results = []
    total_cost_all_items = 0
    
    for item in items:
        item_name = item.get('name')
        quantity = item.get('quantity', 1)
        
        if not item_name:
            continue
            
        quotes = None
        for k, v in VENDOR_QUOTES.items():
            if isinstance(item_name, str) and k.lower() in item_name.lower():
                quotes = v
                break
                
        if not quotes:
            quotes = [
                {"vendor": "Generic Supplier A", "price": 5000, "lead_time_days": 3},
                {"vendor": "Generic Supplier B", "price": 4800, "lead_time_days": 5}
            ]
            
        # Pick the cheapest for demo purposes
        best_quote = min(quotes, key=lambda x: x['price'])
        
        all_results.append({
            "item": item_name,
            "quantity": quantity,
            "vendor": best_quote["vendor"],
            "unit_price": best_quote["price"],
            "total_price": best_quote["price"] * quantity,
            "lead_time_days": best_quote["lead_time_days"]
        })
        total_cost_all_items += (best_quote["price"] * quantity)
        
    return jsonify({
        "results": all_results,
        "grand_total_cost": total_cost_all_items
    })

@app.route('/api/po-template', methods=['GET'])
def get_po_template():
    """
    Retrieves the company's standard Purchase Order format.
    """
    return jsonify({
        "template": PO_TEMPLATE,
        "instructions": "Replace {date}, {po_number}, {items}, {vendor}, {total_cost}, and {status} with actual values before sending to the human agent."
    })

if __name__ == '__main__':
    # Run on port 5001 to avoid colliding with Dify or other typical local services
    app.run(host='0.0.0.0', port=5001, debug=False)
