import requests
import json
import re

# We will simulate the LLM extraction locally. 
# In Dify, this would be an "LLM Node" configured with a JSON extraction prompt.
def simulate_llm_extraction(user_input):
    print(f"\n[LLM Node] Analyzing Request: '{user_input}'")
    
    # Simulating LLM JSON output for the demo
    extracted_data = {
        "items": [
            {"name": "MacBook Pro", "quantity": 5},
            {"name": "Dell Monitor", "quantity": 3}
        ],
        "total_budget_mentioned": 80000 
    }
    print(f"[LLM Node] Extracted JSON: {json.dumps(extracted_data, indent=2)}")
    return extracted_data

# In Dify, this is an "HTTP Request Node" (or Custom Tool)
def fetch_vendor_quotations(items):
    print("\n[Tool Node] Fetching real-time vendor quotations...")
    all_quotes = {}
    for item in items:
        # Calling our local Python Mock Server
        res = requests.get(f"http://127.0.0.1:5001/api/vendor-quotation?item={item['name']}&quantity={item['quantity']}")
        if res.status_code == 200:
            data = res.json()
            # Pick the cheapest vendor for demo purposes
            best_quote = min(data['quotations'], key=lambda x: x['total_price'])
            all_quotes[item['name']] = best_quote
            print(f"  -> Best quote for {item['quantity']}x {item['name']}: {best_quote['vendor']} (Total: {best_quote['total_price']} RMB)")
        else:
            print(f"  -> Failed to fetch quotes for {item['name']}")
    return all_quotes

# In Dify, this is another "HTTP Request Node"
def fetch_po_template():
    print("\n[Tool Node] Fetching PO Template from Database...")
    res = requests.get("http://127.0.0.1:5001/api/po-template")
    if res.status_code == 200:
        return res.json()['template']
    return ""

def run_workflow_demo(user_input):
    print("="*50)
    print("🚀 STARTING AI PROCUREMENT WORKFLOW")
    print("="*50)
    
    # 1. Extraction
    parsed_request = simulate_llm_extraction(user_input)
    
    # 2. Get Quotes
    quotes = fetch_vendor_quotations(parsed_request['items'])
    
    # Calculate actual total cost
    actual_total_cost = sum(q['total_price'] for q in quotes.values())
    print(f"\n[System] Calculated Actual Total Cost based on quotes: {actual_total_cost} RMB")
    
    # 3. IF/ELSE Decision Logic (Budget Threshold)
    # In Dify, this is the "IF/ELSE Node"
    print("\n[Decision Node] Evaluating Budget Condition...")
    if actual_total_cost < 10000:
        status = "APPROVED (Auto-Purchase Flow)"
        print("  -> Condition Met: Budget < 10,000 RMB. Proceeding to Auto-Purchase.")
    else:
        status = "PENDING_APPROVAL (Manager Review Required)"
        print(f"  -> Condition Met: Budget >= 10,000 RMB (It is {actual_total_cost}). Routing to human manager approval queue.")
    
    # 4. Generate Final Document
    # In Dify, this is an "LLM Node" or "Template Generator Node"
    print("\n[Template Node] Generating Final Document...")
    template = fetch_po_template()
    
    # Formatting item list
    item_str = "\\n".join([f"- {i['quantity']}x {i['name']} (Vendor: {quotes[i['name']]['vendor']}, Cost: {quotes[i['name']]['total_price']})" for i in parsed_request['items']])
    
    # String Replacement (Simulating LLM filling out the template)
    final_po = template.format(
        date="2026-03-15",
        po_number="PO-2026-8890",
        items=item_str,
        vendor="Multiple (See Items)",
        total_cost=actual_total_cost,
        status=status
    )
    
    print("\n✅ FINAL OUTPUT DELIVERED TO USER:")
    print(final_po)


if __name__ == "__main__":
    # Simulate a user request that triggers the Approval Flow (Expensive)
    run_workflow_demo("I need 5 MacBook Pros and 3 Dell Monitors for the new design team.")
    
    # Simulate a user request that triggers the Auto-Purchase Flow (Cheap)
    print("\n\\n" + "#"*50 + "\n\\n")
    
    def simulate_llm_extraction_cheap(user_input):
        return {
            "items": [{"name": "Dell Monitor", "quantity": 1}],
            "total_budget_mentioned": 3000
        }
    simulate_llm_extraction = simulate_llm_extraction_cheap
    run_workflow_demo("Keyboard is broken, just get me a Dell Monitor to hook up my laptop.")
